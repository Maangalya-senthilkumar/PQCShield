"""Welch's independent two-sample t-test."""

from __future__ import annotations

from typing import Any

from scipy.stats import ttest_ind


def welch_test(before: Any, after: Any) -> dict[str, float]:
    """Compare two timing populations without assuming equal variance."""
    result = ttest_ind(before, after, equal_var=False, nan_policy="omit")
    return {"t_score": float(result.statistic), "p_value": float(result.pvalue)}
