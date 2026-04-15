"""
main.py — CLI entrypoint for the Indeed Canada job scraper.

Usage:
    python main.py --query "software developer" --location "Toronto, ON"
    python main.py --query "data analyst" --location "Vancouver, BC" --pages 5
"""

import argparse
import asyncio
import signal
import sys

from .browser_manager import BrowserManager
from .job_parser import parse_jobs
from .logger import get_logger
from .proxy_manager import ProxyManager
from .scraper_core import IndeedScraper
from .storage_manager import StorageManager

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Graceful shutdown
# ---------------------------------------------------------------------------

_shutdown_requested = False


def _handle_sigint(sig, frame) -> None:  # noqa: ANN001
    global _shutdown_requested
    _shutdown_requested = True
    log.warning("Ctrl+C received — will save partial results and exit after current page.")


# ---------------------------------------------------------------------------
# Main async flow
# ---------------------------------------------------------------------------


async def run(
    query: str,
    location: str,
    max_pages: int,
    output_dir: str,
    proxy_file: str,
) -> None:
    # Set up storage first so partial results can be saved on interrupt
    storage = StorageManager(output_dir=output_dir)

    # Set up proxies
    proxy_mgr = ProxyManager(proxy_file=proxy_file)
    await proxy_mgr.refresh_healthy()

    # Set up scraper
    scraper = IndeedScraper(proxy_manager=proxy_mgr, max_pages=max_pages)

    raw_jobs: list[dict] = []
    parsed_jobs: list[dict] = []

    try:
        log.info(f'Starting scrape | query="{query}" | location="{location}" | max_pages={max_pages}')

        for page_num in range(max_pages):
            if _shutdown_requested:
                log.warning("Shutdown requested — stopping pagination.")
                break

            start = page_num * 10
            url = scraper._build_url(query, location, start)
            log.info(f"Scraping page {page_num + 1}/{max_pages} …")

            proxy = proxy_mgr.get_next() if proxy_mgr.has_proxies() else None
            page_jobs = await scraper._scrape_page_with_retry(url, proxy=proxy)

            if page_jobs is None:
                log.warning(f"Page {page_num + 1}: exhausted retries — stopping.")
                break
            if not page_jobs:
                log.info(f"Page {page_num + 1}: no jobs found — end of results.")
                break

            raw_jobs.extend(page_jobs)
            batch_parsed = parse_jobs(page_jobs)
            parsed_jobs.extend(batch_parsed)

            # Save incrementally after each page
            storage.save_batch(batch_parsed)

            log.info(
                f"Page {page_num + 1} complete | +{len(batch_parsed)} parsed | "
                f"total: {storage.total_saved}"
            )

            if not _shutdown_requested:
                await BrowserManager.human_delay(1.0, 3.0)

    except asyncio.CancelledError:
        log.warning("Task cancelled — saving partial results.")

    finally:
        log.info(
            f"Scrape complete | total jobs collected: {storage.total_saved} | "
            f"JSON: {storage.json_path} | CSV: {storage.csv_path}"
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="indeed_scraper",
        description="Stealth scraper for Indeed Canada job listings.",
    )
    parser.add_argument(
        "--query",
        required=True,
        help='Job search query (e.g. "software developer")',
    )
    parser.add_argument(
        "--location",
        required=True,
        help='Location to search (e.g. "Toronto, ON")',
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=10,
        metavar="N",
        help="Maximum pages to scrape (default: 10)",
    )
    parser.add_argument(
        "--output",
        default="./output",
        metavar="DIR",
        help="Output directory for JSON/CSV files (default: ./output)",
    )
    parser.add_argument(
        "--proxy-file",
        default="proxies.txt",
        metavar="FILE",
        help="Path to proxy list file (default: proxies.txt)",
    )
    return parser


def main() -> None:
    signal.signal(signal.SIGINT, _handle_sigint)

    parser = build_parser()
    args = parser.parse_args()

    try:
        asyncio.run(
            run(
                query=args.query,
                location=args.location,
                max_pages=args.pages,
                output_dir=args.output,
                proxy_file=args.proxy_file,
            )
        )
    except KeyboardInterrupt:
        log.warning("Interrupted by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
