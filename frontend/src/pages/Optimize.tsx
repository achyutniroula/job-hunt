import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FileText, Sparkles, Download, ChevronRight, Check } from "lucide-react";
import toast from "react-hot-toast";
import { optimizeResume } from "@/lib/api";
import { useAppStore } from "@/store/appStore";
import ResumeDropzone from "@/components/ResumeDropzone";
import Spinner from "@/components/ui/Spinner";
import type { ATSOptimizeResponse } from "@/types";

function ScoreBar({ label, value }: { label: string; value: number | null }) {
  if (value === null) return null;
  const color = value >= 70 ? "#4ade80" : value >= 45 ? "#ffc87c" : "#f87171";
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[10px] font-manrope uppercase tracking-widest text-text-muted">{label}</span>
        <span className="text-sm font-manrope rgb-text-gradient">{value}</span>
      </div>
      <div className="h-1 rounded-full overflow-hidden" style={{ background: "rgba(68,71,72,0.3)" }}>
        <motion.div className="h-full rounded-full" style={{ backgroundColor: color }}
          initial={{ width: 0 }} animate={{ width: `${value}%` }} transition={{ duration: 0.8, ease: "easeOut" }} />
      </div>
    </div>
  );
}

export default function Optimize() {
  const { resumeFilename, selectedJobId } = useAppStore();
  const [jobDesc, setJobDesc] = useState("");
  const [loading, setLoading] = useState(false);
  const [result,  setResult]  = useState<ATSOptimizeResponse | null>(null);
  const [view,    setView]    = useState<"optimized" | "original">("optimized");

  const handleOptimize = async () => {
    if (!resumeFilename) { toast.error("Upload your resume first"); return; }
    if (!jobDesc.trim() && !selectedJobId) { toast.error("Paste a job description or select a job from the dashboard"); return; }
    setLoading(true);
    try {
      const res = await optimizeResume({
        resume_filename: resumeFilename,
        job_id: selectedJobId ?? undefined,
        job_description: jobDesc.trim() || undefined,
      });
      setResult(res);
      toast.success("Resume optimized!");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Optimization failed");
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!result) return;
    const blob = new Blob([result.optimized_text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "resume_optimized.txt"; a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <main className="pt-24 pb-16 px-8 max-w-5xl">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <h1 className="font-manrope font-light text-4xl text-text-primary tracking-tight">
          ATS Resume Optimizer
        </h1>
        <p className="text-text-secondary mt-2 font-light text-sm leading-relaxed">
          Rewrite your resume to maximize keyword alignment and ATS pass rate — same facts, better framing.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input panel */}
        <div className="space-y-4">
          <div className="glass-card-static p-5">
            <p className="text-xs font-manrope font-semibold text-text-secondary uppercase tracking-[0.15em] mb-4 flex items-center gap-2">
              <FileText className="w-3.5 h-3.5 text-text-muted" />
              Your Resume
            </p>
            <ResumeDropzone />
          </div>

          <div className="glass-card-static p-5">
            <p className="text-xs font-manrope font-semibold text-text-secondary uppercase tracking-[0.15em] mb-4">
              Target Job Description
            </p>
            {selectedJobId && (
              <div className="flex items-center gap-2 mb-3 p-2.5 rounded-lg"
                style={{ background: "rgba(198,198,199,0.05)", border: "1px solid rgba(198,198,199,0.15)" }}>
                <Check className="w-3.5 h-3.5 text-text-secondary" />
                <span className="text-xs text-text-secondary font-inter">Job selected from dashboard — description will be loaded automatically</span>
              </div>
            )}
            <textarea
              className="input-base min-h-[180px] resize-none font-mono text-xs leading-relaxed"
              placeholder="Paste the full job description here…"
              value={jobDesc}
              onChange={e => setJobDesc(e.target.value)}
            />
          </div>

          <button className="btn-primary w-full py-3 text-sm" onClick={handleOptimize} disabled={loading}>
            {loading
              ? <><Spinner size="sm" />Optimizing with Claude…</>
              : <><Sparkles className="w-4 h-4" />Optimize Resume</>}
          </button>
        </div>

        {/* Output panel */}
        <div className="space-y-4">
          {!result && !loading && (
            <div className="glass-card p-10 text-center flex flex-col items-center justify-center gap-5 min-h-[400px]">
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center"
                style={{ background: "rgba(198,198,199,0.05)", border: "1px solid rgba(198,198,199,0.1)" }}>
                <Sparkles className="w-6 h-6 text-text-muted opacity-60" />
              </div>
              <div>
                <p className="text-text-secondary font-manrope font-light">Optimized resume will appear here</p>
                <p className="text-text-muted text-sm mt-1 font-inter">Claude will rewrite your content to maximize ATS keywords</p>
              </div>
            </div>
          )}

          {loading && (
            <div className="glass-card p-10 text-center flex flex-col items-center justify-center gap-5 min-h-[400px]">
              <Spinner size="lg" />
              <div>
                <p className="font-manrope font-light text-text-primary">Optimizing your resume…</p>
                <p className="text-text-muted text-sm mt-1 font-inter">Claude is analyzing your experience and tailoring keywords</p>
              </div>
            </div>
          )}

          {result && (
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
              {/* ATS Score */}
              <div className="glass-card p-5 space-y-4">
                <p className="text-xs font-manrope font-semibold text-text-secondary uppercase tracking-[0.15em]">ATS Score Estimate</p>
                <ScoreBar label="Before" value={result.ats_score_before} />
                <ScoreBar label="After"  value={result.ats_score_after} />
              </div>

              {/* Changes */}
              {result.changes_summary.length > 0 && (
                <div className="glass-card-static p-5">
                  <p className="text-xs font-manrope font-semibold text-text-secondary uppercase tracking-[0.15em] mb-4">What changed</p>
                  <ul className="space-y-2">
                    {result.changes_summary.map((c, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-text-secondary font-light">
                        <ChevronRight className="w-3.5 h-3.5 text-accent shrink-0 mt-0.5" />
                        {c}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Before / After toggle */}
              <div className="glass-card p-5">
                <div className="flex items-center gap-2 mb-4">
                  {(["optimized", "original"] as const).map(v => (
                    <button key={v} onClick={() => setView(v)}
                      className="px-3 py-1.5 rounded-lg text-xs font-manrope font-medium capitalize transition-all"
                      style={view === v
                        ? { background: "rgba(198,198,199,0.08)", color: "#e2e2e8", border: "1px solid rgba(198,198,199,0.2)" }
                        : { color: "#8e9192" }}>
                      {v}
                    </button>
                  ))}
                </div>
                <pre className="text-xs text-text-secondary leading-relaxed whitespace-pre-wrap max-h-[400px] overflow-y-auto font-mono no-scrollbar">
                  {view === "optimized" ? result.optimized_text : result.original_text}
                </pre>
              </div>

              <button onClick={handleDownload} className="btn-ghost w-full flex items-center justify-center gap-2 text-xs py-3">
                <Download className="w-3.5 h-3.5" />
                Download Optimized Resume
              </button>
            </motion.div>
          )}
        </div>
      </div>
    </main>
  );
}
