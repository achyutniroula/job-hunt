# JobHunt AI

AI-powered job search platform for the Canadian market. Scrapes 7 job boards concurrently, semantically matches jobs to your resume, optimizes for ATS, generates cover letters, and runs a full interview prep suite with GitHub context awareness.

---

## Features

- **Job Scraping** — LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google Jobs, Eluta.ca, JobBank.gc.ca scraped in parallel
- **Resume Matching** — Semantic similarity scoring via `sentence-transformers`
- **ATS Optimizer** — Claude rewrites your resume for keyword alignment without changing any facts
- **Cover Letter Generator** — Role-specific cover letters with DOCX export
- **Interview Prep** — AI chat coach, brainstorm threads, company links, resume preview
- **GitHub Context** — Pulls your repos (file tree, dependencies, source files) into the interview AI's context

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 20+ |
| npm | 9+ |
| Git | any |

Docker is optional but recommended for production.

---

## Quick Start (Local Dev)

### 1. Clone

```bash
git clone https://github.com/achyutniroula/job-hunt.git
cd job-hunt
```

### 2. Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser (used by scrapers)
playwright install chromium

# Copy env file
cp .env.example .env
```

Open `.env` and fill in your API keys (see [Environment Variables](#environment-variables)).

```bash
# Start the backend at http://localhost:8000
uvicorn app.main:app --reload --port 8000
```

The database (`jobhunt.db`) is created automatically on first run — no migrations needed.

### 3. Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

App runs at **http://localhost:5173**

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in the values below.

### Required

| Variable | Where to get it |
|----------|----------------|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) → API Keys |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) → API Keys (free tier available) |

### Optional but Recommended

| Variable | Purpose |
|----------|---------|
| `GITHUB_TOKEN` | Increases GitHub API rate limit from 60 → 5,000 req/hr. Required for GitHub context in interview prep. Create at [github.com/settings/tokens](https://github.com/settings/tokens) — select **public_repo** read-only scope. |

### App Config (defaults work for local dev)

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `development` | Set to `production` in prod |
| `APP_SECRET_KEY` | `dev-secret-key` | Change in production |
| `DATABASE_URL` | `sqlite+aiosqlite:///./jobhunt.db` | SQLite path |
| `UPLOAD_DIR` | `./uploads` | Resume storage directory |
| `MAX_UPLOAD_SIZE_MB` | `10` | Max resume upload size |
| `ALLOWED_ORIGINS` | `http://localhost:5173,http://localhost:3000` | CORS origins |
| `DEFAULT_LOCATION` | `Canada` | Default job search location |
| `SCRAPER_MAX_WORKERS` | `6` | Concurrent scraper threads |
| `SCRAPER_RATE_LIMIT_DELAY` | `2.0` | Seconds between requests per domain |
| `SCRAPER_MAX_RESULTS_PER_BOARD` | `30` | Jobs returned per board per search |
| `INTERVIEW_RESUME_DIR` | `data/resumes` | Interview session PDF storage |

---

## Docker (Production)

```bash
# Copy and configure env
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Build and start both services
docker compose up --build
```

App is available at **http://localhost** (port 80).

Services started by Docker:
- **backend** — FastAPI on port 8000 (internal)
- **frontend** — React build served by Nginx on port 80, proxies `/api/*` to backend

To stop:

```bash
docker compose down
```

Data persists in `backend/jobhunt.db` via a Docker volume.

---

## How to Use

### Job Search

1. Upload your resume (PDF, DOCX, or TXT) from the **Dashboard**
2. Enter job keywords and location, click **Search**
3. Wait for scraping (~30–60s for all 7 boards)
4. Click **Match to Resume** to score and rank results by fit

### ATS Resume Optimizer

1. Go to **Optimize**
2. Upload your resume and paste a job description
3. Claude rewrites bullet points for ATS keyword alignment — nothing factual is changed
4. Review the transparency report and copy the optimized text

### Cover Letter

1. Go to **Cover Letter**
2. Upload your resume, paste the job description, enter the company name
3. Download as DOCX or copy the text

### Interview Prep

