# Indeed Stealth Scraper

A modular, stealth Playwright-based scraper for **Indeed Canada** job listings.

---

## Features

- Stealth browser: randomised user-agent, viewport, locale; webdriver flag removed
- Proxy rotation with async health-checking and auto-failover on 403/block
- Cloudflare / bot-detection detection with retry + exponential backoff
- Extracts jobs from `window.mosaic.providerData` (JSON) with DOM fallback
- Saves results to timestamped **JSON** and **CSV** files
- Structured logging to console and `logs/scraper.log`
- Graceful Ctrl+C: saves partial results before exit

---

## Requirements

- Python 3.11+
- Chromium (installed via Playwright)

---

## Setup

```bash
# 1. Clone / copy the project
cd indeed-stealth-scraper

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install the Playwright Chromium browser
playwright install chromium
```

---

## Usage

```bash
# Basic search
python -m indeed_scraper.main --query "software developer" --location "Toronto, ON"

# Limit to 5 pages, custom output directory
python -m indeed_scraper.main \
    --query "data analyst" \
    --location "Vancouver, BC" \
    --pages 5 \
    --output ./results

# Use a custom proxy file
python -m indeed_scraper.main \
    --query "machine learning engineer" \
    --location "Montreal, QC" \
    --proxy-file /path/to/my_proxies.txt
```

### CLI Arguments

| Argument | Default | Description |
|---|---|---|
| `--query` | *(required)* | Job search keyword(s) |
| `--location` | *(required)* | City / province (e.g. `"Toronto, ON"`) |
| `--pages` | `10` | Max pages to scrape (10 results per page) |
| `--output` | `./output` | Directory for JSON/CSV output files |
| `--proxy-file` | `proxies.txt` | Path to newline-delimited proxy list |

---

## Proxy Configuration

Add proxies to `proxies.txt` (one per line):

```
http://user:pass@host:port
socks5://host:port
host:port
```

Or set the `PROXY_LIST` environment variable:

```bash
export PROXY_LIST="http://proxy1:8080,http://proxy2:3128"
```

The scraper health-checks all proxies at startup and only uses healthy ones.

---

## Environment Variables

| Variable | Effect |
|---|---|
| `DEBUG=1` | Run browser in **headed** (visible) mode |
| `PROXY_LIST` | Comma-separated proxy list (overrides `proxies.txt`) |

---

## Output Files

Results land in `./output/` (or your `--output` directory):

```
output/
  jobs_20240515_143022.json   # Full structured data (all fields)
  jobs_20240515_143022.csv    # Spreadsheet-friendly flat format
logs/
  scraper.log                 # Detailed debug log
```

### Job Schema

| Field | Type | Description |
|---|---|---|
| `job_id` | `str` | Indeed job key |
| `title` | `str` | Job title |
| `company` | `str` | Employer name |
| `location` | `str` | City / province |
| `salary` | `str` | Salary range (if listed) |
| `description` | `str` | Plain-text job snippet |
| `posted_date` | `str` | Relative date (e.g. "3 days ago") |
| `url` | `str` | Direct link to job posting |
| `employment_type` | `str` | Full-time / Part-time / Contract |
| `remote` | `bool` | `true` if remote-eligible |
| `company_rating` | `float` | Employer rating (if available) |

---

## Running the UI

The scraper includes a local web dashboard built with FastAPI + vanilla JS.

```bash
# From the indeed-stealth-scraper/ directory (with venv active):
python -m indeed_scraper.api.main
```

Then open **http://localhost:8001** in your browser.

### UI Features

- **Dashboard panel** — enter query, location, and page count; hit Start
- **Live status** — status badge, jobs count, pages, elapsed time, proxy errors
- **Live log viewer** — collapsible, streams all scraper logs in real time (polls every 2 s)
- **Results table** — sortable columns, filter by location/company/remote/salary
- **Job detail modal** — full description, metadata, copy-to-clipboard, single-job PDF export
- **Export toolbar** — download all results as `.xlsx` or `.pdf`

### API docs

Interactive Swagger UI: **http://localhost:8001/api/docs**

---

## Project Structure

```
indeed-stealth-scraper/
├── indeed_scraper/
│   ├── __init__.py
│   ├── browser_manager.py      # Playwright + stealth setup
│   ├── proxy_manager.py        # Proxy loading, health-check, rotation
│   ├── scraper_core.py         # Navigation, extraction, pagination
│   ├── job_parser.py           # Normalise raw job dicts
│   ├── storage_manager.py      # JSON + CSV persistence
│   ├── logger.py               # Structured logging
│   ├── main.py                 # CLI entrypoint
│   ├── api/
│   │   ├── main.py             # FastAPI app, mounts routes + static UI
│   │   ├── scrape_runner.py    # Background thread, shared state
│   │   └── routes/
│   │       ├── scrape.py       # POST /api/scrape, DELETE /stop, GET /status
│   │       ├── results.py      # GET /api/results (paginated + filtered)
│   │       └── export.py       # GET /api/export/excel|pdf|pdf/{id}
│   └── ui/
│       ├── index.html          # Single-page dashboard
│       ├── app.js              # Dashboard logic (sort, filter, modal, export)
│       └── style.css           # Dark theme
├── output/                     # Generated JSON + CSV files
├── logs/                       # scraper.log
├── proxies.txt                 # Proxy list template
├── requirements.txt
└── README.md
```

### Phase 2 migration path

When integrating into the job-hunt platform:
1. Replace in-memory `ScrapeState` in `scrape_runner.py` with PostgreSQL writes (SQLAlchemy async session)
2. Extract `indeed_scraper/ui/` as a module inside the job-hunt React dashboard
3. Wire `POST /api/scrape` into the job-hunt orchestrator alongside other board scrapers
4. The `job_parser.py` schema maps 1-to-1 to the existing `job.py` SQLAlchemy model

---

## Troubleshooting

**No jobs extracted?**
- Run with `DEBUG=1` to open a headed browser and watch what loads.
- Indeed's page structure changes; the scraper uses a 3-layer extraction strategy (JS data objects → serialised JSON in script tags → DOM attributes).

**Blocked / Cloudflare challenge?**
- Add more proxies to `proxies.txt`.
- Increase delays by adjusting `human_delay` arguments in `browser_manager.py`.
- Try a residential proxy service.

**`playwright install` not found?**
- Ensure your virtual environment is active and `playwright` is installed via pip.
