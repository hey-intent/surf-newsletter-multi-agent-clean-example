"""Tests for core configuration."""

from src.core.config import (
    ARTICLES_PER_AGENT,
    FINALISTS_COUNT,
    LLM_BASE_URL,
    LLM_MAX_TOKENS,
    LLM_MODEL,
    LLM_TEMPERATURE,
    MAX_ARTICLES,
    MIN_ARTICLES,
    RSS_SOURCES,
)


class TestRSSConfig:
    """Tests for RSS feed configuration."""

    def test_rss_sources_not_empty(self):
        """Test RSS sources list is not empty."""
        assert len(RSS_SOURCES) > 0

    def test_rss_sources_have_required_fields(self):
        """Test each RSS source has name and url."""
        for source in RSS_SOURCES:
            assert "name" in source
            assert "url" in source
            assert len(source["name"]) > 0
            assert source["url"].startswith("http")

    def test_rss_sources_urls_are_valid(self):
        """Test RSS source URLs are properly formatted."""
        for source in RSS_SOURCES:
            url = source["url"]
            assert url.startswith("https://") or url.startswith("http://")
            assert "." in url  # Has a domain


class TestPipelineConfig:
    """Tests for pipeline configuration values."""

    def test_min_articles_positive(self):
        """Test MIN_ARTICLES is positive."""
        assert MIN_ARTICLES > 0

    def test_max_articles_greater_than_min(self):
        """Test MAX_ARTICLES > MIN_ARTICLES."""
        assert MAX_ARTICLES > MIN_ARTICLES

    def test_articles_per_agent_reasonable(self):
        """Test ARTICLES_PER_AGENT is within reasonable range."""
        assert ARTICLES_PER_AGENT > 0
        assert ARTICLES_PER_AGENT <= 20

    def test_finalists_count_positive(self):
        """Test FINALISTS_COUNT is positive."""
        assert FINALISTS_COUNT > 0

    def test_finalists_less_than_max_articles(self):
        """Test FINALISTS_COUNT < MAX_ARTICLES."""
        assert FINALISTS_COUNT < MAX_ARTICLES


class TestLLMConfig:
    """Tests for LLM configuration."""

    def test_llm_model_defined(self):
        """Test LLM model is defined."""
        assert LLM_MODEL is not None
        assert len(LLM_MODEL) > 0

    def test_llm_temperature_valid_range(self):
        """Test LLM temperature is in valid range [0, 2]."""
        assert 0 <= LLM_TEMPERATURE <= 2

    def test_llm_max_tokens_positive(self):
        """Test LLM max tokens is positive."""
        assert LLM_MAX_TOKENS > 0

    def test_llm_base_url_valid(self):
        """Test LLM base URL is a valid URL."""
        assert LLM_BASE_URL.startswith("https://")
        assert "." in LLM_BASE_URL
