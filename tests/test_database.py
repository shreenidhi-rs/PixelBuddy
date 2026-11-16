from app.storage.database import get_recent_activity


records = get_recent_activity(10)

print("\nRecent activity:")
print("-" * 80)

for record in records:
    print(record)