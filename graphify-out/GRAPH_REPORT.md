# Graph Report - .  (2026-04-26)

## Corpus Check
- 135 files · ~127,758 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 914 nodes · 1684 edges · 60 communities detected
- Extraction: 67% EXTRACTED · 33% INFERRED · 0% AMBIGUOUS · INFERRED: 552 edges (avg confidence: 0.62)
- Token cost: 12,800 input · 2,100 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Indeed Stealth Scraper Core|Indeed Stealth Scraper Core]]
- [[_COMMUNITY_Interview API Routes|Interview API Routes]]
- [[_COMMUNITY_Backend Dependencies|Backend Dependencies]]
- [[_COMMUNITY_Interview Module Core|Interview Module Core]]
- [[_COMMUNITY_ATS Optimizer Engine|ATS Optimizer Engine]]
- [[_COMMUNITY_Candidate Profile (Achyut)|Candidate Profile (Achyut)]]
- [[_COMMUNITY_Job Scraper Pipeline|Job Scraper Pipeline]]
- [[_COMMUNITY_Indeed Scraper UI App|Indeed Scraper UI App]]
- [[_COMMUNITY_Resume & Matching Engine|Resume & Matching Engine]]
- [[_COMMUNITY_IT Job Classifier|IT Job Classifier]]
- [[_COMMUNITY_Export & PDF Generator|Export & PDF Generator]]
- [[_COMMUNITY_Canadian Portal Scanner|Canadian Portal Scanner]]
- [[_COMMUNITY_Job API & Data Models|Job API & Data Models]]
- [[_COMMUNITY_UI Design Reference|UI Design Reference]]
- [[_COMMUNITY_GitHub Ingestion & Config|GitHub Ingestion & Config]]
- [[_COMMUNITY_Fit Analyzer Service|Fit Analyzer Service]]
- [[_COMMUNITY_Design System|Design System]]
- [[_COMMUNITY_Archetype Detector|Archetype Detector]]
- [[_COMMUNITY_Indeed Scrape API Routes|Indeed Scrape API Routes]]
- [[_COMMUNITY_Candidate Profile (Sujala)|Candidate Profile (Sujala)]]
- [[_COMMUNITY_Database & App Entry|Database & App Entry]]
- [[_COMMUNITY_Job Card Component|Job Card Component]]
- [[_COMMUNITY_Results API Routes|Results API Routes]]
- [[_COMMUNITY_Profile Input Form|Profile Input Form]]
- [[_COMMUNITY_Dashboard Page|Dashboard Page]]
- [[_COMMUNITY_React App Shell|React App Shell]]
- [[_COMMUNITY_Scraper Init Modules|Scraper Init Modules]]
- [[_COMMUNITY_City Selector|City Selector]]
- [[_COMMUNITY_Navigation Bar|Navigation Bar]]
- [[_COMMUNITY_Sidebar Component|Sidebar Component]]
- [[_COMMUNITY_Skill Tag UI|Skill Tag UI]]
- [[_COMMUNITY_Loading Spinner|Loading Spinner]]
- [[_COMMUNITY_Interview Prep Page|Interview Prep Page]]
- [[_COMMUNITY_Backend App Init|Backend App Init]]
- [[_COMMUNITY_API Module Init|API Module Init]]
- [[_COMMUNITY_API Routes Init|API Routes Init]]
- [[_COMMUNITY_Core Module Init|Core Module Init]]
- [[_COMMUNITY_Models Module Init|Models Module Init]]
- [[_COMMUNITY_Job Rationale|Job Rationale]]
- [[_COMMUNITY_Schemas Module Init|Schemas Module Init]]
- [[_COMMUNITY_Scrapers Module Init|Scrapers Module Init]]
- [[_COMMUNITY_Services Module Init|Services Module Init]]
- [[_COMMUNITY_PostCSS Config|PostCSS Config]]
- [[_COMMUNITY_Tailwind Config|Tailwind Config]]
- [[_COMMUNITY_Vite Config|Vite Config]]
- [[_COMMUNITY_React Entry Point|React Entry Point]]
- [[_COMMUNITY_Distance Slider|Distance Slider]]
- [[_COMMUNITY_Resume Dropzone|Resume Dropzone]]
- [[_COMMUNITY_Transparency Report|Transparency Report]]
- [[_COMMUNITY_Company Links Widget|Company Links Widget]]
- [[_COMMUNITY_GitHub Repos Widget|GitHub Repos Widget]]
- [[_COMMUNITY_Job Details Widget|Job Details Widget]]
- [[_COMMUNITY_Board Badge UI|Board Badge UI]]
- [[_COMMUNITY_Score Ring UI|Score Ring UI]]
- [[_COMMUNITY_Canadian Cities Data|Canadian Cities Data]]
- [[_COMMUNITY_App State Store|App State Store]]
- [[_COMMUNITY_TypeScript Types|TypeScript Types]]
- [[_COMMUNITY_Browser Manager Note A|Browser Manager Note A]]
- [[_COMMUNITY_Browser Manager Note B|Browser Manager Note B]]
- [[_COMMUNITY_Scraper API Routes Init|Scraper API Routes Init]]

