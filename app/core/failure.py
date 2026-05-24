from __future__ import annotations

import random


class RandomActionFailure(RuntimeError):
    """Raised when an action intentionally fails for testing resilience."""


def should_fail(failure_rate: float = 0.2, rng: random.Random | None = None) -> bool:
    if failure_rate < 0 or failure_rate > 1:
        raise ValueError("failure_rate must be between 0 and 1")

    generator = rng or random.Random()
    return generator.random() < failure_rate

