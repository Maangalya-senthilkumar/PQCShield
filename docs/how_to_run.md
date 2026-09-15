# How to Run the ML-KEM Timing Framework

This guide explains how to run the project on Linux, macOS, or Windows. Use the command form for your operating system.

## 1. Open the project folder

Open PowerShell and run:

```powershell
cd C:\Users\maang\pqc_project
```

## 2. Create the Python environment

Run this only if `.venv` does not already exist:

```powershell
py -3.11 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use the Python executable directly in all commands:

```powershell
.venv\Scripts\python.exe
```

## 3. Install dependencies

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Use `requirements.txt` exactly. Do not add a trailing `~`; `requirements.txt~` is a different filename and will fail.

The project uses NumPy, SciPy, Pandas, Matplotlib, Plotly, Flask, and liboqs-python. `liboqs-python` provides the native Open Quantum Safe implementation used by the ML-KEM wrapper.

On Linux and macOS, the standard setup is:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Raspberry Pi, use the same commands. If the native library is built locally, install the system compiler and CMake packages first.

## 4. Verify the real ML-KEM implementation

Run the package self-test after installing dependencies:

```bash
python3 -m collector.benchmark
```

On Windows PowerShell:

```powershell
.venv\Scripts\python.exe -m collector.benchmark
```

The expected result is:

```text
ML-KEM self-test succeeded using ML-KEM-768
```

The self-test performs real key generation, encapsulation, decapsulation, and shared-secret verification. Run it as a module because `collector/benchmark.py` uses package-relative imports.

## 5. Run a quick software test

This test does not require the native liboqs library:

```powershell
.venv\Scripts\python.exe run_experiment.py --mode software --samples 20
```

Expected output has this general form:

```text
Leakage score: 18.853
Overhead: 427.75%
```

The exact numbers change between runs because operating-system timing varies.

## 6. Run the full software experiment

The project requirement is at least 10,000 timing samples:

```powershell
.venv\Scripts\python.exe run_experiment.py --mode software --samples 10000
```

This performs the following steps:

1. Measures the variable-time routine as the `before` condition.
2. Measures the constant-work routine as the `after` condition.
3. Calculates means and standard deviations.
4. Runs Welch's t-test.
5. Calculates the leakage score.
6. Calculates mitigation overhead.
7. Saves CSV files, graphs, and a JSON report.

## 7. Start the dashboard

Open a second PowerShell terminal. Keep the first terminal available for commands.

```powershell
cd C:\Users\maang\pqc_project
.venv\Scripts\python.exe app.py
```

The Flask server should show a local address. Open this address in a browser:

```text
http://127.0.0.1:5000/
```

Keep this terminal running while using the dashboard.

## 8. Start an experiment from the dashboard

Open a third PowerShell terminal and run:

```powershell
cd C:\Users\maang\pqc_project
Invoke-RestMethod -Method POST http://127.0.0.1:5000/api/run
```

Refresh the browser page:

```text
http://127.0.0.1:5000/
```

The page displays the leakage score, Welch t-score, overhead, timing histogram, timing box plot, and localization ranking.

The dashboard starts empty because it does not automatically run a long experiment when the server starts. The `POST /api/run` request starts the experiment explicitly.

## 9. Understand the generated files

After an experiment, inspect these files:

```text
data/before.csv              Before timing measurements
data/after.csv               After timing measurements
reports/report.json          Numerical analysis results
reports/timing_histogram.png Timing distribution graph
reports/timing_boxplot.png   Before/after box plot
```

Each CSV timing record contains:

```text
operation,start_ns,end_ns,duration_ns,label
```

`duration_ns` is the measured execution time in nanoseconds. `label` is either `before` or `after`.

## 10. Run real ML-KEM measurements

The ML-KEM mode uses the real `liboqs-python` implementation and measures:

- Key generation
- Encapsulation
- Decapsulation

Run it with:

```powershell
.venv\Scripts\python.exe run_experiment.py --mode kem --algorithm ML-KEM-768 --samples 10000
```

The command writes ML-KEM timing traces to `data/before.csv` and `data/after.csv`.

On Windows, installing the Python package may also require a C/C++ build environment, CMake, and compatible build tools. If the command reports `No oqs shared libraries found`, install the required native build tools. The same native dependency must be available on the Raspberry Pi target.

## 11. Stop the dashboard

Go to the terminal running `app.py` and press:

```text
Ctrl+C
```

## 12. Common problems

### `ModuleNotFoundError`

Install dependencies again:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On Linux/macOS, use `python3 -m pip install -r requirements.txt`.

### `Could not open requirements file`

Check that the command uses the exact filename:

```bash
python3 -m pip install -r requirements.txt
```

The command `python3 -m pip install -r requirements.txt~` is incorrect.

### `No oqs shared libraries found`

The Python binding cannot locate its native liboqs library. Reinstall `liboqs-python` after installing a compiler and CMake, or follow the platform-specific liboqs installation instructions for the target system.

### PowerShell refuses to activate `.venv`

Do not activate the environment. Use the full executable path:

```powershell
.venv\Scripts\python.exe run_experiment.py --mode software --samples 20
```

### The dashboard is empty

Send the API request from another terminal:

```powershell
Invoke-RestMethod -Method POST http://127.0.0.1:5000/api/run
```

Then refresh the browser.

### Port 5000 is already in use

Stop the other Flask process, or set another port before starting the application:

```powershell
$env:DASHBOARD_PORT="5001"
.venv\Scripts\python.exe app.py
```

Then open:

```text
http://127.0.0.1:5001/
```

## Important interpretation note

The software experiment demonstrates the framework and the statistical workflow. It is not a claim that the Python routine has guaranteed machine-level constant-time behavior. For a real side-channel study, the mitigated ML-KEM routine should be implemented and verified in constant-time native code, then benchmarked on controlled hardware such as the target Raspberry Pi.

## 13. Teacher Presentation Summary

Use the following sequence when explaining the project:

1. **Problem:** Secret-dependent execution time can reveal information through a timing side channel.
2. **Cryptography:** The project uses real ML-KEM-768 from Open Quantum Safe through `oqs.KeyEncapsulation`.
3. **Collection:** `collector/benchmark.py` measures key generation, encapsulation, and decapsulation with `time.perf_counter_ns()`.
4. **Analysis:** `analyzer/` calculates descriptive statistics and Welch's t-test, then assigns a leakage score and localizes suspicious operations.
5. **Mitigation:** `mitigation/` compares variable-work and constant-work software routines and calculates overhead.
6. **Deployment:** The wrapper is hardware-independent, so the same Python architecture can later be used on Raspberry Pi.
7. **Evidence:** The self-test proves that real key exchange works; CSV files, plots, and JSON reports show the timing experiment.

The most important conclusion is: **the framework provides a repeatable way to detect and study timing differences; controlled hardware experiments and constant-time native code are still required for final security conclusions.**
