"""Grader agent for scoring articles."""

from __future__ import annotations

import logging

from src.agents.base import BaseAgent
from src.core.models import Article, GradingResult

logger = logging.getLogger(__name__)


class GraderAgent(BaseAgent):
    """Agent that grades articles according to its persona.

    The grader evaluates a single article based on the persona's
    criteria and returns a score with justification.
    """

    def run(self, article: Article, is_final: bool = False) -> GradingResult:
        """Grade an article.

        Args:
            article: The article to grade.
            is_final: Whether this is the final grading round.

        Returns:
            GradingResult with score and reasoning.
        """
        logger.debug(f"   {self.name}: Grading '{article.title[:40]}...'")

        prompt = self._build_prompt(article, is_final)
        response = self._call_llm(prompt)
        result = self._parse_response(response)

        return result

    def _build_prompt(self, article: Article, is_final: bool) -> str:
        """Build the grading prompt.

        Args:
            article: The article to grade.
            is_final: Whether this is final round.

        Returns:
            Formatted prompt string.
        """
        context = "FINAL ROUND for ranking." if is_final else ""

        return f"""{context}
Evaluate this article according to YOUR criteria:

{self.persona.criteria_text}

ARTICLE:
Title: {article.title}
Source: {article.source}
Summary: {article.excerpt}

SCORING GUIDE (use the full range):
- 5: Exceptional, perfectly matches your criteria - rare
- 4: Very good, strong match on multiple criteria
- 3: Decent, some relevant aspects
- 2: Weak, minimal connection to your interests
- 1: Not relevant to your criteria at all

Be honest and calibrated. Most articles should score 2-4.
Reserve 5 for truly outstanding content. Don't hesitate to give 1-2 for poor matches.

Return a JSON:
{{"score": X, "reasoning": "...", "key_strengths": ["...", "..."]}}"""

    def _parse_response(self, response: str) -> GradingResult:
        """Parse grading response.

        Args:
            response: LLM response string.

        Returns:
            GradingResult with validated score.
        """
        parsed = self._parse_json(response)

        score = parsed.get("score", 3.0)
        if isinstance(score, str):
            try:
                score = float(score)
            except ValueError:
                score = 3.0

        # Clamp to valid range
        score = max(1.0, min(5.0, float(score)))

        return GradingResult(
            grader=self.name,
            score=score,
            reasoning=parsed.get("reasoning", "No reasoning provided"),
            key_strengths=parsed.get("key_strengths", []),
        )
