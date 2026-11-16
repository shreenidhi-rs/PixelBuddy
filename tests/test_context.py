from app.context.workflow_context import (
    classify_application,
    describe_activity
)


print("Testing workflow context...\n")


applications = [
    "Code.exe",
    "chrome.exe",
    "Spotify.exe",
    "Teams.exe",
    "unknown.exe"
]


for application in applications:

    category = classify_application(application)

    print(
        f"{application:15} → {category}"
    )


print("\nDetailed activity:")

activity = describe_activity(
    "Code.exe",
    "interruption_manager.py - Visual Studio Code"
)

print(activity)