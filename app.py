"""Flask application for the timing leakage dashboard."""

from __future__ import annotations

import logging
from pathlib import Path

from flask import Flask, jsonify, render_template

from analyzer.leakage import LeakageAnalyzer
from config import CONFIG, FrameworkConfig
from dashboard.charts import timing_box_plot, timing_histogram
from dashboard.report import save_report
from mitigation.comparison import compare_runs
from mitigation.validator import MitigationValidator

LOGGER = logging.getLogger(__name__)


def run_software_experiment(config: FrameworkConfig = CONFIG) -> dict:
    """Run the software mitigation validation and persist its outputs."""
    config.ensure_directories()
    validator = MitigationValidator(config.sample_count)
    before, after = validator.run()
    before.to_csv(config.before_csv, index=False)
    after.to_csv(config.after_csv, index=False)
    report = compare_runs(before, after, config.leakage_threshold)
    report["localization"] = validator.registry.ranking(config.leakage_threshold)
    analyzer = LeakageAnalyzer(config.leakage_threshold)
    analyzer.histogram(report["traces"], config.reports_dir / "timing_histogram.png")
    analyzer.box_plot(report["traces"], config.reports_dir / "timing_boxplot.png")
    save_report(report, config.reports_dir / "report.json")
    return report


def create_app(config: FrameworkConfig = CONFIG) -> Flask:
    """Create the dashboard application."""
    app = Flask(__name__, template_folder="dashboard/templates")
    state: dict = {"report": None, "ranking": []}

    @app.get("/")
    def dashboard() -> str:
        if state["report"] is None:
            return render_template("index.html", report={"analysis": {"leakage_score": 0, "t_score": 0, "significant": False}, "overhead_percent": 0}, histogram="{}", boxplot="{}", ranking=[])
        report = state["report"]
        return render_template(
            "index.html",
            report=report,
            histogram=timing_histogram(report["traces"]),
            boxplot=timing_box_plot(report["traces"]),
            ranking=state["ranking"],
        )

    @app.post("/api/run")
    def run() -> tuple:
        LOGGER.info("Starting software mitigation experiment")
        state["report"] = run_software_experiment(config)
        state["ranking"] = state["report"].get("localization", [])
        return jsonify({key: value for key, value in state["report"].items() if key != "traces"})

    return app


app = create_app()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(host=CONFIG.dashboard_host, port=CONFIG.dashboard_port, debug=False)
