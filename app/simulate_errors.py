from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

CATEGORIES = [
    "RandomFailure",
    "ValidationError",
    "DatabaseError",
    "TimeoutError",
    "NetworkError",
    "UnknownError",
]

ACTIONS = [
    "refresh_data",
    "apply_filters",
    "prepare_export",
    "load_dashboard",
    "user_login",
    "user_logout",
]

ERROR_MESSAGES = [
    "Random failure triggered for action.",
    "Input validation failed.",
    "Database connection lost.",
    "Request timed out.",
    "Network unreachable.",
    "Unexpected exception occurred.",
]

LOG_FILE = Path("logs") / "app_events.log"


def random_time_within_last_hour() -> str:
    now = datetime.now(timezone.utc)
    delta = timedelta(seconds=random.randint(0, 3600))
    ts = now - delta
    return ts.isoformat()


def simulate_error_log_entry() -> dict:
    category = random.choice(CATEGORIES)
    action = random.choice(ACTIONS)
    error = random.choice(ERROR_MESSAGES)
    context = {"user": f"user{random.randint(1, 10)}"}
    return {
        "timestamp": random_time_within_last_hour(),
        "action": action,
        "status": "error",
        "category": category,
        "error": error,
        "context": context,
    }


def main():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("w", encoding="utf-8") as f:
        for _ in range(500):
            log = simulate_error_log_entry()
            f.write(json.dumps(log) + "\n")
    print(f"Wrote 500 error logs to {LOG_FILE}")


if __name__ == "__main__":
    main()

