import { useState, useEffect } from "react";
import { Sparkles, Copy, CheckCheck, ChevronDown, ChevronUp, AlertCircle, Code2 } from "lucide-react";
import toast from "react-hot-toast";
import { optimizeSessionResume, updateSessionResume, getSessionOptimizeResult } from "@/lib/api";
import type { ATSOptimizeResponse } from "@/types";

interface Props {
  sessionId: string;
  hasGithub: boolean;
  onApply?: (optimizedText: string) => void;
}

function ScoreBadge({ label, score }: { label: string; score: number | null }) {
  if (score === null) return null;
  const color = score >= 70 ? "#22c55e" : score >= 45 ? "#f59e0b" : "#ef4444";
  return (
    <div className="flex flex-col items-center gap-1">
      <span className="text-xs text-text-muted">{label}</span>
      <span className="text-2xl font-manrope font-light" style={{ color }}>{score}</span>
    </div>
  );
}

function Section({ title, content }: { title: string; content: string }) {
  const [open, setOpen] = useState(false);
  if (!content?.trim()) return null;
  return (
    <div className="glass-card overflow-hidden">
      <button
        className="w-full flex items-center justify-between px-5 py-3.5 text-sm text-left"
        onClick={() => setOpen((o) => !o)}
        style={{ color: "rgba(198,198,199,0.7)" }}
      >
        <span className="font-manrope">{title}</span>
        {open ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>
      {open && (
        <div
          className="px-5 pb-4 text-xs leading-relaxed whitespace-pre-wrap"
          style={{ borderTop: "1px solid rgba(72,72,75,0.25)", color: "rgba(198,198,199,0.85)", paddingTop: "12px" }}
        >
          {content}
        </div>
      )}
    </div>
  );
}

export default function ResumeOptimizer({ sessionId, hasGithub, onApply }: Props) {
  const [result, setResult] = useState<ATSOptimizeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [copiedLatex, setCopiedLatex] = useState(false);
  const [applying, setApplying] = useState(false);

  useEffect(() => {
    getSessionOptimizeResult(sessionId)
      .then(setResult)
      .catch(() => {/* 404 = no result yet, silently ignore */})
      .finally(() => setInitialLoading(false));
  }, [sessionId]);

  const handleOptimize = async () => {
    setLoading(true);
    setResult(null);
    try {
      const data = await optimizeSessionResume(sessionId);
      setResult(data);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(msg ?? "Optimization failed");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (!result) return;
    navigator.clipboard.writeText(result.optimized_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCopyLatex = () => {
    if (!result?.latex_text) return;
    navigator.clipboard.writeText(result.latex_text);
    setCopiedLatex(true);
    setTimeout(() => setCopiedLatex(false), 2000);
  };

  const handleApply = async () => {
    if (!result) return;
    setApplying(true);
    try {
      await updateSessionResume(sessionId, result.optimized_text);
      onApply?.(result.optimized_text);
      toast.success("Optimized resume applied to session");
    } catch {
      toast.error("Failed to apply resume");
    } finally {
      setApplying(false);
    }
  };

  if (initialLoading) {
    return (
      <div className="space-y-3">
        {[1, 2].map((i) => <div key={i} className="skeleton h-20 rounded-lg" />)}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 min-w-0 max-w-full overflow-hidden">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="font-manrope font-light text-text-primary text-lg">Resume Optimizer</h2>
          <p className="text-text-muted text-xs mt-1">
            {hasGithub
              ? "Uses your GitHub projects, job description, and resume for deep optimization."
              : "Optimizes resume against job description. Add a GitHub URL for richer results."}
          </p>
        </div>
        <button
          className="btn-primary flex items-center gap-2 text-sm px-4 py-2 shrink-0"
          onClick={handleOptimize}
          disabled={loading}
        >
          <Sparkles className="w-4 h-4" />
          {loading ? "Optimizing…" : "Optimize"}
        </button>
      </div>

      {!hasGithub && !result && (
        <div
          className="flex items-start gap-3 p-4 rounded-lg text-xs"
          style={{ background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.2)", color: "rgba(245,158,11,0.9)" }}
        >
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>No GitHub linked. Start a new session with a GitHub URL for enhanced optimization using your project evidence.</span>
        </div>
      )}

      {loading && (
        <div className="glass-card p-10 text-center text-text-muted">
          <div className="flex items-center justify-center gap-2 mb-2">
            <span className="typing-dot" /><span className="typing-dot" /><span className="typing-dot" />
          </div>
          <p className="text-sm mt-3">Analyzing resume, job description{hasGithub ? ", and GitHub projects" : ""}…</p>
          <p className="text-xs opacity-60 mt-1">This takes ~20–40 seconds</p>
        </div>
      )}

      {result && (
        <div className="flex flex-col gap-4">
          {/* ATS scores */}
          <div className="glass-card p-5">
            <p className="text-text-muted text-xs uppercase tracking-widest mb-4">ATS Score</p>
            <div className="flex items-center gap-8">
              <ScoreBadge label="Before" score={result.ats_score_before} />
              <div className="flex-1 h-px" style={{ background: "rgba(72,72,75,0.4)" }} />
              <ScoreBadge label="After" score={result.ats_score_after} />
            </div>
          </div>

          {/* Keywords */}
          {result.matched_keywords.length > 0 && (
            <div className="glass-card p-5">
              <p className="text-text-muted text-xs uppercase tracking-widest mb-3">Matched Keywords</p>
              <div className="flex flex-wrap gap-1.5">
                {result.matched_keywords.slice(0, 20).map((kw) => (
                  <span
                    key={kw}
                    className="text-xs px-2 py-0.5 rounded-full"
                    style={{ background: "rgba(34,197,94,0.1)", border: "1px solid rgba(34,197,94,0.25)", color: "#4ade80" }}
                  >
                    {kw}
                  </span>
                ))}
              </div>
              {result.missing_keywords.length > 0 && (
                <>
                  <p className="text-text-muted text-xs uppercase tracking-widest mt-4 mb-3">Missing Keywords</p>
                  <div className="flex flex-wrap gap-1.5">
                    {result.missing_keywords.slice(0, 15).map((kw) => (
                      <span
                        key={kw}
                        className="text-xs px-2 py-0.5 rounded-full"
                        style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)", color: "#f87171" }}
                      >
                        {kw}
                      </span>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}

          {/* Optimized text */}
          <div className="glass-card p-5 min-w-0 overflow-hidden">
            <div className="flex items-center justify-between mb-3">
              <p className="text-text-muted text-xs uppercase tracking-widest">Optimized Resume</p>
              <div className="flex items-center gap-2">
                <button
                  className="btn-ghost flex items-center gap-1.5 text-xs px-3 py-1.5"
                  onClick={handleCopy}
                >
                  {copied ? <CheckCheck className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
                  {copied ? "Copied" : "Copy"}
                </button>
                <button
                  className="btn-primary flex items-center gap-1.5 text-xs px-3 py-1.5"
                  onClick={handleApply}
                  disabled={applying}
                >
                  {applying ? "Applying…" : "Apply to Resume"}
                </button>
              </div>
            </div>
            <pre
              className="text-xs leading-relaxed whitespace-pre-wrap font-mono"
              style={{ color: "rgba(198,198,199,0.85)", maxHeight: "400px", width: "100%", boxSizing: "border-box", overflowY: "auto" }}
            >
              {result.optimized_text}
            </pre>
          </div>

          {/* LaTeX source */}
          {result.latex_text && (
            <div className="glass-card p-5 min-w-0 overflow-hidden">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Code2 className="w-4 h-4 text-text-muted" />
                  <p className="text-text-muted text-xs uppercase tracking-widest">LaTeX Source</p>
                </div>
                <button
                  className="btn-ghost flex items-center gap-1.5 text-xs px-3 py-1.5"
                  onClick={handleCopyLatex}
                >
                  {copiedLatex ? <CheckCheck className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
                  {copiedLatex ? "Copied" : "Copy LaTeX"}
                </button>
              </div>
              <p className="text-xs text-text-muted mb-2 opacity-70">
                Paste into <a href="https://www.overleaf.com" target="_blank" rel="noopener noreferrer" className="underline hover:text-text-primary">Overleaf</a> to compile your PDF resume.
              </p>
              <pre
                className="text-xs leading-relaxed whitespace-pre font-mono rounded p-3"
                style={{
                  color: "rgba(198,198,199,0.75)",
                  background: "rgba(0,0,0,0.25)",
                  maxHeight: "400px",
                  width: "100%",
                  boxSizing: "border-box",
                  overflowX: "auto",
                  overflowY: "auto",
                }}
              >
                {result.latex_text}
              </pre>
            </div>
          )}

          <Section title="Transparency Report" content={result.transparency_report} />
          <Section title="Gap Analysis" content={result.gap_analysis} />
          <Section title="Interview Prep" content={result.interview_prep} />
        </div>
      )}
    </div>
  );
}
