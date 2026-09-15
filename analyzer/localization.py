"""Function-level timing instrumentation and leakage ranking."""

from __future__ import annotations

import functools
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, ParamSpec, TypeVar

import numpy as np

P = ParamSpec("P")
T = TypeVar("T")


@dataclass
class _Observation:
    duration_ns: int
    label: str


class InstrumentationRegistry:
    """In-memory registry for decorated function timings."""

    def __init__(self) -> None:
        self._observations: dict[str, list[_Observation]] = defaultdict(list)

    def add(self, name: str, duration_ns: int, label: str) -> None:
        self._observations[name].append(_Observation(duration_ns, label))

    def ranking(self, threshold: float = 4.5) -> list[dict[str, float | str | bool]]:
        """Rank functions by absolute before/after mean separation."""
        rows = []
        for name, observations in self._observations.items():
            before = np.array([item.duration_ns for item in observations if item.label == "before"], dtype=float)
            after = np.array([item.duration_ns for item in observations if item.label == "after"], dtype=float)
            if before.size == 0 or after.size == 0:
                continue
            pooled = float(np.sqrt((np.var(before) + np.var(after)) / 2))
            score = abs(float(np.mean(before) - np.mean(after))) / pooled if pooled else 0.0
            rows.append({
                "function_name": name,
                "average_execution_time_ns": float(np.mean(np.concatenate((before, after)))),
                "variance_ns2": float(np.var(np.concatenate((before, after)))),
                "leakage_score": score,
                "significant": score >= threshold,
            })
        return sorted(rows, key=lambda row: float(row["leakage_score"]), reverse=True)


def timed(registry: InstrumentationRegistry, label: str) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorate a function and record its duration under ``label``."""
    def decorator(function: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(function)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_ns = time.perf_counter_ns()
            try:
                return function(*args, **kwargs)
            finally:
                registry.add(function.__qualname__, time.perf_counter_ns() - start_ns, label)
        return wrapper
    return decorator
