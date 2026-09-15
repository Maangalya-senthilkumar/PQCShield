"""Timing collection and benchmark orchestration."""

from typing import TYPE_CHECKING, Any

from .timer import TimingRecord, time_operation
from .traces import load_traces, save_traces

if TYPE_CHECKING:
	from .benchmark import BenchmarkRunner, MLKEMWrapper


def __getattr__(name: str) -> Any:
	"""Load benchmark classes lazily to keep module execution warning-free."""
	if name in {"BenchmarkRunner", "MLKEMWrapper"}:
		from .benchmark import BenchmarkRunner, MLKEMWrapper

		return {"BenchmarkRunner": BenchmarkRunner, "MLKEMWrapper": MLKEMWrapper}[name]
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
	"BenchmarkRunner",
	"MLKEMWrapper",
	"TimingRecord",
	"load_traces",
	"save_traces",
	"time_operation",
]
