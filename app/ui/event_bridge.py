
"""
Local event bridge between the PixelBuddy monitor and UI.
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
EVENT_PATH = BASE_DIR / "data" / "pixelbuddy_event.json"


def publish_event(event_type, payload):
    EVENT_PATH.parent.mkdir(parents=True, exist_ok=True)

    event = {
        "event_type": event_type,
        "timestamp": datetime.now().isoformat(),
        "payload": payload
    }

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=EVENT_PATH.parent,
            prefix="pixelbuddy_",
            suffix=".tmp",
            delete=False
        ) as file:
            temporary_path = Path(file.name)
            json.dump(event, file, ensure_ascii=False)

        os.replace(temporary_path, EVENT_PATH)

    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def read_event():
    if not EVENT_PATH.exists():
        return None

    try:
        with EVENT_PATH.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return None


def clear_event():
    EVENT_PATH.unlink(missing_ok=True)
