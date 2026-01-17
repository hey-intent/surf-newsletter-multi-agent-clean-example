"""Batch Grader agent for scoring multiple articles in a single call.

Scientific basis: Batch prompting (Cheng et al., 2023 - arXiv:2301.08721)
reduces API calls while maintaining accuracy through structured prompts.
"""

from __future__ import annotations

import logging
from typing import Sequence

from src.agents.base import BaseAgent
from src.core.models import Article, GradingResult, SelectedArticle

logger = logging.getLogger(__name__)


class BatchGraderAgent(BaseAgent):
    """Agent that grades multiple articles in a single LLM call.

    Uses structured prompts with clear separators to prevent
    inter-article interference (per BatchPrompt research).
    """

    def run(
        self,
        articles: Sequence[SelectedArticle],
        is_final: bool = False,
    ) -> list[GradingResult]:
        """Grade multiple articles in one call.

        Args:
            articles: List of articles to grade.
            is_final: Whether this is the final grading round.

        Returns:
            List of GradingResult, one per article (same order).
        """
        # Set call type for token tracking
        self._call_type = "batch_grading_final" if is_final else "batch_grading_phase3"

        if not articles:
            return []

        logger.info(f"   {self.name}: Batch grading {len(articles)} articles...")

        prompt = self._build_batch_prompt(articles, is_final)
        response = self._call_llm(prompt)
        results = self._parse_batch_response(response, len(articles))

        return results

    def _build_batch_prompt(
        self,
        articles: Sequence[SelectedArticle],
        is_final: bool,
    ) -> str:
        """Build structured batch prompt with clear separators.

        Following batch prompting best practices:
        - Numbered articles for unambiguous reference
        - Clear separators (---) between items
        - Explicit independence instruction
        - Structured output format (JSON array)
        """
        context = "FINAL ROUND for ranking." if is_final else ""

        # Build article blocks with clear numbering
        article_blocks = []
        for i, sel_article in enumerate(articles):
            art = sel_article.article
            block = f"""---
ARTICLE #{i + 1}
Title: {art.title}
Source: {art.source}
Summary: {art.excerpt[:300]}
---"""
            article_blocks.append(block)

        articles_text = "\n\n".join(article_blocks)

        return f"""{context}
Grade each article INDEPENDENTLY according to YOUR criteria:

{self.persona.criteria_text}

IMPORTANT: Evaluate each article on its own merits. Do not compare articles.
Process them one by one, as if you were seeing each for the first time.

{articles_text}

SCORING GUIDE (use the full range):
- 5: Exceptional, perfectly matches your criteria - rare
- 4: Very good, strong match on multiple criteria
- 3: Decent, some relevant aspects
- 2: Weak, minimal connection to your interests
- 1: Not relevant to your criteria at all

Be honest and calibrated. Most articles should score 2-4.
Reserve 5 for truly outstanding content. Don't hesitate to give 1-2 for poor matches.

Return a JSON array with EXACTLY {len(articles)} objects, one per article IN ORDER:
[
  {{"article_num": 1, "score": X, "reasoning": "...", "key_strengths": ["...", "..."]}},
  {{"article_num": 2, "score": X, "reasoning": "...", "key_strengths": ["...", "..."]}},
  ...
]

CRITICAL: Return exactly {len(articles)} grades in the same order as the articles."""

    def _parse_batch_response(
        self,
        response: str,
        expected_count: int,
    ) -> list[GradingResult]:
        """Parse batch response into individual GradingResults.

        Args:
            response: LLM response containing JSON array.
            expected_count: Number of articles we expect grades for.

        Returns:
            List of GradingResult objects.
        """
        # Try to extract JSON array from response
        import re

        # First try standard JSON parsing
        parsed = self._parse_json(response)

        # Handle both array and dict-with-array responses
        if isinstance(parsed, dict):
            # LLM might wrap in {"grades": [...]} or similar
            # Also handle our parse_json_response which wraps arrays in {"items": [...]}
            for key in ["items", "grades", "results", "articles", "scores", "evaluations"]:
                if key in parsed and isinstance(parsed[key], list):
                    parsed = parsed[key]
                    break
            else:
                # Single grade returned as dict - wrap it
                parsed = [parsed]

        if not isinstance(parsed, list):
            # Try to find multiple JSON objects in the response
            # Pattern: multiple {...} blocks
            json_pattern = r'\{[^{}]*"score"[^{}]*\}'
            matches = re.findall(json_pattern, response, re.DOTALL)
            if matches:
                logger.debug(f"   {self.name}: Found {len(matches)} individual JSON blocks")
                parsed = []
                for match in matches:
                    try:
                        import json
                        obj = json.loads(match)
                        parsed.append(obj)
                    except json.JSONDecodeError:
                        continue

        if not isinstance(parsed, list) or len(parsed) == 0:
            logger.warning(f"   {self.name}: Could not parse response, using defaults")
            return [self._default_result() for _ in range(expected_count)]

        # Log what we got
        logger.debug(f"   {self.name}: Parsed {len(parsed)} grades (expected {expected_count})")

        results = []
        for i in range(expected_count):
            if i < len(parsed):
                grade_data = parsed[i]
                results.append(self._parse_single_grade(grade_data))
            else:
                # Missing grade - use default
                logger.warning(f"   {self.name}: Missing grade for article {i + 1}")
                results.append(self._default_result())

        return results

    def _parse_single_grade(self, data: dict) -> GradingResult:
        """Parse a single grade from the batch response."""
        score = data.get("score", 3.0)
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
            reasoning=data.get("reasoning", "No reasoning provided"),
            key_strengths=data.get("key_strengths", []),
        )

    def _default_result(self) -> GradingResult:
        """Return a default grade when parsing fails."""
        return GradingResult(
            grader=self.name,
            score=3.0,
            reasoning="Default score (parsing error)",
            key_strengths=[],
        )
