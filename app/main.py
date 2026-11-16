from app.monitor.activity_monitor import monitor_activity
from app.storage.database import initialize_database


if __name__ == "__main__":

    initialize_database()

    monitor_activity()