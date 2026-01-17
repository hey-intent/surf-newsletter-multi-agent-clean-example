"""Shared fixtures for tests."""

from datetime import datetime

import pytest

from src.core.models import Article, GradingResult, SelectedArticle
from src.core.personas import Persona


@pytest.fixture
def sample_persona() -> Persona:
    """Create a test persona."""
    return Persona(
        name="TestPersona",
        description="A test persona for unit testing.",
        system_prompt="You are a test persona.",
        criteria_text="- Test criterion (100%): Testing quality",
    )


@pytest.fixture
def sample_article() -> Article:
    """Create a test article."""
    return Article(
        title="Epic Surf Session at Pipeline",
        url="https://example.com/epic-pipeline",
        excerpt="John John Florence scores perfect 10 at Pipeline Masters.",
        source="Test Surf Mag",
        published=datetime(2025, 1, 15, 10, 30),
        image_url="https://example.com/images/pipeline.jpg",
    )


@pytest.fixture
def sample_articles() -> list[Article]:
    """Create a list of test articles."""
    return [
        Article(
            title="Pipeline Masters Final Results",
            url="https://example.com/article-0",
            excerpt="Competition results from the Pipeline Masters.",
            source="WSL",
            published=datetime(2025, 1, 15),
        ),
        Article(
            title="Best Surf Spots in Portugal",
            url="https://example.com/article-1",
            excerpt="Exploring the beautiful surf destinations in Portugal.",
            source="Travel Surf",
            published=datetime(2025, 1, 14),
        ),
        Article(
            title="Ocean Cleanup Initiative",
            url="https://example.com/article-2",
            excerpt="Surfers lead beach cleanup in California.",
            source="The Inertia",
            published=datetime(2025, 1, 13),
        ),
        Article(
            title="New Board Technology Revealed",
            url="https://example.com/article-3",
            excerpt="Revolutionary fin design changes everything.",
            source="Stab",
            published=datetime(2025, 1, 12),
        ),
        Article(
            title="Women's Championship Highlights",
            url="https://example.com/article-4",
            excerpt="Carissa Moore dominates in the final heat.",
            source="Surfer Mag",
            published=datetime(2025, 1, 11),
        ),
    ]


@pytest.fixture
def sample_grading_result() -> GradingResult:
    """Create a test grading result."""
    return GradingResult(
        grader="TestPersona",
        score=4.0,
        reasoning="Great article with relevant content.",
        key_strengths=["Well written", "Good coverage"],
    )


@pytest.fixture
def sample_selected_article(sample_article: Article) -> SelectedArticle:
    """Create a test selected article."""
    return SelectedArticle(
        article=sample_article,
        selected_by=["Johnny", "Annie"],
    )


@pytest.fixture
def sample_selected_articles(sample_articles: list[Article]) -> list[SelectedArticle]:
    """Create a list of selected articles for testing."""
    return [
        SelectedArticle(article=sample_articles[0], selected_by=["Johnny"]),
        SelectedArticle(article=sample_articles[1], selected_by=["Annie"]),
        SelectedArticle(article=sample_articles[2], selected_by=["Joana"]),
        SelectedArticle(article=sample_articles[3], selected_by=["Johnny", "Annie"]),
        SelectedArticle(article=sample_articles[4], selected_by=["Annie", "Joana"]),
    ]
