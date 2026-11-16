
from datetime import datetime, timedelta

from app.monitor.resumption_manager import (
    WorkflowResumptionManager
)


print("Testing workflow resumption duration threshold...\n")

start = datetime(2026, 10, 10, 12, 0, 0)

# Test 1: A brief interruption
manager = WorkflowResumptionManager(minimum_duration=10)

manager.start_interruption("Development", start)
manager.add_interruption_context("Media")

brief_result = manager.check_resumption(
    "Development",
    start + timedelta(seconds=5)
)

print("Five-second interruption:")
print("Resumption detected:", brief_result)

# Test 2: A sufficiently long interruption
manager.start_interruption("Development", start)
manager.add_interruption_context("Browser / Research")

long_result = manager.check_resumption(
    "Development",
    start + timedelta(seconds=15)
)

print("\nFifteen-second interruption:")
print("Resumption detected:", long_result)

assert brief_result is False
assert long_result is True

print("\nAll resumption threshold tests passed.")