## God Nodes (most connected - your core abstractions)
1. `BrowserManager` - 43 edges
2. `ProxyManager` - 39 edges
3. `Job` - 29 edges
4. `IndeedScraper` - 28 edges
5. `Interview Prep API routes.` - 21 edges
6. `Convert stored github JSON into a rich LLM-friendly string.` - 21 edges
7. `RawJob` - 21 edges
8. `ATSOptimizeResponse` - 20 edges
9. `StorageManager` - 20 edges
10. `ParsedResume` - 18 edges

## Surprising Connections (you probably didn't know these)
- `Project: JobHunt AI` --semantically_similar_to--> `Indeed Scraper UI Frontend`  [INFERRED] [semantically similar]
  backend/uploads/Achyut_Niroula_Resume.pdf → indeed-stealth-scraper/indeed_scraper/ui/index.html
- `Project: Indeed Stealth Scraper` --semantically_similar_to--> `Indeed Scraper UI Frontend`  [INFERRED] [semantically similar]
  backend/uploads/Achyut_Niroula_Resume.pdf → indeed-stealth-scraper/indeed_scraper/ui/index.html
- `Indeed Job Schema (job_id, title, company, etc.)` --semantically_similar_to--> `Job Scraping (7 boards)`  [INFERRED] [semantically similar]
  indeed-stealth-scraper/README.md → README.md
- `Tracks a single scraping run initiated by the user.` --uses--> `Base`  [INFERRED]
  backend\app\models\session.py → backend\app\core\database.py
- `Project: Indeed Stealth Scraper` --shares_data_with--> `Proxy Configuration File`  [INFERRED]
  backend/uploads/Achyut_Niroula_Resume.pdf → indeed-stealth-scraper/proxies.txt

## Hyperedges (group relationships)
- **ATS Optimization Pipeline (Resume + GitHub + Claude)** — readme_ats_optimizer, prompt_github_ingestion_service, prompt_optimize_with_digest, readme_anthropic_claude, prompt_ats_optimize_response_schema [INFERRED 0.90]
- **Interview Prep System (Session + Q&A + Chat + Brainstorm)** — readme_interview_prep, prompt_interview_session_model, prompt_interview_qa_generator, prompt_groq_chat_service, prompt_brainstorm_thread_model, prompt_interview_persistence [EXTRACTED 0.95]
- **Indeed Stealth Scraper Module Suite** — indeed_scraper_browser_manager, indeed_scraper_proxy_manager, indeed_scraper_core, indeed_scraper_job_parser, indeed_scraper_storage_manager [EXTRACTED 1.00]
- **Achyut Niroula Resume Variants as ATS Optimization Pipeline Outputs** — person_achyut_niroula, resume_uuid_370fc369, resume_uuid_80652be1, resume_uuid_f31ac598, resume_uuid_f7e5b2cd, achyut_resume_optimized_orig, achyut_resume_variant_current [INFERRED 0.80]
- **JobHunt AI Full-Stack System (Prompt + UI + Scraper)** — master_prompt_system, code_html_jobhunt_optimize_ui, scraper_ui_index_html, proxies_txt_proxy_config [INFERRED 0.85]
- **Indeed Scraper Diagnostic Test Pipeline** — scraper_ui_index_html, diag_page_start0, diag_page_start10 [INFERRED 0.78]
- **Optimize Page Layout Components** — screen_active_applications, screen_letter_synthesis_panel, screen_metrics_bar, screen_concierge_hero [EXTRACTED 1.00]
- **Active Job Application Cards** — screen_job_card_ux_designer, screen_job_card_product_strategist, screen_job_card_ai_researcher [EXTRACTED 1.00]
- **Letter Quality Metrics Group** — screen_metric_ats_match, screen_metric_tone_analysis, screen_metric_keywords [EXTRACTED 1.00]
- **Dual Navigation System (Top + Sidebar)** — screen_topnav, screen_sidebar, screen_nav_optimize, screen_sidebar_optimize [INFERRED 0.85]
- **AI Letter Generation Flow** — screen_synthesis_powered_by, screen_synthesis_textarea, screen_generate_button, screen_letter_synthesis_panel [INFERRED 0.85]

