
"""
Task Identity and Grouping

Creates stable identifiers for desktop tasks
using application names and normalized window titles.

This module does not classify activities as
productive or distracting.
"""

import re
import unicodedata

from app.context.task_understanding import infer_task_type


def normalize_window_title(window_title):
    """
    Normalize window titles to reduce superficial
    differences between observations.
    """

    if not window_title:
        return ""

    title = unicodedata.normalize(
        "NFKC",
        str(window_title)
    )

    # Remove common leading status indicators.
    title = re.sub(
        r"^[\s●•*]+",
        "",
        title
    )

    # Normalize whitespace.
    title = re.sub(
        r"\s+",
        " ",
        title
    )

    return title.strip().casefold()


def normalize_application(application_name):
    """
    Normalize application names for comparison.
    """

    if not application_name:
        return ""

    return str(application_name).strip().casefold()


def get_task_identity(application_name, window_title):
    """
    Return a stable identity for an observed task.

    Different superficial window-title variations
    will map to the same identity.
    """

    application = normalize_application(
        application_name
    )

    window = normalize_window_title(
        window_title
    )

    if not application or not window:
        return None

    return (application, window)


def describe_task_identity(application_name, window_title):
    """
    Return structured task identity information.
    """

    identity = get_task_identity(
        application_name,
        window_title
    )

    if identity is None:
        return None

    return {
        "task_id": identity,
        "application": application_name,
        "normalized_window": identity[1],
        "task_type": infer_task_type(
            application_name,
            window_title
        )
    }


if __name__ == "__main__":
    examples = [
        (
            "Code.exe",
            "● activity_monitor.py - adaptive-edge-companion - Visual Studio Code"
        ),
        (
            "Code.exe",
            "activity_monitor.py - adaptive-edge-companion - Visual Studio Code"
        ),
        (
            "chrome.exe",
            "YouTube - Google Chrome"
        )
    ]

    for application, window in examples:
        result = describe_task_identity(
            application,
            window
        )

        print(f"\nOriginal: {window}")
        print(f"Identity: {result['task_id']}")
        print(f"Task type: {result['task_type']}")

    first = get_task_identity(*examples[0])
    second = get_task_identity(*examples[1])

    assert first == second

    print("\nPASS: Equivalent window titles share one task identity.")
