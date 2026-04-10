import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Sparkles, Copy, Download, Check, FileText, Building2, X } from "lucide-react";
import toast from "react-hot-toast";
import { generateCoverLetter, downloadCoverLetterDocx } from "@/lib/api";
import { useAppStore } from "@/store/appStore";
import ResumeDropzone from "@/components/ResumeDropzone";
import Spinner from "@/components/ui/Spinner";
import type { CoverLetterResponse } from "@/types";

export default function CoverLetter() {
  const { resumeFilename, selectedJobId, selectedJob } = useAppStore();
  const [jobDesc,      setJobDesc]      = useState("");
  const [company,      setCompany]      = useState(selectedJob?.company ?? "");
  const [jobTitle,     setJobTitle]     = useState(selectedJob?.title ?? "");
  const [extraNotes,   setExtraNotes]   = useState("");
  const [loading,      setLoading]      = useState(false);
  const [result,       setResult]       = useState<CoverLetterResponse | null>(null);

  // Sync company/title when selectedJob changes (but not if user has already generated)
  useEffect(() => {
    if (selectedJob && !result) {
      setCompany(selectedJob.company ?? "");
      setJobTitle(selectedJob.title ?? "");
    }
  }, [selectedJob]);
  const [editedLetter, setEditedLetter] = useState("");
  const [copied,       setCopied]       = useState(false);
  const [docxLoading,  setDocxLoading]  = useState(false);
  const [bannerDismissed, setBannerDismissed] = useState(false);

  const handleGenerate = async () => {
    if (!resumeFilename) { toast.error("Upload your resume first"); return; }
    if (!jobDesc.trim() && !selectedJobId) { toast.error("Paste a job description or select a job from the dashboard"); return; }
    setLoading(true);
    try {
      const res = await generateCoverLetter({
        resume_filename: resumeFilename,
        job_id: selectedJobId ?? undefined,
        job_description: jobDesc.trim() || undefined,
        company_name: company.trim() || undefined,
        job_title: jobTitle.trim() || undefined,
        extra_notes: extraNotes.trim() || undefined,
      });
      setResult(res);
      setEditedLetter(res.cover_letter);
      toast.success("Cover letter generated!");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Generation failed");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(editedLetter);
    setCopied(true);
    toast.success("Copied to clipboard!");
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadTxt = () => {
    const blob = new Blob([editedLetter], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `cover_letter_${company.trim().replace(/\s+/g, "_") || "company"}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadDocx = async () => {
    setDocxLoading(true);
    try {
      const blob = await downloadCoverLetterDocx(editedLetter, company.trim() || "company");
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `cover_letter_${company.trim().replace(/\s+/g, "_") || "company"}.docx`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Word document downloaded!");
    } catch {
      toast.error("Failed to generate .docx");
    } finally {
      setDocxLoading(false);
    }
  };

  return (
    <main className="pt-24 pb-16 px-8 max-w-6xl mx-auto">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <h1 className="font-manrope font-light text-4xl text-text-primary tracking-tight">
          Cover Letter Generator
        </h1>
        <p className="text-text-secondary mt-2 font-light text-sm">
          AI-written, human-sounding letters — concise, specific, never generic.
        </p>
      </motion.div>

      {/* Job context banner */}
      {selectedJob && !bannerDismissed && (
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
          className="mb-5 px-4 py-3 rounded-xl flex items-center gap-3"
          style={{ background: "rgba(124,208,255,0.06)", border: "1px solid rgba(124,208,255,0.15)" }}>
          <Building2 className="w-4 h-4 shrink-0" style={{ color: "#7cd0ff" }} />
          <div className="min-w-0 flex-1">
            <p className="text-xs font-manrope font-medium text-text-secondary truncate">
              {selectedJob.title} · {selectedJob.company ?? "Unknown Company"}
            </p>
            {selectedJob.description && (
              <p className="text-[10px] text-text-muted mt-0.5 line-clamp-1">
                {selectedJob.description.slice(0, 120)}…
              </p>
            )}
          </div>
          <button onClick={() => setBannerDismissed(true)} className="shrink-0 p-1 rounded hover:bg-white/[0.06] transition-colors text-text-muted hover:text-text-secondary">
            <X className="w-3.5 h-3.5" />
          </button>
        </motion.div>
      )}

      <div className="space-y-4">
        {/* Input panel */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_1fr] gap-4">
          <div className="glass-card-static p-5">
            <p className="text-xs font-manrope font-semibold text-text-secondary uppercase tracking-[0.15em] mb-4">
              Your Resume
            </p>
            <ResumeDropzone />
          </div>

          <div className="glass-card-static p-5 space-y-4">
            <p className="text-xs font-manrope font-semibold text-text-secondary uppercase tracking-[0.15em]">
              Job Details
            </p>

            {selectedJobId && (
              <div className="flex items-center gap-2 p-2.5 rounded-lg"
                style={{ background: "rgba(198,198,199,0.05)", border: "1px solid rgba(198,198,199,0.15)" }}>
                <Check className="w-3.5 h-3.5 text-text-secondary" />
                <span className="text-xs text-text-secondary">Job selected from dashboard</span>
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[10px] text-text-muted font-manrope uppercase tracking-widest block mb-1.5">Job Title</label>
                <input type="text" className="input-base" placeholder="Senior Engineer"
                  value={jobTitle} onChange={e => setJobTitle(e.target.value)} />
              </div>
              <div>
                <label className="text-[10px] text-text-muted font-manrope uppercase tracking-widest block mb-1.5">Company</label>
                <input type="text" className="input-base" placeholder="Acme Corp"
                  value={company} onChange={e => setCompany(e.target.value)} />
              </div>
            </div>

            <div>
              <label className="text-[10px] text-text-muted font-manrope uppercase tracking-widest block mb-1.5">Extra notes <span className="text-text-dim normal-case tracking-normal">(optional)</span></label>
              <input type="text" className="input-base"
                placeholder="e.g. Referred by John Smith…"
                value={extraNotes} onChange={e => setExtraNotes(e.target.value)} />
            </div>
          </div>
        </div>

        {/* Job description - full width */}
        <div className="glass-card-static p-5">
          <label className="text-[10px] text-text-muted font-manrope uppercase tracking-widest block mb-2">Job Description</label>
          <textarea className="input-base min-h-[120px] resize-none font-mono text-xs leading-relaxed w-full"
            placeholder="Paste the full job description…"
            value={jobDesc} onChange={e => setJobDesc(e.target.value)} />
        </div>

        <button className="btn-primary w-full py-3 text-sm" onClick={handleGenerate} disabled={loading}>
          {loading
            ? <><Spinner size="sm" />Writing with Claude…</>
            : <><Sparkles className="w-4 h-4" />Generate Cover Letter</>}
        </button>

        {/* Output panel — centered full-width */}
        {!result && !loading && (
          <div className="glass-card p-10 text-center flex flex-col items-center justify-center gap-5 min-h-[280px]">
            <div className="w-14 h-14 rounded-2xl flex items-center justify-center"
              style={{ background: "rgba(214,186,255,0.06)", border: "1px solid rgba(214,186,255,0.12)" }}>
              <Sparkles className="w-6 h-6 opacity-40" style={{ color: "#d6baff" }} />
            </div>
            <div>
              <p className="text-text-secondary font-manrope font-light">Your cover letter will appear here</p>
              <p className="text-text-muted text-sm mt-1 font-inter">Human-tone, specific to the role — never generic</p>
            </div>
          </div>
        )}

        {loading && (
          <div className="glass-card p-10 text-center flex flex-col items-center justify-center gap-5 min-h-[280px]">
            <Spinner size="lg" />
            <div>
              <p className="font-manrope font-light text-text-primary">Writing your cover letter…</p>
              <p className="text-text-muted text-sm mt-1 font-inter">Claude is crafting a human-sounding letter</p>
            </div>
          </div>
        )}

        {result && !loading && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
            {/* Letter area */}
            <div className="glass-card p-5 group relative">
              {/* Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <span className="badge" style={{ color: "#4ade80", background: "rgba(74,222,128,0.08)", border: "1px solid rgba(74,222,128,0.15)" }}>
                    {result.word_count} words
                  </span>
                  <span className="badge">Editable</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <button onClick={handleCopy} className="btn-ghost text-xs px-3 py-1.5">
                    {copied
                      ? <><Check className="w-3 h-3 text-success" />Copied</>
                      : <><Copy className="w-3 h-3" />Copy</>}
                  </button>
                  <button onClick={handleDownloadTxt} className="btn-ghost text-xs px-3 py-1.5">
                    <FileText className="w-3 h-3" />.txt
                  </button>
                  <button onClick={handleDownloadDocx} disabled={docxLoading} className="btn-ghost text-xs px-3 py-1.5"
                    style={{ color: "#7cd0ff", borderColor: "rgba(124,208,255,0.2)" }}>
                    {docxLoading ? <Spinner size="sm" /> : <Download className="w-3 h-3" />}.docx
                  </button>
                </div>
              </div>

              <textarea
                className="w-full bg-transparent text-text-secondary text-sm leading-relaxed resize-none outline-none min-h-[420px] focus:text-text-primary transition-colors font-inter no-scrollbar"
                value={editedLetter}
                onChange={e => setEditedLetter(e.target.value)}
                spellCheck
              />
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: "Word Count", value: result.word_count },
                { label: "Tone",       value: "Confident" },
                { label: "Target",     value: jobTitle || "Role" },
              ].map(({ label, value }) => (
                <div key={label} className="glass-card p-4">
                  <div className="text-[10px] uppercase tracking-widest text-text-muted mb-1 font-manrope">{label}</div>
                  <div className="text-base font-manrope rgb-text-gradient">{value}</div>
                </div>
              ))}
            </div>

            <button onClick={handleGenerate} className="btn-ghost w-full text-xs py-3 flex items-center justify-center gap-2">
              <Sparkles className="w-3.5 h-3.5" />
              Regenerate
            </button>
          </motion.div>
        )}
      </div>
    </main>
  );
}
