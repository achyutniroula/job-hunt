"""
Diagnostic: dump what Indeed actually serves to our browser.
Run:  python tests/diagnose_page.py
Saves page1.html, page2.html, and mosaic_dump.json to tests/diag/
"""
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from indeed_scraper.browser_manager import BrowserManager
from indeed_scraper.scraper_core import IndeedScraper

DIAG_DIR = Path(__file__).parent / "diag"
DIAG_DIR.mkdir(exist_ok=True)

QUERY = "software developer"
LOCATION = "Ontario"


async def probe_page(start: int) -> dict:
    url = IndeedScraper._build_url(QUERY, LOCATION, start)
    print(f"\n{'='*60}", flush=True)
    print(f"Probing: {url}", flush=True)

    async with BrowserManager() as bm:
        page = await bm.new_page()

        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        print(f"  domcontentloaded fired", flush=True)

        # Wait a bit more for React
        await asyncio.sleep(3)
        print(f"  +3s extra wait", flush=True)

        title = await page.title()
        print(f"  title: {title!r}", flush=True)

        # Full page HTML
        html = await page.content()
        out_html = DIAG_DIR / f"page_start{start}.html"
        out_html.write_text(html, encoding="utf-8")
        print(f"  HTML saved → {out_html} ({len(html):,} bytes)", flush=True)

        # Dump everything we can find about mosaic
        diag = await page.evaluate("""() => {
            const out = {};

            // mosaic top-level keys
            try { out.mosaic_keys = Object.keys(window.mosaic || {}); } catch(e) { out.mosaic_keys = String(e); }

            // providerData keys
            try { out.providerData_keys = Object.keys((window.mosaic || {}).providerData || {}); } catch(e) { out.providerData_keys = String(e); }

            // jobcards model presence
            try {
                const jc = (window.mosaic.providerData || {})['mosaic-provider-jobcards'] || {};
                out.has_jobcards = !!jc;
                out.jobcards_keys = Object.keys(jc);
                const model = (jc.metaData || {}).mosaicProviderJobCardsModel;
                out.has_model = !!model;
                if (model) {
                    out.model_keys = Object.keys(model);
                    const cards = model.jobCards || model.results;
                    out.job_count_via_model = cards ? cards.length : 0;
                    // Grab first card keys to understand shape
                    if (cards && cards[0]) out.first_card_keys = Object.keys(cards[0]);
                }
            } catch(e) { out.jobcards_error = String(e); }

            // _initialData
            try {
                const id = window._initialData || {};
                out.initialData_keys = Object.keys(id);
                out.jobKeysWithInfo_count = Object.keys(id.jobKeysWithInfo || {}).length;
            } catch(e) { out.initialData_error = String(e); }

            // script tags that reference mosaic
            try {
                const scripts = document.querySelectorAll('script');
                let mosaicScripts = 0;
                let totalSize = 0;
                for (const s of scripts) {
                    const t = s.textContent || '';
                    if (t.includes('mosaic') || t.includes('jobCards') || t.includes('providerData')) {
                        mosaicScripts++;
                        totalSize += t.length;
                    }
                }
                out.mosaic_script_count = mosaicScripts;
                out.mosaic_script_total_bytes = totalSize;
            } catch(e) { out.script_error = String(e); }

            // DOM job cards
            try {
                out.dom_data_jk_count = document.querySelectorAll('[data-jk]').length;
            } catch(e) {}

            // __NEXT_DATA__ (Next.js)
            try {
                const nd = window.__NEXT_DATA__;
                out.has_next_data = !!nd;
                if (nd) out.next_data_keys = Object.keys(nd);
            } catch(e) {}

            // window keys that look relevant
            try {
                const interesting = Object.keys(window).filter(k =>
                    k.includes('mosaic') || k.includes('indeed') || k.includes('Initial') ||
                    k.includes('jobKey') || k.includes('_data') || k.includes('Data')
                ).slice(0, 30);
                out.interesting_window_keys = interesting;
            } catch(e) {}

            return out;
        }""")

        out_json = DIAG_DIR / f"mosaic_start{start}.json"
        out_json.write_text(json.dumps(diag, indent=2), encoding="utf-8")
        print(f"  Mosaic dump saved → {out_json}", flush=True)
        print(f"\n  === Key findings ===", flush=True)
        for k, v in diag.items():
            print(f"    {k}: {v}", flush=True)

        return diag


async def main():
    print("Indeed Page Diagnostic", flush=True)
    print("Probing page 1 (start=0) and page 2 (start=10)...", flush=True)

    await probe_page(0)
    await asyncio.sleep(2)
    await probe_page(10)

    print(f"\n\nDiagnostic files written to: {DIAG_DIR}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
