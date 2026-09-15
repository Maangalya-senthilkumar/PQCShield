# Architecture

- `collector/` owns high-resolution records, CSV persistence, the liboqs adapter, and repeated benchmarks.
- `analyzer/` owns Welch's test, descriptive statistics, plots, and function-level localization.
- `mitigation/` owns the replaceable routine interface, software constant-work demonstration, and before/after comparison.
- `dashboard/` owns Plotly serialization, report output, and the Flask template.
- `app.py` is the application boundary; `run_experiment.py` is the repeatable CLI boundary.

`collector.MLKEMWrapper` is the hardware-independent boundary around `oqs.KeyEncapsulation`. It exposes explicit byte-oriented `keygen`, `encapsulate`, and `decapsulate` operations while keeping native liboqs details out of the analyzer and mitigation layers. `BenchmarkRunner` times those operations without changing the trace schema.

The wrapper defaults to `ML-KEM-768`, but accepts another liboqs algorithm name through configuration or the CLI. A Raspberry Pi deployment can use the same Python API and trace consumers; only the native liboqs installation and target hardware environment change.
