import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MapPin, Building2, DollarSign, Clock, ExternalLink, ChevronDown, ChevronUp, Wifi, FileText, Mail, BarChart2, Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import type { Job, FitAnalysis } from "@/types";
import ScoreRing from "@/components/ui/ScoreRing";
import SkillTag from "@/components/ui/SkillTag";
import BoardBadge from "@/components/ui/BoardBadge";
import { useAppStore } from "@/store/appStore";

interface JobCardProps {
  job: Job;
  resumeSkills?: string[];
}

function formatSalary(job: Job): string | null {
  if (!job.salary_min && !job.salary_max) return null;
  const fmt = (n: number) => n >= 1000 ? `${(n / 1000).toFixed(0)}k` : `${n}`;
  const currency = job.salary_currency || "CAD";
  const interval = job.salary_interval ? `/${job.salary_interval.replace("ly", "")}` : "";
  if (job.salary_min && job.salary_max) return `${currency} $${fmt(job.salary_min)}–$${fmt(job.salary_max)}${interval}`;
  return `${currency} $${fmt(job.salary_min || job.salary_max || 0)}${interval}`;
}

function formatDate(dateStr: string | null): { relative: string; absolute: string } | null {
  if (!dateStr) return null;
  const date = new Date(dateStr);
  const diff = Date.now() - date.getTime();
  const days = Math.floor(diff / 86400000);
  const relative =
    days === 0 ? "Today" :
    days === 1 ? "Yesterday" :
    days < 7  ? `${days}d ago` :
    days < 30 ? `${Math.floor(days / 7)}w ago` :
                `${Math.floor(days / 30)}mo ago`;
  const absolute = date.toLocaleDateString("en-CA", { month: "short", day: "numeric", year: "numeric" });
  return { relative, absolute };
}

