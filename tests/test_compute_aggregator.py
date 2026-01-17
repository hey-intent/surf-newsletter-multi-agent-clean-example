"""Tests for compute aggregator functions."""

import pytest

from src.compute.aggregator import (
    aggregate_final_grades,
    aggregate_phase3_grades,
    build_selected_articles,
)
from src.core.models import Article, GradingResult, SelectedArticle


class TestBuildSelectedArticles:
    """Tests for build_selected_articles function."""

    def test_build_with_single_agent(self, sample_articles: list[Article]):
        """Test building with selections from one agent."""
        selections = {"Johnny": [0, 2]}

        result = build_selected_articles(selections, sample_articles)

        assert len(result) == 2
        assert result[0].article == sample_articles[0]
        assert result[0].selected_by == ["Johnny"]
        assert result[1].article == sample_articles[2]
        assert result[1].selected_by == ["Johnny"]

    def test_build_with_multiple_agents(self, sample_articles: list[Article]):
        """Test building with selections from multiple agents."""
        selections = {
            "Johnny": [0, 1],
            "Annie": [1, 2],
            "Joana": [2, 3],
        }

        result = build_selected_articles(selections, sample_articles)

        # Should have 4 unique articles (0, 1, 2, 3)
        assert len(result) == 4

        # Find article at index 1 (selected by Johnny and Annie)
        article_1 = next(r for r in result if r.article == sample_articles[1])
        assert set(article_1.selected_by) == {"Johnny", "Annie"}

        # Find article at index 2 (selected by Annie and Joana)
        article_2 = next(r for r in result if r.article == sample_articles[2])
        assert set(article_2.selected_by) == {"Annie", "Joana"}

    def test_build_with_empty_selections(self, sample_articles: list[Article]):
        """Test building with no selections."""
        selections = {}

        result = build_selected_articles(selections, sample_articles)

        assert len(result) == 0

    def test_build_filters_invalid_indices(self, sample_articles: list[Article]):
        """Test invalid indices are filtered out."""
        selections = {"Johnny": [0, 100, -1, 2]}  # 100 and -1 are invalid

        result = build_selected_articles(selections, sample_articles)

        assert len(result) == 2
        urls = [r.article.url for r in result]
        assert sample_articles[0].url in urls
        assert sample_articles[2].url in urls

    def test_build_tracks_duplicates(self, sample_articles: list[Article]):
        """Test that duplicate selections (same article by multiple agents) are tracked."""
        selections = {
            "Johnny": [0],
            "Annie": [0],
            "Joana": [0],
        }

        result = build_selected_articles(selections, sample_articles)

        assert len(result) == 1
        assert set(result[0].selected_by) == {"Johnny", "Annie", "Joana"}


