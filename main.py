# main.py

import asyncio
from scraper_core import run_scraper_and_analysis
from config import (
    DEFAULT_DB_URL,
    DEFAULT_START_URL,
    DEFAULT_PAGES_TO_SCRAPE,
    DEFAULT_CONCURRENCY_LIMIT
)
import argparse

def parse_args():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run a concurrent web scraper and sentiment analyzer."
    )
    parser.add_argument(
        '--url',
        type=str,
        default=DEFAULT_START_URL,
        help=f"The starting URL to scrape (default: {DEFAULT_START_URL})"
    )
    parser.add_argument(
        '--pages',
        type=int,
        default=DEFAULT_PAGES_TO_SCRAPE,
        help=f"The number of pages to attempt to scrape (default: {DEFAULT_PAGES_TO_SCRAPE})"
    )
    parser.add_argument(
        '--concurrency',
        type=int,
        default=DEFAULT_CONCURRENCY_LIMIT,
        help=f"The maximum number of concurrent requests (default: {DEFAULT_CONCURRENCY_LIMIT})"
    )
    parser.add_argument(
        '--db_url',
        type=str,
        default=DEFAULT_DB_URL,
        help="The PostgreSQL database connection URL."
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # Check if a loop is already running (e.g., in Jupyter/Colab)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
    except RuntimeError:
        # Create a new event loop if none exists
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    run_scraper_and_analysis(
        db_url=args.db_url,
        start_url=args.url,
        pages_to_scrape=args.pages,
        concurrency=args.concurrency
    )