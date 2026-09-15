"""Command-line entry point for ML-KEM and mitigation experiments."""

from __future__ import annotations

import argparse
import logging

from app import run_software_experiment
from collector.benchmark import BenchmarkRunner
from collector.traces import save_traces
from config import CONFIG


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("software", "kem"), default="software")
    parser.add_argument("--samples", type=int, default=CONFIG.sample_count)
    parser.add_argument("--algorithm", default=CONFIG.algorithm)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    config = CONFIG
    if args.mode == "software":
        config = type(CONFIG)(sample_count=args.samples)
        report = run_software_experiment(config)
        print(f"Leakage score: {report['analysis']['leakage_score']:.3f}")
        print(f"Overhead: {report['overhead_percent']:.2f}%")
        return
    runner = BenchmarkRunner(algorithm=args.algorithm, sample_count=args.samples)
    config.ensure_directories()
    before = runner.run("before")
    after = runner.run("after")
    save_traces(before, config.before_csv)
    save_traces(after, config.after_csv)
    print(f"Collected {len(before) + len(after)} ML-KEM timing records")


if __name__ == "__main__":
    main()
