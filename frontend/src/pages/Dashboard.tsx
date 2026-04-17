import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Filter, Wifi, AlertTriangle, ArrowLeft, Cpu } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { getSession, getJobs, matchJobsToResume } from "@/lib/api";
import { useAppStore } from "@/store/appStore";
import JobCard from "@/components/JobCard";
import Spinner from "@/components/ui/Spinner";
import type { Job } from "@/types";

const SENIORITY_OPTS = ["internship", "junior", "mid", "senior", "lead", "executive"];
const BOARDS = ["linkedin", "indeed", "glassdoor", "ziprecruiter", "google", "eluta", "jobbank", "greenhouse", "lever", "ashby", "custom"];
const BOARD_LABELS: Record<string, string> = {
  linkedin: "LinkedIn", indeed: "Indeed", glassdoor: "Glassdoor",
  ziprecruiter: "ZipRecruiter", google: "Google", eluta: "Eluta", jobbank: "JobBank",
  greenhouse: "Greenhouse", lever: "Lever", ashby: "Ashby", custom: "Direct Portals",
};
const BOARD_GROUPS = [
  { label: "Job Boards", keys: ["linkedin", "indeed", "glassdoor", "ziprecruiter", "google", "eluta", "jobbank"] },
  { label: "Canadian Portals", keys: ["greenhouse", "lever", "ashby", "custom"] },
];
const POLL_MS = 3000;
const FIT_POLL_MS = 6000;

