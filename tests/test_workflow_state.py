from datetime import datetime, timedelta

from app.context.workflow_state import WorkflowState


print("Testing workflow state representation...\n")

start_time = datetime.now()

state = WorkflowState(
    application="Code.exe",
    window_title=(
        "activity_monitor.py - Visual Studio Code"
    ),
    process_id=1234,
    context="Development",
    task_type="Technical / Development",
    description="Development activity",
    start_time=start_time
)

# Simulate 25 seconds of activity without waiting.
test_time = start_time + timedelta(seconds=25)

print("Current workflow state:")

for key, value in state.to_dict(test_time).items():
    print(f"{key}: {value}")

print("\nClosing workflow state...")

state.close(test_time)

print("\nClosed workflow state:")

for key, value in state.to_dict().items():
    print(f"{key}: {value}")

print("\nWorkflow state test completed.")