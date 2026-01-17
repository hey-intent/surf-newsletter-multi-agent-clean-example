"""LangGraph nodes for the newsletter pipeline.

Each node is a pure function that takes state and returns state updates.
Nodes use agents (SelectorAgent, GraderAgent) for LLM operations.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from src.agents.batch_grader import BatchGraderAgent
from src.agents.selector import SelectorAgent
from src.compute.aggregator import (
    aggregate_final_grades,
    aggregate_phase3_grades,
    build_selected_articles,
)
from src.compute.fetcher import fetch_articles
from src.compute.renderer import render_newsletter
from src.pipelines.newsletter_state import (
    BatchGradingTaskInput,
    NewsletterState,
    SelectionTaskInput,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Phase 1: Sourcing
# =============================================================================


def sourcing_node(state: NewsletterState) -> dict[str, Any]:
    """Fetch articles from RSS feeds.

    Returns:
        State update with articles list.
    """
    days = state.get("days", 7)
    min_articles = state.get("min_articles")
    logger.info(f"Phase 1: Sourcing articles (last {days} days)...")

    articles = fetch_articles(days, min_articles=min_articles)
    logger.info(f"   Sourced {len(articles)} articles")

    return {"articles": articles}


# =============================================================================
# Phase 2: Selection
# =============================================================================


def selection_node(state: SelectionTaskInput) -> dict[str, Any]:
    """Single agent selection node (called via Send for parallelism).

    Args:
        state: Contains persona and articles list.

    Returns:
        State update with selections dict.
    """
    persona = state["persona"]
    articles = state["articles"]

    agent = SelectorAgent(persona)
    indices = agent.run(articles)

    return {"selections": {persona.name: indices}}


def aggregate_selections_node(state: NewsletterState) -> dict[str, Any]:
    """Merge all agent selections into SelectedArticle objects.

    Returns:
        State update with selected_articles list.
    """
    articles = state["articles"]
    selections = state.get("selections", {})

    selected_articles = build_selected_articles(selections, articles)

    return {"selected_articles": selected_articles}


# =============================================================================
# Phase 3: Cross-Grading (BATCH VERSION)
# =============================================================================


def batch_cross_grading_node(state: BatchGradingTaskInput) -> dict[str, Any]:
    """Batch cross-grading: one persona grades ALL articles in a single call.

    Scientific basis: Batch prompting (Cheng et al., 2023) reduces API calls
    while maintaining accuracy through structured prompts with clear separators.

    Args:
        state: Contains persona and list of articles to grade.

    Returns:
        State update with phase3_grades list.
    """
    persona = state["persona"]
    articles = state["articles"]

    agent = BatchGraderAgent(persona)
    results = agent.run(articles, is_final=False)

    # Convert to the expected format (list of {article_idx, grade} dicts)
    grades = [
        {"article_idx": idx, "grade": result}
        for idx, result in enumerate(results)
    ]

    return {"phase3_grades": grades}


def aggregate_phase3_node(state: NewsletterState) -> dict[str, Any]:
    """Aggregate Phase 3 grades and select finalists.

    Returns:
        State update with finalists list.
    """
    selected_articles = state["selected_articles"]
    phase3_grades = state.get("phase3_grades", [])

    finalists = aggregate_phase3_grades(selected_articles, phase3_grades)

    return {"finalists": finalists}


# =============================================================================
# Phase 4: Final Grading (BATCH VERSION)
# =============================================================================


def batch_final_grading_node(state: BatchGradingTaskInput) -> dict[str, Any]:
    """Batch final grading: one persona grades ALL finalists in a single call.

    Args:
        state: Contains persona and list of finalist articles.

    Returns:
        State update with final_grades list.
    """
    persona = state["persona"]
    articles = state["articles"]

    agent = BatchGraderAgent(persona)
    results = agent.run(articles, is_final=True)

    # Convert to the expected format
    grades = [
        {"article_idx": idx, "grade": result}
        for idx, result in enumerate(results)
    ]

    return {"final_grades": grades}


def aggregate_final_node(state: NewsletterState) -> dict[str, Any]:
    """Aggregate final grades and produce ranked articles.

    Returns:
        State update with ranked_articles list.
    """
    finalists = state["finalists"]
    final_grades = state.get("final_grades", [])

    ranked_articles = aggregate_final_grades(finalists, final_grades)

    return {"ranked_articles": ranked_articles}


# =============================================================================
# Phase 5: Generate HTML
# =============================================================================


def generate_html_node(state: NewsletterState) -> dict[str, Any]:
    """Generate HTML newsletter from ranked articles.

    Returns:
        State update with generated_html path.
    """
    ranked_articles = state["ranked_articles"]
    output_path = state.get(
        "output_path",
        f"newsletter_{datetime.now().strftime('%Y%m%d')}.html"
    )

    result_path = render_newsletter(ranked_articles, output_path)

    return {"generated_html": str(result_path)}
