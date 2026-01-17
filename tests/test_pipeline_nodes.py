"""Tests for pipeline node functions."""

from unittest.mock import MagicMock, patch

import pytest

from src.core.models import Article, GradingResult, SelectedArticle
from src.core.personas import JOHNNY, ANNIE, JOANA
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
from src.pipelines.newsletter_state import (
    BatchGradingTaskInput,
    NewsletterState,
    SelectionTaskInput,
)


class TestSourcingNode:
    """Tests for sourcing_node function."""

    @patch("src.pipelines.newsletter_nodes.fetch_articles")
    def test_sourcing_returns_articles(
        self, mock_fetch: MagicMock, sample_articles: list[Article]
    ):
        """Test sourcing node fetches and returns articles."""
        mock_fetch.return_value = sample_articles
        state: NewsletterState = {"days": 7}

        result = sourcing_node(state)

        assert "articles" in result
        assert result["articles"] == sample_articles
        mock_fetch.assert_called_once_with(7, min_articles=None)

    @patch("src.pipelines.newsletter_nodes.fetch_articles")
    def test_sourcing_uses_default_days(self, mock_fetch: MagicMock):
        """Test sourcing uses default 7 days when not specified."""
        mock_fetch.return_value = []
        state: NewsletterState = {}

        sourcing_node(state)

        mock_fetch.assert_called_once_with(7, min_articles=None)

    @patch("src.pipelines.newsletter_nodes.fetch_articles")
    def test_sourcing_uses_custom_days(self, mock_fetch: MagicMock):
        """Test sourcing uses custom days value."""
        mock_fetch.return_value = []
        state: NewsletterState = {"days": 14}

        sourcing_node(state)

        mock_fetch.assert_called_once_with(14, min_articles=None)

    @patch("src.pipelines.newsletter_nodes.fetch_articles")
    def test_sourcing_uses_custom_min_articles(self, mock_fetch: MagicMock):
        """Test sourcing passes min_articles to fetch_articles."""
        mock_fetch.return_value = []
        state: NewsletterState = {"days": 7, "min_articles": 30}

        sourcing_node(state)

        mock_fetch.assert_called_once_with(7, min_articles=30)


class TestSelectionNode:
    """Tests for selection_node function."""

    @patch("src.pipelines.newsletter_nodes.SelectorAgent")
    def test_selection_returns_selections_dict(
        self, mock_agent_class: MagicMock, sample_articles: list[Article]
    ):
        """Test selection node returns selections dictionary."""
        mock_agent = MagicMock()
        mock_agent.run.return_value = [0, 2, 4]
        mock_agent_class.return_value = mock_agent

        state: SelectionTaskInput = {
            "persona": JOHNNY,
            "articles": sample_articles,
        }

        result = selection_node(state)

        assert "selections" in result
        assert result["selections"] == {"Johnny": [0, 2, 4]}

    @patch("src.pipelines.newsletter_nodes.SelectorAgent")
    def test_selection_creates_agent_with_persona(
        self, mock_agent_class: MagicMock, sample_articles: list[Article]
    ):
        """Test selection creates agent with correct persona."""
        mock_agent = MagicMock()
        mock_agent.run.return_value = []
        mock_agent_class.return_value = mock_agent

        state: SelectionTaskInput = {
            "persona": ANNIE,
            "articles": sample_articles,
        }

        selection_node(state)

        mock_agent_class.assert_called_once_with(ANNIE)

    @patch("src.pipelines.newsletter_nodes.SelectorAgent")
    def test_selection_passes_articles_to_agent(
        self, mock_agent_class: MagicMock, sample_articles: list[Article]
    ):
        """Test selection passes articles to agent.run()."""
        mock_agent = MagicMock()
        mock_agent.run.return_value = [0]
        mock_agent_class.return_value = mock_agent

        state: SelectionTaskInput = {
            "persona": JOHNNY,
            "articles": sample_articles,
        }

        selection_node(state)

        mock_agent.run.assert_called_once_with(sample_articles)


