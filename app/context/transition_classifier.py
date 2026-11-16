
"""
Workflow Transition Classifier

Classifies changes between observed activities without assuming
that every application or window change represents a new task.
"""


def classify_transition(
    previous_application,
    previous_context,
    previous_task_type,
    current_application,
    current_context,
    current_task_type
):
    """
    Return the most significant observed transition.

    Window titles are intentionally excluded from this decision.
    """

    if previous_context != current_context:
        return "CONTEXT_CHANGE"

    if previous_task_type != current_task_type:
        return "TASK_CHANGE"

    if previous_application != current_application:
        return "APPLICATION_CHANGE"

    return "SAME_WORKFLOW"
