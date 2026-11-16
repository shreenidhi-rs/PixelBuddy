class ContextHistory:
    """
    Maintains a short history of workflow contexts.
    """

    def __init__(self, max_history=10):
        self.max_history = max_history
        self.history = []

    def add_context(self, context):
        """
        Add a workflow context to the history.

        Repeated consecutive contexts are not added.
        """

        if not context:
            return

        # Avoid duplicate consecutive contexts
        if self.history:
            if self.history[-1] == context:
                return

        self.history.append(context)

        # Keep only the most recent contexts
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def get_history(self):
        """
        Return the current workflow context history.
        """

        return self.history.copy()

    def get_previous_context(self):
        """
        Return the context immediately before the current one.
        """

        if len(self.history) < 2:
            return None

        return self.history[-2]

    def get_current_context(self):
        """
        Return the current workflow context.
        """

        if not self.history:
            return None

        return self.history[-1]

    def clear(self):
        """
        Clear the context history.
        """

        self.history.clear()