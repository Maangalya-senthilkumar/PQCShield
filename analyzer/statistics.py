"""Descriptive statistics for timing traces."""

from __future__ import annotations

from typing import Any

import numpy as np


def describe(values: Any) -> dict[str, float]:
    """Return stable descriptive statistics for a numeric sample."""
    array = np.asarray(values, dtype=float)
    if array.size == 0:
        raise ValueError("Cannot describe an empty sample")
    return {
        "count": float(array.size),
        "mean_ns": float(np.mean(array)),
        "std_ns": float(np.std(array, ddof=1)) if array.size > 1 else 0.0,
        "variance_ns2": float(np.var(array, ddof=1)) if array.size > 1 else 0.0,
        "min_ns": float(np.min(array)),
        "max_ns": float(np.max(array)),
    }