class TestAggregateSelectionsNode:
    """Tests for aggregate_selections_node function."""

    def test_aggregate_returns_selected_articles(self, sample_articles: list[Article]):
        """Test aggregate creates SelectedArticle objects."""
        state: NewsletterState = {
            "articles": sample_articles,
            "selections": {"Johnny": [0, 1], "Annie": [1, 2]},
        }

        result = aggregate_selections_node(state)

        assert "selected_articles" in result
        assert len(result["selected_articles"]) == 3  # 0, 1, 2 unique

    def test_aggregate_tracks_selected_by(self, sample_articles: list[Article]):
        """Test aggregate tracks which agents selected each article."""
        state: NewsletterState = {
            "articles": sample_articles,
            "selections": {"Johnny": [0], "Annie": [0], "Joana": [0]},
        }

        result = aggregate_selections_node(state)

        assert len(result["selected_articles"]) == 1
        assert set(result["selected_articles"][0].selected_by) == {"Johnny", "Annie", "Joana"}

    def test_aggregate_handles_empty_selections(self, sample_articles: list[Article]):
        """Test aggregate handles empty selections."""
        state: NewsletterState = {
            "articles": sample_articles,
            "selections": {},
        }

        result = aggregate_selections_node(state)

        assert result["selected_articles"] == []


class TestBatchCrossGradingNode:
    """Tests for batch_cross_grading_node function."""

    @patch("src.pipelines.newsletter_nodes.BatchGraderAgent")
    def test_batch_cross_grading_returns_grade_list(
        self, mock_agent_class: MagicMock, sample_selected_articles: list[SelectedArticle]
    ):
        """Test batch cross grading returns phase3_grades list."""
        mock_agent = MagicMock()
        mock_agent.run.return_value = [
            GradingResult(grader="Johnny", score=4.0, reasoning="Good"),
            GradingResult(grader="Johnny", score=3.5, reasoning="OK"),
        ]
        mock_agent_class.return_value = mock_agent

        articles = sample_selected_articles[:2]
        state: BatchGradingTaskInput = {
            "persona": JOHNNY,
            "articles": articles,
            "is_final": False,
        }

        result = batch_cross_grading_node(state)

        assert "phase3_grades" in result
        assert len(result["phase3_grades"]) == 2
        assert result["phase3_grades"][0]["article_idx"] == 0
        assert result["phase3_grades"][0]["grade"].score == 4.0
        assert result["phase3_grades"][1]["article_idx"] == 1
        assert result["phase3_grades"][1]["grade"].score == 3.5

    @patch("src.pipelines.newsletter_nodes.BatchGraderAgent")
    def test_batch_cross_grading_calls_agent_with_is_final_false(
        self, mock_agent_class: MagicMock, sample_selected_articles: list[SelectedArticle]
    ):
        """Test batch cross grading calls agent with is_final=False."""
        mock_agent = MagicMock()
        mock_agent.run.return_value = [
            GradingResult(grader="Test", score=3.0, reasoning="OK"),
        ]
        mock_agent_class.return_value = mock_agent

        articles = sample_selected_articles[:1]
        state: BatchGradingTaskInput = {
            "persona": ANNIE,
            "articles": articles,
            "is_final": False,
        }

        batch_cross_grading_node(state)

        mock_agent.run.assert_called_once_with(articles, is_final=False)


class TestAggregatePhase3Node:
    """Tests for aggregate_phase3_node function."""

    def test_aggregate_phase3_returns_finalists(
        self, sample_selected_articles: list[SelectedArticle]
    ):
        """Test aggregate_phase3 returns finalists list."""
        state: NewsletterState = {
            "selected_articles": sample_selected_articles,
            "phase3_grades": [],
        }

        result = aggregate_phase3_node(state)

        assert "finalists" in result
        assert isinstance(result["finalists"], list)

    def test_aggregate_phase3_uses_grades(
        self, sample_selected_articles: list[SelectedArticle]
    ):
        """Test aggregate_phase3 processes grade data."""
        grades = [
            {
                "article_idx": 0,
                "grade": GradingResult(grader="Annie", score=5.0, reasoning="Great"),
            }
        ]
        state: NewsletterState = {
            "selected_articles": sample_selected_articles,
            "phase3_grades": grades,
        }

        result = aggregate_phase3_node(state)

        # Should have finalists with scores
        assert len(result["finalists"]) > 0


