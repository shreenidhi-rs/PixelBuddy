from datetime import datetime

from app.storage.database import (
    create_workflow_session,
    close_workflow_session
)


class WorkflowSessionManager:
    """
    Manages the beginning and end of workflow sessions.
    """

    def __init__(self):
        self.session_id = None
        self.session_start = None
        self.activity_count = 0

    def start_session(self, start_time):
        """
        Start a new workflow session.
        """

        self.session_start = start_time
        self.session_id = create_workflow_session(
            start_time.strftime("%Y-%m-%d %H:%M:%S")
        )

        self.activity_count = 1

        print(
            f"    Workflow session started "
            f"(ID: {self.session_id})"
        )

    def add_activity(self):
        """
        Increase the number of activities
        belonging to the current session.
        """

        self.activity_count += 1

    def end_session(self, end_time):
        """
        Close the current workflow session.
        """

        if self.session_id is None:
            return

        duration = (
            end_time - self.session_start
        ).total_seconds()

        close_workflow_session(
            self.session_id,
            end_time.strftime("%Y-%m-%d %H:%M:%S"),
            duration,
            self.activity_count
        )

        print(
            f"    Workflow session ended "
            f"(ID: {self.session_id})"
        )

        print(
            f"    Session duration: "
            f"{duration:.1f} seconds"
        )

        print(
            f"    Activities in session: "
            f"{self.activity_count}"
        )

        self.session_id = None
        self.session_start = None
        self.activity_count = 0