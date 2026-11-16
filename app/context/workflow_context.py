"""
Workflow Context Understanding

Classifies desktop applications into broad,
work-agnostic workflow categories.

The system describes activity without assuming
that any particular application is a distraction.
"""


# =============================================================
# APPLICATION CATEGORIES
# =============================================================

APPLICATION_CATEGORIES = {

    "Development": [
        "Code.exe",
        "devenv.exe",
        "pycharm64.exe",
        "idea64.exe",
        "eclipse.exe",
        "notepad++.exe"
    ],

    "Browser / Research": [
        "chrome.exe",
        "msedge.exe",
        "firefox.exe",
        "brave.exe",
        "opera.exe"
    ],

    "Communication": [
        "Teams.exe",
        "ms-teams.exe",
        "slack.exe",
        "discord.exe",
        "WhatsApp.exe"
    ],

    "Media": [
        "Spotify.exe",
        "vlc.exe",
        "wmplayer.exe"
    ]
}


# =============================================================
# APPLICATION CLASSIFICATION
# =============================================================

def classify_application(application_name):
    """
    Classify an application into a broad workflow category.

    The classification describes the type of activity
    associated with an application. It does not determine
    whether the activity is productive or distracting.
    """

    if not application_name:
        return "Other"

    application_name = application_name.lower()

    for category, applications in APPLICATION_CATEGORIES.items():

        for application in applications:

            if application.lower() == application_name:
                return category

    return "Other"


# =============================================================
# ACTIVITY DESCRIPTION
# =============================================================

def describe_activity(application_name, window_title=""):
    """
    Generate a neutral human-readable description
    of the current desktop activity.
    """

    category = classify_application(application_name)

    if category == "Development":
        description = "Development activity"

    elif category == "Browser / Research":
        description = "Browser / research activity"

    elif category == "Communication":
        description = "Communication activity"

    elif category == "Media":
        description = "Media activity"

    else:
        description = "Other desktop activity"

    return {
        "application": application_name,
        "window": window_title,
        "category": category,
        "description": description
    }