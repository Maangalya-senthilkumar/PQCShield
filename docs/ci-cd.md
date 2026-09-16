# CI/CD

PQCShield uses GitHub Actions for continuous integration. CI means that every relevant branch update is checked in a clean Ubuntu environment. CD is not a production deployment in this project; the workflow builds the Docker image as a reproducibility check but does not publish or deploy it.

## When CI Runs

The workflow is defined in `.github/workflows/ci.yml` and runs on:

- Pushes to `main`.
- Pushes to `review-devops`.
- Pull requests targeting `main`.

## Pipeline Stages

The job runs on Ubuntu 22.04 with Python 3.11. It installs the native build tools and libraries required by `liboqs-python`, including Git, CMake, Ninja, OpenSSL headers, and a C/C++ toolchain. Python dependencies are then installed from the existing `requirements.txt` without changing the project's dependency requirements.

### Python Validation

CI runs:

```bash
python3 -m compileall -q .
```

This catches Python syntax and bytecode-compilation errors across the project.

### Real ML-KEM Self-Test

CI runs:

```bash
python3 -m collector.benchmark
```

This invokes the real `oqs.KeyEncapsulation` implementation with ML-KEM-768 and verifies key generation, encapsulation, decapsulation, and matching shared secrets. It is not a fake cryptographic test.

### Localization Validation

CI calls the existing localization API with only 10 samples per condition:

```python
from analyzer.localization import localize
localize(sample_count=10)
```

This performs real ML-KEM wrapper-level measurements and generates `reports/localization_report.csv`. CI verifies that the report exists and is non-empty. The localization regions are explicit Python adapter boundaries; they do not claim to identify hidden internal liboqs C functions.

### Docker Image Build

CI builds the existing container definition:

```bash
docker build -t pqcshield:ci .
```

This verifies that the Python 3.11 image, native build dependencies, `liboqs-python`, and application files can be assembled reproducibly.

## What Causes CI to Fail

The pipeline fails when any of these checks fails:

- Dependencies cannot be installed.
- Python syntax validation fails.
- The real ML-KEM self-test fails.
- The localization run fails or does not create a non-empty report.
- The Docker image cannot be built.

## Why Large Timing Experiments Are Not Automatic

The normal timing experiment collects thousands of measurements and is intentionally not run in CI. Timing is affected by host load, scheduling, CPU frequency scaling, virtualized runners, and other environmental factors. A large run would make CI slow and would not provide reliable side-channel conclusions. Controlled experiments belong in dedicated environments and on target hardware.

Passing CI demonstrates that the software workflow is installable and executable. It does not prove the absence of timing side-channel leakage, constant-time behavior, or security on Raspberry Pi hardware.
