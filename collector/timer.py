"""High-resolution timing primitives."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Any, Callable, TypeVar


T = TypeVar("T")


@dataclass(frozen=True)
class TimingRecord:
    """A single operation timing observation."""

    operation: str
    start_ns: int
    end_ns: int
    duration_ns: int
    label: str

    def as_dict(self) -> dict[str, Any]:
        """Return a CSV/DataFrame-friendly representation."""
        return asdict(self)


def time_operation(
    operation: str,
    label: str,
    function: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> tuple[T, TimingRecord]:
    """Execute ``function`` and measure it with ``perf_counter_ns``."""
    start_ns = time.perf_counter_ns()
    result = function(*args, **kwargs)
    end_ns = time.perf_counter_ns()
    return result, TimingRecord(
        operation=operation,
        start_ns=start_ns,
        end_ns=end_ns,
        duration_ns=end_ns - start_ns,
        label=label,
    )
