"""RSS feed parsing and article fetching."""

import logging
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import feedparser
from bs4 import BeautifulSoup

from src.core.config import MAX_ARTICLES, MIN_ARTICLES, RSS_SOURCES
from src.core.models import Article

logger = logging.getLogger(__name__)


def parse_date(date_str: str | None) -> datetime | None:
    """Parse various date formats from RSS feeds.

    Args:
        date_str: Date string to parse.

    Returns:
        Parsed datetime or None if parsing fails.
    """
    if not date_str:
        return None

    # Try RFC 2822 format (common in RSS)
    try:
        return parsedate_to_datetime(date_str)
    except (ValueError, TypeError):
        pass

    # Try ISO format
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        pass

    return None


def fetch_rss_articles(days: int = 7) -> list[Article]:
    """Fetch articles from RSS feeds within the time window.

    Args:
        days: Number of days to look back.

    Returns:
        List of articles from RSS feeds.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    articles: list[Article] = []

    for source in RSS_SOURCES:
        try:
            logger.info(f"Fetching RSS: {source['name']}")
            feed = feedparser.parse(source["url"])

            for entry in feed.entries:
                # Parse publication date
                pub_date = parse_date(
                    entry.get("published") or entry.get("updated")
                )
                if pub_date is None:
                    pub_date = datetime.now(timezone.utc)

                # Make timezone-aware if needed
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)

                # Skip old articles
                if pub_date < cutoff:
                    continue

                # Extract excerpt
                excerpt = ""
                if hasattr(entry, "summary"):
                    soup = BeautifulSoup(entry.summary, "html.parser")
                    excerpt = soup.get_text()[:500]
                elif hasattr(entry, "description"):
                    soup = BeautifulSoup(entry.description, "html.parser")
                    excerpt = soup.get_text()[:500]

                # Extract image
                image_url = None
                if hasattr(entry, "media_content") and entry.media_content:
                    image_url = entry.media_content[0].get("url")
                elif hasattr(entry, "enclosures") and entry.enclosures:
                    for enc in entry.enclosures:
                        if enc.get("type", "").startswith("image"):
                            image_url = enc.get("href")
                            break

                try:
                    article = Article(
                        title=entry.get("title", "Untitled"),
                        url=entry.get("link", ""),
                        excerpt=excerpt,
                        source=source["name"],
                        published=pub_date,
                        image_url=image_url,
                    )
                    articles.append(article)
                except Exception as e:
                    logger.warning(f"Skipping invalid entry: {e}")

        except Exception as e:
            logger.error(f"Error fetching {source['name']}: {e}")

    logger.info(f"Fetched {len(articles)} articles from RSS feeds")
    return articles


def search_web_articles(queries: list[str], days: int = 7) -> list[Article]:
    """Fallback web search for additional articles.

    Note: This is a placeholder. In production, you would integrate
    with a search API like Google Custom Search, Bing, or SerpAPI.

    Args:
        queries: Search queries to execute.
        days: Number of days to look back.

    Returns:
        List of articles from web search.
    """
    logger.info("Web search fallback triggered (placeholder)")
    return []


def deduplicate_articles(articles: list[Article]) -> list[Article]:
    """Remove duplicate articles by URL and similar titles.

    Args:
        articles: List of articles to deduplicate.

    Returns:
        Deduplicated list of articles.
    """
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    unique: list[Article] = []

    for article in articles:
        url_str = str(article.url)
        title_lower = article.title.lower().strip()

        # Skip if URL already seen
        if url_str in seen_urls:
            continue

        # Simple title dedup (exact match on normalized title)
        if title_lower in seen_titles:
            continue

        seen_urls.add(url_str)
        seen_titles.add(title_lower)
        unique.append(article)

    logger.info(f"Deduplicated: {len(articles)} -> {len(unique)} articles")
    return unique


def fetch_articles(days: int = 7, min_articles: int | None = None) -> list[Article]:
    """Main function to fetch all articles.

    Args:
        days: Number of days to look back.
        min_articles: Minimum number of articles to fetch (uses config default if None).

    Returns:
        Deduplicated and sorted list of articles.
    """
    min_count = min_articles if min_articles is not None else MIN_ARTICLES

    # 1. Fetch from RSS
    articles = fetch_rss_articles(days)

    # 2. Web search fallback if needed
    if len(articles) < min_count:
        logger.warning(
            f"Only {len(articles)} articles from RSS, "
            f"running web search (need {min_count})"
        )
        web_articles = search_web_articles([], days)
        articles.extend(web_articles)

    # 3. Deduplicate
    articles = deduplicate_articles(articles)

    # 4. Sort by date (newest first)
    articles.sort(key=lambda a: a.published, reverse=True)

    # 5. Cap at max
    if len(articles) > MAX_ARTICLES:
        articles = articles[:MAX_ARTICLES]

    logger.info(f"Final article count: {len(articles)}")
    return articles
