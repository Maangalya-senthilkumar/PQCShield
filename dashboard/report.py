"""JSON report serialization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def save_report(report: dict[str, Any], destination: Path) -> None:
    """Write analysis output while omitting non-serializable DataFrames."""
    serializable = {key: value for key, value in report.items() if key != "traces"}
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(serializable, indent=2), encoding="utf-8")
