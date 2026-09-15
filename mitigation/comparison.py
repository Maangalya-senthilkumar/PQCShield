"""Before/after performance and leakage comparison."""

from __future__ import annotations

from typing import Any

import pandas as pd

from analyzer.leakage import LeakageAnalyzer


def compare_runs(
    before: pd.DataFrame,
    after: pd.DataFrame,
    threshold: float = 4.5,
) -> dict[str, Any]:
    """Combine traces, compare leakage, and calculate execution overhead."""
    before_frame = before.copy()
    after_frame = after.copy()
    before_frame["label"] = "before"
    after_frame["label"] = "after"
    combined = pd.concat([before_frame, after_frame], ignore_index=True)
    analysis = LeakageAnalyzer(threshold).compare(combined)
    before_mean = float(before_frame["duration_ns"].mean())
    after_mean = float(after_frame["duration_ns"].mean())
    overhead = ((after_mean - before_mean) / before_mean * 100.0) if before_mean else 0.0
    return {
        "analysis": analysis.as_dict(),
        "before_mean_ns": before_mean,
        "after_mean_ns": after_mean,
        "overhead_percent": overhead,
        "traces": combined,
    }
