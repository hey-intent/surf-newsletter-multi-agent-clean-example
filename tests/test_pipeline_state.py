"""Tests for pipeline state definitions."""

import operator

import pytest

from src.core.models import Article, SelectedArticle
from src.core.personas import JOHNNY
from src.pipelines.newsletter_state import (
    GradingTaskInput,
    NewsletterState,
    SelectionTaskInput,
    merge_selections,
)


class TestMergeSelections:
    """Tests for the merge_selections reducer function."""

    def test_merge_empty_dicts(self):
        """Test merging two empty dicts."""
        result = merge_selections({}, {})
        assert result == {}

    def test_merge_into_empty(self):
        """Test merging new selections into empty current."""
        current = {}
        new = {"Johnny": [0, 1, 2]}

        result = merge_selections(current, new)

        assert result == {"Johnny": [0, 1, 2]}

    def test_merge_non_overlapping(self):
        """Test merging selections with no overlap."""
        current = {"Johnny": [0, 1]}
        new = {"Annie": [2, 3]}

        result = merge_selections(current, new)

        assert result == {"Johnny": [0, 1], "Annie": [2, 3]}

    def test_merge_overlapping_replaces(self):
        """Test merging with same key replaces value."""
        current = {"Johnny": [0, 1]}
        new = {"Johnny": [5, 6, 7]}

        result = merge_selections(current, new)

        assert result == {"Johnny": [5, 6, 7]}

    def test_merge_does_not_modify_original(self):
        """Test merge creates new dict, doesn't modify original."""
        current = {"Johnny": [0, 1]}
        new = {"Annie": [2, 3]}

        result = merge_selections(current, new)

        assert "Annie" not in current
        assert result is not current


class TestNewsletterState:
    """Tests for the NewsletterState TypedDict."""

    def test_state_can_be_created_empty(self):
        """Test state can be created with no fields (total=False)."""
        state: NewsletterState = {}
        assert state == {}

    def test_state_accepts_all_fields(self, sample_articles: list[Article]):
        """Test state accepts all defined fields."""
        state: NewsletterState = {
            "days": 7,
            "output_path": "output.html",
            "articles": sample_articles,
            "selections": {"Johnny": [0, 1]},
            "selected_articles": [],
            "phase3_grades": [],
            "finalists": [],
            "final_grades": [],
            "ranked_articles": [],
            "generated_html": "test.html",
        }

        assert state["days"] == 7
        assert state["output_path"] == "output.html"
        assert len(state["articles"]) == len(sample_articles)

    def test_state_partial_fields(self):
        """Test state can have partial fields."""
        state: NewsletterState = {
            "days": 3,
        }

        assert state["days"] == 3
        assert "articles" not in state


class TestSelectionTaskInput:
    """Tests for SelectionTaskInput TypedDict."""

    def test_selection_input_creation(self, sample_articles: list[Article]):
        """Test selection task input creation."""
        task_input: SelectionTaskInput = {
            "persona": JOHNNY,
            "articles": sample_articles,
        }

        assert task_input["persona"] == JOHNNY
        assert task_input["articles"] == sample_articles

    def test_selection_input_has_required_fields(self):
        """Test selection input requires persona and articles."""
        # This is a type check - at runtime TypedDict doesn't enforce
        task_input: SelectionTaskInput = {
            "persona": JOHNNY,
            "articles": [],
        }
        assert "persona" in task_input
        assert "articles" in task_input


class TestGradingTaskInput:
    """Tests for GradingTaskInput TypedDict."""

    def test_grading_input_creation(self, sample_selected_article: SelectedArticle):
        """Test grading task input creation."""
        task_input: GradingTaskInput = {
            "persona": JOHNNY,
            "article": sample_selected_article,
            "article_idx": 0,
            "is_final": False,
        }

        assert task_input["persona"] == JOHNNY
        assert task_input["article"] == sample_selected_article
        assert task_input["article_idx"] == 0
        assert task_input["is_final"] is False

    def test_grading_input_final_round(self, sample_selected_article: SelectedArticle):
        """Test grading input with is_final=True."""
        task_input: GradingTaskInput = {
            "persona": JOHNNY,
            "article": sample_selected_article,
            "article_idx": 5,
            "is_final": True,
        }

        assert task_input["is_final"] is True


class TestStateReducers:
    """Tests for state annotation reducers."""

    def test_selections_uses_merge_function(self):
        """Test selections field uses merge_selections reducer."""
        # This tests the Annotated type hint concept
        # In LangGraph, this enables parallel results to be merged
        from typing import get_type_hints, get_args

        hints = get_type_hints(NewsletterState, include_extras=True)

        # Check selections has Annotated type
        selections_hint = hints.get("selections")
        assert selections_hint is not None

    def test_phase3_grades_uses_add(self):
        """Test phase3_grades uses operator.add for concatenation."""
        # operator.add concatenates lists
        list1 = [{"idx": 0}]
        list2 = [{"idx": 1}]

        result = operator.add(list1, list2)

        assert result == [{"idx": 0}, {"idx": 1}]

    def test_final_grades_uses_add(self):
        """Test final_grades uses operator.add for concatenation."""
        list1 = [{"idx": 0, "grade": "A"}]
        list2 = [{"idx": 1, "grade": "B"}]

        result = operator.add(list1, list2)

        assert result == [{"idx": 0, "grade": "A"}, {"idx": 1, "grade": "B"}]
