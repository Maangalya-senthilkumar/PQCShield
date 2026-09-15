"""Replaceable constant-time routine boundary.

Python itself cannot guarantee machine-level constant-time execution. This module
therefore demonstrates the algorithmic shape and exposes a boundary where a
verified C/Rust implementation can later be injected.
"""

from __future__ import annotations

from typing import Protocol


class IntegerRoutine(Protocol):
    """Interface implemented by variable-time and mitigated routines."""

    def process(self, secret: int) -> int:
        ...


class VariableTimeRoutine:
    """Intentionally variable-work routine used as a teaching baseline."""

    def process(self, secret: int) -> int:
        result = 0
        for _ in range(max(1, secret & 0xFF)):
            result = (result * 33 + secret) % 65537
        return result


class ConstantTimeRoutine:
    """Fixed-iteration replacement suitable for native constant-time hardening."""

    ITERATIONS = 256

    def process(self, secret: int) -> int:
        result = 0
        for index in range(self.ITERATIONS):
            mask = -int(index < (secret & 0xFF))
            candidate = (result * 33 + secret + index) % 65537
            result = (candidate & mask) | (result & ~mask)
        return result


def process_with_routine(routine: IntegerRoutine, secret: int) -> int:
    """Call the replaceable routine through a stable application API."""
    return routine.process(secret)
