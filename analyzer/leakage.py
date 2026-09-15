"""High-level leakage metrics and visualizations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .statistics import describe
from .welch import welch_test


@dataclass(frozen=True)
class LeakageResult:
    """Statistical comparison of before and after timing populations."""

    t_score: float
    p_value: float
    leakage_score: float
    significant: bool
    before_mean_ns: float
    after_mean_ns: float
    before_std_ns: float
    after_std_ns: float

    def as_dict(self) -> dict[str, float | bool]:
        return asdict(self)


class LeakageAnalyzer:
    """Analyze timing traces grouped by operation and experimental label."""

    def __init__(self, threshold: float = 4.5) -> None:
        self.threshold = threshold

    def compare(self, frame: pd.DataFrame, operation: str | None = None) -> LeakageResult:
        """Run Welch's test and report absolute t-score as leakage score."""
        selected = frame if operation is None else frame[frame["operation"] == operation]
        before = selected.loc[selected["label"] == "before", "duration_ns"]
        after = selected.loc[selected["label"] == "after", "duration_ns"]
        if before.empty or after.empty:
            raise ValueError("Both before and after samples are required")
        test = welch_test(before, after)
        before_stats = describe(before)
        after_stats = describe(after)
        score = abs(test["t_score"])
        return LeakageResult(
            t_score=test["t_score"],
            p_value=test["p_value"],
            leakage_score=score,
            significant=score >= self.threshold,
            before_mean_ns=before_stats["mean_ns"],
            after_mean_ns=after_stats["mean_ns"],
            before_std_ns=before_stats["std_ns"],
            after_std_ns=after_stats["std_ns"],
        )

    def histogram(self, frame: pd.DataFrame, destination: Path, operation: str | None = None) -> None:
        """Save an overlaid before/after timing histogram."""
        selected = frame if operation is None else frame[frame["operation"] == operation]
        figure, axis = plt.subplots(figsize=(10, 6))
        for label, color in (("before", "#c2410c"), ("after", "#0f766e")):
            values = selected.loc[selected["label"] == label, "duration_ns"]
            axis.hist(values, bins=40, alpha=0.55, label=label, color=color)
        axis.set(xlabel="Duration (ns)", ylabel="Observations", title="Timing distribution")
        axis.legend()
        figure.tight_layout()
        destination.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(destination, dpi=160)
        plt.close(figure)

    def box_plot(self, frame: pd.DataFrame, destination: Path, operation: str | None = None) -> None:
        """Save before/after box plots."""
        selected = frame if operation is None else frame[frame["operation"] == operation]
        groups = [selected.loc[selected["label"] == label, "duration_ns"] for label in ("before", "after")]
        figure, axis = plt.subplots(figsize=(8, 6))
        axis.boxplot(groups, tick_labels=["before", "after"], showfliers=False)
        axis.set(ylabel="Duration (ns)", title="Before/after timing")
        figure.tight_layout()
        destination.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(destination, dpi=160)
        plt.close(figure)