1. Go to **Interview** → **New Session**
2. Fill in job title, company, and job description
3. Paste your resume text (auto-filled if you used the optimizer)
4. Optionally add your GitHub URL — the AI will read your repos, file structure, and dependencies for full context
5. Click **Create Session**

Inside a session you get six tabs:

| Tab | What it does |
|-----|-------------|
| **Resume** | Renders your resume as a formatted preview |
| **Job Details** | Summary of the role |
| **Company** | Glassdoor, LinkedIn, Indeed links auto-generated |
| **Chat** | Ask the AI interview questions, strategy, or anything about the role. Uses your GitHub context if provided. |
| **GitHub** | Visual breakdown of your repos, languages, and key files |
| **Brainstorm** | Threaded discussions for deeper prep on any topic |

---

## Project Structure

```
job-hunt/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app + lifespan
│   │   ├── core/
│   │   │   ├── config.py         # Pydantic settings (reads .env)
│   │   │   └── database.py       # Async SQLAlchemy engine + auto init
│   │   ├── models/               # SQLAlchemy ORM models
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── api/routes/
│   │   │   ├── jobs.py
│   │   │   ├── resume.py
│   │   │   ├── generate.py
│   │   │   └── interview.py
│   │   ├── scrapers/             # Per-board scraper implementations
│   │   └── services/
│   │       ├── ats_optimizer.py
│   │       ├── github_ingestion.py
│   │       ├── groq_chat.py
│   │       ├── interview_qa_generator.py
│   │       └── ...
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   │   └── interview/
│   │   ├── store/                # Zustand state
│   │   ├── lib/api.ts            # Axios client
│   │   └── types/
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
└── README.md
```

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, SQLite |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Zustand |
| AI | Anthropic Claude (claude-sonnet-4-6), Groq (llama-3.3-70b) |
| ML | sentence-transformers (all-MiniLM-L6-v2) |
| Scraping | python-jobspy, httpx, BeautifulSoup4, Playwright |
| Export | fpdf2 (PDF), python-docx (DOCX) |
| Deployment | Docker, Nginx |

---

## API Reference

```
GET  /api/health

POST /api/jobs/scrape
GET  /api/jobs/session/{id}
GET  /api/jobs/{session_id}
POST /api/jobs/{session_id}/match
GET  /api/jobs/detail/{job_id}

POST /api/resume/upload
GET  /api/resume/{filename}/parsed
GET  /api/resume/{filename}/download

POST /api/generate/optimize
POST /api/generate/cover-letter
POST /api/generate/cover-letter-docx
POST /api/generate/fetch-url

POST /api/interview/session
GET  /api/interview/sessions
GET  /api/interview/session/{id}
GET  /api/interview/session/{id}/resume.pdf
GET  /api/interview/session/{id}/github
POST /api/interview/{id}/chat
GET  /api/interview/{id}/chat
POST /api/interview/{id}/brainstorm/thread
GET  /api/interview/{id}/brainstorm/threads
POST /api/interview/{id}/brainstorm/thread/{thread_id}/message
```

Interactive docs at **http://localhost:8000/docs** when the backend is running.

---

## Troubleshooting

**`ModuleNotFoundError` on backend start**
Make sure the virtual environment is activated before running `uvicorn`.

**Scraping returns 0 jobs**
Some boards block headless browsers. Try reducing `SCRAPER_MAX_WORKERS` to `2` and increasing `SCRAPER_RATE_LIMIT_DELAY` to `3.0`.

**GitHub context not loading in interview prep**
Without a `GITHUB_TOKEN`, GitHub's unauthenticated limit is 60 requests/hour and exhausts quickly. Add a token — a classic PAT with only `public_repo` read scope is enough.

**PDF generation fails**
`fpdf2` must be installed (`pip install fpdf2`). It is in `requirements.txt` but double-check your venv is active.

**`playwright install` hangs or fails**
Try `playwright install --with-deps chromium` to also install OS-level browser dependencies.

**CORS errors in browser**
Add your frontend URL to `ALLOWED_ORIGINS` in `.env`, e.g. `http://localhost:5173`.

---

## License

MIT
