"""Core module - foundational components shared across the application."""

from src.core.models import Article, GradingResult, SelectedArticle
from src.core.personas import ALL_PERSONAS, ANNIE, JOHNNY, JOANA, Persona

__all__ = [
    "Article",
    "GradingResult",
    "SelectedArticle",
    "Persona",
    "JOHNNY",
    "ANNIE",
    "JOANA",
    "ALL_PERSONAS",
]
