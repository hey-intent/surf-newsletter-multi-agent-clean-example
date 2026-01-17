"""Pydantic models for the surf newsletter pipeline."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class Article(BaseModel):
    """Raw article fetched from RSS or web search."""

    title: str
    url: HttpUrl
    excerpt: str = ""
    source: str
    published: datetime
    image_url: Optional[HttpUrl] = None

    def __hash__(self) -> int:
        return hash(str(self.url))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Article):
            return False
        return str(self.url) == str(other.url)


class GradingResult(BaseModel):
    """Individual agent's score and reasoning for an article."""

    grader: str
    score: float = Field(ge=1, le=5)
    reasoning: str
    key_strengths: list[str] = Field(default_factory=list)


class SelectedArticle(BaseModel):
    """Article with selection and scoring metadata."""

    article: Article
    selected_by: list[str] = Field(default_factory=list)
    phase3_scores: list[GradingResult] = Field(default_factory=list)
    phase3_avg: float = 0.0
    final_scores: list[GradingResult] = Field(default_factory=list)
    final_avg: float = 0.0

    def __hash__(self) -> int:
        return hash(self.article)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SelectedArticle):
            return False
        return self.article == other.article
