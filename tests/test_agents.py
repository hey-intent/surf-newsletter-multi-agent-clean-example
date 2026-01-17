"""Tests for agents (selector and grader)."""

from unittest.mock import MagicMock, patch

import pytest

from src.agents.grader import GraderAgent
from src.agents.selector import SelectorAgent
from src.core.models import Article, GradingResult
from src.core.personas import JOHNNY, Persona


class TestSelectorAgent:
    """Tests for the SelectorAgent."""

    def test_selector_creation(self, sample_persona: Persona):
        """Test selector agent creation with persona."""
        agent = SelectorAgent(sample_persona)
        assert agent.name == "TestPersona"
        assert agent.persona == sample_persona

    def test_selector_name_from_persona(self):
        """Test selector gets name from persona."""
        agent = SelectorAgent(JOHNNY)
        assert agent.name == "Johnny"

    def test_build_prompt_includes_criteria(
        self, sample_persona: Persona, sample_articles: list[Article]
    ):
        """Test selection prompt includes persona criteria."""
        agent = SelectorAgent(sample_persona)
        prompt = agent._build_prompt(sample_articles, k=3)

        assert sample_persona.criteria_text in prompt
        assert "3" in prompt  # k value
        assert str(len(sample_articles)) in prompt  # total articles

    def test_build_prompt_includes_articles(
        self, sample_persona: Persona, sample_articles: list[Article]
    ):
        """Test selection prompt includes article info."""
        agent = SelectorAgent(sample_persona)
        prompt = agent._build_prompt(sample_articles, k=3)

        for i, article in enumerate(sample_articles):
            assert f"[{i}]" in prompt
            assert article.title in prompt
            assert article.source in prompt

    def test_parse_response_valid(self, sample_persona: Persona):
        """Test parsing valid selection response."""
        agent = SelectorAgent(sample_persona)
        response = '{"selected": [0, 2, 4], "reasoning": "Good picks"}'

        indices = agent._parse_response(response, k=3, total=5)

        assert indices == [0, 2, 4]
        assert len(indices) == 3

    def test_parse_response_filters_invalid_indices(self, sample_persona: Persona):
        """Test invalid indices are filtered out."""
        agent = SelectorAgent(sample_persona)
        response = '{"selected": [0, 10, -1, 2], "reasoning": "Mixed"}'

        indices = agent._parse_response(response, k=3, total=5)

        # Only 0 and 2 are valid (10 and -1 out of range)
        assert 0 in indices
        assert 2 in indices
        assert 10 not in indices
        assert -1 not in indices

    def test_parse_response_fills_if_needed(self, sample_persona: Persona):
        """Test response fills up to k if not enough valid indices."""
        agent = SelectorAgent(sample_persona)
        response = '{"selected": [0], "reasoning": "Only one"}'

        indices = agent._parse_response(response, k=3, total=5)

        assert len(indices) == 3
        assert 0 in indices

    def test_parse_response_truncates_if_too_many(self, sample_persona: Persona):
        """Test response is truncated if more than k indices."""
        agent = SelectorAgent(sample_persona)
        response = '{"selected": [0, 1, 2, 3, 4], "reasoning": "All"}'

        indices = agent._parse_response(response, k=3, total=5)

        assert len(indices) == 3

    @patch.object(SelectorAgent, "_call_llm")
    def test_run_calls_llm(
        self,
        mock_llm: MagicMock,
        sample_persona: Persona,
        sample_articles: list[Article],
    ):
        """Test run method calls LLM and parses response."""
        mock_llm.return_value = '{"selected": [1, 3], "reasoning": "Selected"}'

        agent = SelectorAgent(sample_persona)
        indices = agent.run(sample_articles, k=2)

        mock_llm.assert_called_once()
        assert len(indices) == 2
        assert 1 in indices
        assert 3 in indices


