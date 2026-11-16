import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "workflow.db"


def initialize_database():
    """
    Create the SQLite database and required tables.
    """

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # ---------------------------------------------------------
    # Activity table
    # ---------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            application TEXT,
            window TEXT,
            process_id INTEGER,
            duration_seconds REAL DEFAULT 0
        )
    """)

    # ---------------------------------------------------------
    # Workflow session table
    # ---------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflow_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT NOT NULL,
            end_time TEXT,
            duration_seconds REAL DEFAULT 0,
            activity_count INTEGER DEFAULT 0
        )
    """)

    # ---------------------------------------------------------
    # Interruption table
    # ---------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interruptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            previous_application TEXT,
            previous_window TEXT,
            interruption_application TEXT,
            interruption_window TEXT,
            start_time TEXT NOT NULL,
            end_time TEXT,
            duration_seconds REAL DEFAULT 0,
            resumed INTEGER DEFAULT 0
        )
    """)

    connection.commit()
    connection.close()


# =============================================================
# ACTIVITY FUNCTIONS
# =============================================================

def save_activity(
    timestamp,
    application,
    window,
    process_id,
    duration_seconds=0
):
    """
    Save one activity record.
    """

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO activity (
            timestamp,
            application,
            window,
            process_id,
            duration_seconds
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        timestamp,
        application,
        window,
        process_id,
        duration_seconds
    ))

    connection.commit()
    connection.close()


def get_recent_activity(limit=10):
    """
    Retrieve recent activity records.
    """

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            timestamp,
            application,
            window,
            process_id,
            duration_seconds
        FROM activity
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    records = cursor.fetchall()

    connection.close()

    return records


# =============================================================
# WORKFLOW SESSION FUNCTIONS
# =============================================================

def create_workflow_session(start_time):
    """
    Create a new workflow session.
    Returns the session ID.
    """

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO workflow_sessions (
            start_time
        )
        VALUES (?)
    """, (start_time,))

    session_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return session_id


def close_workflow_session(
    session_id,
    end_time,
    duration_seconds,
    activity_count
):
    """
    Close an existing workflow session.
    """

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE workflow_sessions
        SET
            end_time = ?,
            duration_seconds = ?,
            activity_count = ?
        WHERE id = ?
    """, (
        end_time,
        duration_seconds,
        activity_count,
        session_id
    ))

    connection.commit()
    connection.close()


def get_recent_sessions(limit=10):
    """
    Retrieve recent workflow sessions.
    """

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            start_time,
            end_time,
            duration_seconds,
            activity_count
        FROM workflow_sessions
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    records = cursor.fetchall()

    connection.close()

    return records


# =============================================================
# INTERRUPTION FUNCTIONS
# =============================================================

def save_interruption(
    previous_activity,
    interruption_activities,
    start_time,
    end_time,
    duration_seconds,
    resumed
):
    """
    Save a continuous interruption.

    Multiple applications visited during the interruption
    are stored as a sequence.
    """

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # ---------------------------------------------------------
    # Convert interruption activities into readable sequences
    # ---------------------------------------------------------

    interruption_applications = " → ".join(
        activity[0]
        for activity in interruption_activities
    )

    interruption_windows = " → ".join(
        activity[1]
        for activity in interruption_activities
    )

    # ---------------------------------------------------------
    # Save interruption
    # ---------------------------------------------------------

    cursor.execute("""
        INSERT INTO interruptions (
            previous_application,
            previous_window,
            interruption_application,
            interruption_window,
            start_time,
            end_time,
            duration_seconds,
            resumed
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        previous_activity[0],
        previous_activity[1],
        interruption_applications,
        interruption_windows,
        start_time.strftime("%Y-%m-%d %H:%M:%S"),
        end_time.strftime("%Y-%m-%d %H:%M:%S"),
        duration_seconds,
        int(resumed)
    ))

    connection.commit()
    connection.close()


def get_recent_interruptions(limit=10):
    """
    Retrieve recent interruption records.
    """

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            previous_application,
            previous_window,
            interruption_application,
            interruption_window,
            start_time,
            end_time,
            duration_seconds,
            resumed
        FROM interruptions
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    records = cursor.fetchall()

    connection.close()

    return records