## Communities

### Community 0 - "Indeed Stealth Scraper Core"
Cohesion: 0.04
Nodes (87): sleep(), BrowserManager, human_delay(), browser_manager.py — Stealth Playwright browser lifecycle management., Open and return a new stealth page., Manages a single Playwright Chromium browser instance with stealth settings., subtle_mouse_move(), main() (+79 more)

### Community 1 - "Interview API Routes"
Cohesion: 0.03
Nodes (37): clearInterviewChat(), createBrainstormThread(), createInterviewSession(), deleteBrainstormThread(), deleteInterviewChatMessage(), deleteInterviewSession(), downloadCoverLetterDocx(), fetchJobUrl() (+29 more)

### Community 2 - "Backend Dependencies"
Cohesion: 0.04
Nodes (69): Anthropic SDK (backend dep), BeautifulSoup4 HTML Parser (backend dep), FastAPI Framework (backend dep), fpdf2 PDF Generator (backend dep), httpx Async HTTP Client (backend dep), python-jobspy Multi-board Scraper (backend dep), pdfplumber Resume Parser (backend dep), Playwright (backend dep) (+61 more)

### Community 3 - "Interview Module Core"
Cohesion: 0.07
Nodes (47): Base, BaseModel, CompanyLinks, enrich_company(), Company enrichment — DuckDuckGo + slug-based URL construction. No paid APIs., _slug(), Base, DeclarativeBase (+39 more)

### Community 4 - "ATS Optimizer Engine"
Cohesion: 0.09
Nodes (53): _build_rich_github_summary(), _estimate_ats_score(), _extract_tag(), _generate_latex(), _jd_keywords(), _keyword_breakdown(), optimize_for_session(), optimize_resume() (+45 more)

### Community 5 - "Candidate Profile (Achyut)"
Cohesion: 0.05
Nodes (52): Nipissing University — B.Sc. Honours Computer Science, Web Developer / Research Assistant at Nipissing University, Project: AI Video Analytics Platform, Project: Cloud Chat Distributed Messaging System, Project: Cloud Inventory Tracker, Project: Indeed Stealth Scraper, Project: JobHunt AI, Project: Multimodal Video Understanding Platform (+44 more)

### Community 6 - "Job Scraper Pipeline"
Cohesion: 0.09
Nodes (31): BaseScraper, Normalised job record produced by any scraper., Every board scraper must implement this interface., RawJob, BaseScraper, ElutaScraper, _parse_relative_date(), Scraper for Eluta.ca — Canada's largest job search engine aggregating postings f (+23 more)

### Community 7 - "Indeed Scraper UI App"
Cohesion: 0.08
Nodes (36): addITKeyword(), api(), _appendRows(), applyFilters(), applySortToDisplay(), _buildRowCells(), changePage(), clearFilters() (+28 more)

### Community 8 - "Resume & Matching Engine"
Cohesion: 0.09
Nodes (40): compute_match_score(), _cosine_sim(), _get_model(), _keyword_density_score(), Semantic job-to-resume matching engine.  Combines:   1. Sentence-transformer cos, Return a match score 0–100 for a (resume, job) pair., Compute match scores for all jobs, attach to job objects in-place,     and retur, Load sentence-transformer model once, cache it. (+32 more)

