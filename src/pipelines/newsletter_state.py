"""LangGraph state definition for the newsletter pipeline."""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from src.core.models import Article, GradingResult, SelectedArticle
from src.core.personas import Persona


def merge_selections(
    current: dict[str, list[int]], new: dict[str, list[int]]
) -> dict[str, list[int]]:
    """Merge agent selections into a single dict."""
    result = current.copy()
    result.update(new)
    return result


class NewsletterState(TypedDict, total=False):
    """Central state for the newsletter generation pipeline.

    Uses Annotated types with reducers for parallel execution support.
    LangGraph will automatically merge results from parallel nodes.
    """

    # Configuration
    days: int
    min_articles: int | None
    output_path: str

    # Phase 1: Sourcing
    articles: list[Article]

    # Phase 2: Selection (parallel agents)
    selections: Annotated[dict[str, list[int]], merge_selections]

    # Aggregated selections after Phase 2
    selected_articles: list[SelectedArticle]

    # Phase 3: Cross-grading (parallel)
    phase3_grades: Annotated[list[dict], operator.add]

    # Finalists after Phase 3
    finalists: list[SelectedArticle]

    # Phase 4: Final grading (parallel)
    final_grades: Annotated[list[dict], operator.add]

    # Final ranked articles
    ranked_articles: list[SelectedArticle]

    # Output
    generated_html: str


class SelectionTaskInput(TypedDict):
    """Input for a single agent's selection task (via Send)."""

    persona: Persona
    articles: list[Article]


class GradingTaskInput(TypedDict):
    """Input for a single agent's grading task (via Send)."""

    persona: Persona
    article: SelectedArticle
    article_idx: int
    is_final: bool


class BatchGradingTaskInput(TypedDict):
    """Input for batch grading task (one persona, all articles)."""

    persona: Persona
    articles: list[SelectedArticle]
    is_final: bool