class TestGraderAgent:
    """Tests for the GraderAgent."""

    def test_grader_creation(self, sample_persona: Persona):
        """Test grader agent creation with persona."""
        agent = GraderAgent(sample_persona)
        assert agent.name == "TestPersona"
        assert agent.persona == sample_persona

    def test_grader_name_from_persona(self):
        """Test grader gets name from persona."""
        agent = GraderAgent(JOHNNY)
        assert agent.name == "Johnny"

    def test_build_prompt_includes_criteria(
        self, sample_persona: Persona, sample_article: Article
    ):
        """Test grading prompt includes persona criteria."""
        agent = GraderAgent(sample_persona)
        prompt = agent._build_prompt(sample_article, is_final=False)

        assert sample_persona.criteria_text in prompt

    def test_build_prompt_includes_article_info(
        self, sample_persona: Persona, sample_article: Article
    ):
        """Test grading prompt includes article details."""
        agent = GraderAgent(sample_persona)
        prompt = agent._build_prompt(sample_article, is_final=False)

        assert sample_article.title in prompt
        assert sample_article.source in prompt
        assert sample_article.excerpt in prompt

    def test_build_prompt_final_round_context(
        self, sample_persona: Persona, sample_article: Article
    ):
        """Test final round adds context to prompt."""
        agent = GraderAgent(sample_persona)

        prompt_normal = agent._build_prompt(sample_article, is_final=False)
        prompt_final = agent._build_prompt(sample_article, is_final=True)

        assert "FINAL ROUND" in prompt_final
        assert "FINAL ROUND" not in prompt_normal

    def test_build_prompt_includes_scoring_guide(
        self, sample_persona: Persona, sample_article: Article
    ):
        """Test grading prompt includes scoring guide."""
        agent = GraderAgent(sample_persona)
        prompt = agent._build_prompt(sample_article, is_final=False)

        assert "SCORING GUIDE" in prompt
        assert "5: Exceptional" in prompt
        assert "1: Not relevant" in prompt

    def test_parse_response_valid(self, sample_persona: Persona):
        """Test parsing valid grading response."""
        agent = GraderAgent(sample_persona)
        response = '{"score": 4, "reasoning": "Good article", "key_strengths": ["Strong", "Relevant"]}'

        result = agent._parse_response(response)

        assert result.grader == "TestPersona"
        assert result.score == 4.0
        assert result.reasoning == "Good article"
        assert result.key_strengths == ["Strong", "Relevant"]

    def test_parse_response_clamps_high_score(self, sample_persona: Persona):
        """Test scores above 5 are clamped."""
        agent = GraderAgent(sample_persona)
        response = '{"score": 10, "reasoning": "Too high"}'

        result = agent._parse_response(response)

        assert result.score == 5.0

    def test_parse_response_clamps_low_score(self, sample_persona: Persona):
        """Test scores below 1 are clamped."""
        agent = GraderAgent(sample_persona)
        response = '{"score": 0, "reasoning": "Too low"}'

        result = agent._parse_response(response)

        assert result.score == 1.0

    def test_parse_response_handles_string_score(self, sample_persona: Persona):
        """Test score provided as string is converted."""
        agent = GraderAgent(sample_persona)
        response = '{"score": "3.5", "reasoning": "String score"}'

        result = agent._parse_response(response)

        assert result.score == 3.5

    def test_parse_response_default_score(self, sample_persona: Persona):
        """Test default score when missing."""
        agent = GraderAgent(sample_persona)
        response = '{"reasoning": "No score provided"}'

        result = agent._parse_response(response)

        assert result.score == 3.0

    def test_parse_response_default_reasoning(self, sample_persona: Persona):
        """Test default reasoning when missing."""
        agent = GraderAgent(sample_persona)
        response = '{"score": 4}'

        result = agent._parse_response(response)

        assert result.reasoning == "No reasoning provided"

    def test_parse_response_default_strengths(self, sample_persona: Persona):
        """Test default empty strengths when missing."""
        agent = GraderAgent(sample_persona)
        response = '{"score": 4, "reasoning": "Test"}'

        result = agent._parse_response(response)

        assert result.key_strengths == []

    @patch.object(GraderAgent, "_call_llm")
    def test_run_calls_llm(
        self, mock_llm: MagicMock, sample_persona: Persona, sample_article: Article
    ):
        """Test run method calls LLM and returns GradingResult."""
        mock_llm.return_value = '{"score": 4, "reasoning": "Good", "key_strengths": ["Test"]}'

        agent = GraderAgent(sample_persona)
        result = agent.run(sample_article, is_final=False)

        mock_llm.assert_called_once()
        assert isinstance(result, GradingResult)
        assert result.score == 4.0
