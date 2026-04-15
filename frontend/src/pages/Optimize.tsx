import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileText, Sparkles, Download, ChevronRight, Check,
  Link2, Loader2, ChevronDown, ChevronUp, AlertTriangle,
  RotateCcw, Copy, Code2, Eye, ArrowRight, Info, BriefcaseBusiness,
} from "lucide-react";
import toast from "react-hot-toast";
import { optimizeResume, fetchJobUrl } from "@/lib/api";
import { useAppStore } from "@/store/appStore";
import ResumeDropzone from "@/components/ResumeDropzone";
import Spinner from "@/components/ui/Spinner";
import ProfileInputForm from "@/components/ProfileInputForm";
import TransparencyReport from "@/components/TransparencyReport";
import type { ATSOptimizeResponse, ChangeItem } from "@/types";

// ── Design tokens ─────────────────────────────────────────────────────────────

const CHANGE_STYLES: Record<string, { color: string; bg: string; border: string; label: string }> = {
  verb:        { color: "#4ade80", bg: "rgba(74,222,128,0.08)",  border: "rgba(74,222,128,0.2)",  label: "Verb" },
  keyword:     { color: "#7cd0ff", bg: "rgba(124,208,255,0.08)", border: "rgba(124,208,255,0.2)", label: "Keyword" },
  title:       { color: "#d6baff", bg: "rgba(214,186,255,0.08)", border: "rgba(214,186,255,0.2)", label: "Title" },
  skill:       { color: "#a5f3fc", bg: "rgba(165,243,252,0.08)", border: "rgba(165,243,252,0.2)", label: "Skill" },
  metric:      { color: "#ffc87c", bg: "rgba(255,200,124,0.08)", border: "rgba(255,200,124,0.2)", label: "Metric" },
  reframe:     { color: "#c4b5fd", bg: "rgba(196,181,253,0.08)", border: "rgba(196,181,253,0.2)", label: "Reframe" },
  removed:     { color: "#f87171", bg: "rgba(248,113,113,0.06)", border: "rgba(248,113,113,0.15)", label: "Removed" },
  restructure: { color: "#c6c6c7", bg: "rgba(198,198,199,0.06)", border: "rgba(198,198,199,0.15)", label: "Structure" },
};

// ── Sub-components ─────────────────────────────────────────────────────────────

function ScoreGauge({ label, value, prev }: { label: string; value: number | null; prev?: number | null }) {
  if (value === null) return null;
  const color = value >= 70 ? "#4ade80" : value >= 45 ? "#ffc87c" : "#f87171";
  const delta = prev != null ? value - prev : null;
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs font-manrope uppercase tracking-widest text-text-muted">{label}</span>
        <div className="flex items-center gap-2">
          {delta !== null && delta !== 0 && (
            <span className="text-xs" style={{ color: delta > 0 ? "#4ade80" : "#f87171" }}>
              {delta > 0 ? "+" : ""}{delta}
            </span>
          )}
          <span className="text-base font-manrope font-medium" style={{ color }}>{value}</span>
        </div>
      </div>
      <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(68,71,72,0.35)" }}>
        <motion.div className="h-full rounded-full" style={{ backgroundColor: color }}
          initial={{ width: 0 }} animate={{ width: `${value}%` }} transition={{ duration: 0.9, ease: "easeOut" }} />
      </div>
    </div>
  );
}

function KeywordPill({ label, variant }: { label: string; variant: "match" | "miss" }) {
  return (
    <span className="text-xs px-1.5 py-0.5 rounded font-inter"
      style={variant === "match"
        ? { background: "rgba(124,208,255,0.08)", color: "#7cd0ff", border: "1px solid rgba(124,208,255,0.18)" }
        : { background: "rgba(255,200,124,0.07)", color: "#ffc87c", border: "1px solid rgba(255,200,124,0.15)" }}>
      {label}
    </span>
  );
}

function ChangeBadge({ category }: { category: string }) {
  const s = CHANGE_STYLES[category] ?? CHANGE_STYLES.reframe;
  return (
    <span className="shrink-0 text-[10px] font-manrope font-semibold uppercase tracking-widest px-1.5 py-0.5 rounded"
      style={{ color: s.color, background: s.bg, border: `1px solid ${s.border}` }}>
      {s.label}
    </span>
  );
}

