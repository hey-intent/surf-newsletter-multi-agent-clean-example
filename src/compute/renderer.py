"""HTML rendering for the newsletter."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.core.models import SelectedArticle

logger = logging.getLogger(__name__)


def render_newsletter(
    articles: list[SelectedArticle],
    output_path: str | Path,
    template_name: str = "newsletter.html",
) -> Path:
    """Render the newsletter HTML from ranked articles.

    Args:
        articles: Ranked list of articles (best first).
        output_path: Path to save the HTML file.
        template_name: Name of the Jinja2 template.

    Returns:
        Path to the generated HTML file.
    """
    logger.info("Generating newsletter HTML...")

    # Setup Jinja2
    template_dir = Path(__file__).parent.parent.parent / "templates"
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_name)

    # Render
    html = template.render(
        articles=articles,
        date=datetime.now().strftime("%B %d, %Y"),
        cover_article=articles[0] if articles else None,
    )

    # Write output
    output_path = Path(output_path)
    output_path.write_text(html, encoding="utf-8")

    logger.info(f"   Newsletter saved to: {output_path}")

    return output_path