class TestBatchFinalGradingNode:
    """Tests for batch_final_grading_node function."""

    @patch("src.pipelines.newsletter_nodes.BatchGraderAgent")
    def test_batch_final_grading_returns_grade_list(
        self, mock_agent_class: MagicMock, sample_selected_articles: list[SelectedArticle]
    ):
        """Test batch final grading returns final_grades list."""
        mock_agent = MagicMock()
        mock_agent.run.return_value = [
            GradingResult(grader="Joana", score=5.0, reasoning="Excellent"),
            GradingResult(grader="Joana", score=4.5, reasoning="Great"),
        ]
        mock_agent_class.return_value = mock_agent

        articles = sample_selected_articles[:2]
        state: BatchGradingTaskInput = {
            "persona": JOANA,
            "articles": articles,
            "is_final": True,
        }

        result = batch_final_grading_node(state)

        assert "final_grades" in result
        assert len(result["final_grades"]) == 2
        assert result["final_grades"][0]["article_idx"] == 0
        assert result["final_grades"][0]["grade"].score == 5.0
        assert result["final_grades"][1]["article_idx"] == 1
        assert result["final_grades"][1]["grade"].score == 4.5

    @patch("src.pipelines.newsletter_nodes.BatchGraderAgent")
    def test_batch_final_grading_calls_agent_with_is_final_true(
        self, mock_agent_class: MagicMock, sample_selected_articles: list[SelectedArticle]
    ):
        """Test batch final grading calls agent with is_final=True."""
        mock_agent = MagicMock()
        mock_agent.run.return_value = [
            GradingResult(grader="Test", score=4.0, reasoning="Good"),
        ]
        mock_agent_class.return_value = mock_agent

        articles = sample_selected_articles[:1]
        state: BatchGradingTaskInput = {
            "persona": JOHNNY,
            "articles": articles,
            "is_final": True,
        }

        batch_final_grading_node(state)

        mock_agent.run.assert_called_once_with(articles, is_final=True)


class TestAggregateFinalNode:
    """Tests for aggregate_final_node function."""

    def test_aggregate_final_returns_ranked_articles(
        self, sample_selected_articles: list[SelectedArticle]
    ):
        """Test aggregate_final returns ranked_articles list."""
        finalists = sample_selected_articles[:3]
        state: NewsletterState = {
            "finalists": finalists,
            "final_grades": [],
        }

        result = aggregate_final_node(state)

        assert "ranked_articles" in result
        assert isinstance(result["ranked_articles"], list)

    def test_aggregate_final_processes_grades(
        self, sample_selected_articles: list[SelectedArticle]
    ):
        """Test aggregate_final processes final grades."""
        finalists = sample_selected_articles[:2]
        grades = [
            {
                "article_idx": 0,
                "grade": GradingResult(grader="Johnny", score=5.0, reasoning="Best"),
            },
            {
                "article_idx": 1,
                "grade": GradingResult(grader="Johnny", score=3.0, reasoning="OK"),
            },
        ]
        state: NewsletterState = {
            "finalists": finalists,
            "final_grades": grades,
        }

        result = aggregate_final_node(state)

        # First article should have higher score
        assert result["ranked_articles"][0].final_avg == 5.0


class TestGenerateHtmlNode:
    """Tests for generate_html_node function."""

    @patch("src.pipelines.newsletter_nodes.render_newsletter")
    def test_generate_returns_html_path(
        self, mock_render: MagicMock, sample_selected_articles: list[SelectedArticle]
    ):
        """Test generate node returns generated_html path."""
        mock_render.return_value = "/path/to/newsletter.html"

        state: NewsletterState = {
            "ranked_articles": sample_selected_articles,
            "output_path": "test_output.html",
        }

        result = generate_html_node(state)

        assert "generated_html" in result
        assert result["generated_html"] == "/path/to/newsletter.html"

    @patch("src.pipelines.newsletter_nodes.render_newsletter")
    def test_generate_passes_articles_and_path(
        self, mock_render: MagicMock, sample_selected_articles: list[SelectedArticle]
    ):
        """Test generate passes correct args to renderer."""
        mock_render.return_value = "output.html"

        state: NewsletterState = {
            "ranked_articles": sample_selected_articles,
            "output_path": "custom_path.html",
        }

        generate_html_node(state)

        mock_render.assert_called_once_with(sample_selected_articles, "custom_path.html")

    @patch("src.pipelines.newsletter_nodes.render_newsletter")
    def test_generate_uses_default_path(
        self, mock_render: MagicMock, sample_selected_articles: list[SelectedArticle]
    ):
        """Test generate uses default path when not specified."""
        mock_render.return_value = "default.html"

        state: NewsletterState = {
            "ranked_articles": sample_selected_articles,
        }

        generate_html_node(state)

        # Should have called with a default path containing date
        call_args = mock_render.call_args[0]
        assert "newsletter_" in call_args[1]
        assert ".html" in call_args[1]
