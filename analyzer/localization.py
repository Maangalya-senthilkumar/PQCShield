"""Hierarchical timing localization for ML-KEM operation regions.

The software baseline instruments only explicit calls at the Python ML-KEM
adapter boundary. These regions are not claims about hidden functions inside
the native liboqs implementation. A future native instrumentor can implement
the same ``RegionInstrumentor`` interface and provide finer-grained C-level
regions without changing the reporting layer.
"""

from __future__ import annotations

import abc
import functools
import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, ParamSpec, TypeVar

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from collector.benchmark import MLKEMWrapper


LOGGER = logging.getLogger(__name__)
REPORT_COLUMNS = [
    "Rank",
    "Operation",
    "Region",
    "Samples",
    "Mean_ns",
    "Std_ns",
    "Variance_ns",
    "CV",
    "Leakage_Score",
]

P = ParamSpec("P")
T = TypeVar("T")


@dataclass(frozen=True)
class TimingRegion:
    """Descriptive timing statistics for one instrumented region."""

    operation_name: str
    region_name: str
    sample_count: int
    mean_ns: float
    std_ns: float
    variance_ns: float
    min_ns: float
    max_ns: float


@dataclass(frozen=True)
class LocalizationResult:
    """Ranked, non-cryptographic variability result for one region."""

    operation: str
    region: str
    mean_timing: float
    variance: float
    coefficient_of_variation: float
    leakage_score: float
    rank: int


@dataclass(frozen=True)
class RegionSample:
    """One observation emitted by a region instrumentor."""

    operation: str
    region: str
    duration_ns: int
    label: str


class RegionInstrumentor(abc.ABC):
    """Interface for software or future native region instrumentors."""

    @abc.abstractmethod
    def collect(self, label: str, sample_count: int) -> list[RegionSample]:
        """Collect region observations for one experimental condition."""


class SoftwareBaselineInstrumentor(RegionInstrumentor):
    """Time explicit Python adapter-call boundaries around real ML-KEM.

    The regions are intentionally coarse: ``wrapper_keygen``,
    ``wrapper_encapsulation``, and ``wrapper_decapsulation``. They measure the
    complete Python-to-liboqs call boundary and do not identify hidden native
    liboqs functions. Native C instrumentation can later replace this class.
    """

    def __init__(self, algorithm: str = "ML-KEM-768") -> None:
        self.algorithm = algorithm

    def collect(self, label: str, sample_count: int) -> list[RegionSample]:
        """Collect real ML-KEM timings for each explicit wrapper region."""
        if sample_count < 1:
            raise ValueError("sample_count must be positive")

        wrapper = MLKEMWrapper(self.algorithm)
        observations: list[RegionSample] = []
        try:
            for sample_index in range(sample_count):
                start_ns = time.perf_counter_ns()
                public_key, _ = wrapper.keygen()
                observations.append(
                    RegionSample("key_generation", "wrapper_keygen", time.perf_counter_ns() - start_ns, label)
                )

                start_ns = time.perf_counter_ns()
                ciphertext, _ = wrapper.encapsulate(public_key)
                observations.append(
                    RegionSample(
                        "encapsulation",
                        "wrapper_encapsulation",
                        time.perf_counter_ns() - start_ns,
                        label,
                    )
                )

                start_ns = time.perf_counter_ns()
                wrapper.decapsulate(ciphertext)
                observations.append(
                    RegionSample(
                        "decapsulation",
                        "wrapper_decapsulation",
                        time.perf_counter_ns() - start_ns,
                        label,
                    )
                )

                if (sample_index + 1) % 1000 == 0:
                    LOGGER.info("Localized %d/%d samples for %s", sample_index + 1, sample_count, label)
        finally:
            wrapper.close()
        return observations


def _timing_region(operation: str, region: str, values: np.ndarray) -> TimingRegion:
    """Build a timing summary from a non-empty numeric sample."""
    if values.size == 0:
        raise ValueError(f"Region {operation}/{region} has no samples")
    variance = float(np.var(values, ddof=1)) if values.size > 1 else 0.0
    return TimingRegion(
        operation_name=operation,
        region_name=region,
        sample_count=int(values.size),
        mean_ns=float(np.mean(values)),
        std_ns=float(np.std(values, ddof=1)) if values.size > 1 else 0.0,
        variance_ns=variance,
        min_ns=float(np.min(values)),
        max_ns=float(np.max(values)),
    )


