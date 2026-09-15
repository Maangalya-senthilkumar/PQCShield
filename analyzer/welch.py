"""Welch's independent two-sample t-test helpers."""

from __future__ import annotations

from typing import Any

from scipy.stats import ttest_ind


def welch_test(before: Any, after: Any) -> dict[str, float]:
    """Compare two timing populations without assuming equal variance.

    The returned t-score is signed; callers can use its absolute value when
    ranking the magnitude of a timing difference.
    """
    result = ttest_ind(before, after, equal_var=False, nan_policy="omit")
    t_score = float(result.statistic)
    p_value = float(result.pvalue)
    return {
        "t_score": t_score,
        "absolute_t_score": abs(t_score),
        "p_value": p_value,
    }
