"""Aggregation functions for combining agent outputs."""

from __future__ import annotations

import logging

from src.core.config import FINALISTS_COUNT
from src.core.models import Article, GradingResult, SelectedArticle

logger = logging.getLogger(__name__)


def build_selected_articles(
    selections: dict[str, list[int]],
    articles: list[Article],
) -> list[SelectedArticle]:
    """Build SelectedArticle objects from agent selections.

    Tracks which agents selected each article and handles duplicates
    (same article selected by multiple agents).

    Args:
        selections: Dict mapping agent name to list of article indices.
        articles: Full list of articles that were available for selection.

    Returns:
        List of SelectedArticle objects with selection metadata.
    """
    logger.info("Aggregating selections...")

    # Track selections by article index
    article_selections: dict[int, list[str]] = {}

    for agent_name, indices in selections.items():
        for idx in indices:
            if idx not in article_selections:
                article_selections[idx] = []
            article_selections[idx].append(agent_name)

    # Create SelectedArticle objects
    selected_articles = []
    for idx, selected_by in article_selections.items():
        if 0 <= idx < len(articles):
            selected_articles.append(
                SelectedArticle(
                    article=articles[idx],
                    selected_by=selected_by,
                )
            )

    duplicates = sum(1 for s in selected_articles if len(s.selected_by) > 1)
    logger.info(
        f"   Total: {len(selected_articles)} unique articles "
        f"({duplicates} selected by multiple agents)"
    )

    return selected_articles


def aggregate_phase3_grades(
    selected_articles: list[SelectedArticle],
    grades: list[dict],
    finalists_count: int = FINALISTS_COUNT,
) -> list[SelectedArticle]:
    """Aggregate Phase 3 cross-grading results.

    Calculates average scores and filters to top finalists.

    Args:
        selected_articles: Articles that were selected in Phase 2.
        grades: List of dicts with 'article_idx' and 'grade' (GradingResult).
        finalists_count: Number of top articles to keep.

    Returns:
        Top finalists sorted by Phase 3 average score.
    """
    logger.info("Aggregating Phase 3 grades...")

    # Group grades by article index
    grades_by_article: dict[int, list[GradingResult]] = {}
    for grade_entry in grades:
        idx = grade_entry["article_idx"]
        grade = grade_entry["grade"]
        if idx not in grades_by_article:
            grades_by_article[idx] = []
        grades_by_article[idx].append(grade)

    # Calculate averages and update articles
    for idx, article in enumerate(selected_articles):
        scores = grades_by_article.get(idx, [])
        article.phase3_scores = scores

        if scores:
            article.phase3_avg = sum(s.score for s in scores) / len(scores)
        else:
            # Unanimous selection - all agents selected it
            article.phase3_avg = 5.0

    # Sort by Phase 3 score (descending)
    selected_articles.sort(key=lambda x: x.phase3_avg, reverse=True)

    # Take top finalists
    finalists = selected_articles[:finalists_count]

    if finalists:
        avg_score = sum(s.phase3_avg for s in finalists) / len(finalists)
        logger.info(f"   Average score: {avg_score:.2f}")

    logger.info(f"   Top {len(finalists)} qualified for final round")

    return finalists


def aggregate_final_grades(
    finalists: list[SelectedArticle],
    grades: list[dict],
) -> list[SelectedArticle]:
    """Aggregate final grading results.

    Calculates final average scores and produces ranked list.

    Args:
        finalists: Articles that qualified for final round.
        grades: List of dicts with 'article_idx' and 'grade' (GradingResult).

    Returns:
        Articles sorted by final average score (descending).
    """
    logger.info("Aggregating final grades...")

    # Group grades by article index
    grades_by_article: dict[int, list[GradingResult]] = {}
    for grade_entry in grades:
        idx = grade_entry["article_idx"]
        grade = grade_entry["grade"]
        if idx not in grades_by_article:
            grades_by_article[idx] = []
        grades_by_article[idx].append(grade)

    # Calculate final averages
    for idx, article in enumerate(finalists):
        scores = grades_by_article.get(idx, [])
        article.final_scores = scores

        if scores:
            article.final_avg = sum(s.score for s in scores) / len(scores)
        else:
            article.final_avg = article.phase3_avg

    # Sort by final score (descending)
    finalists.sort(key=lambda x: x.final_avg, reverse=True)

    if finalists:
        winner = finalists[0]
        logger.info(
            f"   Winner: '{winner.article.title[:50]}...' "
            f"({winner.final_avg:.2f}/5)"
        )

    return finalists
