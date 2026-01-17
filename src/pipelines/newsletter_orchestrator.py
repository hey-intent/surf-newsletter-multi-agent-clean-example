"""Pipeline orchestrator using LangGraph for multi-agent newsletter generation."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from src.agents.base import get_token_usage, reset_token_usage
from src.pipelines.newsletter_graph import newsletter_graph

logger = logging.getLogger(__name__)


class NewsletterPipeline:
    """Orchestrates the newsletter generation using LangGraph.

    The pipeline executes 5 phases:
    1. Sourcing: Fetch articles from RSS feeds
    2. Selection: Each persona selects top articles (parallel)
    3. Cross-grading: Personas grade articles they didn't select (parallel)
    4. Final ranking: All personas grade all finalists (parallel)
    5. Generate: Render HTML newsletter
    """

    def __init__(self, days: int = 7, min_articles: int | None = None, debug: bool = False):
        """Initialize the pipeline.

        Args:
            days: Number of days to look back for articles.
            min_articles: Minimum number of articles to fetch (uses config default if None).
            debug: Enable debug logging.
        """
        self.days = days
        self.min_articles = min_articles
        self.graph = newsletter_graph

        if debug:
            logging.getLogger("src").setLevel(logging.DEBUG)

    def run(self, output_path: str | Path | None = None) -> Path:
        """Run the complete newsletter pipeline.

        Args:
            output_path: Path to save the HTML newsletter.
                        Defaults to newsletter_YYYYMMDD.html

        Returns:
            Path to the generated newsletter file.
        """
        # Default output path
        if output_path is None:
            output_path = f"newsletter_{datetime.now().strftime('%Y%m%d')}.html"

        print("\n" + "=" * 50)
        print("   SURF NEWSLETTER PIPELINE (LangGraph)")
        print("=" * 50 + "\n")

        # Prepare initial state
        initial_state = {
            "days": self.days,
            "output_path": str(output_path),
        }
        if self.min_articles is not None:
            initial_state["min_articles"] = self.min_articles

        # Execute the graph
        logger.info("Starting LangGraph execution...")

        # Reset token counters
        reset_token_usage()

        try:
            result = self.graph.invoke(initial_state)

            generated_path = result.get("generated_html", str(output_path))

            print("\n" + "=" * 50)
            print("   PIPELINE COMPLETE")
            print("=" * 50 + "\n")

            # Print token usage
            self._print_token_usage()

            return Path(generated_path)

        except Exception as e:
            logger.exception(f"Pipeline execution failed: {e}")
            raise

    def _print_token_usage(self) -> None:
        """Print token usage summary."""
        usage = get_token_usage()

        if not usage:
            return

        print("TOKEN USAGE:")
        print("-" * 60)
        print(f"{'Call Type':<25} {'Calls':>6} {'Input':>10} {'Output':>10} {'Total':>10}")
        print("-" * 60)

        total_calls = 0
        total_input = 0
        total_output = 0

        for call_type, stats in sorted(usage.items()):
            calls = stats["calls"]
            inp = stats["input"]
            out = stats["output"]
            total = inp + out

            total_calls += calls
            total_input += inp
            total_output += out

            # Calculate average per call
            avg_in = inp // calls if calls > 0 else 0
            avg_out = out // calls if calls > 0 else 0

            print(f"{call_type:<25} {calls:>6} {inp:>10,} {out:>10,} {total:>10,}")
            print(f"  (avg per call)                  {avg_in:>10,} {avg_out:>10,}")

        print("-" * 60)
        print(f"{'TOTAL':<25} {total_calls:>6} {total_input:>10,} {total_output:>10,} {total_input + total_output:>10,}")
        print()


def run_pipeline(
    days: int = 7,
    output_path: str | None = None,
    min_articles: int | None = None,
    debug: bool = False,
) -> Path:
    """Convenience function to run the newsletter pipeline.

    Args:
        days: Number of days to look back for articles.
        output_path: Path to save the HTML newsletter.
        min_articles: Minimum number of articles to fetch.
        debug: Enable debug logging.

    Returns:
        Path to the generated newsletter file.
    """
    pipeline = NewsletterPipeline(days=days, min_articles=min_articles, debug=debug)
    return pipeline.run(output_path)
