# How to Run the ML-KEM Timing Framework

This guide explains how to run the project on Windows using PowerShell.

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

The project uses NumPy, SciPy, Pandas, Matplotlib, Plotly, Flask, and liboqs-python.

## 4. Run a quick software test

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

## 5. Run the full software experiment

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

## 6. Start the dashboard

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

## 7. Start an experiment from the dashboard

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

## 8. Understand the generated files

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

## 9. Run real ML-KEM measurements

The ML-KEM mode uses `liboqs-python` and measures:

- Key generation
- Encapsulation
- Decapsulation

Run it with:

```powershell
.venv\Scripts\python.exe run_experiment.py --mode kem --algorithm ML-KEM-768 --samples 10000
```

The command writes ML-KEM timing traces to `data/before.csv` and `data/after.csv`.

On Windows, installing the Python package is not sufficient by itself. The native `liboqs` library also needs a C/C++ build environment, CMake, and compatible build tools. If the command reports `No oqs shared libraries found`, install the required native build tools or run this mode on the Raspberry Pi/Linux environment later.

## 10. Stop the dashboard

Go to the terminal running `app.py` and press:

```text
Ctrl+C
```

## 11. Common problems

### `ModuleNotFoundError`

Install dependencies again:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

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
