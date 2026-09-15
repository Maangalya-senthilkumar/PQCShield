Project Title:
Timing Side-Channel Leakage Detection and Mitigation Framework for ML-KEM (CRYSTALS-Kyber) using Raspberry Pi.

For the current review, I only need a complete software implementation that later can run on Raspberry Pi. Do not use hardware-specific code yet.

The project is inspired by two papers:

1. KyberSlash: Exploiting Secret-Dependent Division Timings in Kyber Implementations.
2. Side-Channel Analysis of CRYSTALS-Kyber and A Novel Low-Cost Countermeasure.
Goal:
Create a modular framework that:

- executes ML-KEM operations,
- measures execution time,
- detects timing leakage statistically,
- localizes which operation leaks,
- applies a constant-time mitigation,
- compares before-and-after leakage,
- reports performance overhead.
Technology stack:

- Python 3.11
- liboqs-python (Open Quantum Safe)
- NumPy
- SciPy
- Pandas
- Matplotlib
- Plotly
- Flask for a lightweight dashboard.
Project structure:

kyber-timing-framework/
│
├── app.py
├── requirements.txt
├── config.py
│
├── collector/
│ ├── timer.py
│ ├── benchmark.py
│ └── traces.py
│
├── analyzer/
│ ├── welch.py
│ ├── leakage.py
│ ├── localization.py
│ └── statistics.py
│
├── mitigation/
│ ├── constant_time.py
│ ├── validator.py
│ └── comparison.py
│
├── dashboard/
│ ├── charts.py
│ ├── report.py
│ └── templates/
│
├── data/
│ ├── before.csv
│ ├── after.csv
│ └── traces/
│
└── docs/

Implementation requirements:

1. Timing Collector

- Use time.perf_counter_ns().
- Collect at least 10,000 timing samples.
- Record:

- operation name,
- start time,
- end time,
- duration in nanoseconds,
- test label (before or after).

1. ML-KEM Wrapper

- Use liboqs-python.
- Implement:

- key generation,
- encapsulation,
- decapsulation.
- Keep the API isolated so it can later be replaced with Raspberry Pi deployment.

1. Leakage Detection
Implement:

- Welch's t-test.
- Mean and standard deviation.
- Histogram plotting.
- Box plots.
- Leakage threshold highlighting.

1. Leakage Localization
Create instrumentation decorators that time individual functions.
Produce a ranked table of:

- function name,
- average execution time,
- variance,
- leakage score.

1. Mitigation Module
Create a software demonstration of replacing a variable-time routine with a constant-time implementation.
Even if the actual low-level patch is simulated, structure it so a real constant-time implementation can later replace it.
2. Validation
Automatically run:

- Before benchmark
- After benchmark
- Compare:

- t-score
- execution time
- overhead percentage.

1. Dashboard
Build a Flask dashboard showing:

- timing histogram
- before/after box plots
- leakage score
- overhead
- localization ranking.

1. Code Quality

- object-oriented where appropriate
- type hints
- docstrings
- logging
- modular architecture
- production-quality folder structure.
Generate the implementation one module at a time, starting with requirements.txt and config.py, then continue sequentially through the project.
