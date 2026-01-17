"""Tests for core models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.core.models import Article, GradingResult, SelectedArticle


class TestArticle:
    """Tests for the Article model."""

    def test_create_article(self, sample_article: Article):
        """Test article creation with valid data."""
        assert sample_article.title == "Epic Surf Session at Pipeline"
        assert str(sample_article.url) == "https://example.com/epic-pipeline"
        assert sample_article.source == "Test Surf Mag"
        assert sample_article.published == datetime(2025, 1, 15, 10, 30)

    def test_article_with_minimal_fields(self):
        """Test article creation with only required fields."""
        article = Article(
            title="Test Article",
            url="https://example.com/test",
            source="Test Source",
            published=datetime.now(),
        )
        assert article.excerpt == ""
        assert article.image_url is None

    def test_article_hash(self):
        """Test article hashing based on URL."""
        article1 = Article(
            title="Article 1",
            url="https://example.com/same-url",
            source="Source 1",
            published=datetime.now(),
        )
        article2 = Article(
            title="Article 2",
            url="https://example.com/same-url",
            source="Source 2",
            published=datetime.now(),
        )
        assert hash(article1) == hash(article2)

    def test_article_equality(self):
        """Test article equality based on URL."""
        article1 = Article(
            title="Article 1",
            url="https://example.com/same-url",
            source="Source 1",
            published=datetime.now(),
        )
        article2 = Article(
            title="Different Title",
            url="https://example.com/same-url",
            source="Different Source",
            published=datetime.now(),
        )
        assert article1 == article2

    def test_article_inequality(self):
        """Test articles with different URLs are not equal."""
        article1 = Article(
            title="Same Title",
            url="https://example.com/url-1",
            source="Same Source",
            published=datetime.now(),
        )
        article2 = Article(
            title="Same Title",
            url="https://example.com/url-2",
            source="Same Source",
            published=datetime.now(),
        )
        assert article1 != article2

    def test_article_invalid_url(self):
        """Test article creation with invalid URL raises error."""
        with pytest.raises(ValidationError):
            Article(
                title="Test",
                url="not-a-valid-url",
                source="Test",
                published=datetime.now(),
            )


class TestGradingResult:
    """Tests for the GradingResult model."""

    def test_create_grading_result(self, sample_grading_result: GradingResult):
        """Test grading result creation."""
        assert sample_grading_result.grader == "TestPersona"
        assert sample_grading_result.score == 4.0
        assert sample_grading_result.reasoning == "Great article with relevant content."
        assert len(sample_grading_result.key_strengths) == 2

    def test_grading_result_score_bounds(self):
        """Test score must be between 1 and 5."""
        # Valid scores
        result = GradingResult(grader="Test", score=1.0, reasoning="Min score")
        assert result.score == 1.0

        result = GradingResult(grader="Test", score=5.0, reasoning="Max score")
        assert result.score == 5.0

        # Invalid scores
        with pytest.raises(ValidationError):
            GradingResult(grader="Test", score=0.5, reasoning="Too low")

        with pytest.raises(ValidationError):
            GradingResult(grader="Test", score=5.5, reasoning="Too high")

    def test_grading_result_default_strengths(self):
        """Test default empty key_strengths list."""
        result = GradingResult(grader="Test", score=3.0, reasoning="Test")
        assert result.key_strengths == []


class TestSelectedArticle:
    """Tests for the SelectedArticle model."""

    def test_create_selected_article(
        self, sample_article: Article, sample_selected_article: SelectedArticle
    ):
        """Test selected article creation."""
        assert sample_selected_article.article == sample_article
        assert sample_selected_article.selected_by == ["Johnny", "Annie"]
        assert sample_selected_article.phase3_avg == 0.0
        assert sample_selected_article.final_avg == 0.0

    def test_selected_article_default_values(self, sample_article: Article):
        """Test default values for selected article."""
        selected = SelectedArticle(article=sample_article)
        assert selected.selected_by == []
        assert selected.phase3_scores == []
        assert selected.final_scores == []

    def test_selected_article_hash(self, sample_article: Article):
        """Test selected article hashing based on article."""
        selected1 = SelectedArticle(article=sample_article, selected_by=["A"])
        selected2 = SelectedArticle(article=sample_article, selected_by=["B"])
        assert hash(selected1) == hash(selected2)

    def test_selected_article_equality(self, sample_article: Article):
        """Test selected article equality based on article."""
        selected1 = SelectedArticle(article=sample_article, selected_by=["A"])
        selected2 = SelectedArticle(article=sample_article, selected_by=["B"])
        assert selected1 == selected2

    def test_selected_article_with_scores(
        self, sample_article: Article, sample_grading_result: GradingResult
    ):
        """Test selected article with grading scores."""
        selected = SelectedArticle(
            article=sample_article,
            selected_by=["Johnny"],
            phase3_scores=[sample_grading_result],
            phase3_avg=4.0,
        )
        assert len(selected.phase3_scores) == 1
        assert selected.phase3_avg == 4.0
