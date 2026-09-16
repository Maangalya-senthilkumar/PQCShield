# Running PQCShield with Docker

This guide builds a reproducible Linux container for the existing PQCShield workflow. The image installs the Python dependencies from `requirements.txt`, including `liboqs-python`, and compiles or uses the native liboqs runtime required by the binding.

## 1. Prerequisites

Install Docker Engine or Docker Desktop and confirm that the daemon is running:

```bash
docker --version
docker info
```

The host does not need a Python virtual environment for the container workflow. Docker needs network access during the image build so it can download the base image and Python packages.

## 2. Build the image

Run this command from the project root:

```bash
docker build -t pqcshield:latest .
```

The first build can take several minutes because `liboqs-python` may build native liboqs components. Later builds reuse Docker's build cache when the dependency files are unchanged.

## 3. Run a shell or module

The image defaults to the ML-KEM self-test. To run it explicitly and preserve generated files on the host, mount the project data and report directories:

```bash
docker run --rm \
  -v "$PWD/data:/app/data" \
  -v "$PWD/reports:/app/reports" \
  pqcshield:latest \
  python3 -m collector.benchmark
```

The container runs as the non-root `pqcshield` user. The mounted directories must be writable by that container user on systems that enforce host ownership permissions.

## 4. Run the ML-KEM self-test

```bash
docker run --rm pqcshield:latest python3 -m collector.benchmark
```

Expected output includes:

```text
ML-KEM self-test succeeded using ML-KEM-768
```

This performs real ML-KEM key generation, encapsulation, decapsulation, and shared-secret verification through `oqs.KeyEncapsulation`.

## 5. Run the timing experiment

For a quick smoke run:

```bash
docker run --rm \
  -v "$PWD/data:/app/data" \
  -v "$PWD/reports:/app/reports" \
  pqcshield:latest \
  python3 run_experiment.py --mode kem --algorithm ML-KEM-768 --samples 20
```

For the project-scale run:

```bash
docker run --rm \
  -v "$PWD/data:/app/data" \
  -v "$PWD/reports:/app/reports" \
  pqcshield:latest \
  python3 run_experiment.py --mode kem --algorithm ML-KEM-768 --samples 10000
```

This records key-generation, encapsulation, and decapsulation timings in `data/before.csv` and `data/after.csv` on the host.

## 6. Run leakage analysis and localization

Analyze the mounted timing CSV files:

```bash
docker run --rm \
  -v "$PWD/data:/app/data" \
  -v "$PWD/reports:/app/reports" \
  pqcshield:latest \
  python3 -m analyzer.leakage
```

Run hierarchical localization using real ML-KEM wrapper calls:

```bash
docker run --rm \
  -v "$PWD/data:/app/data" \
  -v "$PWD/reports:/app/reports" \
  pqcshield:latest \
  python3 -m analyzer.localization
```

The localization baseline measures explicit Python wrapper boundaries only. It does not claim to identify hidden internal liboqs C functions. Native instrumentation can replace the instrumentor later without changing the reporting interface.

## 7. Generated reports

When `data/` and `reports/` are mounted, outputs remain on the host:

- `reports/leakage_report.csv`
- `reports/figures/*_histogram.png`
- `reports/figures/*_boxplot.png`
- `reports/figures/*_mean.png`
- `reports/localization_report.csv`
- `reports/figures/localization_ranking.png`

The image excludes existing generated CSVs, reports, virtual environments, caches, and Git metadata through `.dockerignore`.

## 8. Known limitations

- Docker provides a reproducible software environment, not reproducible CPU timing. Host scheduling, virtualization, CPU frequency scaling, and load affect timing results.
- Python-level timing does not prove or disprove machine-level constant-time behavior.
- The localization baseline identifies wrapper-level regions, not hidden native liboqs internals.
- This container is not a Raspberry Pi deployment. Target-hardware measurements must be repeated on the actual device.
- Native liboqs compilation can require substantial build time and disk space during the first image build.