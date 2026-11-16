from app.storage.database import get_recent_sessions


sessions = get_recent_sessions(10)

print("\nRecent workflow sessions:")
print("-" * 80)

for session in sessions:
    print(session)