### Community 9 - "IT Job Classifier"
Cohesion: 0.1
Nodes (34): classify_it_job(), _emb_backend(), _emb_threshold(), extract_level(), _load_emb_model(), it_classifier.py — Strict 4-layer IT job classifier.  Layers ------ 1. Title sco, Classify whether a job is an IT/tech position.      Returns     -------     {, Returns (score, matched_whitelist_labels, matched_blacklist_labels). (+26 more)

### Community 10 - "Export & PDF Generator"
Cohesion: 0.07
Nodes (30): _build_pdf_response(), _build_single_job_pdf(), export_excel(), export_pdf(), export_single_pdf(), routes/export.py — GET /api/export/excel, /api/export/pdf, /api/export/pdf/{job_, Stream a single job's details as a PDF., Stream all scraped jobs as an .xlsx file. (+22 more)

### Community 11 - "Canadian Portal Scanner"
Cohesion: 0.13
Nodes (19): PortalConfig, HTMLParser, _HTMLStripper, _matches_keywords(), _normalise(), Canadian company portal scanner — Greenhouse/Lever/Ashby APIs + Playwright fallb, Scans Canadian company portals for job listings matching keywords.     Greenhous, _scan_ashby() (+11 more)

### Community 12 - "Job API & Data Models"
Cohesion: 0.19
Nodes (25): JobBase, JobFilter, JobRead, ScrapeRequest, ScrapeSessionRead, get_job(), get_session(), _grade_jobs_background() (+17 more)

### Community 13 - "UI Design Reference"
Cohesion: 0.09
Nodes (28): Active Applications Panel, The Concierge Hero Section, Generate Button, Import New Listing Button, Job Card - Lead AI Researcher, Job Card - Product Strategist (Selected), Job Card - Senior UX Designer, JOBHUNT AI Application (+20 more)

### Community 14 - "GitHub Ingestion & Config"
Cohesion: 0.13
Nodes (22): BaseSettings, get_settings(), Settings, _extract_username(), _fetch_file_content(), fetch_github_digest(), fetch_github_profile(), _fetch_repo_detail() (+14 more)

### Community 15 - "Fit Analyzer Service"
Cohesion: 0.13
Nodes (24): Exception, analyze_all_jobs(), analyze_fit(), detect_seniority(), detect_user_level(), _estimate_years(), extract_requirements(), _parse_fit_response() (+16 more)

### Community 16 - "Design System"
Cohesion: 0.16
Nodes (15): Digital Concierge Creative North Star, Elevation and Depth via Surface Token Shifts, No-Line Rule (border via surface tiers), Obsidian Ether Design System, Surface Hierarchy (nested translucent layers), Typography Pairing: Manrope + Inter, CSS Custom Properties (dark + light theme tokens), Glass Button UI Component Pattern (+7 more)

### Community 17 - "Archetype Detector"
Cohesion: 0.23
Nodes (11): detect_archetype(), get_archetype_weights(), Job archetype detection via Groq (10-token call)., _call_detect(), _mock_groq_response(), Tests for archetype_detector.py — mocks Groq, no real API calls., test_archetype_weights(), test_backend() (+3 more)

### Community 18 - "Indeed Scrape API Routes"
Cohesion: 0.22
Nodes (8): routes/scrape.py — POST /api/scrape, DELETE /api/scrape/stop, GET /api/scrape/st, Start a background scrape session., Signal the running scrape to stop., Return the current scrape state (status, counters, recent logs)., scrape_status(), ScrapeRequest, start_scrape_endpoint(), stop_scrape_endpoint()

### Community 19 - "Candidate Profile (Sujala)"
Cohesion: 0.25
Nodes (8): Sujala Niroula (Person), BSc Biology and Chemistry — University of Alberta, BSc Honours Microbiology — University of North Bengal, Ontario Mortgage Agent Course, Co-owner/Operator — Northern Himalayan Cafe, Settlement Worker in Schools Coordinator — NBDMC, Skills: Microsoft Office Suite and Teams, Skills: English, Nepali, Hindi, Bengali

### Community 20 - "Database & App Entry"
Cohesion: 0.29
Nodes (3): init_db(), Create all tables on startup, and migrate new columns if needed., lifespan()

### Community 21 - "Job Card Component"
Cohesion: 0.4
Nodes (2): FitAnalysisPanel(), gradeColor()

### Community 22 - "Results API Routes"
Cohesion: 0.4
Nodes (5): get_results(), _load_from_latest_file(), routes/results.py — GET /api/results  (paginated, filtered)  Reads from in-memor, Return jobs from the newest JSON file in the output directory., Return a paginated, filtered slice of the job list.

### Community 23 - "Profile Input Form"
Cohesion: 0.5
Nodes (0): 

### Community 24 - "Dashboard Page"
Cohesion: 0.5
Nodes (0): 

### Community 25 - "React App Shell"
Cohesion: 0.67
Nodes (0): 

### Community 26 - "Scraper Init Modules"
Cohesion: 0.67
Nodes (1): indeed_scraper.api — FastAPI web UI for the Indeed scraper.

### Community 27 - "City Selector"
Cohesion: 1.0
Nodes (0): 

### Community 28 - "Navigation Bar"
Cohesion: 1.0
Nodes (0): 

### Community 29 - "Sidebar Component"
Cohesion: 1.0
Nodes (0): 

### Community 30 - "Skill Tag UI"
Cohesion: 1.0
Nodes (0): 

### Community 31 - "Loading Spinner"
Cohesion: 1.0
Nodes (0): 

### Community 32 - "Interview Prep Page"
Cohesion: 1.0
Nodes (0): 

### Community 33 - "Backend App Init"
Cohesion: 1.0
Nodes (0): 

### Community 34 - "API Module Init"
Cohesion: 1.0
Nodes (0): 

### Community 35 - "API Routes Init"
Cohesion: 1.0
Nodes (0): 

### Community 36 - "Core Module Init"
Cohesion: 1.0
Nodes (0): 

### Community 37 - "Models Module Init"
Cohesion: 1.0
Nodes (0): 

### Community 38 - "Job Rationale"
Cohesion: 1.0
Nodes (1): skills is stored as JSON string in DB; deserialize it.

### Community 39 - "Schemas Module Init"
Cohesion: 1.0
Nodes (0): 

### Community 40 - "Scrapers Module Init"
Cohesion: 1.0
Nodes (0): 

### Community 41 - "Services Module Init"
Cohesion: 1.0
Nodes (0): 

### Community 42 - "PostCSS Config"
Cohesion: 1.0
Nodes (0): 

### Community 43 - "Tailwind Config"
Cohesion: 1.0
Nodes (0): 

### Community 44 - "Vite Config"
Cohesion: 1.0
Nodes (0): 

### Community 45 - "React Entry Point"
Cohesion: 1.0
Nodes (0): 

### Community 46 - "Distance Slider"
Cohesion: 1.0
Nodes (0): 

### Community 47 - "Resume Dropzone"
Cohesion: 1.0
Nodes (0): 

### Community 48 - "Transparency Report"
Cohesion: 1.0
Nodes (0): 

### Community 49 - "Company Links Widget"
Cohesion: 1.0
Nodes (0): 

### Community 50 - "GitHub Repos Widget"
Cohesion: 1.0
Nodes (0): 

### Community 51 - "Job Details Widget"
Cohesion: 1.0
Nodes (0): 

### Community 52 - "Board Badge UI"
Cohesion: 1.0
Nodes (0): 

### Community 53 - "Score Ring UI"
Cohesion: 1.0
Nodes (0): 

### Community 54 - "Canadian Cities Data"
Cohesion: 1.0
Nodes (0): 

### Community 55 - "App State Store"
Cohesion: 1.0
Nodes (0): 

### Community 56 - "TypeScript Types"
Cohesion: 1.0
Nodes (0): 

### Community 57 - "Browser Manager Note A"
Cohesion: 1.0
Nodes (1): Sleep for a random duration to mimic human pacing.

### Community 58 - "Browser Manager Note B"
Cohesion: 1.0
Nodes (1): Move the mouse along a short random path before an interaction         to reduce

### Community 59 - "Scraper API Routes Init"
Cohesion: 1.0
Nodes (0): 

## Ambiguous Edges - Review These
- `Groq Chat Service (groq_chat.py)` → `Groq Chat Service (groq_chat.py)`  [AMBIGUOUS]
  prompts/interview_prep_prompt.txt · relation: semantically_similar_to

## Knowledge Gaps
- **154 isolated node(s):** `Tests for archetype_detector.py — mocks Groq, no real API calls.`, `Test script for the ATS pipeline. - Real GitHub API calls (tests plumbing) - Moc`, `Build a mock AsyncAnthropic client with pre-set call responses.`, `Tests for fit_analyzer.py — mocks Groq, no real API calls.`, `Tests for canadian_portals.py and portal_scanner.py — mocks httpx.` (+149 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `City Selector`** (2 nodes): `CitySelector()`, `CitySelector.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Navigation Bar`** (2 nodes): `Navbar.tsx`, `isActive()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Sidebar Component`** (2 nodes): `Sidebar.tsx`, `Sidebar()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Skill Tag UI`** (2 nodes): `SkillTag.tsx`, `SkillTag()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Loading Spinner`** (2 nodes): `Spinner.tsx`, `Spinner()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Interview Prep Page`** (2 nodes): `InterviewPrep.tsx`, `switchModule()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Backend App Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API Module Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API Routes Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Core Module Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Models Module Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Job Rationale`** (1 nodes): `skills is stored as JSON string in DB; deserialize it.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Schemas Module Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Scrapers Module Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Services Module Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `PostCSS Config`** (1 nodes): `postcss.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Tailwind Config`** (1 nodes): `tailwind.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Vite Config`** (1 nodes): `vite.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `React Entry Point`** (1 nodes): `main.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Distance Slider`** (1 nodes): `DistanceSlider.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Resume Dropzone`** (1 nodes): `ResumeDropzone.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Transparency Report`** (1 nodes): `TransparencyReport.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Company Links Widget`** (1 nodes): `CompanyLinks.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `GitHub Repos Widget`** (1 nodes): `GitHubRepos.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Job Details Widget`** (1 nodes): `JobDetails.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Board Badge UI`** (1 nodes): `BoardBadge.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Score Ring UI`** (1 nodes): `ScoreRing.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Canadian Cities Data`** (1 nodes): `canadianCities.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `App State Store`** (1 nodes): `appStore.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `TypeScript Types`** (1 nodes): `index.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Browser Manager Note A`** (1 nodes): `Sleep for a random duration to mimic human pacing.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Browser Manager Note B`** (1 nodes): `Move the mouse along a short random path before an interaction         to reduce`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Scraper API Routes Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Groq Chat Service (groq_chat.py)` and `Groq Chat Service (groq_chat.py)`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **Why does `sleep()` connect `Indeed Stealth Scraper Core` to `Canadian Portal Scanner`, `Fit Analyzer Service`, `Job Scraper Pipeline`, `Indeed Scraper UI App`?**
  _High betweenness centrality (0.236) - this node is a cross-community bridge._
- **Why does `Indeed Stealth Scraper (Standalone Phase 1)` connect `Export & PDF Generator` to `Indeed Stealth Scraper Core`, `Backend Dependencies`?**
  _High betweenness centrality (0.122) - this node is a cross-community bridge._
- **Are the 35 inferred relationships involving `BrowserManager` (e.g. with `api/main.py — FastAPI application: mounts API routes and serves the UI.  Run fro` and `IndeedScraper`) actually correct?**
  _`BrowserManager` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `ProxyManager` (e.g. with `api/main.py — FastAPI application: mounts API routes and serves the UI.  Run fro` and `IndeedScraper`) actually correct?**
  _`ProxyManager` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `Job` (e.g. with `DocxRequest` and `FetchUrlRequest`) actually correct?**
  _`Job` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `IndeedScraper` (e.g. with `api/main.py — FastAPI application: mounts API routes and serves the UI.  Run fro` and `BrowserManager`) actually correct?**
  _`IndeedScraper` has 21 INFERRED edges - model-reasoned connections that need verification._