function WhatChanged({ items, plain, open, onToggle }: {
  items: ChangeItem[]; plain: string[]; open: boolean; onToggle: () => void;
}) {
  // Group by category
  const grouped = items.reduce<Record<string, ChangeItem[]>>((acc, item) => {
    (acc[item.category] ||= []).push(item);
    return acc;
  }, {});

  const displayItems = items.length > 0 ? items : plain.map(t => ({ category: "reframe" as const, text: t }));
  const count = displayItems.length;

  return (
    <div className="rounded-xl overflow-hidden" style={{ background: "rgba(22,24,28,0.6)", border: "1px solid rgba(68,71,72,0.4)" }}>
      <button onClick={onToggle}
        className="w-full flex items-center justify-between px-5 py-3.5 text-left group transition-colors hover:bg-white/[0.02]">
        <div className="flex items-center gap-2.5">
          <ArrowRight className="w-3.5 h-3.5 text-text-muted" />
          <span className="text-sm font-manrope font-semibold text-text-secondary uppercase tracking-[0.15em]">
            What Changed
          </span>
          {count > 0 && (
            <span className="text-[10px] px-1.5 py-0.5 rounded font-manrope"
              style={{ background: "rgba(198,198,199,0.1)", color: "#c6c6c7", border: "1px solid rgba(198,198,199,0.15)" }}>
              {count}
            </span>
          )}
        </div>
        {open ? <ChevronUp className="w-3.5 h-3.5 text-text-muted" /> : <ChevronDown className="w-3.5 h-3.5 text-text-muted" />}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
            <div className="px-4 pb-4" style={{ borderTop: "1px solid rgba(68,71,72,0.3)" }}>
              {/* Category legend */}
              <div className="flex flex-wrap gap-1.5 py-3 mb-1">
                {Object.entries(CHANGE_STYLES).filter(([cat]) => grouped[cat]?.length).map(([cat, s]) => (
                  <span key={cat} className="text-[10px] px-1.5 py-0.5 rounded font-manrope uppercase tracking-widest"
                    style={{ color: s.color, background: s.bg, border: `1px solid ${s.border}` }}>
                    {s.label} ({grouped[cat].length})
                  </span>
                ))}
              </div>

              {/* Change items */}
              <div className="space-y-2 max-h-72 overflow-y-auto no-scrollbar pr-1">
                {displayItems.map((item, i) => (
                  <motion.div key={i}
                    initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.03, duration: 0.2 }}
                    className="flex items-start gap-2.5 p-2.5 rounded-lg"
                    style={{ background: CHANGE_STYLES[item.category]?.bg ?? "rgba(198,198,199,0.04)" }}>
                    <ChangeBadge category={item.category} />
                    <span className="text-sm text-text-secondary font-light leading-relaxed">{item.text}</span>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function ATSBreakdown({ result, open, onToggle, onApplyImprovements, applyLoading }: {
  result: ATSOptimizeResponse;
  open: boolean;
  onToggle: () => void;
  onApplyImprovements: () => void;
  applyLoading: boolean;
}) {
  return (
    <div className="rounded-xl overflow-hidden" style={{ background: "rgba(22,24,28,0.6)", border: "1px solid rgba(68,71,72,0.4)" }}>
      <button onClick={onToggle}
        className="w-full flex items-center justify-between px-5 py-3.5 text-left transition-colors hover:bg-white/[0.02]">
        <div className="flex items-center gap-2.5">
          <Sparkles className="w-3.5 h-3.5 text-text-muted" />
          <span className="text-sm font-manrope font-semibold text-text-secondary uppercase tracking-[0.15em]">
            ATS Score Breakdown
          </span>
          {result.ats_score_after != null && (
            <span className="text-xs font-manrope font-medium px-1.5 py-0.5 rounded"
              style={{
                color: result.ats_score_after >= 70 ? "#4ade80" : result.ats_score_after >= 45 ? "#ffc87c" : "#f87171",
                background: "rgba(255,255,255,0.04)", border: "1px solid rgba(68,71,72,0.4)"
              }}>
              {result.ats_score_after}
            </span>
          )}
        </div>
        {open ? <ChevronUp className="w-3.5 h-3.5 text-text-muted" /> : <ChevronDown className="w-3.5 h-3.5 text-text-muted" />}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
            <div className="px-5 pb-5 space-y-4" style={{ borderTop: "1px solid rgba(68,71,72,0.3)" }}>
              <div className="pt-4 space-y-3">
                <ScoreGauge label="Before" value={result.ats_score_before} />
                <ScoreGauge label="After"  value={result.ats_score_after} prev={result.ats_score_before} />
                <p className="text-xs text-text-dim leading-relaxed">
                  Estimated via keyword overlap with job description. Industry ceiling ≈ 85.
                </p>
              </div>

              {result.matched_keywords.length > 0 && (
                <div>
                  <p className="text-xs text-text-dim uppercase tracking-widest mb-2">
                    Matched <span style={{ color: "#7cd0ff" }}>({result.matched_keywords.length})</span>
                  </p>
                  <div className="flex flex-wrap gap-1">{result.matched_keywords.map(k => <KeywordPill key={k} label={k} variant="match" />)}</div>
                </div>
              )}
              {result.missing_keywords.length > 0 && (
                <div>
                  <p className="text-xs text-text-dim uppercase tracking-widest mb-2">
                    Missing <span style={{ color: "#ffc87c" }}>({result.missing_keywords.length})</span>
                  </p>
                  <div className="flex flex-wrap gap-1">{result.missing_keywords.map(k => <KeywordPill key={k} label={k} variant="miss" />)}</div>
                </div>
              )}
              {result.improvements.length > 0 && (
                <div>
                  <p className="text-xs text-text-dim uppercase tracking-widest mb-2">
                    Suggested improvements ({result.improvements.length})
                  </p>
                  <ul className="space-y-1.5 mb-3">
                    {result.improvements.map((imp, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-text-secondary font-light">
                        <AlertTriangle className="w-3 h-3 text-[#ffc87c] shrink-0 mt-0.5" />
                        {imp}
                      </li>
                    ))}
                  </ul>
                  <button
                    onClick={onApplyImprovements}
                    disabled={applyLoading}
                    className="w-full flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-manrope font-medium transition-all"
                    style={{ background: "rgba(255,200,124,0.08)", color: "#ffc87c", border: "1px solid rgba(255,200,124,0.2)" }}
                  >
                    {applyLoading
                      ? <><Loader2 className="w-3 h-3 animate-spin" />Applying…</>
                      : <><Sparkles className="w-3 h-3" />Apply All Improvements to Resume</>}
                  </button>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function ResumeViewer({ result, onReoptimize, reoptLoading }: {
  result: ATSOptimizeResponse;
  onReoptimize: () => void;
  reoptLoading: boolean;
}) {
  const [view, setView] = useState<"optimized" | "original" | "latex">("optimized");

  const handleCopy = () => {
    const text = view === "latex" ? result.latex_text ?? "" : view === "optimized" ? result.optimized_text : result.original_text;
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard");
  };

  const handleDownloadTxt = () => {
    const blob = new Blob([result.optimized_text], { type: "text/plain;charset=utf-8" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "resume_optimized.txt"; a.click();
  };
  const handleDownloadLatex = () => {
    if (!result.latex_text) return;
    const blob = new Blob([result.latex_text], { type: "text/x-tex;charset=utf-8" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "resume_optimized.tex"; a.click();
  };

  const displayContent = view === "latex" ? result.latex_text ?? "" : view === "optimized" ? result.optimized_text : result.original_text;

  return (
    <div className="rounded-xl overflow-hidden" style={{ background: "rgba(17,19,23,0.8)", border: "1px solid rgba(68,71,72,0.4)" }}>
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: "1px solid rgba(68,71,72,0.3)" }}>
        <div className="flex gap-1">
          {([
            { v: "optimized", icon: <Eye className="w-3 h-3" />, label: "Optimized" },
            { v: "original",  icon: <FileText className="w-3 h-3" />, label: "Original" },
            ...(result.latex_text ? [{ v: "latex", icon: <Code2 className="w-3 h-3" />, label: "LaTeX" }] : []),
          ] as { v: string; icon: React.ReactNode; label: string }[]).map(({ v, icon, label }) => (
            <button key={v} onClick={() => setView(v as any)}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-manrope uppercase tracking-wide transition-all"
              style={view === v
                ? { background: "rgba(198,198,199,0.1)", color: "#e2e2e8", border: "1px solid rgba(198,198,199,0.2)" }
                : { color: "#6b6e72" }}>
              {icon}{label}
            </button>
          ))}
        </div>
        <button onClick={handleCopy} className="flex items-center gap-1 text-xs text-text-muted hover:text-text-secondary transition-colors">
          <Copy className="w-3 h-3" />Copy
        </button>
      </div>

      {/* Content */}
      <pre className="text-sm text-text-secondary leading-relaxed whitespace-pre-wrap break-words px-5 py-4 max-h-[460px] overflow-y-auto overflow-x-hidden font-mono no-scrollbar w-full">
        {displayContent}
      </pre>

      {/* Footer actions */}
      <div className="flex gap-2 px-4 pb-4 pt-2 flex-wrap" style={{ borderTop: "1px solid rgba(68,71,72,0.25)" }}>
        <button onClick={handleDownloadTxt} className="btn-ghost flex-1 flex items-center justify-center gap-1.5 text-sm py-2">
          <Download className="w-3 h-3" />.txt
        </button>
        {result.latex_text && (
          <button onClick={handleDownloadLatex}
            className="btn-ghost flex-1 flex items-center justify-center gap-1.5 text-sm py-2"
            style={{ color: "#7cd0ff", borderColor: "rgba(124,208,255,0.2)" }}>
            <Download className="w-3 h-3" />.tex
          </button>
        )}
        <button onClick={onReoptimize} disabled={reoptLoading}
          className="btn-ghost flex items-center gap-1.5 text-sm py-2 px-4"
          style={{ color: "#d6baff", borderColor: "rgba(214,186,255,0.2)" }}>
          {reoptLoading
            ? <Loader2 className="w-3 h-3 animate-spin" />
            : <RotateCcw className="w-3 h-3" />}
          Re-optimize
        </button>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function Optimize() {
  const navigate = useNavigate();
  const { resumeFilename, selectedJobId, selectedJob,
          optimizeResult: result, setOptimizeResult: setResult,
          optimizePassNum: passNum, setOptimizePassNum: setPassNum } = useAppStore();

  // Profile inputs
  const [githubUrls,  setGithubUrls]  = useState<string[]>([""]);
  const [linkedinUrl, setLinkedinUrl] = useState("");

  // Input state
  const [jobDesc,     setJobDesc]     = useState("");
  const [urlInput,    setUrlInput]    = useState("");
  const [urlLoading,  setUrlLoading]  = useState(false);
  const [fetchedMeta, setFetchedMeta] = useState<{ title?: string; company?: string } | null>(null);

  // Result state
  const [loading,      setLoading]      = useState(false);
  const [reoptLoading, setReoptLoading] = useState(false);

  // Panel open state
  const [atsOpen,     setAtsOpen]     = useState(true);
  const [changesOpen, setChangesOpen] = useState(true);

  // Stored job desc for re-optimization
  const [activeJobDesc, setActiveJobDesc] = useState("");

  // Exit warning when result exists
  useEffect(() => {
    if (!result) return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = "";
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [result]);

  const handleFetchUrl = async () => {
    if (!urlInput.trim()) return;
    setUrlLoading(true);
    try {
      const data = await fetchJobUrl(urlInput.trim());
      setJobDesc(data.description);
      setFetchedMeta({ title: data.title ?? undefined, company: data.company ?? undefined });
      toast.success(`Fetched${data.source !== "unknown" ? ` from ${data.source}` : ""}`);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Could not fetch — paste description manually");
    } finally {
      setUrlLoading(false);
    }
  };

  const runOptimize = async (
    prevOptimized?: string,
    pNum = 1,
    prevImprovements?: string[],
  ) => {
    if (!resumeFilename) { toast.error("Upload your resume first"); return; }
    const jd = activeJobDesc || jobDesc.trim();
    if (!jd && !selectedJobId) { toast.error("Provide a job description or select from dashboard"); return; }

    if (pNum > 1) setReoptLoading(true); else setLoading(true);
    try {
      const validGithubUrls = githubUrls.filter((u) => u.trim());
      const res = await optimizeResume({
        resume_filename: resumeFilename,
        job_id: selectedJobId ?? undefined,
        job_description: jd || undefined,
        previous_optimized: prevOptimized,
        previous_improvements: prevImprovements,
        github_urls: validGithubUrls.length > 0 ? validGithubUrls : undefined,
        linkedin_url: linkedinUrl.trim() || undefined,
      });
      setResult(res);
      setPassNum(pNum);
      if (pNum === 1) setActiveJobDesc(jd);
      toast.success(pNum > 1 ? `Pass ${pNum} complete` : "Resume optimized!");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Optimization failed");
    } finally {
      setLoading(false);
      setReoptLoading(false);
    }
  };

  const handleOptimize = () => runOptimize(undefined, 1);
  const handleReoptimize = () => {
    if (!result) return;
    runOptimize(result.optimized_text, passNum + 1);
  };
  const handleApplyImprovements = () => {
    if (!result || !result.improvements.length) return;
    runOptimize(result.optimized_text, passNum + 1, result.improvements);
  };

  return (
    <main className="pt-24 pb-16 px-8 max-w-7xl mx-auto">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <div className="flex items-end justify-between gap-4 flex-wrap">
          <div>
            <h1 className="font-manrope font-light text-5xl text-text-primary tracking-tight">
              ATS Resume Optimizer
            </h1>
            <p className="text-text-secondary mt-1.5 font-light text-base">
              World-class rewrite engine — strategic psychology, keyword science, LaTeX export.
            </p>
          </div>
          {result && (
            <div className="flex items-center gap-2">
              <button
                className="btn-ghost flex items-center gap-1.5 text-xs px-3 py-1.5"
                style={{ color: "#6ee7b7", borderColor: "rgba(110,231,183,0.2)" }}
                onClick={() => navigate("/interview/new")}
              >
                <BriefcaseBusiness className="w-3.5 h-3.5" />
                Interview Prep
              </button>
              <button onClick={() => { setResult(null); setPassNum(1); }}
                className="btn-ghost text-xs px-3 py-1.5" style={{ color: "#f87171", borderColor: "rgba(248,113,113,0.2)" }}>
                Clear result
              </button>
            </div>
          )}
          {passNum > 1 && (
            <span className="mb-1 text-xs px-2.5 py-1 rounded-full font-manrope uppercase tracking-widest"
              style={{ background: "rgba(214,186,255,0.1)", color: "#d6baff", border: "1px solid rgba(214,186,255,0.2)" }}>
              Pass {passNum}
            </span>
          )}
        </div>
      </motion.div>


      <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.1fr] gap-6 items-start">
        {/* ── Left: Input ─────────────────────────────────────────────────── */}
        <div className="space-y-4 lg:sticky lg:top-24">
          {/* GitHub + LinkedIn */}
          <ProfileInputForm
            githubUrls={githubUrls}
            linkedinUrl={linkedinUrl}
            onGithubUrlsChange={setGithubUrls}
            onLinkedinUrlChange={setLinkedinUrl}
          />

          {/* Resume */}
          <div className="glass-card-static p-5">
            <p className="text-sm font-manrope font-semibold text-text-secondary uppercase tracking-[0.15em] mb-4 flex items-center gap-2">
              <FileText className="w-3.5 h-3.5 text-text-muted" />Your Resume
            </p>
            <ResumeDropzone />
          </div>

          {/* Job input */}
          <div className="glass-card-static p-5 space-y-4">
            <p className="text-sm font-manrope font-semibold text-text-secondary uppercase tracking-[0.15em]">
              Target Job
            </p>

            {/* URL fetch */}
            <div>
              <p className="text-xs text-text-muted uppercase tracking-widest mb-1.5 font-manrope">Job URL</p>
              <div className="flex gap-2">
                <input type="url" className="input-base text-base flex-1"
                  placeholder="https://linkedin.com/jobs/view/…"
                  value={urlInput} onChange={e => setUrlInput(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && handleFetchUrl()} />
                <button onClick={handleFetchUrl} disabled={urlLoading || !urlInput.trim()}
                  className="btn-ghost text-base px-3 py-2 shrink-0">
                  {urlLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Link2 className="w-3.5 h-3.5" />}
                </button>
              </div>
              {fetchedMeta && (
                <div className="flex items-center gap-1.5 mt-1.5">
                  <Check className="w-3 h-3 text-[#4ade80]" />
                  <span className="text-xs text-text-muted">{[fetchedMeta.title, fetchedMeta.company].filter(Boolean).join(" · ")}</span>
                </div>
              )}
            </div>

            <div className="flex items-center gap-2">
              <div className="flex-1 h-px" style={{ background: "rgba(68,71,72,0.4)" }} />
              <span className="text-xs text-text-dim">or paste</span>
              <div className="flex-1 h-px" style={{ background: "rgba(68,71,72,0.4)" }} />
            </div>

            {selectedJobId && selectedJob && (
              <div className="flex items-center gap-2 p-2.5 rounded-lg"
                style={{ background: "rgba(198,198,199,0.05)", border: "1px solid rgba(198,198,199,0.15)" }}>
                <Check className="w-3.5 h-3.5 text-text-secondary" />
                <span className="text-base text-text-secondary">Job selected from dashboard</span>
              </div>
            )}
            <textarea className="input-base min-h-[160px] resize-none font-mono text-base leading-relaxed"
              placeholder="Paste the full job description…"
              value={jobDesc} onChange={e => setJobDesc(e.target.value)} />
          </div>

          <button className="btn-primary w-full py-3 text-base" onClick={handleOptimize} disabled={loading || reoptLoading}>
            {loading ? <><Spinner size="sm" />Optimizing with Claude…</> : <><Sparkles className="w-4 h-4" />Optimize Resume</>}
          </button>
        </div>

        {/* ── Right: Output ───────────────────────────────────────────────── */}
        <div className="space-y-3">
          {!result && !loading && (
            <div className="rounded-xl p-12 text-center flex flex-col items-center gap-5"
              style={{ background: "rgba(17,19,23,0.6)", border: "1px solid rgba(68,71,72,0.3)" }}>
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center"
                style={{ background: "rgba(198,198,199,0.04)", border: "1px solid rgba(198,198,199,0.1)" }}>
                <Sparkles className="w-6 h-6 text-text-muted opacity-50" />
              </div>
              <div>
                <p className="font-manrope font-light text-text-secondary">Your optimized resume appears here</p>
                <p className="text-text-muted text-base mt-1">Strategic rewrite · ATS scoring · LaTeX export</p>
              </div>
            </div>
          )}

          {loading && (
            <div className="rounded-xl p-12 text-center flex flex-col items-center gap-5"
              style={{ background: "rgba(17,19,23,0.6)", border: "1px solid rgba(68,71,72,0.3)" }}>
              <Spinner size="lg" />
              <div>
                <p className="font-manrope font-light text-text-primary">Optimizing…</p>
                <p className="text-text-muted text-base mt-1">Applying strategic framing, keyword science, and ATS alignment</p>
              </div>
            </div>
          )}

          {result && (
            <motion.div key={passNum} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-3">
              {/* LinkedIn warning */}
              {result.linkedin_unavailable && (
                <div className="flex items-start gap-2.5 px-4 py-3 rounded-xl text-sm font-inter"
                  style={{ background: "rgba(255,200,124,0.06)", border: "1px solid rgba(255,200,124,0.15)", color: "#ffc87c" }}>
                  <Info className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                  LinkedIn profile could not be accessed — optimization used GitHub data only. Results are still strong.
                </div>
              )}

              {/* ATS Breakdown */}
              <ATSBreakdown
                result={result}
                open={atsOpen}
                onToggle={() => setAtsOpen(v => !v)}
                onApplyImprovements={handleApplyImprovements}
                applyLoading={reoptLoading}
              />

              {/* What Changed */}
              {(result.change_items.length > 0 || result.changes_summary.length > 0) && (
                <WhatChanged
                  items={result.change_items}
                  plain={result.changes_summary}
                  open={changesOpen}
                  onToggle={() => setChangesOpen(v => !v)}
                />
              )}

              {/* Resume viewer + actions */}
              <ResumeViewer result={result} onReoptimize={handleReoptimize} reoptLoading={reoptLoading} />

              {/* Transparency report */}
              <TransparencyReport
                transparencyReport={result.transparency_report}
                gapAnalysis={result.gap_analysis}
                interviewPrep={result.interview_prep}
              />
            </motion.div>
          )}
        </div>
      </div>
    </main>
  );
}
