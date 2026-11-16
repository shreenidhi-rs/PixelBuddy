
from datetime import datetime, timedelta

from app.monitor.resumption_manager import (
    WorkflowResumptionManager
)


def main():
    print("Testing workflow resumption...\n")

    start_time = datetime(2026, 10, 10, 12, 0, 0)

    manager = WorkflowResumptionManager(
        minimum_duration=10
    )

    manager.start_interruption(
        "Development",
        start_time
    )
    manager.add_interruption_context("Media")
    manager.add_interruption_context("Browser / Research")

    print("Previous workflow: Development")
    print("Interruption contexts:", manager.interruption_contexts)

    result = manager.check_resumption(
        "Development",
        start_time + timedelta(seconds=15)
    )

    print("\nResumption detected:", result)

    assert result is True

    print("\nWorkflow resumption test passed.")


if __name__ == "__main__":
    main()
