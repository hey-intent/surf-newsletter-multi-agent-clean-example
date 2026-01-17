"""Configuration for the newsletter pipeline."""

# RSS Feed sources for surf news
RSS_SOURCES: list[dict[str, str]] = [
    # General surf media
    {"name": "Surfer Magazine", "url": "https://www.surfer.com/feed/"},
    {"name": "Surfline News", "url": "https://www.surfline.com/surf-news/rss"},
    {"name": "BeachGrit", "url": "https://beachgrit.com/feed/"},
    {"name": "Stab Magazine", "url": "https://stabmag.com/feed/"},
    # Competition & Performance
    {"name": "Surfing Magazine", "url": "https://www.surfingmagazine.com/feed/"},
    # Culture & Lifestyle
    {"name": "The Inertia", "url": "https://www.theinertia.com/feed/"},
    {"name": "Wavelength Magazine", "url": "https://wavelengthmag.com/feed/"},
]

# Pipeline configuration
MIN_ARTICLES = 50
MAX_ARTICLES = 100
ARTICLES_PER_AGENT = 6
FINALISTS_COUNT = 8

# LLM configuration
LLM_MODEL = "mistralai/mistral-small-3.2-24b-instruct"
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 2000
LLM_BASE_URL = "https://openrouter.ai/api/v1"
