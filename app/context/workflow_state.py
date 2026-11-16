
"""
Workflow State Representation

Combines desktop activity, context, task understanding,
and duration into a structured workflow state.
"""

from datetime import datetime


class WorkflowState:
    """Represents the user's current workflow activity."""

    def __init__(
        self,
        application,
        window_title,
        process_id,
        context,
        task_type,
        description,
        start_time=None
    ):
        self.application = application
        self.window_title = window_title
        self.process_id = process_id
        self.context = context
        self.task_type = task_type
        self.description = description

        self.start_time = start_time or datetime.now()
        self.end_time = None

    def get_duration(self, current_time=None):
        """Return elapsed duration, freezing it after closure."""

        if self.end_time is not None:
            end_time = self.end_time
        elif current_time is not None:
            end_time = current_time
        else:
            end_time = datetime.now()

        return max(
            0.0,
            (end_time - self.start_time).total_seconds()
        )

    def close(self, end_time=None):
        """Mark the workflow activity as completed."""

        if self.end_time is None:
            self.end_time = end_time or datetime.now()

    def to_dict(self, current_time=None):
        """Return the workflow state as a dictionary."""

        return {
            "application": self.application,
            "window_title": self.window_title,
            "process_id": self.process_id,
            "context": self.context,
            "task_type": self.task_type,
            "description": self.description,
            "start_time": self.start_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "duration_seconds": round(
                self.get_duration(current_time),
                2
            ),
            "is_active": self.end_time is None
        }
