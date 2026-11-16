from app.context.task_understanding import describe_task


print("Testing task understanding...\n")


test_cases = [

    (
        "chrome.exe",
        "Python SQLite database tutorial - Google Chrome"
    ),

    (
        "chrome.exe",
        "Marvels Daredevil - Season 1 Episode 3 | kisskh"
    ),

    (
        "Code.exe",
        "activity_monitor.py - Visual Studio Code"
    ),

    (
        "chrome.exe",
        "GitHub - Adaptive Edge Companion"
    ),

    (
        "Teams.exe",
        "Project Meeting"
    )
]


for application, window in test_cases:

    result = describe_task(
        application,
        window
    )

    print(f"Application: {application}")
    print(f"Window: {window}")
    print(f"Task type: {result['task_type']}")
    print()