# Architecture

- `collector/` owns high-resolution records, CSV persistence, the liboqs adapter, and repeated benchmarks.
- `analyzer/` owns Welch's test, descriptive statistics, plots, and function-level localization.
- `mitigation/` owns the replaceable routine interface, software constant-work demonstration, and before/after comparison.
- `dashboard/` owns Plotly serialization, report output, and the Flask template.
- `app.py` is the application boundary; `run_experiment.py` is the repeatable CLI boundary.

The ML-KEM adapter deliberately keeps native liboqs details out of the analyzer and mitigation layers. A Raspberry Pi deployment can replace the adapter or routine implementation without changing trace schemas or report consumers.
