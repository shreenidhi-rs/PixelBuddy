
"""Exercise the real monitor and SQLite writers without desktop input or waits.

Run with: python -B -m unittest tests.test_workflow_integration -v
Only OS observations, the clock, sleep and console output are replaced.
"""

import contextlib
from datetime import datetime, timedelta
import io
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from app.context import workflow_state
from app.monitor import activity_monitor as monitor
from app.storage import database


CODE = ("Code.exe", "project.py - Visual Studio Code", 101)
BROWSER = ("chrome.exe", "Python tutorial", 202)
MEDIA = ("vlc.exe", "Movie", 303)
MISSING = (None, None, None)


class WorkflowIntegrationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.db_path = Path(temporary.name) / "workflow.db"
        redirect = patch.object(database, "DB_PATH", self.db_path)
        redirect.start()
        self.addCleanup(redirect.stop)
        database.initialize_database()
        self.start = datetime(2026, 10, 10, 12)

    def rows(self, table):
        with contextlib.closing(sqlite3.connect(self.db_path)) as connection:
            connection.row_factory = sqlite3.Row
            return connection.execute(
                f"SELECT * FROM {table} ORDER BY id"
            ).fetchall()

    def run_monitor(self, observations, stop_at):
        """Each observation is (seconds since start, foreground tuple)."""
        clock = [self.start]
        samples = iter(observations)
        self.states = []
        self.histories = []
        self.interruptions = []
        self.resumptions = []
        self.sessions = []

        def observe():
            try:
                seconds, activity = next(samples)
            except StopIteration:
                clock[0] = self.start + timedelta(seconds=stop_at)
                raise KeyboardInterrupt
            clock[0] = self.start + timedelta(seconds=seconds)
            return activity

        def capture(cls, instances):
            def create(*args, **kwargs):
                instance = cls(*args, **kwargs)
                instances.append(instance)
                return instance
            return create

        self.output = io.StringIO()

        with contextlib.ExitStack() as stack:
            stack.enter_context(
                patch.object(
                    monitor,
                    "get_active_window",
                    side_effect=observe
                )
            )

            mocked_clock = stack.enter_context(
                patch.object(monitor, "datetime")
            )
            mocked_clock.now.side_effect = lambda: clock[0]

            stack.enter_context(
                patch.object(monitor.time, "sleep")
            )

            for name, instances in (
                ("WorkflowState", self.states),
                ("ContextHistory", self.histories),
                ("InterruptionManager", self.interruptions),
                ("WorkflowResumptionManager", self.resumptions),
                ("WorkflowSessionManager", self.sessions),
            ):
                stack.enter_context(
                    patch.object(
                        monitor,
                        name,
                        side_effect=capture(
                            getattr(monitor, name),
                            instances
                        )
                    )
                )

            stack.enter_context(
                contextlib.redirect_stdout(self.output)
            )

            monitor.monitor_activity()

    def assert_session(self, duration, count):
        sessions = self.rows("workflow_sessions")

        self.assertEqual(len(sessions), 1)
        self.assertEqual(
            sessions[0]["start_time"],
            "2026-10-10 12:00:00"
        )
        self.assertEqual(
            sessions[0]["end_time"],
            (
                self.start + timedelta(seconds=duration)
            ).strftime("%Y-%m-%d %H:%M:%S")
        )
        self.assertEqual(
            sessions[0]["duration_seconds"],
            duration
        )
        self.assertEqual(
            sessions[0]["activity_count"],
            count
        )
        self.assertIsNone(self.sessions[0].session_id)
        self.assertEqual(
            sum(
                row["duration_seconds"]
                for row in self.rows("activity")
            ),
            duration
        )

    def test_unchanged_activity_saved_once_on_shutdown(self):
        self.run_monitor(
            [(0, CODE), (5, CODE), (10, CODE)],
            15
        )

        activities = self.rows("activity")

        self.assertEqual(len(activities), 1)
        self.assertEqual(
            tuple(activities[0])[2:],
            (*CODE, 15)
        )
        self.assert_session(15, 1)
        self.assertEqual(
            self.states[0].to_dict()["duration_seconds"],
            15
        )
        self.assertFalse(
            self.states[0].to_dict()["is_active"]
        )

    def test_title_change_retains_state_and_does_not_interrupt(self):
        renamed = (
            CODE[0],
            "other.py - Visual Studio Code",
            CODE[2]
        )

        self.run_monitor(
            [(0, CODE), (5, renamed)],
            12
        )

        self.assertEqual(
            [
                r["duration_seconds"]
                for r in self.rows("activity")
            ],
            [5, 7]
        )
        self.assertEqual(len(self.states), 1)
        self.assertEqual(
            self.histories[0].get_history(),
            ["Development"]
        )
        self.assertEqual(self.rows("interruptions"), [])
        self.assertIsNone(
            self.interruptions[0].previous_workflow
        )
        self.assertIn(
            "Transition type: SAME_WORKFLOW",
            self.output.getvalue()
        )
        self.assert_session(12, 2)

    def test_application_change_retains_workflow_state(self):
        edge = ("msedge.exe", BROWSER[1], 404)

        self.run_monitor(
            [(0, BROWSER), (5, edge)],
            12
        )

        self.assertEqual(len(self.states), 1)
        self.assertEqual(
            self.histories[0].get_history(),
            ["Browser / Research"]
        )
        self.assertIn(
            "Transition type: APPLICATION_CHANGE",
            self.output.getvalue()
        )
        self.assert_session(12, 2)

    def test_task_change_within_browser_creates_state_without_app_interruption(self):
        movie = (
            BROWSER[0],
            "Movie episode",
            BROWSER[2]
        )

        self.run_monitor(
            [(0, BROWSER), (5, movie)],
            12
        )

        self.assertEqual(
            [s.task_type for s in self.states],
            ["Technical / Development", "Media"]
        )
        self.assertEqual(
            [
                s.to_dict()["duration_seconds"]
                for s in self.states
            ],
            [5, 7]
        )
        self.assertEqual(self.rows("interruptions"), [])
        self.assertIsNone(
            self.resumptions[0].previous_context
        )
        self.assertIn(
            "Transition type: TASK_CHANGE",
            self.output.getvalue()
        )
        self.assert_session(12, 2)

    def test_resumption_threshold_and_manager_reset(self):
        for away in (5, 10, 15):
            with self.subTest(away=away):
                before = len(
                    self.rows("interruptions")
                )

                self.run_monitor(
                    [
                        (0, CODE),
                        (2, MEDIA),
                        (2 + away, CODE)
                    ],
                    4 + away
                )

                records = self.rows("interruptions")

                self.assertEqual(
                    len(records) - before,
                    int(away >= 10)
                )

                if away >= 10:
                    self.assertEqual(
                        records[-1]["previous_application"],
                        CODE[0]
                    )
                    self.assertEqual(
                        records[-1]["interruption_application"],
                        MEDIA[0]
                    )
                    self.assertEqual(
                        records[-1]["duration_seconds"],
                        away
                    )
                    self.assertEqual(
                        records[-1]["resumed"],
                        1
                    )

                self.assertIsNone(
                    self.interruptions[0].previous_workflow
                )
                self.assertIsNone(
                    self.resumptions[0].previous_context
                )
                self.assertEqual(
                    self.resumptions[0].interruption_contexts,
                    []
                )
                self.assertEqual(
                    "WORKFLOW RESUMED" in self.output.getvalue(),
                    away >= 10
                )

    def test_multi_application_interruption_and_return_to_different_window(self):
        returned = (
            CODE[0],
            "new.py - Visual Studio Code",
            505
        )

        self.run_monitor(
            [
                (0, CODE),
                (5, MEDIA),
                (10, BROWSER),
                (20, returned)
            ],
            25
        )

        records = self.rows("interruptions")

        self.assertEqual(len(records), 1)

        record = records[0]

        self.assertEqual(
            record["previous_window"],
            CODE[1]
        )
        self.assertLess(
            record["interruption_application"].index(MEDIA[0]),
            record["interruption_application"].index(BROWSER[0])
        )
        self.assertIn(
            MEDIA[1],
            record["interruption_window"]
        )
        self.assertIn(
            BROWSER[1],
            record["interruption_window"]
        )
        self.assertEqual(
            record["start_time"],
            "2026-10-10 12:00:05"
        )
        self.assertEqual(
            record["end_time"],
            "2026-10-10 12:00:20"
        )
        self.assertEqual(
            record["duration_seconds"],
            15
        )
        self.assertEqual(
            record["resumed"],
            1
        )
        self.assertEqual(
            self.histories[0].get_history(),
            [
                "Development",
                "Media",
                "Browser / Research",
                "Development"
            ]
        )
        self.assertEqual(
            [
                s.to_dict()["duration_seconds"]
                for s in self.states
            ],
            [5, 5, 10, 5]
        )
        self.assertIsNone(
            self.interruptions[0].previous_workflow
        )
        self.assertIsNone(
            self.resumptions[0].previous_context
        )
        self.assert_session(25, 4)

    def test_missing_foreground_does_not_create_activity(self):
        self.run_monitor(
            [
                (0, CODE),
                (5, MISSING),
                (10, CODE)
            ],
            15
        )

        self.assertEqual(
            len(self.rows("activity")),
            1
        )
        self.assert_session(15, 1)

    def test_shutdown_without_observations_creates_no_records(self):
        self.run_monitor(
            [(0, MISSING)],
            5
        )

        for table in (
            "activity",
            "workflow_sessions",
            "interruptions"
        ):
            self.assertEqual(
                self.rows(table),
                []
            )

        self.assertEqual(self.states, [])

    def test_initialization_preserves_existing_records(self):
        self.run_monitor(
            [(0, CODE)],
            5
        )

        before = {
            table: [
                tuple(row)
                for row in self.rows(table)
            ]
            for table in (
                "activity",
                "workflow_sessions",
                "interruptions"
            )
        }

        database.initialize_database()

        for table, records in before.items():
            self.assertEqual(
                [
                    tuple(row)
                    for row in self.rows(table)
                ],
                records
            )

    def test_unclassified_applications_can_interrupt_and_resume(self):
        first = (
            "first.exe",
            "Workspace",
            601
        )
        second = (
            "second.exe",
            "Workspace",
            602
        )

        self.run_monitor(
            [
                (0, first),
                (5, second),
                (20, first)
            ],
            25
        )

        record, = self.rows("interruptions")

        self.assertEqual(
            record["previous_application"],
            first[0]
        )
        self.assertEqual(
            record["interruption_application"],
            second[0]
        )
        self.assertEqual(
            record["duration_seconds"],
            15
        )
        self.assertEqual(
            record["resumed"],
            1
        )
        self.assertEqual(
            self.histories[0].get_history(),
            ["Other"]
        )
        self.assertEqual(len(self.states), 1)
        self.assert_session(25, 3)

    def test_brief_return_clears_all_interruption_tracking(self):
        """Verify brief interruptions leave no stale tracking data."""

        self.run_monitor(
            [
                (0, CODE),
                (2, MEDIA),
                (7, CODE)
            ],
            10
        )

        self.assertEqual(
            self.rows("interruptions"),
            []
        )
        self.assertIsNone(
            self.interruptions[0].previous_workflow
        )
        self.assertIsNone(
            self.interruptions[0].interruption_start
        )
        self.assertEqual(
            self.interruptions[0].interruption_activities,
            []
        )

    def test_closed_workflow_duration_stays_fixed_after_shutdown(self):
        """Verify closed workflow durations do not increase."""

        self.run_monitor(
            [(0, CODE)],
            5
        )

        with patch.object(
            workflow_state,
            "datetime"
        ) as clock:
            clock.now.return_value = (
                self.start + timedelta(seconds=100)
            )

            self.assertEqual(
                self.states[0].get_duration(),
                5
            )


if __name__ == "__main__":
    unittest.main()
