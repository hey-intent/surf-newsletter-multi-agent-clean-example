#!/usr/bin/env python3
"""Surf Newsletter Generator - Entry Point."""

import argparse
import logging
import sys
from datetime import datetime

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def setup_logging(debug: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate a curated surf newsletter using AI agents.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to look back for articles",
    )
    parser.add_argument(
        "--min-articles",
        type=int,
        default=50,
        help="Minimum number of articles to fetch",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output HTML filename (default: newsletter_YYYYMMDD.html)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)

    # Default output filename
    output_path = args.output
    if output_path is None:
        output_path = f"newsletter_{datetime.now().strftime('%Y%m%d')}.html"

    try:
        # Import here to allow --help without loading all deps
        from src.pipelines.newsletter_orchestrator import NewsletterPipeline

        # Run pipeline
        pipeline = NewsletterPipeline(
            days=args.days,
            min_articles=args.min_articles,
            debug=args.debug,
        )
        result = pipeline.run(output_path)

        print(f"\nNewsletter generated: {result}")
        return 0

    except ValueError as e:
        logger.error(f"Pipeline error: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
