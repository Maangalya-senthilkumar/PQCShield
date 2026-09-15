# ML-KEM Timing Side-Channel Framework

Software-only framework for measuring ML-KEM timing, detecting statistically significant leakage, localizing suspicious operations, and comparing a replaceable mitigation. The collector uses `time.perf_counter_ns()`, and the ML-KEM adapter uses the real Open Quantum Safe `liboqs-python` implementation.

The code is hardware-independent and can run unchanged on a Raspberry Pi once Python, the project dependencies, and the native liboqs runtime are available.

## Features

- Real ML-KEM key generation, encapsulation, and decapsulation.
- Default algorithm: `ML-KEM-768`.
- Nanosecond timing records with operation, timestamps, duration, and condition labels.
- Welch's t-test, descriptive statistics, leakage scoring, plots, and localization.
- Replaceable constant-work mitigation demonstration and overhead comparison.
- Flask dashboard for reports and visualizations.

## Project Layout

```text
app.py                  Flask dashboard entry point
config.py               Shared runtime configuration
run_experiment.py       Software and ML-KEM benchmark CLI
collector/              Timing, traces, and liboqs ML-KEM adapter
analyzer/               Statistics, leakage analysis, and localization
mitigation/             Constant-work demonstration and validation
dashboard/              Charts, reports, and Flask template
data/                   Example and generated timing traces
docs/                   Architecture and run instructions
```

## Installation

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Linux systems where the `python` alias is unavailable, use `python3` instead:

```bash
python3 -m pip install -r requirements.txt
python3 -m collector.benchmark
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

`liboqs-python` builds or locates the native Open Quantum Safe library for the target environment. A C compiler and CMake may be required when a prebuilt native package is unavailable.

## Verify Native ML-KEM

Run the guarded end-to-end self-test through the package context:

```bash
python3 -m collector.benchmark
```

Do not run `python collector/benchmark.py` directly: the module uses package-relative imports. On Linux, `python` may also be unavailable; use `python3`.

Expected output:

```text
ML-KEM self-test succeeded using ML-KEM-768
```

The test generates a real key pair, encapsulates a real shared secret, decapsulates the ciphertext, and verifies that both secrets match.

## Run Experiments

Run the software mitigation demonstration:

```bash
python3 run_experiment.py --mode software --samples 10000
```

Run real ML-KEM timing collection:

```bash
python3 run_experiment.py --mode kem --algorithm ML-KEM-768 --samples 10000
```

The ML-KEM benchmark records key generation, encapsulation, and decapsulation timings to `data/before.csv` and `data/after.csv`. The adapter is isolated in `collector/benchmark.py`; its public flow is:

```python
public_key, secret_key = wrapper.keygen()
ciphertext, sender_secret = wrapper.encapsulate(public_key)
receiver_secret = wrapper.decapsulate(ciphertext)
```

`sender_secret` and `receiver_secret` must match. The secret key is returned as raw bytes for callers that need key material; liboqs retains the active key pair for decapsulation.

## Dashboard

```bash
python3 app.py
```

Open `http://127.0.0.1:5000/`, then trigger a run with `POST /api/run`. Generated reports are written under `reports/`.

## How to Explain the Project

Use this short explanation for a project presentation:

> This project measures whether ML-KEM operations have timing differences that could reveal information about secret-dependent computation. It uses the real Open Quantum Safe implementation through `liboqs-python`, not a simulated cryptographic algorithm. The collector measures key generation, encapsulation, and decapsulation with nanosecond-resolution timers. The analyzer compares timing distributions using Welch's t-test and reports a leakage score. The mitigation part demonstrates how a variable-work routine can be replaced with a constant-work routine, then measures the performance overhead. The design keeps the cryptographic wrapper separate from the analyzer, so the same software can later run on a Raspberry Pi.

Explain the workflow in five steps:

1. Generate a real ML-KEM key pair.
2. Encapsulate a shared secret using the public key.
3. Decapsulate the ciphertext and verify both shared secrets match.
4. Collect repeated timing samples and store them in CSV files.
5. Analyze the distributions and compare leakage and overhead.

The main evidence to show is the successful self-test, the CSV timing records, the Welch t-score and leakage score, the before/after plots, and the generated report. The reported timing results depend on the operating system, CPU load, compiler, and hardware. Therefore, the results demonstrate the measurement method and software baseline; they do not by themselves prove that an implementation is or is not secure against every side-channel attack.

## Important Interpretation Note

Python-level timing is an experimental baseline, not proof of machine-level constant-time behavior. Meaningful side-channel conclusions require controlled hardware, repeated measurements, environmental controls, and constant-time native implementations for any mitigation under evaluation.

For the complete setup procedure and troubleshooting, see [docs/how_to_run.md](docs/how_to_run.md). The module boundaries are described in [docs/architecture.md](docs/architecture.md).