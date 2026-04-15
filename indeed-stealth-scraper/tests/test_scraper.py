"""
tests/test_scraper.py -- End-to-end integration test for the Indeed scraper.

Runs against live Indeed Canada. No test framework needed -- all output goes
to stdout. Exit code 0 = all assertions passed, 1 = at least one failed.

IMPORTANT -- Indeed requires authentication for paginated results (page 2+).
Without a saved session, only page 1 (15 jobs) is accessible.
Cloudflare may also rate-limit page 1 after many rapid requests.

To enable full pagination:
    1. Run:  set DEBUG=1 && python tests/capture_session.py
    2. Log into Indeed in the headed browser, then press Enter
    3. Re-run this test -- it will now paginate freely

Usage:
    python tests/test_scraper.py               # 20-page test (session required for full pass)
    python tests/test_scraper.py --pages 3    # quick 3-page smoke test
"""

import asyncio
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

SESSION_FILE = ROOT / "session" / "indeed_cookies.json"

from indeed_scraper.proxy_manager import ProxyManager
from indeed_scraper.scraper_core import IndeedScraper, BlockedError, _load_session_cookies
from indeed_scraper.browser_manager import BrowserManager
from indeed_scraper.scraper_core import _extract_jobs_from_page, _is_blocked
from indeed_scraper.job_parser import parse_jobs

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_QUERY = "software developer"
DEFAULT_LOCATION = "Ontario"
DEFAULT_PAGES = 20

HAS_SESSION = SESSION_FILE.exists()

# Thresholds are computed per-run in main() once we know --pages.
# Defaults here are overridden below.
ASSERT_MIN_JOBS  = 0
ASSERT_MIN_PAGES = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sep(char="-", width=60) -> None:
    print(char * width, flush=True)

def _pass(msg: str) -> None:
    print(f"  PASS  {msg}", flush=True)

def _fail(msg: str) -> None:
    print(f"  FAIL  {msg}", flush=True)

def _warn(msg: str) -> None:
    print(f"  WARN  {msg}", flush=True)


# ---------------------------------------------------------------------------
# Single-page fetch (1 attempt + 1 Cloudflare retry with backoff)
# ---------------------------------------------------------------------------

CF_RETRY_WAIT = 25  # seconds to wait before retrying a Cloudflare challenge


async def _fetch_one(scraper: IndeedScraper, url: str, attempt: int = 1) -> tuple[str, list[dict]]:
    """
    Fetch `url` once. If Cloudflare challenges us, wait CF_RETRY_WAIT seconds
    and retry once. Returns (status, jobs): status is 'ok', 'blocked', or 'error'.
    """
    try:
        async with BrowserManager() as bm:
            page = await bm.new_page()
            await _load_session_cookies(page)
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            try:
                await page.wait_for_function(
                    """() => {
                        try {
                            const pd = window.mosaic && window.mosaic.providerData;
                            if (!pd) return false;
                            const jc = pd['mosaic-provider-jobcards'];
                            return !!(jc && jc.metaData && jc.metaData.mosaicProviderJobCardsModel);
                        } catch(e) { return false; }
                    }""",
                    timeout=8_000,
                )
            except Exception:
                await asyncio.sleep(1.5)
            title = await page.title()
            snippet = (await page.content())[:2000]
            if _is_blocked(title, snippet):
                if attempt == 1 and "just a moment" in title.lower():
                    # Cloudflare rate-limit — back off and retry once
                    print(f"    [Cloudflare] waiting {CF_RETRY_WAIT}s before retry...", flush=True)
                    await asyncio.sleep(CF_RETRY_WAIT)
                    return await _fetch_one(scraper, url, attempt=2)
                return f"blocked:{title}", []
            jobs_raw = await _extract_jobs_from_page(page)
            return "ok", parse_jobs(jobs_raw)
    except Exception as exc:
        return f"error:{exc}", []


# ---------------------------------------------------------------------------
# Core test: pagination + per-page counts
# ---------------------------------------------------------------------------

