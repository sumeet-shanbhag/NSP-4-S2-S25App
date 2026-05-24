from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, TypeVar

from app.core.failure import RandomActionFailure, should_fail
from app.core.logger import ActionLogger

T = TypeVar("T")


@dataclass
class ActionHandler:
    logger: ActionLogger
    failure_rate: float = 0.2

    def run(self, action: str, context: dict[str, Any], work: Callable[[], T]) -> T:
        try:
            if should_fail(self.failure_rate):
                raise RandomActionFailure(f"Random failure triggered for action '{action}'")

            result = work()
            self.logger.log(action=action, status="success", context=context)
            return result
        except Exception as exc:  # noqa: BLE001 - deliberate catch for centralized logging
            self.logger.log(action=action, status="error", context=context, error=str(exc))
            raise

