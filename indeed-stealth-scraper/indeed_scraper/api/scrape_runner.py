"""
scrape_runner.py — Runs the scraper in a background thread and exposes
shared state (status, jobs, logs, proxy_errors, elapsed_time) to the API.

Does NOT modify any existing scraper module — imports them as-is.
"""

import asyncio
import logging
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Make sure the project root is on sys.path when run standalone
_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from indeed_scraper.browser_manager import BrowserManager
from indeed_scraper.job_parser import parse_jobs
from indeed_scraper.logger import get_logger
from indeed_scraper.proxy_manager import ProxyManager
from indeed_scraper.scraper_core import IndeedScraper
from indeed_scraper.storage_manager import StorageManager

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------


@dataclass
class ScrapeState:
    status: str = "idle"          # idle | running | completed | failed | stopped
    jobs: list = field(default_factory=list)
    logs: list = field(default_factory=list)
    proxy_errors: int = 0
    elapsed_time: float = 0.0
    query: str = ""
    location: str = ""
    pages_total: int = 0
    pages_done: int = 0
    last_start_offset: int = 0   # tracks where next "Get More" run should start
    _start_ts: Optional[float] = None


_state = ScrapeState()
_state_lock = threading.Lock()
_stop_event = threading.Event()
_scrape_thread: Optional[threading.Thread] = None


# ---------------------------------------------------------------------------
# Log interception — captures indeed_scraper.* loggers into state.logs
# ---------------------------------------------------------------------------


class _UILogHandler(logging.Handler):
    """Appends formatted log records to the shared state log list."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            with _state_lock:
                _state.logs.append(msg)
                # Count proxy-related warnings as proxy_errors
                if record.levelno >= logging.WARNING and (
                    "proxy" in msg.lower() or "block" in msg.lower()
                ):
                    _state.proxy_errors += 1
        except Exception:  # noqa: BLE001
            pass


_ui_handler = _UILogHandler()
_ui_handler.setFormatter(
    logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s", "%H:%M:%S")
)


def _attach_log_handler() -> None:
    pkg_logger = logging.getLogger("indeed_scraper")
    pkg_logger.addHandler(_ui_handler)


def _detach_log_handler() -> None:
    pkg_logger = logging.getLogger("indeed_scraper")
    pkg_logger.removeHandler(_ui_handler)


# ---------------------------------------------------------------------------
# Background thread entry point
# ---------------------------------------------------------------------------


def _thread_main(query: str, location: str, pages: int, output_dir: str, start_offset: int) -> None:
    """Runs inside a daemon thread; drives the async scrape loop."""
    asyncio.run(_async_main(query, location, pages, output_dir, start_offset))


async def _async_main(query: str, location: str, pages: int, output_dir: str, start_offset: int) -> None:
    proxy_mgr = ProxyManager()
    await proxy_mgr.refresh_healthy()

    scraper = IndeedScraper(proxy_manager=proxy_mgr, max_pages=pages)
    storage = StorageManager(output_dir=output_dir)

    with _state_lock:
        _state.pages_total = pages

    for page_num in range(pages):
        if _stop_event.is_set():
            with _state_lock:
                _state.status = "stopped"
            break

        start = start_offset + page_num * 10
        url = IndeedScraper._build_url(query, location, start)
        log.info(f"Page {page_num + 1}/{pages} | start={start} | {url}")

        proxy = proxy_mgr.get_next() if proxy_mgr.has_proxies() else None
        page_jobs = await scraper._scrape_page_with_retry(url, proxy=proxy)

        with _state_lock:
            if _state._start_ts:
                _state.elapsed_time = time.monotonic() - _state._start_ts

        if page_jobs is None:
            log.error(f"Page {page_num + 1}: retries exhausted — marking failed.")
            with _state_lock:
                _state.status = "failed"
            break

        log.info(f"Page {page_num + 1}: {len(page_jobs)} raw jobs returned.")

        # Process whatever came back (even a partial last page)
        if page_jobs:
            page_jobs = await scraper.enrich_with_descriptions(page_jobs)
            batch = parse_jobs(page_jobs)
            storage.save_batch(batch)
            with _state_lock:
                _state.jobs.extend(batch)
                _state.pages_done = page_num + 1
                _state.last_start_offset = start + len(page_jobs)
                _state.elapsed_time = time.monotonic() - _state._start_ts

        # Stop ONLY when the page is truly empty — partial pages are fine
        if len(page_jobs) == 0:
            log.info(f"Page {page_num + 1}: empty — end of results.")
            break

        if not _stop_event.is_set():
            await BrowserManager.human_delay(1.0, 3.0)

    # Final state update
    with _state_lock:
        if _state.status == "running":
            _state.status = "completed"
        if _state._start_ts:
            _state.elapsed_time = time.monotonic() - _state._start_ts


def _run_thread(query: str, location: str, pages: int, output_dir: str, start_offset: int) -> None:
    """Wrapper that sets terminal state even if the thread crashes."""
    try:
        _thread_main(query, location, pages, output_dir, start_offset)
    except Exception as exc:  # noqa: BLE001
        with _state_lock:
            _state.status = "failed"
            _state.logs.append(f"FATAL: {exc}")
    finally:
        _detach_log_handler()


# ---------------------------------------------------------------------------
# Public API used by route handlers
# ---------------------------------------------------------------------------


def start_scrape(
    query: str,
    location: str,
    pages: int,
    output_dir: str = "output",
    resume: bool = False,
) -> bool:
    """
    Start a scrape in a background thread.
    If resume=True, pagination continues from last_start_offset and
    existing jobs are kept (new ones appended + deduplicated by job_id).
    Returns False if a scrape is already running.
    """
    global _scrape_thread

    with _state_lock:
        if _state.status == "running":
            return False

        start_offset = _state.last_start_offset if resume else 0

        _state.status = "running"
        _state.logs = []
        _state.proxy_errors = 0
        _state.elapsed_time = 0.0
        _state.query = query
        _state.location = location
        _state.pages_total = pages
        _state.pages_done = 0
        _state._start_ts = time.monotonic()

        if not resume:
            _state.jobs = []
            _state.last_start_offset = 0

    _stop_event.clear()
    _attach_log_handler()

    _scrape_thread = threading.Thread(
        target=_run_thread,
        args=(query, location, pages, output_dir, start_offset),
        daemon=True,
        name="scrape-worker",
    )
    _scrape_thread.start()
    return True


def stop_scrape() -> None:
    """Signal the running scrape to stop after the current page."""
    _stop_event.set()


def get_state_snapshot() -> dict:
    """Return a thread-safe snapshot of the current scrape state."""
    with _state_lock:
        return {
            "status": _state.status,
            "query": _state.query,
            "location": _state.location,
            "jobs_count": len(_state.jobs),
            "pages_done": _state.pages_done,
            "pages_total": _state.pages_total,
            "proxy_errors": _state.proxy_errors,
            "elapsed_time": round(_state.elapsed_time, 1),
            "last_start_offset": _state.last_start_offset,
            "logs": list(_state.logs[-200:]),  # last 200 lines
        }


def get_jobs() -> list[dict]:
    """Return a copy of all scraped jobs."""
    with _state_lock:
        return list(_state.jobs)
