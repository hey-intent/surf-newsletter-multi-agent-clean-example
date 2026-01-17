"""Base agent class for all AI agents."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.llm import get_llm, parse_json_response
from src.core.personas import Persona

logger = logging.getLogger(__name__)

# Global token counter for the session
_token_usage: dict[str, dict[str, int]] = {}


def get_token_usage() -> dict[str, dict[str, int]]:
    """Get accumulated token usage by call type."""
    return _token_usage.copy()


def reset_token_usage() -> None:
    """Reset token counters."""
    global _token_usage
    _token_usage = {}


class BaseAgent(ABC):
    """Abstract base class for all agents.

    An agent combines a Persona (editorial perspective) with
    specific behavior (selection, grading, etc.).
    """

    # Default call type, override in subclasses
    _call_type: str = "unknown"

    def __init__(self, persona: Persona):
        """Initialize the agent with a persona.

        Args:
            persona: The persona that defines this agent's perspective.
        """
        self.persona = persona
        self._llm: ChatOpenAI | None = None

    @property
    def name(self) -> str:
        """Get the agent's name (from persona)."""
        return self.persona.name

    @property
    def llm(self) -> ChatOpenAI:
        """Lazy initialization of LLM."""
        if self._llm is None:
            self._llm = get_llm()
        return self._llm

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    def _call_llm(self, user_prompt: str) -> str:
        """Call LLM with the agent's system prompt.

        Args:
            user_prompt: The user message to send.

        Returns:
            The LLM response content as string.
        """
        messages = [
            {"role": "system", "content": self.persona.system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        response = self.llm.invoke(messages)

        # Track token usage from response metadata
        self._track_tokens(response)

        return str(response.content)

    def _track_tokens(self, response: Any) -> None:
        """Track token usage from LLM response."""
        global _token_usage

        # Extract usage from response metadata (OpenRouter/OpenAI format)
        usage = getattr(response, "usage_metadata", None) or {}
        if not usage and hasattr(response, "response_metadata"):
            usage = response.response_metadata.get("token_usage", {})

        input_tokens = usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0)
        output_tokens = usage.get("output_tokens", 0) or usage.get("completion_tokens", 0)

        if input_tokens or output_tokens:
            call_type = self._call_type
            if call_type not in _token_usage:
                _token_usage[call_type] = {"calls": 0, "input": 0, "output": 0}

            _token_usage[call_type]["calls"] += 1
            _token_usage[call_type]["input"] += input_tokens
            _token_usage[call_type]["output"] += output_tokens

            logger.debug(
                f"   {self.name} [{call_type}]: {input_tokens} in / {output_tokens} out"
            )

    def _parse_json(self, response: str) -> dict[str, Any]:
        """Parse JSON from LLM response."""
        return parse_json_response(response)

    @abstractmethod
    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the agent's main task.

        Must be implemented by subclasses.
        """
        pass
