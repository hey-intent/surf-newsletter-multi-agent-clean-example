"""Persona definitions for the surf newsletter editors."""

from src.core.personas.annie import ANNIE
from src.core.personas.base import Persona
from src.core.personas.joana import JOANA
from src.core.personas.johnny import JOHNNY

ALL_PERSONAS = [JOHNNY, ANNIE, JOANA]

__all__ = [
    "Persona",
    "JOHNNY",
    "ANNIE",
    "JOANA",
    "ALL_PERSONAS",
]
