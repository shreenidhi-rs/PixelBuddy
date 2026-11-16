from app.storage.database import save_interruption


class InterruptionManager:
    """
    Tracks a continuous interruption between a workflow
    application and its eventual resumption.
    """

    def __init__(self, minimum_duration=10):
        self.minimum_duration = minimum_duration

        self.previous_workflow = None
        self.interruption_start = None
        self.interruption_activities = []

    def start_interruption(
        self,
        previous_activity,
        interruption_activity,
        start_time
    ):
        """
        Start tracking a possible interruption.
        """

        self.previous_workflow = previous_activity
        self.interruption_start = start_time

        self.interruption_activities = [
            interruption_activity
        ]

    def add_interruption_activity(self, activity):
        """
        Add an application visited during the interruption.

        Activities are stored at application level so that
        multiple windows/tabs of the same application are
        treated as one interruption application.
        """

        # Do not add the same application repeatedly
        # when only the window changes.
        for existing_activity in self.interruption_activities:

            if existing_activity[0] == activity[0]:
                return

        self.interruption_activities.append(activity)

    def check_resumption(
        self,
        current_activity,
        current_time
    ):
        """
        Check whether the original workflow application
        has resumed.

        Resumption is based on the application/process name,
        not the exact window title.
        """

        if self.previous_workflow is None:
            return False

        # Check application/process only
        if current_activity[0] != self.previous_workflow[0]:
            return False

        duration = (
            current_time - self.interruption_start
        ).total_seconds()

        # Ignore very short interruptions
        if duration < self.minimum_duration:
            self.reset()
            return False

        save_interruption(
            self.previous_workflow,
            self.interruption_activities,
            self.interruption_start,
            current_time,
            duration,
            True
        )

        interruption_apps = " → ".join(
            activity[0]
            for activity in self.interruption_activities
        )

        print(
            f"    INTERRUPTION DETECTED → "
            f"{self.previous_workflow[0]} → "
            f"{interruption_apps} → RESUMED"
        )

        print(
            f"    Interruption duration: "
            f"{duration:.1f} seconds"
        )

        self.reset()

        return True

    def reset(self):
        """
        Reset interruption tracking.
        """

        self.previous_workflow = None
        self.interruption_start = None
        self.interruption_activities = []