"""Compute module - non-LLM operations (fetching, aggregation, rendering)."""

from src.compute.aggregator import (
    aggregate_final_grades,
    aggregate_phase3_grades,
    build_selected_articles,
)
from src.compute.fetcher import fetch_articles
from src.compute.renderer import render_newsletter

__all__ = [
    "fetch_articles",
    "build_selected_articles",
    "aggregate_phase3_grades",
    "aggregate_final_grades",
    "render_newsletter",
]
