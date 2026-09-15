"""Validation benchmark for the mitigation demonstration."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from analyzer.localization import InstrumentationRegistry
from collector.timer import TimingRecord, time_operation

from .constant_time import (
    ConstantTimeRoutine,
    IntegerRoutine,
    VariableTimeRoutine,
    process_with_routine,
)


@dataclass
class MitigationValidator:
    """Collect comparable traces for a routine over controlled secret classes."""

    sample_count: int = 10_000
    registry: InstrumentationRegistry = field(default_factory=InstrumentationRegistry)

    def collect(self, routine: IntegerRoutine, label: str) -> list[TimingRecord]:
        """Measure the routine for alternating low/high secret values."""
        records = []
        for index in range(self.sample_count):
            secret = 8 if index % 2 == 0 else 248
            _, record = time_operation(
                "secret_dependent_routine", label, process_with_routine, routine, secret
            )
            records.append(record)
            self.registry.add(f"{routine.__class__.__name__}.process", record.duration_ns, label)
        return records

    def run(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Return before and after DataFrames for the variable/fixed routines."""
        before = self.collect(VariableTimeRoutine(), "before")
        after = self.collect(ConstantTimeRoutine(), "after")
        return pd.DataFrame([record.as_dict() for record in before]), pd.DataFrame(
            [record.as_dict() for record in after]
        )
