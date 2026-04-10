# JobHunt AI

Multi-board Canadian job scraper with AI-powered resume matching, ATS optimization, and cover letter generation.

## Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy async, aiosqlite |
| Scraping | python-jobspy (LinkedIn/Indeed/Glassdoor/ZipRecruiter/Google), custom httpx scrapers (Eluta, JobBank) |
| Resume | pdfplumber (PDF), python-docx (DOCX) |
| Matching | sentence-transformers (all-MiniLM-L6-v2) |
| AI | Anthropic Claude (claude-sonnet-4-6) |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS + Framer Motion |

## Quick Start (Local Dev)

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt

# Copy and fill in your Anthropic API key
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=sk-ant-...

uvicorn app.main:app --reload --port 8000
```

Backend API docs available at: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

### 3. Docker (Production)

```bash
# Set your API key
export ANTHROPIC_API_KEY=sk-ant-...

docker compose up --build
```

App: http://localhost:80

## Features

- **7 boards scraped concurrently**: LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google Jobs, Eluta.ca, JobBank.gc.ca
- **Resume upload**: PDF, DOCX, or TXT — auto-parsed for skills, experience, seniority
- **Semantic matching**: sentence-transformers + skill overlap + seniority alignment → 0–100 match score
- **ATS optimizer**: Claude rewrites your resume content to maximize keyword alignment while preserving your template
- **Cover letter generator**: Human-tone, concise, role-specific letters via Claude

## Project Structure

```
job-hunt/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/          # config, database
│   │   ├── models/        # SQLAlchemy ORM
│   │   ├── schemas/       # Pydantic
│   │   ├── scrapers/      # per-board + orchestrator
│   │   ├── services/      # resume_parser, matcher, ats_optimizer, cover_letter
│   │   └── api/routes/    # jobs, resume, generate
│   └── requirements.txt
└── frontend/
    └── src/
        ├── pages/         # Landing, Dashboard, Optimize, CoverLetter
        ├── components/    # JobCard, ResumeDropzone, ui/*
        ├── store/         # Zustand
        └── lib/api.ts     # Axios client
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/jobs/scrape` | Start async scrape session |
| GET | `/api/jobs/session/{id}` | Poll session status |
| GET | `/api/jobs/{session_id}` | List jobs (with filters) |
| POST | `/api/jobs/{session_id}/match` | Score jobs against resume |
| POST | `/api/resume/upload` | Upload + parse resume |
| POST | `/api/generate/optimize` | ATS-optimize resume |
| POST | `/api/generate/cover-letter` | Generate cover letter |