class TestAggregatePhase3Grades:
    """Tests for aggregate_phase3_grades function."""

    def test_aggregate_calculates_averages(
        self, sample_selected_articles: list[SelectedArticle]
    ):
        """Test average calculation for Phase 3 grades."""
        grades = [
            {"article_idx": 0, "grade": GradingResult(grader="Annie", score=4.0, reasoning="Good")},
            {"article_idx": 0, "grade": GradingResult(grader="Joana", score=3.0, reasoning="OK")},
            {"article_idx": 1, "grade": GradingResult(grader="Johnny", score=5.0, reasoning="Great")},
        ]

        result = aggregate_phase3_grades(sample_selected_articles, grades, finalists_count=5)

        # Find articles by their original index position before sorting
        # After sorting by score, we need to check the actual values
        scores_found = {r.phase3_avg for r in result}

        # Article idx 0 should have avg = (4 + 3) / 2 = 3.5
        assert 3.5 in scores_found

        # Article idx 1 should have avg = 5.0
        assert 5.0 in scores_found

    def test_aggregate_returns_top_finalists(
        self, sample_selected_articles: list[SelectedArticle]
    ):
        """Test that only top N finalists are returned."""
        # Give distinct scores so we can verify sorting
        grades = [
            {"article_idx": 0, "grade": GradingResult(grader="Test", score=2.0, reasoning="Low")},
            {"article_idx": 1, "grade": GradingResult(grader="Test", score=5.0, reasoning="High")},
            {"article_idx": 2, "grade": GradingResult(grader="Test", score=3.0, reasoning="Mid")},
        ]

        result = aggregate_phase3_grades(sample_selected_articles, grades, finalists_count=2)

        assert len(result) == 2
        # Top 2 should be articles with scores 5.0 and 3.0
        scores = [r.phase3_avg for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_aggregate_sorts_by_score_descending(
        self, sample_selected_articles: list[SelectedArticle]
    ):
        """Test articles are sorted by score in descending order."""
        grades = [
            {"article_idx": 0, "grade": GradingResult(grader="Test", score=2.0, reasoning="R")},
            {"article_idx": 1, "grade": GradingResult(grader="Test", score=4.0, reasoning="R")},
            {"article_idx": 2, "grade": GradingResult(grader="Test", score=3.0, reasoning="R")},
            {"article_idx": 3, "grade": GradingResult(grader="Test", score=5.0, reasoning="R")},
            {"article_idx": 4, "grade": GradingResult(grader="Test", score=1.0, reasoning="R")},
        ]

        result = aggregate_phase3_grades(sample_selected_articles, grades, finalists_count=5)

        scores = [r.phase3_avg for r in result]
        assert scores == [5.0, 4.0, 3.0, 2.0, 1.0]

    def test_aggregate_unanimous_gets_5(
        self, sample_selected_articles: list[SelectedArticle]
    ):
        """Test articles with no cross-grades (unanimous) get 5.0."""
        # No grades for any article
        grades = []

        result = aggregate_phase3_grades(sample_selected_articles, grades, finalists_count=5)

        # All should have phase3_avg = 5.0 (unanimous selection)
        for article in result:
            assert article.phase3_avg == 5.0

    def test_aggregate_stores_scores_on_articles(
        self, sample_selected_articles: list[SelectedArticle]
    ):
        """Test grades are stored on the SelectedArticle objects."""
        grade1 = GradingResult(grader="Annie", score=4.0, reasoning="Good")
        grade2 = GradingResult(grader="Joana", score=3.0, reasoning="OK")
        grades = [
            {"article_idx": 0, "grade": grade1},
            {"article_idx": 0, "grade": grade2},
        ]

        result = aggregate_phase3_grades(sample_selected_articles, grades, finalists_count=5)

        # Find the article that received scores (has phase3_avg of 3.5 = (4+3)/2)
        scored_article = next((r for r in result if r.phase3_avg == 3.5), None)
        assert scored_article is not None
        assert len(scored_article.phase3_scores) == 2
        assert grade1 in scored_article.phase3_scores
        assert grade2 in scored_article.phase3_scores


class TestAggregateFinalGrades:
    """Tests for aggregate_final_grades function."""

    def test_aggregate_calculates_final_averages(
        self, sample_selected_articles: list[SelectedArticle]
    ):
        """Test average calculation for final grades."""
        finalists = sample_selected_articles[:3]
        grades = [
            {"article_idx": 0, "grade": GradingResult(grader="Johnny", score=4.0, reasoning="R")},
            {"article_idx": 0, "grade": GradingResult(grader="Annie", score=5.0, reasoning="R")},
            {"article_idx": 0, "grade": GradingResult(grader="Joana", score=3.0, reasoning="R")},
        ]

        result = aggregate_final_grades(finalists, grades)

        # Article 0 avg = (4 + 5 + 3) / 3 = 4.0
        assert result[0].final_avg == 4.0

    def test_aggregate_sorts_by_final_score(
        self, sample_selected_articles: list[SelectedArticle]
    ):
        """Test articles are sorted by final score descending."""
        finalists = sample_selected_articles[:3]
        grades = [
            {"article_idx": 0, "grade": GradingResult(grader="Test", score=2.0, reasoning="R")},
            {"article_idx": 1, "grade": GradingResult(grader="Test", score=5.0, reasoning="R")},
            {"article_idx": 2, "grade": GradingResult(grader="Test", score=3.0, reasoning="R")},
        ]

        result = aggregate_final_grades(finalists, grades)

        final_scores = [r.final_avg for r in result]
        assert final_scores == [5.0, 3.0, 2.0]

    def test_aggregate_falls_back_to_phase3_avg(
        self, sample_selected_articles: list[SelectedArticle]
    ):
        """Test articles with no final grades use phase3_avg."""
        finalists = sample_selected_articles[:2]
        finalists[0].phase3_avg = 4.5
        finalists[1].phase3_avg = 3.5

        grades = []  # No final grades

        result = aggregate_final_grades(finalists, grades)

        assert result[0].final_avg == 4.5
        assert result[1].final_avg == 3.5

    def test_aggregate_stores_final_scores(
        self, sample_selected_articles: list[SelectedArticle]
    ):
        """Test final grades are stored on articles."""
        finalists = sample_selected_articles[:1]
        grade = GradingResult(grader="Johnny", score=4.0, reasoning="Test")
        grades = [{"article_idx": 0, "grade": grade}]

        result = aggregate_final_grades(finalists, grades)

        assert len(result[0].final_scores) == 1
        assert result[0].final_scores[0] == grade