/** Strip common escape artifacts from jobspy descriptions before rendering */
function cleanDescription(text: string): string {
  return text
    .replace(/\\n/g, "\n")
    .replace(/\\-/g, "-")
    .replace(/\\"/g, '"')
    .replace(/\\\*/g, "*")
    .trim();
}

// ── Fit Analysis Panel ────────────────────────────────────────────────────────

function FitAnalysisPanel({ fit }: { fit: FitAnalysis }) {
  const gc = gradeColor(fit.grade);
  return (
    <div className="mt-4 rounded-xl p-4" style={{ background: "rgba(30,32,36,0.7)", border: `1px solid ${gc}22` }}>
      <div className="flex items-center gap-3 mb-3">
        <div className="flex items-center justify-center w-10 h-10 rounded-full shrink-0"
          style={{ background: `${gc}12`, border: `2px solid ${gc}44` }}>
          <span className="font-manrope font-bold text-base" style={{ color: gc }}>{fit.grade}</span>
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-[10px] font-manrope uppercase tracking-[0.15em] text-text-muted mb-0.5">AI Fit Grade</p>
          <p className="text-xs text-text-secondary leading-relaxed">{fit.summary}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-3">
        <div>
          <p className="text-[10px] text-text-dim uppercase tracking-widest mb-1.5" style={{ color: "#4ade80" }}>Strengths</p>
          <div className="flex flex-wrap gap-1">
            {fit.strengths.map(s => (
              <span key={s} className="text-[10px] px-1.5 py-0.5 rounded"
                style={{ background: "rgba(74,222,128,0.08)", color: "#4ade80", border: "1px solid rgba(74,222,128,0.2)" }}>
                {s}
              </span>
            ))}
          </div>
        </div>
        <div>
          <p className="text-[10px] text-text-dim uppercase tracking-widest mb-1.5" style={{ color: "#ffc87c" }}>Gaps</p>
          <div className="flex flex-wrap gap-1">
            {fit.gaps.map(g => (
              <span key={g} className="text-[10px] px-1.5 py-0.5 rounded"
                style={{ background: "rgba(255,200,124,0.08)", color: "#ffc87c", border: "1px solid rgba(255,200,124,0.15)" }}>
                {g}
              </span>
            ))}
          </div>
        </div>
      </div>

      {fit.tip && (
        <div className="pt-3 flex gap-2" style={{ borderTop: "1px solid rgba(68,71,72,0.25)" }}>
          <Sparkles className="w-3 h-3 shrink-0 mt-0.5" style={{ color: gc }} />
          <p className="text-[11px] text-text-secondary leading-relaxed">{fit.tip}</p>
        </div>
      )}

      <div className="flex gap-2 mt-3 pt-2" style={{ borderTop: "1px solid rgba(68,71,72,0.15)" }}>
        {fit.seniority !== "any" && (
          <span className="badge text-[9px] capitalize">Job: {fit.seniority}</span>
        )}
        {fit.user_level && (
          <span className="badge text-[9px] capitalize">You: {fit.user_level}</span>
        )}
      </div>
    </div>
  );
}

// ── Score breakdown helpers ───────────────────────────────────────────────────
const SENIORITY_ORDER = ["internship", "junior", "mid", "senior", "lead", "executive"];

function seniorityScore(resumeSeniority: string | null, jobSeniority: string | null): number {
  if (!resumeSeniority || !jobSeniority) return 50;
  const ri = SENIORITY_ORDER.indexOf(resumeSeniority);
  const ji = SENIORITY_ORDER.indexOf(jobSeniority);
  if (ri === -1 || ji === -1) return 50;
  return Math.round(Math.max(10, 100 - Math.abs(ri - ji) * 30));
}

function skillOverlapScore(resumeSkills: string[], jobSkills: string[]): number {
  if (!jobSkills.length) return 50;
  if (!resumeSkills.length) return 0;
  const rs = new Set(resumeSkills.map(s => s.toLowerCase()));
  const js = jobSkills.map(s => s.toLowerCase());
  const matched = js.filter(s => rs.has(s));
  return Math.round((matched.length / js.length) * 100);
}

function gradeColor(grade: string): string {
  const g = grade.toUpperCase();
  if (g.startsWith("A")) return "#4ade80";
  if (g.startsWith("B")) return "#7cd0ff";
  if (g.startsWith("C")) return "#fbbf24";
  if (g.startsWith("D") || g.startsWith("F")) return "#f87171";
  return "#8a8680";
}

// ─────────────────────────────────────────────────────────────────────────────

export default function JobCard({ job, resumeSkills = [] }: JobCardProps) {
  const [expanded,     setExpanded]     = useState(false);
  const [hovered,      setHovered]      = useState(false);
  const [showBreakdown, setShowBreakdown] = useState(false);
  const [showFit,      setShowFit]      = useState(false);
  const navigate = useNavigate();
  const { setSelectedJobId, setSelectedJob, resumeFilename, parsedResume } = useAppStore();
  const salary   = formatSalary(job);
  const dateInfo = formatDate(job.posted_at);

  // Pre-compute breakdown (only meaningful after matching)
  const allResumeSkills = parsedResume?.skills ?? resumeSkills;
  const matchedSkills   = job.skills.filter(s => allResumeSkills.some(r => r.toLowerCase() === s.toLowerCase()));
  const missingSkills   = job.skills.filter(s => !allResumeSkills.some(r => r.toLowerCase() === s.toLowerCase()));
  const skillPct        = skillOverlapScore(allResumeSkills, job.skills);
  const seniorityPct    = seniorityScore(parsedResume?.seniority_level ?? null, job.seniority_level ?? null);
  // Semantic & keyword weights can't be computed client-side; show estimated semantic from overall score
  const estimatedSemantic = job.match_score !== null
    ? Math.min(100, Math.round((job.match_score - 0.35 * skillPct - 0.10 * seniorityPct) / 0.55))
    : null;

  return (
    <motion.div
      layout
      className="glass-card p-5 transition-all duration-200"
      style={hovered ? { boxShadow: "inset 2px 0 0 rgba(198,198,199,0.2), 0 0 20px rgba(198,198,199,0.04)" } : {}}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Header */}
      <div className="flex items-start gap-4">
        <ScoreRing score={job.match_score} size={52} />

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 flex-wrap">
            <div>
              <h3 className="font-manrope font-medium text-[#edeae4] text-base leading-snug">
                {job.title}
              </h3>
              {job.company && (
                <div className="flex items-center gap-1.5 mt-0.5">
                  <Building2 className="w-3 h-3 text-text-muted" />
                  <span className="text-sm text-text-secondary font-light">{job.company}</span>
                </div>
              )}
            </div>
            <div className="flex items-center gap-1.5 flex-wrap justify-end">
              <BoardBadge board={job.board} />
              {job.archetype && job.archetype !== "Other" && (
                <span className="badge text-[9px]" style={{ color: "#a78bfa", background: "rgba(167,139,250,0.06)", border: "1px solid rgba(167,139,250,0.15)" }}>
                  {job.archetype}
                </span>
              )}
            </div>
          </div>

          {/* Meta row */}
          <div className="flex flex-wrap items-center gap-3 mt-2">
            {job.location && (
              <div className="flex items-center gap-1 text-xs text-text-muted">
                <MapPin className="w-3 h-3" /><span>{job.location}</span>
              </div>
            )}
            {job.is_remote && (
              <div className="flex items-center gap-1 text-xs text-success">
                <Wifi className="w-3 h-3" /><span>Remote</span>
              </div>
            )}
            {salary && (
              <div className="flex items-center gap-1 text-xs text-text-muted">
                <DollarSign className="w-3 h-3" /><span>{salary}</span>
              </div>
            )}
            {dateInfo && (
              <div className="flex items-center gap-1 text-xs text-text-muted" title={dateInfo.absolute}>
                <Clock className="w-3 h-3" />
                <span>{dateInfo.relative}</span>
                <span className="text-text-dim">·</span>
                <span className="text-text-dim">{dateInfo.absolute}</span>
              </div>
            )}
            {job.seniority_level && (
              <span className="badge capitalize">{job.seniority_level}</span>
            )}
          </div>

          {/* Skills (collapsed: 8, expanded: all) */}
          {job.skills.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-2.5">
              {(expanded ? job.skills : job.skills.slice(0, 8)).map(s => (
                <SkillTag key={s} label={s}
                  highlighted={resumeSkills.some(r => r.toLowerCase() === s.toLowerCase())} />
              ))}
              {!expanded && job.skills.length > 8 && (
                <span className="badge">+{job.skills.length - 8} more</span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Score Breakdown */}
      <AnimatePresence>
        {showBreakdown && job.match_score !== null && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="mt-4 rounded-xl p-4" style={{ background: "rgba(30,32,36,0.7)", border: "1px solid rgba(124,208,255,0.1)" }}>
              <p className="text-[10px] font-manrope uppercase tracking-[0.15em] text-text-muted mb-3">Score Breakdown</p>

              {/* Component bars */}
              {[
                { label: "Semantic Match", weight: "45%", pct: Math.max(0, Math.min(100, estimatedSemantic ?? 0)), color: "#7cd0ff",
                  note: "How closely your resume's overall profile aligns with the job description (NLP embedding similarity)." },
                { label: "Skill Overlap",  weight: "35%", pct: skillPct,     color: "#d6baff",
                  note: `${matchedSkills.length} of ${job.skills.length} required skills matched.` },
                { label: "Seniority Fit",  weight: "10%", pct: seniorityPct, color: "#ffc87c",
                  note: parsedResume?.seniority_level && job.seniority_level
                    ? `Your level (${parsedResume.seniority_level}) vs job (${job.seniority_level}).`
                    : "Seniority level not specified — neutral score applied." },
                { label: "Keyword Density", weight: "10%", pct: Math.min(100, Math.round(job.match_score * 0.8)),  color: "#c6c6c7",
                  note: "How many key terms from the job description appear in your resume text." },
              ].map(({ label, weight, pct, color, note }) => (
                <div key={label} className="mb-3 last:mb-0">
                  <div className="flex justify-between items-baseline mb-1">
                    <span className="text-[11px] text-text-secondary font-inter">{label}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-text-dim">{weight} weight</span>
                      <span className="text-xs font-manrope" style={{ color }}>{pct}%</span>
                    </div>
                  </div>
                  <div className="h-1 rounded-full w-full" style={{ background: "rgba(255,255,255,0.05)" }}>
                    <motion.div
                      className="h-1 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${pct}%` }}
                      transition={{ duration: 0.6, ease: "easeOut" }}
                      style={{ background: color, boxShadow: `0 0 6px ${color}40` }}
                    />
                  </div>
                  <p className="text-[10px] text-text-dim mt-0.5 leading-relaxed">{note}</p>
                </div>
              ))}

              {/* Matched / Missing skills */}
              {job.skills.length > 0 && (
                <div className="mt-4 pt-3 grid grid-cols-2 gap-3" style={{ borderTop: "1px solid rgba(68,71,72,0.3)" }}>
                  <div>
                    <p className="text-[10px] text-text-dim uppercase tracking-widest mb-1.5">
                      Matched <span style={{ color: "#d6baff" }}>({matchedSkills.length})</span>
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {matchedSkills.slice(0, 10).map(s => (
                        <span key={s} className="text-[10px] px-1.5 py-0.5 rounded"
                          style={{ background: "rgba(214,186,255,0.1)", color: "#d6baff", border: "1px solid rgba(214,186,255,0.2)" }}>
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-[10px] text-text-dim uppercase tracking-widest mb-1.5">
                      Missing <span style={{ color: "#ffc87c" }}>({missingSkills.length})</span>
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {missingSkills.slice(0, 10).map(s => (
                        <span key={s} className="text-[10px] px-1.5 py-0.5 rounded"
                          style={{ background: "rgba(255,200,124,0.08)", color: "#ffc87c", border: "1px solid rgba(255,200,124,0.15)" }}>
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              <p className="text-[10px] text-text-dim mt-3 pt-3 leading-relaxed" style={{ borderTop: "1px solid rgba(68,71,72,0.2)" }}>
                Final score = 45% semantic + 35% skill overlap + 10% seniority + 10% keyword density.
                Semantic and keyword components require the full resume text processed server-side.
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Fit Analysis Panel */}
      <AnimatePresence>
        {showFit && job.fit_analysis && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <FitAnalysisPanel fit={job.fit_analysis} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Expanded description */}
      <AnimatePresence>
        {expanded && job.description && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="mt-5 pt-4" style={{ borderTop: "1px solid rgba(68,71,72,0.3)" }}>
              {/* Scrollable description with max height */}
              <div
                className="overflow-y-auto no-scrollbar pr-1"
                style={{ maxHeight: "420px" }}
              >
                <div className="prose-sm text-text-secondary font-light leading-relaxed"
                  style={{
                    fontSize: "0.8125rem",
                    lineHeight: "1.75",
                  }}>
                  <ReactMarkdown
                    components={{
                      h1: ({ children }) => <p className="font-manrope font-semibold text-[#edeae4] text-sm mt-4 mb-1">{children}</p>,
                      h2: ({ children }) => <p className="font-manrope font-semibold text-[#edeae4] text-sm mt-4 mb-1">{children}</p>,
                      h3: ({ children }) => <p className="font-manrope font-medium text-text-primary text-xs mt-3 mb-0.5 uppercase tracking-wide">{children}</p>,
                      strong: ({ children }) => <strong className="text-text-primary font-medium">{children}</strong>,
                      ul: ({ children }) => <ul className="space-y-0.5 my-1.5 ml-3 list-none">{children}</ul>,
                      ol: ({ children }) => <ol className="space-y-0.5 my-1.5 ml-3 list-decimal list-inside">{children}</ol>,
                      li: ({ children }) => (
                        <li className="flex gap-2 text-text-secondary">
                          <span className="text-text-dim mt-1 shrink-0">·</span>
                          <span>{children}</span>
                        </li>
                      ),
                      p: ({ children }) => <p className="my-1.5 text-text-secondary">{children}</p>,
                      a: ({ href, children }) => (
                        <a href={href} target="_blank" rel="noopener noreferrer"
                          className="text-text-secondary underline underline-offset-2 hover:text-text-primary transition-colors">
                          {children}
                        </a>
                      ),
                      hr: () => <hr style={{ borderColor: "rgba(68,71,72,0.3)", margin: "0.75rem 0" }} />,
                    }}
                  >
                    {cleanDescription(job.description)}
                  </ReactMarkdown>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Footer */}
      <div className="flex items-center justify-between mt-4 pt-4" style={{ borderTop: "1px solid rgba(68,71,72,0.3)" }}>
        <div className="flex items-center gap-1.5 flex-wrap">
          {job.job_url && (
            <a href={job.job_url} target="_blank" rel="noopener noreferrer" className="btn-ghost text-xs px-3 py-1.5">
              <ExternalLink className="w-3 h-3" />Apply
            </a>
          )}
          {resumeFilename && (
            <>
              <button onClick={() => { setSelectedJobId(job.id); setSelectedJob(job); navigate("/optimize"); }}
                className="btn-ghost text-xs px-3 py-1.5">
                <FileText className="w-3 h-3" />Optimize Resume
              </button>
              <button onClick={() => { setSelectedJobId(job.id); setSelectedJob(job); navigate("/cover-letter"); }}
                className="btn-ghost text-xs px-3 py-1.5">
                <Mail className="w-3 h-3" />Cover Letter
              </button>
            </>
          )}
          {job.match_score !== null && (
            <button
              onClick={() => setShowBreakdown(v => !v)}
              className="btn-ghost text-xs px-3 py-1.5 transition-all"
              style={showBreakdown ? { color: "#7cd0ff", borderColor: "rgba(124,208,255,0.3)" } : {}}
            >
              <BarChart2 className="w-3 h-3" />
              {showBreakdown ? "Hide Score" : "Score Breakdown"}
            </button>
          )}
          {job.fit_analysis ? (
            <button
              onClick={() => setShowFit(v => !v)}
              className="btn-ghost text-xs px-3 py-1.5 transition-all"
              style={showFit ? { color: gradeColor(job.fit_analysis.grade), borderColor: `${gradeColor(job.fit_analysis.grade)}40` } : {}}
            >
              <Sparkles className="w-3 h-3" />
              AI Grade: <span style={{ color: gradeColor(job.fit_analysis.grade), fontWeight: 600 }}>{job.fit_analysis.grade}</span>
            </button>
          ) : job.match_score !== null && (
            <span className="text-[10px] text-text-dim animate-pulse px-2">AI grading…</span>
          )}
        </div>

        {job.description && (
          <button onClick={() => setExpanded(v => !v)}
            className="text-text-muted hover:text-text-secondary transition-colors flex items-center gap-1 text-xs shrink-0 ml-2">
            {expanded
              ? <>Collapse <ChevronUp className="w-3 h-3" /></>
              : <>Details <ChevronDown className="w-3 h-3" /></>}
          </button>
        )}
      </div>
    </motion.div>
  );
}