async def run_pagination_test(pages: int) -> dict:
    """
    Scrape N pages (one attempt each) and report per-page counts + assertions.
    Thresholds auto-adjust based on whether session/indeed_cookies.json exists.
    """
    _sep("*")
    print("TEST: Pagination & Job Count", flush=True)
    print(f"  query={DEFAULT_QUERY!r}  location={DEFAULT_LOCATION!r}  pages={pages}", flush=True)
    print(f"  session: {'YES - full pagination enabled' if HAS_SESSION else 'NO  - only page 1 accessible'}", flush=True)
    _sep()

    scraper = IndeedScraper(max_pages=pages)

    all_jobs: list[dict] = []
    per_page: list[dict] = []
    blocked_count = 0
    start_ts = time.monotonic()

    for page_num in range(pages):
        start_offset = page_num * 10
        url = IndeedScraper._build_url(DEFAULT_QUERY, DEFAULT_LOCATION, start_offset)

        print(f"\n  Page {page_num + 1:>2}/{pages} | start={start_offset}", flush=True)
        print(f"  {url}", flush=True)

        t0 = time.monotonic()
        status, jobs = await _fetch_one(scraper, url)
        elapsed = time.monotonic() - t0

        if status == "ok":
            all_jobs.extend(jobs)
            print(f"    parsed={len(jobs)}  elapsed={elapsed:.1f}s  total={len(all_jobs)}", flush=True)
            per_page.append({"page": page_num + 1, "parsed": len(jobs), "status": "ok"})
            if len(jobs) == 0:
                print(f"    (empty page -- end of results)", flush=True)
                break
        else:
            blocked_count += 1
            reason = "auth/Cloudflare" if "blocked" in status else "error"
            title_hint = status.split(":", 1)[1] if ":" in status else status
            print(f"    {reason.upper()} after {elapsed:.1f}s | {title_hint}", flush=True)
            per_page.append({"page": page_num + 1, "parsed": 0, "status": reason})

            # Without session, page 2+ will always fail -- don't waste time
            if not HAS_SESSION and page_num >= 1:
                print(f"    (no session -- stopping: pages 2+ require authentication)", flush=True)
                break

            # With session, a single blocked page may be transient -- keep going
            # Without session, even page 1 may be rate-limited -- wait and warn
            if not HAS_SESSION:
                print(f"    Possible rate-limit on page 1. Wait a minute and retry.", flush=True)
                break

        # Pause between pages — 3s minimum reduces Cloudflare rate-limiting
        if page_num < pages - 1 and status == "ok":
            await asyncio.sleep(3.0)

    total_elapsed = time.monotonic() - start_ts
    pages_with_results = sum(1 for p in per_page if p.get("parsed", 0) > 0)

    # ── Summary ──
    _sep()
    print(f"\nSUMMARY", flush=True)
    print(f"  Session         : {'yes' if HAS_SESSION else 'no  (run capture_session.py)'}", flush=True)
    print(f"  Pages attempted : {len(per_page)}", flush=True)
    print(f"  Pages OK        : {pages_with_results}", flush=True)
    print(f"  Pages blocked   : {blocked_count}", flush=True)
    print(f"  Total jobs      : {len(all_jobs)}", flush=True)
    print(f"  Elapsed         : {total_elapsed:.1f}s", flush=True)

    print(f"\nPer-page breakdown:", flush=True)
    for p in per_page:
        status_str = f"parsed={p['parsed']:>3}" if p["status"] == "ok" else p["status"].upper()
        print(f"  Page {p['page']:>2}: {status_str}", flush=True)

    # ── Assertions ──
    _sep()
    print(f"\nASSERTIONS  (min_jobs={ASSERT_MIN_JOBS}, min_pages={ASSERT_MIN_PAGES})", flush=True)
    passed = True

    if len(all_jobs) >= ASSERT_MIN_JOBS:
        _pass(f"total jobs {len(all_jobs)} >= {ASSERT_MIN_JOBS}")
    else:
        _fail(f"total jobs {len(all_jobs)} < {ASSERT_MIN_JOBS}")
        if not HAS_SESSION:
            print("        Indeed blocks page 2+ without authentication.", flush=True)
            print("        Run:  set DEBUG=1 && python tests/capture_session.py", flush=True)
        passed = False

    if pages_with_results >= ASSERT_MIN_PAGES:
        _pass(f"{pages_with_results} pages returned results (>= {ASSERT_MIN_PAGES})")
    else:
        _fail(f"only {pages_with_results} pages returned results (wanted >= {ASSERT_MIN_PAGES})")
        if not HAS_SESSION:
            print("        Expected -- pages 2+ require a session.", flush=True)
            if blocked_count > 0 and pages_with_results == 0:
                print("        If page 1 was also blocked: IP was rate-limited. Wait 1-2 min.", flush=True)
        passed = False

    if blocked_count > 0:
        if HAS_SESSION:
            _warn(f"{blocked_count} page(s) blocked even with session -- check cookie freshness")
        else:
            _warn(f"{blocked_count} page(s) blocked (expected without session)")
    else:
        _pass("no pages blocked")

    return {
        "passed": passed,
        "total_jobs": len(all_jobs),
        "pages_with_results": pages_with_results,
        "blocked_count": blocked_count,
        "per_page": per_page,
        "elapsed": total_elapsed,
        "has_session": HAS_SESSION,
    }


