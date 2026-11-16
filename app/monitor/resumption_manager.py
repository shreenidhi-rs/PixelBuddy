
from datetime import datetime


class WorkflowResumptionManager:
    """
    Detects workflow resumption after a meaningful interruption.

    The duration threshold is neutral: no application is
    automatically classified as a distraction.
    """

    def __init__(self, minimum_duration=10):
        self.minimum_duration = minimum_duration
        self.previous_context = None
        self.interruption_contexts = []
        self.interruption_start = None

    def start_interruption(
        self,
        previous_context,
        start_time=None
    ):
        """Begin tracking an interruption."""

        self.previous_context = previous_context
        self.interruption_contexts = []
        self.interruption_start = start_time or datetime.now()

    def add_interruption_context(self, context):
        """Record a context encountered during interruption."""

        if not context:
            return

        if (
            not self.interruption_contexts
            or self.interruption_contexts[-1] != context
        ):
            self.interruption_contexts.append(context)

    def check_resumption(
        self,
        current_context,
        current_time=None
    ):
        """Confirm resumption only after the duration threshold."""

        if self.previous_context is None:
            return False

        if current_context != self.previous_context:
            return False

        if not self.interruption_contexts:
            return False

        now = current_time or datetime.now()

        duration = (
            now - self.interruption_start
        ).total_seconds()

        if duration < self.minimum_duration:
            # Too brief to count as a meaningful interruption.
            self.reset()
            return False

        print(
            f"    WORKFLOW RESUMED → "
            f"{self.previous_context}"
        )

        print(
            f"    Interruption contexts: "
            f"{' → '.join(self.interruption_contexts)}"
        )

        print(
            f"    Context interruption duration: "
            f"{duration:.1f} seconds"
        )

        self.reset()
        return True

    def reset(self):
        """Clear interruption tracking."""

        self.previous_context = None
        self.interruption_contexts = []
        self.interruption_start = None
