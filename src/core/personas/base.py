"""Base Persona dataclass."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Persona:
    """A persona that can be assigned to any agent.

    Attributes:
        name: Unique identifier for the persona.
        description: Short description of the persona's background.
        system_prompt: LLM system prompt defining behavior and style.
        criteria_text: Evaluation criteria with weights.
    """

    name: str
    description: str
    system_prompt: str
    criteria_text: str
