
def classify_transition(
    previous_application,
    previous_context,
    previous_task_type,
    current_application,
    current_context,
    current_task_type
):
    """Classify workflow transitions without relying on window titles."""

    if previous_context != current_context:
        return "CONTEXT_CHANGE"

    if previous_task_type != current_task_type:
        return "TASK_CHANGE"

    if previous_application != current_application:
        return "APPLICATION_CHANGE"

    return "SAME_WORKFLOW"


def main():
    print("Testing workflow transition rules...\n")

    tests = [
        (
            "Same application and task",
            ("chrome.exe", "Browser / Research", "Technical / Development",
             "chrome.exe", "Browser / Research", "Technical / Development"),
            "SAME_WORKFLOW",
        ),
        (
            "Different application, same workflow",
            ("chrome.exe", "Browser / Research", "Technical / Development",
             "msedge.exe", "Browser / Research", "Technical / Development"),
            "APPLICATION_CHANGE",
        ),
        (
            "Same context, different task",
            ("chrome.exe", "Browser / Research", "Technical / Development",
             "chrome.exe", "Browser / Research", "Media"),
            "TASK_CHANGE",
        ),
        (
            "Different context",
            ("Code.exe", "Development", "Technical / Development",
             "chrome.exe", "Browser / Research", "Technical / Development"),
            "CONTEXT_CHANGE",
        ),
    ]

    for name, args, expected in tests:
        actual = classify_transition(*args)
        print(f"{name}: {actual}")
        assert actual == expected, (
            f"{name}: expected {expected}, got {actual}"
        )

    print("\nAll transition rule tests passed.")


if __name__ == "__main__":
    main()

