"""Plotly chart builders for the dashboard."""

from __future__ import annotations

import json

import plotly.express as px
import pandas as pd


def timing_histogram(frame: pd.DataFrame) -> str:
    """Return an embeddable Plotly histogram."""
    figure = px.histogram(frame, x="duration_ns", color="label", nbins=40, barmode="overlay")
    figure.update_layout(template="plotly_white", xaxis_title="Duration (ns)", yaxis_title="Count")
    return json.dumps(figure, cls=__import__("plotly").utils.PlotlyJSONEncoder)


def timing_box_plot(frame: pd.DataFrame) -> str:
    """Return an embeddable before/after box plot."""
    figure = px.box(frame, x="label", y="duration_ns", color="label", points=False)
    figure.update_layout(template="plotly_white", yaxis_title="Duration (ns)")
    return json.dumps(figure, cls=__import__("plotly").utils.PlotlyJSONEncoder)
