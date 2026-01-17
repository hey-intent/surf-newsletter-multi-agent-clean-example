"""LangGraph workflow definition for the newsletter pipeline."""

from __future__ import annotations

import logging

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from src.core.personas import ALL_PERSONAS
from src.pipelines.newsletter_nodes import (
    aggregate_final_node,
    aggregate_phase3_node,
    aggregate_selections_node,
    batch_cross_grading_node,
    batch_final_grading_node,
    generate_html_node,
    selection_node,
    sourcing_node,
)
from src.pipelines.newsletter_state import NewsletterState

logger = logging.getLogger(__name__)


# =============================================================================
# Routing functions (return Send objects for parallel execution)
# =============================================================================


def route_to_selection(state: NewsletterState) -> list[Send]:
    """Route to parallel agent selection nodes.

    Returns a list of Send objects, one per persona.
    Each persona receives the full article list and selects their top picks.
    """
    articles = state["articles"]

    if not articles:
        logger.warning("No articles to select from")
        return []

    logger.info(f"Phase 2: Dispatching selection to {len(ALL_PERSONAS)} agents...")

    return [
        Send(
            "selection",
            {
                "persona": persona,
                "articles": articles,
            },
        )
        for persona in ALL_PERSONAS
    ]


def route_to_batch_cross_grading(state: NewsletterState) -> list[Send]:
    """Route to batch cross-grading: one call per persona for ALL articles.

    Batch prompting reduces API calls from N×M to just M (one per persona),
    per Cheng et al. (2023) research on batch prompting efficiency.
    """
    selected_articles = state.get("selected_articles", [])

    if not selected_articles:
        logger.warning("No articles to cross-grade")
        return []

    logger.info(f"Phase 3: Dispatching BATCH cross-grading for {len(selected_articles)} articles...")
    logger.info(f"   Using batch mode: {len(ALL_PERSONAS)} API calls (was {len(selected_articles) * len(ALL_PERSONAS)})")

    # One Send per persona - each persona grades ALL articles in one call
    sends = [
        Send(
            "batch_cross_grading",
            {
                "persona": persona,
                "articles": selected_articles,
                "is_final": False,
            },
        )
        for persona in ALL_PERSONAS
    ]

    return sends


def route_to_batch_final_grading(state: NewsletterState) -> list[Send]:
    """Route to batch final grading: one call per persona for ALL finalists.

    Reduces API calls from N×M to just M (one per persona).
    """
    finalists = state.get("finalists", [])

    if not finalists:
        logger.warning("No finalists to grade")
        return []

    logger.info(f"Phase 4: Dispatching BATCH final grading for {len(finalists)} finalists...")
    logger.info(f"   Using batch mode: {len(ALL_PERSONAS)} API calls (was {len(finalists) * len(ALL_PERSONAS)})")

    # One Send per persona - each persona grades ALL finalists in one call
    sends = [
        Send(
            "batch_final_grading",
            {
                "persona": persona,
                "articles": finalists,
                "is_final": True,
            },
        )
        for persona in ALL_PERSONAS
    ]

    return sends


# =============================================================================
# Graph construction
# =============================================================================


def build_newsletter_graph() -> StateGraph:
    """Build and compile the newsletter generation graph.

    The graph has 5 phases:

    1. Sourcing: Fetch articles from RSS feeds
    2. Selection: Each persona selects top articles (parallel via Send)
    3. Cross-grading: BATCH - each persona grades ALL articles in one call
    4. Final ranking: BATCH - each persona grades ALL finalists in one call
    5. Generate: Render HTML newsletter

    Batch grading reduces API calls from ~72 to ~6 (3 personas × 2 phases).
    Based on batch prompting research (Cheng et al., 2023).

    Returns:
        Compiled StateGraph ready for execution.
    """
    graph = StateGraph(NewsletterState)

    # =========================================================================
    # Add nodes
    # =========================================================================

    # Phase 1: Sourcing
    graph.add_node("sourcing", sourcing_node)

    # Phase 2: Selection
    graph.add_node("selection", selection_node)
    graph.add_node("aggregate_selections", aggregate_selections_node)

    # Phase 3: Batch cross-grading (one call per persona)
    graph.add_node("batch_cross_grading", batch_cross_grading_node)
    graph.add_node("aggregate_phase3", aggregate_phase3_node)

    # Phase 4: Batch final grading (one call per persona)
    graph.add_node("batch_final_grading", batch_final_grading_node)
    graph.add_node("aggregate_final", aggregate_final_node)

    # Phase 5: Generate
    graph.add_node("generate", generate_html_node)

    # =========================================================================
    # Add edges
    # =========================================================================

    # START -> Phase 1
    graph.add_edge(START, "sourcing")

    # Phase 1 -> Phase 2 (parallel selection)
    graph.add_conditional_edges(
        "sourcing",
        route_to_selection,
        ["selection"],
    )

    # Phase 2: Selection -> Aggregate
    graph.add_edge("selection", "aggregate_selections")

    # Phase 2 aggregate -> Phase 3 (BATCH cross-grading: 3 parallel calls)
    graph.add_conditional_edges(
        "aggregate_selections",
        route_to_batch_cross_grading,
        ["batch_cross_grading"],
    )

    # Phase 3: Batch cross-grading -> Aggregate
    graph.add_edge("batch_cross_grading", "aggregate_phase3")

    # Phase 3 aggregate -> Phase 4 (BATCH final grading: 3 parallel calls)
    graph.add_conditional_edges(
        "aggregate_phase3",
        route_to_batch_final_grading,
        ["batch_final_grading"],
    )

    # Phase 4: Batch final grading -> Aggregate
    graph.add_edge("batch_final_grading", "aggregate_final")

    # Phase 4 aggregate -> Phase 5
    graph.add_edge("aggregate_final", "generate")

    # Phase 5 -> END
    graph.add_edge("generate", END)

    # =========================================================================
    # Compile
    # =========================================================================

    return graph.compile()


# Pre-built graph instance for direct import
newsletter_graph = build_newsletter_graph()
