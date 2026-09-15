"""File-based leakage analysis, reporting, and visualizations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .statistics import describe
from .welch import welch_test


LOGGER = logging.getLogger(__name__)
REQUIRED_COLUMNS = {"operation", "duration_ns"}
REPORT_COLUMNS = [
    "Operation",
    "Samples Before",
    "Samples After",
    "Mean Before",
    "Mean After",
    "Std Before",
    "Std After",
    "Variance Before",
    "Variance After",
    "t-score",
    "p-value",
    "Leakage Status",
]


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
    before_median_ns: float = 0.0
    after_median_ns: float = 0.0
    before_variance_ns2: float = 0.0
    after_variance_ns2: float = 0.0
    before_count: int = 0
    after_count: int = 0

    def as_dict(self) -> dict[str, float | bool]:
        return asdict(self)


class LeakageAnalyzer:
    """Analyze timing traces grouped by operation and experimental label."""

    def __init__(self, threshold: float = 4.5, significance_level: float = 0.05) -> None:
        self.threshold = threshold
        self.significance_level = significance_level

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
            significant=test["p_value"] < self.significance_level,
            before_mean_ns=before_stats["mean_ns"],
            after_mean_ns=after_stats["mean_ns"],
            before_std_ns=before_stats["std_ns"],
            after_std_ns=after_stats["std_ns"],
            before_median_ns=before_stats["median_ns"],
            after_median_ns=after_stats["median_ns"],
            before_variance_ns2=before_stats["variance_ns2"],
            after_variance_ns2=after_stats["variance_ns2"],
            before_count=int(before_stats["count"]),
            after_count=int(after_stats["count"]),
        )

    @staticmethod
    def load_trace(path: Path) -> pd.DataFrame:
        """Load and validate one timing CSV file."""
        frame = pd.read_csv(path)
        missing = REQUIRED_COLUMNS - set(frame.columns)
        if missing:
            raise ValueError(f"{path} is missing columns: {sorted(missing)}")
        frame = frame[["operation", "duration_ns"]].copy()
        frame["duration_ns"] = pd.to_numeric(frame["duration_ns"], errors="coerce")
        frame = frame.dropna(subset=["operation", "duration_ns"])
        if frame.empty:
            raise ValueError(f"{path} contains no valid timing samples")
        return frame

    def analyze_files(
        self,
        before_path: Path,
        after_path: Path,
        report_path: Path = Path("reports/leakage_report.csv"),
        figures_dir: Path = Path("reports/figures"),
    ) -> pd.DataFrame:
        """Analyze two trace files, save the report and operation figures."""
        before = self.load_trace(before_path)
        after = self.load_trace(after_path)
        operations = sorted(set(before["operation"]) | set(after["operation"]))
        rows: list[dict[str, object]] = []
        for operation in operations:
            before_values = before.loc[before["operation"] == operation, "duration_ns"]
            after_values = after.loc[after["operation"] == operation, "duration_ns"]
            if before_values.empty or after_values.empty:
                LOGGER.warning("Skipping %s because both conditions are required", operation)
                continue
            combined = pd.concat(
                [
                    pd.DataFrame({"operation": operation, "duration_ns": before_values, "label": "before"}),
                    pd.DataFrame({"operation": operation, "duration_ns": after_values, "label": "after"}),
                ],
                ignore_index=True,
            )
            result = self.compare(combined, operation)
            before_stats = describe(before_values)
            after_stats = describe(after_values)
            rows.append(
                {
                    "Operation": operation,
                    "Samples Before": int(before_stats["count"]),
                    "Samples After": int(after_stats["count"]),
                    "Mean Before": before_stats["mean_ns"],
                    "Mean After": after_stats["mean_ns"],
                    "Std Before": before_stats["std_ns"],
                    "Std After": after_stats["std_ns"],
                    "Variance Before": before_stats["variance_ns2"],
                    "Variance After": after_stats["variance_ns2"],
                    "t-score": result.t_score,
                    "p-value": result.p_value,
                    "Leakage Status": (
                        "Significant timing difference"
                        if result.significant
                        else "No significant leakage"
                    ),
                }
            )
            self.histogram(combined, figures_dir / f"{operation}_histogram.png", operation)
            self.box_plot(combined, figures_dir / f"{operation}_boxplot.png", operation)
            self.mean_plot(combined, figures_dir / f"{operation}_mean.png", operation)
        report = pd.DataFrame(rows, columns=REPORT_COLUMNS)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report.to_csv(report_path, index=False)
        self.print_summary(report)
        LOGGER.info("Saved leakage report to %s", report_path)
        return report

    @staticmethod
    def print_summary(report: pd.DataFrame) -> None:
        """Print a compact terminal summary of the leakage report."""
        print("Operation          t-score    p-value  Status")
        print("-" * 70)
        for _, row in report.iterrows():
            print(
                f"{str(row['Operation']):<18} {row['t-score']:>8.2f}  "
                f"{row['p-value']:>8.4g}  {row['Leakage Status']}"
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

    def mean_plot(self, frame: pd.DataFrame, destination: Path, operation: str | None = None) -> None:
        """Save a before/after mean-duration comparison bar chart."""
        selected = frame if operation is None else frame[frame["operation"] == operation]
        means = [
            selected.loc[selected["label"] == label, "duration_ns"].mean()
            for label in ("before", "after")
        ]
        figure, axis = plt.subplots(figsize=(8, 6))
        axis.bar(["before", "after"], means, color=["#c2410c", "#0f766e"])
        axis.set(ylabel="Mean duration (ns)", title="Mean timing comparison")
        figure.tight_layout()
        destination.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(destination, dpi=160)
        plt.close(figure)


def analyze_timing_files(
    before_path: Path = Path("data/before.csv"),
    after_path: Path = Path("data/after.csv"),
    report_path: Path = Path("reports/leakage_report.csv"),
    figures_dir: Path = Path("reports/figures"),
) -> pd.DataFrame:
    """Run the default file-based leakage analysis pipeline."""
    return LeakageAnalyzer().analyze_files(before_path, after_path, report_path, figures_dir)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    analyze_timing_files()