export default function Dashboard() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { resumeFilename, parsedResume, setActiveSession } = useAppStore();

  const [jobs,            setJobs]           = useState<Job[]>([]);
  const [matching,        setMatching]        = useState(false);
  const [matched,         setMatched]         = useState(false);
  const [gradingActive,   setGradingActive]   = useState(false);
  const [remoteFilter,    setRemoteFilter]    = useState(false);
  const [boardFilter,     setBoardFilter]     = useState<string[]>([]);
  const [seniorityFilter, setSeniorityFilter] = useState<string[]>([]);
  const [minScore,        setMinScore]        = useState<number | null>(null);
  const [sortBy,          setSortBy]          = useState<"match_score" | "posted_at">("posted_at");
  const [itMode,          setItMode]          = useState(false);

  const { data: session } = useQuery({
    queryKey: ["session", sessionId],
    queryFn: () => getSession(sessionId!),
    refetchInterval: query =>
      query.state.data?.status === "pending" || query.state.data?.status === "running" ? POLL_MS : false,
    enabled: !!sessionId,
  });

  const fetchJobs = useCallback(async () => {
    if (!sessionId) return;
    const params: Record<string, unknown> = { sort_by: sortBy, limit: 100 };
    if (remoteFilter) params.remote_only = true;
    if (seniorityFilter.length) params.seniority = seniorityFilter.join(",");
    if (minScore !== null) params.min_score = minScore;
    if (boardFilter.length) params.boards = boardFilter.join(",");
    const data = await getJobs(sessionId, params as any);
    setJobs(data);
  }, [sessionId, remoteFilter, boardFilter, seniorityFilter, minScore, sortBy]);

  const handleMatch = useCallback(async () => {
    if (!resumeFilename || !sessionId) return;
    setMatching(true);
    try {
      const scored = await matchJobsToResume(sessionId, resumeFilename);
      setJobs(scored);
      setMatched(true);
      setSortBy("match_score");
      toast.success("Jobs matched — AI grades loading…");
      setGradingActive(true);
    } catch {
      toast.error("Matching failed — try again");
    } finally {
      setMatching(false);
    }
  }, [resumeFilename, sessionId]);

  // Trigger matching automatically when scrape finishes
  useEffect(() => {
    if (session?.status === "done") {
      setActiveSession(session);
      fetchJobs();
      if (resumeFilename && !session.resume_filename && !matched && !matching) {
        handleMatch();
      }
      if (session.resume_filename && !matched) {
        setMatched(true);
        setSortBy("match_score");
        setGradingActive(true);
      }
    } else if (session?.status === "running" && (session?.job_count ?? 0) > 0) {
      fetchJobs();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session?.status, session?.job_count, session?.resume_filename]);

  useEffect(() => {
    if (session?.status === "done") fetchJobs();
  }, [remoteFilter, boardFilter, seniorityFilter, minScore, sortBy]);

  // Poll for fit_analysis updates while background grading is running
  useEffect(() => {
    if (!gradingActive || !sessionId) return;
    const interval = setInterval(async () => {
      const data = await getJobs(sessionId, { sort_by: sortBy, limit: 100 });
      setJobs(data);
      const allGraded = data.length > 0 && data.every(j => j.fit_analysis !== null);
      if (allGraded) {
        setGradingActive(false);
        clearInterval(interval);
        toast.success("AI fit grades ready!", { id: "grading-done" });
      }
    }, FIT_POLL_MS);
    return () => clearInterval(interval);
  }, [gradingActive, sessionId, sortBy]);

  const toggleSeniority = (s: string) =>
    setSeniorityFilter(prev => prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s]);
  const toggleBoard = (b: string) =>
    setBoardFilter(prev => prev.includes(b) ? prev.filter(x => x !== b) : [...prev, b]);

  if (!sessionId) return null;
  const isLoading = session?.status === "pending" || session?.status === "running";

  // ── IT Mode filter ──────────────────────────────────────────────────────────
  const IT_TITLE_KEYWORDS = [
    "software", "engineer", "developer", "dev ", " dev", "devops", "sre",
    "frontend", "front-end", "front end", "backend", "back-end", "back end",
    "fullstack", "full-stack", "full stack",
    "cloud", "platform", "infrastructure", "infra",
    "machine learning", " ml ", "artificial intelligence", " ai ",
    "data engineer", "data scientist", "data analyst", "analytics engineer",
    "mobile", "ios", "android",
    "react", "node", "python", "java", "golang", "typescript", "javascript",
    "qa engineer", "test engineer", "automation engineer",
    "security engineer", "cybersecurity", "database administrator", "dba",
    "solutions architect", "systems architect", "tech lead", "technical lead",
    "product engineer", "site reliability",
  ];
  const IT_SKILL_KEYWORDS = [
    "python", "javascript", "typescript", "java", "c#", "c++", "golang", "rust",
    "ruby", "php", "swift", "kotlin", "scala", "r ",
    "react", "vue", "angular", "next.js", "node.js", "django", "flask", "spring",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "git", "linux", "sql",
  ];

  const isITJob = (job: Job) => {
    const title = (job.title ?? "").toLowerCase();
    if (IT_TITLE_KEYWORDS.some(kw => title.includes(kw))) return true;
    const skillsStr = job.skills.join(" ").toLowerCase();
    if (IT_SKILL_KEYWORDS.some(kw => skillsStr.includes(kw))) return true;
    return false;
  };

  const displayedJobs = itMode ? jobs.filter(isITJob) : jobs;

  const chipActive = {
    background: "rgba(214,186,255,0.12)",
    color: "#d6baff",
    border: "1px solid rgba(214,186,255,0.3)",
    boxShadow: "0 0 8px rgba(214,186,255,0.2)",
  };

  return (
    <main className="pt-20 pb-16 px-6 max-w-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-8 flex-wrap gap-4 max-w-7xl mx-auto">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate("/")} className="text-text-muted hover:text-text-primary transition-colors p-2 rounded-lg hover:bg-bg-elevated">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="font-manrope font-light text-2xl text-text-primary tracking-tight">
              {session?.keywords ? `"${session.keywords}"` : "Job Results"}
            </h1>
            <p className="text-text-muted text-xs mt-0.5 font-inter">
              {session?.location} ·{" "}
              {isLoading
                ? <span className="text-warning">Searching…</span>
                : <span className="text-success">{displayedJobs.length}{itMode && jobs.length !== displayedJobs.length ? ` / ${jobs.length}` : ""} results</span>}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {matching && (
            <span className="badge animate-pulse" style={{ color: "#7cd0ff", background: "rgba(124,208,255,0.06)", border: "1px solid rgba(124,208,255,0.2)" }}>
              <Spinner size="sm" />Matching…
            </span>
          )}
          {!matching && matched && !gradingActive && (
            <span className="badge" style={{ color: "#4ade80", background: "rgba(74,222,128,0.08)", border: "1px solid rgba(74,222,128,0.2)" }}>
              ✓ Matched &amp; Graded
            </span>
          )}
          {!matching && matched && gradingActive && (
            <span className="badge animate-pulse" style={{ color: "#d6baff", background: "rgba(214,186,255,0.06)", border: "1px solid rgba(214,186,255,0.2)" }}>
              ✦ AI grading…
            </span>
          )}
          {!matching && !matched && resumeFilename && session?.status === "done" && (
            <button className="btn-primary text-xs px-5 py-2" onClick={handleMatch}>
              Match with Resume
            </button>
          )}
          {!resumeFilename && session?.status === "done" && (
            <span className="text-[10px] text-text-dim">Upload a resume on the home page to get AI grades</span>
          )}
        </div>
      </div>

      {/* IT Mode banner (visible on mobile where sidebar is hidden) */}
      {itMode && (
        <div className="max-w-7xl mx-auto mb-4 lg:hidden">
          <div
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs"
            style={{ background: "rgba(124,208,255,0.06)", border: "1px solid rgba(124,208,255,0.2)", color: "#7cd0ff" }}
          >
            <Cpu className="w-3.5 h-3.5 shrink-0" />
            <span>IT Mode active — showing tech roles only</span>
            <button onClick={() => setItMode(false)} className="ml-auto opacity-60 hover:opacity-100 transition-opacity text-[10px] uppercase tracking-widest">
              Clear
            </button>
          </div>
        </div>
      )}

      {/* Loading */}
      {isLoading && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          className="flex flex-col items-center justify-center py-24 gap-6">
          <div className="relative">
            <div className="w-16 h-16 rounded-full" style={{ border: "2px solid rgba(68,71,72,0.4)" }} />
            <div className="absolute inset-0 w-16 h-16 rounded-full animate-spin"
              style={{ border: "2px solid transparent", borderTopColor: "#7cd0ff" }} />
          </div>
          <div className="text-center">
            <p className="font-manrope font-light text-text-primary text-lg">Scraping job boards…</p>
            <p className="text-text-muted text-sm mt-1 font-inter">
              Searching job boards + Canadian portals concurrently
            </p>
          </div>
          <div className="flex gap-2 flex-wrap justify-center max-w-lg">
            {["LinkedIn", "Indeed", "Glassdoor", "ZipRecruiter", "Google", "Eluta", "JobBank", "Greenhouse", "Lever", "Ashby"].map(b => (
              <span key={b} className="badge animate-pulse text-[10px]">{b}</span>
            ))}
          </div>
        </motion.div>
      )}

      {/* Error */}
      {session?.status === "failed" && (
        <div className="glass-card p-8 text-center max-w-md mx-auto">
          <AlertTriangle className="w-10 h-10 text-danger mx-auto mb-3" />
          <p className="font-manrope font-medium text-text-primary">Search failed</p>
          <p className="text-text-muted text-sm mt-1">{session.error}</p>
          <button className="btn-primary mt-6" onClick={() => navigate("/")}>Try again</button>
        </div>
      )}

      {/* Results — show during running (partial) and done */}
      {(session?.status === "done" || (session?.status === "running" && jobs.length > 0)) && (
        <div className="flex gap-6 max-w-7xl mx-auto">
          {/* Filter sidebar */}
          <aside className="w-56 shrink-0 hidden lg:block">
            <div className="sticky top-24 space-y-6 flex flex-col items-center">
              <p className="text-[10px] font-manrope font-semibold text-text-muted uppercase tracking-[0.15em] flex items-center gap-2 w-full justify-center">
                <Filter className="w-3 h-3" /> Filters
              </p>

              {/* Sort */}
              <div className="w-full">
                <p className="text-[10px] text-text-muted uppercase tracking-widest mb-2 font-manrope text-center">Sort by</p>
                <div className="flex gap-1">
                  {(["posted_at", "match_score"] as const).map(v => (
                    <button key={v} onClick={() => setSortBy(v)}
                      className="flex-1 py-1.5 text-[10px] font-manrope uppercase tracking-wide rounded-md transition-all"
                      style={sortBy === v
                        ? { background: "rgba(214,186,255,0.12)", color: "#d6baff", border: "1px solid rgba(214,186,255,0.3)", boxShadow: "0 0 8px rgba(214,186,255,0.2)" }
                        : { background: "transparent", color: "#8a8680", border: "1px solid rgba(68,71,72,0.3)" }}>
                      {v === "posted_at" ? "Date" : "Score"}
                    </button>
                  ))}
                </div>
              </div>

              {/* Remote */}
              <button
                onClick={() => setRemoteFilter(v => !v)}
                className="flex items-center gap-2 text-xs w-full px-3 py-2 rounded-lg transition-all"
                style={remoteFilter ? { background: "rgba(74,222,128,0.08)", border: "1px solid rgba(74,222,128,0.2)", color: "#4ade80" }
                  : { background: "rgba(255,255,255,0.03)", border: "1px solid rgba(68,71,72,0.4)", color: "#8e9192" }}
              >
                <Wifi className="w-3.5 h-3.5" />
                Remote only
              </button>

              {/* IT Mode */}
              <button
                onClick={() => setItMode(v => !v)}
                className="flex items-center gap-2 text-xs w-full px-3 py-2 rounded-lg transition-all relative overflow-hidden"
                style={itMode
                  ? { background: "rgba(124,208,255,0.06)", border: "1px solid rgba(124,208,255,0.25)", color: "#7cd0ff" }
                  : { background: "rgba(255,255,255,0.03)", border: "1px solid rgba(68,71,72,0.4)", color: "#8e9192" }}
              >
                {itMode && (
                  <span
                    className="absolute inset-0 pointer-events-none"
                    style={{
                      background: "linear-gradient(90deg, rgba(124,208,255,0.04) 0%, rgba(214,186,255,0.04) 50%, rgba(255,200,124,0.04) 100%)",
                    }}
                  />
                )}
                <Cpu className="w-3.5 h-3.5 shrink-0" />
                <span className="flex-1 text-left">IT / Tech only</span>
                {itMode && (
                  <span
                    className="text-[9px] font-manrope uppercase tracking-widest px-1.5 py-0.5 rounded"
                    style={{ background: "rgba(124,208,255,0.12)", color: "#7cd0ff" }}
                  >
                    ON
                  </span>
                )}
              </button>

              {/* Min Score */}
              {matched && (
                <div className="w-full">
                  <p className="text-[10px] text-text-muted uppercase tracking-widest mb-2 font-manrope text-center">Min match score</p>
                  <select value={minScore ?? ""} onChange={e => setMinScore(e.target.value ? Number(e.target.value) : null)}
                    className="input-base text-xs py-2">
                    <option value="">All</option>
                    <option value="30">30+</option>
                    <option value="50">50+</option>
                    <option value="70">70+</option>
                    <option value="85">85+</option>
                  </select>
                </div>
              )}

              {/* Seniority */}
              <div className="w-full">
                <p className="text-[10px] text-text-muted uppercase tracking-widest mb-2 font-manrope text-center">Seniority</p>
                <div className="flex flex-wrap gap-1.5 justify-center">
                  {SENIORITY_OPTS.map(s => (
                    <button key={s} onClick={() => toggleSeniority(s)}
                      className="badge cursor-pointer capitalize transition-all"
                      style={seniorityFilter.includes(s) ? chipActive : {}}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              {/* Boards — grouped */}
              {BOARD_GROUPS.map(group => (
                <div key={group.label} className="w-full">
                  <p className="text-[10px] text-text-muted uppercase tracking-widest mb-2 font-manrope text-center">{group.label}</p>
                  <div className="flex flex-wrap gap-1.5 justify-center">
                    {group.keys.map(b => (
                      <button key={b} onClick={() => toggleBoard(b)}
                        className="badge cursor-pointer transition-all"
                        style={boardFilter.includes(b) ? chipActive : {}}>
                        {BOARD_LABELS[b]}
                      </button>
                    ))}
                  </div>
                </div>
              ))}

              {/* Grading indicator */}
              {gradingActive && (
                <div className="w-full px-3 py-2 rounded-lg text-[10px] text-center"
                  style={{ background: "rgba(214,186,255,0.06)", border: "1px solid rgba(214,186,255,0.15)", color: "#d6baff" }}>
                  <span className="animate-pulse">AI grading in progress…</span>
                </div>
              )}
            </div>
          </aside>

          {/* Job list */}
          <div className="flex-1 min-w-0 space-y-3">
            {displayedJobs.length === 0 ? (
              <div className="glass-card p-10 text-center">
                <p className="text-text-secondary font-light">
                  {itMode && jobs.length > 0
                    ? "No IT/tech roles found in current results."
                    : "No jobs match the current filters."}
                </p>
              </div>
            ) : (
              displayedJobs.map(job => (
                <motion.div key={job.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }}>
                  <JobCard job={job} resumeSkills={parsedResume?.tech_stack ?? []} />
                </motion.div>
              ))
            )}
          </div>
        </div>
      )}
    </main>
  );
}
