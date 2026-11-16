
"""
Task Recommendation Engine

Ranks previously observed desktop tasks using
recency, duration, and frequency.

Uses normalized task identities to group
equivalent window titles.
"""

from collections import defaultdict
from datetime import datetime, timedelta
import math

from app.storage.database import get_recent_activity
from app.intelligence.task_identity import get_task_identity
from app.context.task_understanding import infer_task_type


class TaskRanker:
    def __init__(
        self,
        recency_weight=0.5,
        duration_weight=0.3,
        frequency_weight=0.2,
        recency_half_life_hours=24
    ):
        if recency_half_life_hours <= 0:
            raise ValueError(
                "recency_half_life_hours must be positive"
            )

        if any(
            weight < 0
            for weight in (
                recency_weight,
                duration_weight,
                frequency_weight
            )
        ):
            raise ValueError("Weights cannot be negative")

        total_weight = (
            recency_weight
            + duration_weight
            + frequency_weight
        )

        if total_weight <= 0:
            raise ValueError(
                "At least one ranking weight must be positive"
            )

        self.recency_weight = recency_weight / total_weight
        self.duration_weight = duration_weight / total_weight
        self.frequency_weight = frequency_weight / total_weight
        self.recency_half_life_hours = recency_half_life_hours

    def rank_tasks(self, limit=5, history_limit=500, now=None):
        """
        Rank tasks using recorded desktop activity.

        Equivalent window titles are grouped together.
        """

        if limit <= 0 or history_limit <= 0:
            return []

        now = now or datetime.now()
        activities = get_recent_activity(history_limit)

        tasks = defaultdict(
            lambda: {
                "application": "",
                "window": "",
                "task_id": None,
                "task_type": "",
                "total_duration": 0.0,
                "frequency": 0,
                "last_seen": None
            }
        )

        for record in activities:
            timestamp, application, window, process_id, duration = record

            task_id = get_task_identity(
                application,
                window
            )

            if task_id is None:
                continue

            try:
                observed_at = datetime.strptime(
                    timestamp,
                    "%Y-%m-%d %H:%M:%S"
                )
                duration_seconds = max(
                    0.0,
                    float(duration or 0)
                )
            except (TypeError, ValueError, OverflowError):
                continue

            task = tasks[task_id]

            task["task_id"] = task_id
            task["total_duration"] += duration_seconds
            task["frequency"] += 1

            # Prefer the latest observation as the
            # representative window title.
            if (
                task["last_seen"] is None
                or observed_at > task["last_seen"]
            ):
                task["application"] = application
                task["window"] = window
                task["task_type"] = infer_task_type(
                    application,
                    window
                )
                task["last_seen"] = observed_at

        if not tasks:
            return []

        max_duration = max(
            task["total_duration"]
            for task in tasks.values()
        )

        max_frequency = max(
            task["frequency"]
            for task in tasks.values()
        )

        recommendations = []

        for task in tasks.values():
            elapsed_hours = max(
                0.0,
                (
                    now - task["last_seen"]
                ).total_seconds() / 3600
            )

            recency_score = math.exp(
                -math.log(2)
                * elapsed_hours
                / self.recency_half_life_hours
            )

            duration_score = (
                math.log1p(task["total_duration"])
                / math.log1p(max_duration)
                if max_duration > 0
                else 0.0
            )

            frequency_score = (
                task["frequency"] / max_frequency
                if max_frequency > 0
                else 0.0
            )

            final_score = (
                self.recency_weight * recency_score
                + self.duration_weight * duration_score
                + self.frequency_weight * frequency_score
            )

            recommendations.append({
                "task_id": task["task_id"],
                "application": task["application"],
                "window": task["window"],
                "task_type": task["task_type"],
                "total_duration_seconds": round(
                    task["total_duration"], 2
                ),
                "frequency": task["frequency"],
                "last_seen": task["last_seen"].strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "recency_score": round(
                    recency_score, 4
                ),
                "duration_score": round(
                    duration_score, 4
                ),
                "frequency_score": round(
                    frequency_score, 4
                ),
                "score": round(final_score, 4)
            })

        recommendations.sort(
            key=lambda task: (
                -task["score"],
                -task["frequency"],
                task["task_id"]
            )
        )

        return recommendations[:limit]


if __name__ == "__main__":
    ranker = TaskRanker()

    print("=" * 60)
    print("PIXELBUDDY - TASK RECOMMENDATIONS")
    print("=" * 60)

    recommendations = ranker.rank_tasks(limit=5)

    if not recommendations:
        print("No recorded tasks available yet.")

    for index, task in enumerate(
        recommendations,
        start=1
    ):
        print(f"\n{index}. {task['window']}")
        print(f"   Application: {task['application']}")
        print(f"   Task type: {task['task_type']}")
        print(f"   Score: {task['score']:.4f}")
        print(f"   Frequency: {task['frequency']}")
        print(
            f"   Total duration: "
            f"{task['total_duration_seconds']:.1f} seconds"
        )
        print(f"   Last seen: {task['last_seen']}")