# ---------------------------------------------------------------------------
# Unit test: _normalize_date
# ---------------------------------------------------------------------------

def run_date_normalization_test() -> bool:
    """Verify posted_date normalisation works correctly (no network)."""
    _sep("*")
    print("TEST: posted_date normalisation", flush=True)
    _sep()

    from indeed_scraper.job_parser import _normalize_date

    cases = [
        (1712534400000, "2024-"),
        (1712534400,    "2024-"),
        ("1712534400000", "2024-"),
        ("3 days ago",   "3 days"),
        (None,           None),
        ("",             None),
    ]

    passed = True
    for raw, expected in cases:
        result = _normalize_date(raw)
        if expected is None:
            ok = result is None
        elif isinstance(expected, str) and expected.endswith("-"):
            ok = isinstance(result, str) and result.startswith(expected)
        else:
            ok = isinstance(result, str) and result.startswith(expected)

        status = "PASS" if ok else "FAIL"
        print(f"  {status}  _normalize_date({raw!r}) -> {result!r}", flush=True)
        if not ok:
            passed = False

    return passed


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    global ASSERT_MIN_JOBS, ASSERT_MIN_PAGES

    pages = DEFAULT_PAGES

    if "--pages" in sys.argv:
        idx = sys.argv.index("--pages")
        try:
            pages = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("Usage: python tests/test_scraper.py [--pages N]", flush=True)
            sys.exit(1)

    # Scale thresholds to the number of pages actually being run.
    # Indeed serves ~15 jobs/page; expect at least 12 on average to allow some variance.
    if HAS_SESSION:
        ASSERT_MIN_JOBS  = pages * 12          # e.g. 5 pages → 60, 20 pages → 240
        ASSERT_MIN_PAGES = max(1, int(pages * 0.8))  # allow up to 20% rate-limited pages
    else:
        ASSERT_MIN_JOBS  = 10
        ASSERT_MIN_PAGES = 1

    print("\n" + "*" * 60, flush=True)
    print("  INDEED SCRAPER -- INTEGRATION TEST SUITE", flush=True)
    print("*" * 60 + "\n", flush=True)

    if not HAS_SESSION:
        print("  NOTE: No session found at session/indeed_cookies.json", flush=True)
        print("  Indeed blocks pagination beyond page 1 without a login session.", flush=True)
        print("  To capture a session:", flush=True)
        print("    set DEBUG=1 && python tests/capture_session.py\n", flush=True)

    all_passed = True

    date_ok = run_date_normalization_test()
    all_passed = all_passed and date_ok

    result = await run_pagination_test(pages)
    all_passed = all_passed and result["passed"]

    _sep("*")
    if all_passed:
        print("\n  ALL TESTS PASSED\n", flush=True)
        sys.exit(0)
    else:
        if not HAS_SESSION:
            print("\n  TESTS INCOMPLETE -- run capture_session.py for full pagination\n", flush=True)
        else:
            print("\n  ONE OR MORE TESTS FAILED -- see output above\n", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