def _localization_results(regions: list[TimingRegion]) -> list[LocalizationResult]:
    """Rank regions by normalized timing variability.

    ``Leakage_Score`` is a software triage metric, not a cryptographic leakage
    proof. It is the average of variance and coefficient of variation after
    each is normalized by the maximum observed value among these regions.
    """
    if not regions:
        return []
    max_variance = max(region.variance_ns for region in regions)
    max_cv = max(
        (region.std_ns / region.mean_ns) if region.mean_ns else 0.0
        for region in regions
    )
    scored: list[tuple[TimingRegion, float, float]] = []
    for region in regions:
        cv = region.std_ns / region.mean_ns if region.mean_ns else 0.0
        normalized_variance = region.variance_ns / max_variance if max_variance else 0.0
        normalized_cv = cv / max_cv if max_cv else 0.0
        scored.append((region, cv, (normalized_variance + normalized_cv) / 2.0))
    scored.sort(key=lambda item: item[2], reverse=True)
    return [
        LocalizationResult(
            operation=region.operation_name,
            region=region.region_name,
            mean_timing=region.mean_ns,
            variance=region.variance_ns,
            coefficient_of_variation=cv,
            leakage_score=score,
            rank=index,
        )
        for index, (region, cv, score) in enumerate(scored, start=1)
    ]


def localize(
    sample_count: int = 1000,
    algorithm: str = "ML-KEM-768",
    report_path: Path = Path("reports/localization_report.csv"),
    figure_path: Path = Path("reports/figures/localization_ranking.png"),
) -> pd.DataFrame:
    """Run both conditions, rank regions, and write the localization outputs."""
    instrumentor = SoftwareBaselineInstrumentor(algorithm)
    samples = instrumentor.collect("before", sample_count)
    samples.extend(instrumentor.collect("after", sample_count))
    frame = pd.DataFrame([sample.__dict__ for sample in samples])
    regions: list[TimingRegion] = []
    for (operation, region), group in frame.groupby(["operation", "region"]):
        regions.append(_timing_region(operation, region, group["duration_ns"].to_numpy(dtype=float)))
    results = _localization_results(regions)
    report = pd.DataFrame(
        [
            {
                "Rank": result.rank,
                "Operation": result.operation,
                "Region": result.region,
                "Samples": next(
                    region.sample_count
                    for region in regions
                    if region.operation_name == result.operation and region.region_name == result.region
                ),
                "Mean_ns": result.mean_timing,
                "Std_ns": next(
                    region.std_ns
                    for region in regions
                    if region.operation_name == result.operation and region.region_name == result.region
                ),
                "Variance_ns": result.variance,
                "CV": result.coefficient_of_variation,
                "Leakage_Score": result.leakage_score,
            }
            for result in results
        ],
        columns=REPORT_COLUMNS,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(report_path, index=False)
    _save_ranking_chart(report, figure_path)
    _print_summary(report)
    LOGGER.info("Saved localization report to %s", report_path)
    return report


def _save_ranking_chart(report: pd.DataFrame, destination: Path) -> None:
    """Save the ranked software-baseline variability chart."""
    figure, axis = plt.subplots(figsize=(10, 6))
    labels = [f"{row.Operation}/{row.Region}" for row in report.itertuples()]
    axis.barh(labels[::-1], report["Leakage_Score"].to_numpy()[::-1], color="#0f766e")
    axis.set(xlabel="Normalized timing variability score", title="Hierarchical region ranking")
    figure.tight_layout()
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination, dpi=160)
    plt.close(figure)


def _print_summary(report: pd.DataFrame) -> None:
    """Print a compact ranking summary."""
    print("Rank  Operation        Region                  Mean_ns    CV       Score")
    print("-" * 78)
    for row in report.itertuples(index=False):
        print(
            f"{row.Rank:>4}  {row.Operation:<16} {row.Region:<24} "
            f"{row.Mean_ns:>8.2f}  {row.CV:>7.4f}  {row.Leakage_Score:>7.4f}"
        )


@dataclass
class _Observation:
    duration_ns: int
    label: str


class InstrumentationRegistry:
    """Backward-compatible registry for decorated Python functions."""

    def __init__(self) -> None:
        self._observations: dict[str, list[_Observation]] = defaultdict(list)

    def add(self, name: str, duration_ns: int, label: str) -> None:
        """Store one decorated-function timing observation."""
        self._observations[name].append(_Observation(duration_ns, label))

    def ranking(self, threshold: float = 4.5) -> list[dict[str, float | str | bool]]:
        """Rank decorated functions by absolute before/after mean separation."""
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


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    localize()
