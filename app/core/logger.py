from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class ActionLogger:
    """Writes one JSON log line per app action."""

    log_file: Path

    def __post_init__(self) -> None:
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(self, action: str, status: str, context: dict[str, Any], error: str | None = None) -> None:
        if status != "error":
            return

        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "status": status,
            "context": context,
        }
        if error:
            payload["error"] = error

        with self.log_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")

