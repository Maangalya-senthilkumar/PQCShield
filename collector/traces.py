"""Persistence helpers for timing traces."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from .timer import TimingRecord


TRACE_COLUMNS = ["operation", "start_ns", "end_ns", "duration_ns", "label"]


def save_traces(records: Iterable[TimingRecord], destination: Path) -> pd.DataFrame:
    """Write records to CSV and return the normalized DataFrame."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame([record.as_dict() for record in records], columns=TRACE_COLUMNS)
    frame.to_csv(destination, index=False)
    return frame


def load_traces(source: Path) -> pd.DataFrame:
    """Load and validate a trace CSV."""
    frame = pd.read_csv(source)
    missing = set(TRACE_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Trace file is missing columns: {sorted(missing)}")
    return frame[TRACE_COLUMNS]
