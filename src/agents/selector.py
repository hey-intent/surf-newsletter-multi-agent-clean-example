"""Selector agent for choosing the best articles."""

from __future__ import annotations

import logging

from src.agents.base import BaseAgent
from src.core.config import ARTICLES_PER_AGENT
from src.core.models import Article

logger = logging.getLogger(__name__)


class SelectorAgent(BaseAgent):
    """Agent that selects the best articles according to its persona.

    The selector evaluates articles based on the persona's criteria
    and returns the indices of the top k articles.
    """

    _call_type = "selection"

    def run(self, articles: list[Article], k: int = ARTICLES_PER_AGENT) -> list[int]:
        """Select the top k articles.

        Args:
            articles: List of articles to choose from.
            k: Number of articles to select.

        Returns:
            List of indices of selected articles.
        """
        logger.info(f"   {self.name}: Selecting {k} articles from {len(articles)}...")

        prompt = self._build_prompt(articles, k)
        response = self._call_llm(prompt)
        indices = self._parse_response(response, k, len(articles))

        logger.info(f"   {self.name}: Selected {len(indices)} articles")
        return indices

    def _build_prompt(self, articles: list[Article], k: int) -> str:
        """Build the selection prompt.

        Args:
            articles: List of articles.
            k: Number to select.

        Returns:
            Formatted prompt string.
        """
        articles_text = "\n\n".join(
            f"[{i}] {a.title}\n    Source: {a.source}\n    Summary: {a.excerpt[:200]}..."
            for i, a in enumerate(articles)
        )

        return f"""Analyze these {len(articles)} surf articles.
Select the {k} MOST relevant according to YOUR evaluation criteria:

{self.persona.criteria_text}

ARTICLES:
{articles_text}

Return a JSON with the indices of the {k} best articles:
{{"selected": [0, 5, 12, ...], "reasoning": "Brief explanation"}}"""

    def _parse_response(self, response: str, k: int, total: int) -> list[int]:
        """Parse selection response and validate indices.

        Args:
            response: LLM response string.
            k: Expected number of selections.
            total: Total number of articles.

        Returns:
            List of valid article indices.
        """
        parsed = self._parse_json(response)
        selected = parsed.get("selected", [])[:k]

        # Validate indices
        valid_indices = [
            idx for idx in selected
            if isinstance(idx, int) and 0 <= idx < total
        ]

        # Fill if needed
        if len(valid_indices) < k:
            for i in range(total):
                if i not in valid_indices:
                    valid_indices.append(i)
                if len(valid_indices) >= k:
                    break

        return valid_indices
