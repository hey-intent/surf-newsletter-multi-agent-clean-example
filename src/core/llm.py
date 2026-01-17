"""LLM utilities and factory functions."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from langchain_openai import ChatOpenAI

from src.core.config import LLM_BASE_URL, LLM_MAX_TOKENS, LLM_MODEL, LLM_TEMPERATURE

logger = logging.getLogger(__name__)

_llm_instance: ChatOpenAI | None = None


def get_llm() -> ChatOpenAI:
    """Get or create a singleton LLM instance.

    Returns:
        Configured ChatOpenAI instance.

    Raises:
        ValueError: If OPENROUTER_API_KEY environment variable is not set.
    """
    global _llm_instance

    if _llm_instance is None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable is not set. "
                "Please set it in your .env file or environment."
            )

        _llm_instance = ChatOpenAI(
            model=LLM_MODEL,
            base_url=LLM_BASE_URL,
            api_key=api_key,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
        )

    return _llm_instance


def parse_json_response(response: str) -> dict[str, Any]:
    """Extract JSON from LLM response.

    Handles responses that may contain markdown code blocks or
    extra text around the JSON.

    Args:
        response: Raw LLM response string.

    Returns:
        Parsed JSON as a dictionary, or empty dict if parsing fails.
    """
    # Try to find JSON object
    start = response.find("{")
    end = response.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass

    # Try to find JSON array
    start = response.find("[")
    end = response.rfind("]") + 1
    if start != -1 and end > start:
        try:
            return {"items": json.loads(response[start:end])}
        except json.JSONDecodeError:
            pass

    logger.warning(f"Could not parse JSON from response: {response[:200]}...")
    return {}


def reset_llm() -> None:
    """Reset the LLM singleton (useful for testing)."""
    global _llm_instance
    _llm_instance = None
