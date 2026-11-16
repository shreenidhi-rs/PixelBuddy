"""
Task Understanding

Uses application names and window titles to infer
a broad description of the user's current activity.

This module is intentionally neutral.
It does not label activities as productive or distracting.
"""


def infer_task_type(application_name, window_title):
    """
    Infer a broad task type from the application
    and window title.
    """

    application = (
        application_name.lower()
        if application_name
        else ""
    )

    window = (
        window_title.lower()
        if window_title
        else ""
    )

    text = f"{application} {window}"

    # ---------------------------------------------------------
    # Development / Programming
    # ---------------------------------------------------------

    development_keywords = [
        "python",
        "code",
        "programming",
        "github",
        "gitlab",
        "stackoverflow",
        "stack overflow",
        "debug",
        "debugging",
        "terminal",
        "visual studio",
        "jupyter",
        "database",
        "sqlite",
        "sql"
    ]

    for keyword in development_keywords:
        if keyword in text:
            return "Technical / Development"


    # ---------------------------------------------------------
    # Documentation / Writing
    # ---------------------------------------------------------

    documentation_keywords = [
        "documentation",
        "docs",
        "report",
        "document",
        "word",
        "latex",
        "research paper",
        "paper",
        "resume"
    ]

    for keyword in documentation_keywords:
        if keyword in text:
            return "Documentation / Writing"


    # ---------------------------------------------------------
    # Research / Learning
    # ---------------------------------------------------------

    research_keywords = [
        "tutorial",
        "course",
        "lecture",
        "research",
        "study",
        "learning",
        "guide",
        "article",
        "how to"
    ]

    for keyword in research_keywords:
        if keyword in text:
            return "Research / Learning"


    # ---------------------------------------------------------
    # Communication
    # ---------------------------------------------------------

    communication_keywords = [
        "meeting",
        "chat",
        "message",
        "call",
        "teams",
        "discord",
        "whatsapp",
        "slack"
    ]

    for keyword in communication_keywords:
        if keyword in text:
            return "Communication"


    # ---------------------------------------------------------
    # Media
    # ---------------------------------------------------------

    media_keywords = [
        "spotify",
        "youtube",
        "netflix",
        "movie",
        "episode",
        "music",
        "song",
        "video",
        "film"
    ]

    for keyword in media_keywords:
        if keyword in text:
            return "Media"


    # ---------------------------------------------------------
    # Default
    # ---------------------------------------------------------

    return "General Desktop Activity"


def describe_task(application_name, window_title):
    """
    Return structured information about the
    inferred task.
    """

    task_type = infer_task_type(
        application_name,
        window_title
    )

    return {
        "application": application_name,
        "window": window_title,
        "task_type": task_type
    }