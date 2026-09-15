"""Central configuration for the ML-KEM timing leakage framework."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class FrameworkConfig:
    """Runtime settings shared by collection, analysis, and reporting."""

    project_root: Path = PROJECT_ROOT
    data_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data")
    traces_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "traces")
    before_csv: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "before.csv")
    after_csv: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "after.csv")
    reports_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "reports")
    algorithm: str = field(default_factory=lambda: os.getenv("MLKEM_ALGORITHM", "ML-KEM-768"))
    sample_count: int = field(
        default_factory=lambda: int(os.getenv("TIMING_SAMPLE_COUNT", "10000"))
    )
    leakage_threshold: float = field(
        default_factory=lambda: float(os.getenv("LEAKAGE_THRESHOLD", "4.5"))
    )
    random_seed: int = field(default_factory=lambda: int(os.getenv("TIMING_RANDOM_SEED", "2026")))
    dashboard_host: str = field(default_factory=lambda: os.getenv("DASHBOARD_HOST", "127.0.0.1"))
    dashboard_port: int = field(
        default_factory=lambda: int(os.getenv("DASHBOARD_PORT", "5000"))
    )

    def ensure_directories(self) -> None:
        """Create directories required for benchmark output and reports."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.traces_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)


CONFIG = FrameworkConfig()
