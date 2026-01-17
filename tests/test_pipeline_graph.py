"""Tests for pipeline graph construction and routing."""

from unittest.mock import MagicMock, patch

import pytest
from langgraph.types import Send

from src.core.models import Article, SelectedArticle
from src.core.personas import ALL_PERSONAS, ANNIE, JOHNNY, JOANA
from src.pipelines.newsletter_graph import (
    build_newsletter_graph,
    newsletter_graph,
    route_to_batch_cross_grading,
    route_to_batch_final_grading,
    route_to_selection,
)
from src.pipelines.newsletter_state import NewsletterState


class TestRouteToSelection:
    """Tests for route_to_selection routing function."""

    def test_route_creates_send_per_persona(self, sample_articles: list[Article]):
        """Test routing creates a Send for each persona."""
        state: NewsletterState = {"articles": sample_articles}

        sends = route_to_selection(state)

        assert len(sends) == len(ALL_PERSONAS)
        assert all(isinstance(s, Send) for s in sends)

    def test_route_sends_to_selection_node(self, sample_articles: list[Article]):
        """Test all Sends target the 'selection' node."""
        state: NewsletterState = {"articles": sample_articles}

        sends = route_to_selection(state)

        for send in sends:
            assert send.node == "selection"

    def test_route_includes_persona_and_articles(self, sample_articles: list[Article]):
        """Test each Send includes persona and full article list."""
        state: NewsletterState = {"articles": sample_articles}

        sends = route_to_selection(state)

        persona_names = set()
        for send in sends:
            assert "persona" in send.arg
            assert "articles" in send.arg
            assert send.arg["articles"] == sample_articles
            persona_names.add(send.arg["persona"].name)

        # All personas should be included
        expected_names = {p.name for p in ALL_PERSONAS}
        assert persona_names == expected_names

    def test_route_empty_articles_returns_empty(self):
        """Test routing with no articles returns empty list."""
        state: NewsletterState = {"articles": []}

        sends = route_to_selection(state)

        assert sends == []


class TestRouteToBatchCrossGrading:
    """Tests for route_to_batch_cross_grading routing function."""

    def test_route_creates_send_per_persona(
        self, sample_articles: list[Article]
    ):
        """Test batch routing creates one Send per persona."""
        selected = [
            SelectedArticle(article=sample_articles[0], selected_by=["Johnny"]),
            SelectedArticle(article=sample_articles[1], selected_by=["Annie"]),
        ]
        state: NewsletterState = {"selected_articles": selected}

        sends = route_to_batch_cross_grading(state)

        # Batch mode: one call per persona (3 total), not per article
        assert len(sends) == len(ALL_PERSONAS)

    def test_route_sends_to_batch_cross_grading_node(
        self, sample_articles: list[Article]
    ):
        """Test all Sends target 'batch_cross_grading' node."""
        selected = [
            SelectedArticle(article=sample_articles[0], selected_by=["Johnny"]),
        ]
        state: NewsletterState = {"selected_articles": selected}

        sends = route_to_batch_cross_grading(state)

        for send in sends:
            assert send.node == "batch_cross_grading"

    def test_route_includes_all_articles(self, sample_articles: list[Article]):
        """Test each Send includes all selected articles."""
        selected = [
            SelectedArticle(article=sample_articles[0], selected_by=[]),
            SelectedArticle(article=sample_articles[1], selected_by=[]),
        ]
        state: NewsletterState = {"selected_articles": selected}

        sends = route_to_batch_cross_grading(state)

        for send in sends:
            assert send.arg["articles"] == selected

    def test_route_empty_selected_returns_empty(self):
        """Test routing with no selected articles returns empty."""
        state: NewsletterState = {"selected_articles": []}

        sends = route_to_batch_cross_grading(state)

        assert sends == []


class TestRouteToBatchFinalGrading:
    """Tests for route_to_batch_final_grading routing function."""

    def test_route_creates_send_per_persona(
        self, sample_articles: list[Article]
    ):
        """Test batch routing creates one Send per persona."""
        finalists = [
            SelectedArticle(article=sample_articles[0], selected_by=["Johnny"]),
            SelectedArticle(article=sample_articles[1], selected_by=["Annie"]),
        ]
        state: NewsletterState = {"finalists": finalists}

        sends = route_to_batch_final_grading(state)

        # Batch mode: one call per persona (3 total), not per finalist
        assert len(sends) == len(ALL_PERSONAS)

    def test_route_sends_to_batch_final_grading_node(
        self, sample_articles: list[Article]
    ):
        """Test all Sends target 'batch_final_grading' node."""
        finalists = [
            SelectedArticle(article=sample_articles[0], selected_by=[]),
        ]
        state: NewsletterState = {"finalists": finalists}

        sends = route_to_batch_final_grading(state)

        for send in sends:
            assert send.node == "batch_final_grading"

    def test_route_sets_is_final_true(self, sample_articles: list[Article]):
        """Test all final grading tasks have is_final=True."""
        finalists = [
            SelectedArticle(article=sample_articles[0], selected_by=[]),
        ]
        state: NewsletterState = {"finalists": finalists}

        sends = route_to_batch_final_grading(state)

        for send in sends:
            assert send.arg["is_final"] is True

    def test_route_empty_finalists_returns_empty(self):
        """Test routing with no finalists returns empty."""
        state: NewsletterState = {"finalists": []}

        sends = route_to_batch_final_grading(state)

        assert sends == []


class TestBuildNewsletterGraph:
    """Tests for graph construction."""

    def test_build_returns_compiled_graph(self):
        """Test build_newsletter_graph returns a compiled graph."""
        graph = build_newsletter_graph()

        # Should have nodes
        assert graph is not None

    def test_prebuilt_graph_exists(self):
        """Test newsletter_graph module-level instance exists."""
        assert newsletter_graph is not None

    def test_graph_has_expected_nodes(self):
        """Test graph contains all expected nodes."""
        graph = build_newsletter_graph()

        # Get node names from graph
        node_names = set(graph.nodes.keys())

        expected_nodes = {
            "sourcing",
            "selection",
            "aggregate_selections",
            "batch_cross_grading",
            "aggregate_phase3",
            "batch_final_grading",
            "aggregate_final",
            "generate",
        }

        # All expected nodes should be present
        for node in expected_nodes:
            assert node in node_names, f"Missing node: {node}"


class TestGraphIntegration:
    """Integration tests for graph structure."""

    def test_graph_is_compiled(self):
        """Test the graph is properly compiled and can be inspected."""
        # Graph should be a compiled state graph
        assert newsletter_graph is not None
        # Should have the invoke method (indicates it's compiled)
        assert hasattr(newsletter_graph, "invoke")
        assert hasattr(newsletter_graph, "nodes")

    def test_graph_nodes_are_present(self):
        """Test all expected nodes exist in the compiled graph."""
        node_names = set(newsletter_graph.nodes.keys())

        # Core pipeline nodes
        assert "sourcing" in node_names
        assert "selection" in node_names
        assert "aggregate_selections" in node_names
        assert "batch_cross_grading" in node_names
        assert "aggregate_phase3" in node_names
        assert "batch_final_grading" in node_names
        assert "aggregate_final" in node_names
        assert "generate" in node_names
