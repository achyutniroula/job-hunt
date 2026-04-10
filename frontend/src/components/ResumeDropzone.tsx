import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileText, CheckCircle, X } from "lucide-react";
import clsx from "clsx";
import toast from "react-hot-toast";
import { uploadResume } from "@/lib/api";
import { useAppStore } from "@/store/appStore";
import Spinner from "@/components/ui/Spinner";

const ACCEPTED = {
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
  "application/msword": [".doc"],
  "text/plain": [".txt"],
};

interface ResumeDropzoneProps {
  onUploaded?: (filename: string) => void;
}

export default function ResumeDropzone({ onUploaded }: ResumeDropzoneProps) {
  const [loading, setLoading] = useState(false);
  const { resumeFilename, parsedResume, setResume, clearResume } = useAppStore();

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;
    setLoading(true);
    try {
      const res = await uploadResume(file);
      setResume(res.filename, res.parsed);
      onUploaded?.(res.filename);
      toast.success("Resume uploaded and parsed successfully!");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Upload failed");
    } finally {
      setLoading(false);
    }
  }, [setResume, onUploaded]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: ACCEPTED, maxFiles: 1, disabled: loading,
  });

  if (resumeFilename && parsedResume) {
    return (
      <motion.div initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }}
        className="glass-card p-4 flex items-start gap-4">
        <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
          style={{ background: "rgba(74,222,128,0.08)", border: "1px solid rgba(74,222,128,0.2)" }}>
          <CheckCircle className="w-4 h-4 text-success" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-manrope font-medium text-text-primary truncate">{resumeFilename}</p>
          <p className="text-xs text-text-muted mt-0.5 font-inter">
            {parsedResume.skills.length} skills · {parsedResume.seniority_level ?? "unknown"} level
            {parsedResume.experience_years ? ` · ${parsedResume.experience_years}+ yrs` : ""}
          </p>
          <div className="flex flex-wrap gap-1.5 mt-2">
            {parsedResume.tech_stack.slice(0, 6).map(s => (
              <span key={s} className="badge" style={{ color: "#e2e2e8", background: "rgba(198,198,199,0.08)", border: "1px solid rgba(198,198,199,0.18)" }}>
                {s}
              </span>
            ))}
            {parsedResume.tech_stack.length > 6 && (
              <span className="badge">+{parsedResume.tech_stack.length - 6} more</span>
            )}
          </div>
        </div>
        <button onClick={clearResume} className="text-text-muted hover:text-danger transition-colors shrink-0 mt-0.5" title="Remove resume">
          <X className="w-4 h-4" />
        </button>
      </motion.div>
    );
  }

  return (
    <div
      {...getRootProps()}
      className={clsx(
        "border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200",
        isDragActive ? "border-accent/50 bg-accent/5" : "hover:bg-bg-elevated/30"
      )}
      style={{
        border: isDragActive
          ? "2px dashed rgba(198,198,199,0.4)"
          : "2px dashed rgba(68,71,72,0.4)",
      }}
    >
      <input {...getInputProps()} />
      <AnimatePresence mode="wait">
        {loading ? (
          <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="flex flex-col items-center gap-3">
            <Spinner size="lg" />
            <p className="text-text-secondary text-sm font-light">Parsing resume…</p>
          </motion.div>
        ) : (
          <motion.div key="idle" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="flex flex-col items-center gap-3">
            <div className="w-11 h-11 rounded-xl flex items-center justify-center"
              style={{ background: "rgba(198,198,199,0.05)", border: "1px solid rgba(198,198,199,0.12)" }}>
              {isDragActive
                ? <Upload className="w-5 h-5 text-text-secondary" />
                : <FileText className="w-5 h-5 text-text-secondary" />}
            </div>
            <div>
              <p className="text-text-primary font-manrope font-light text-sm">
                {isDragActive ? "Drop your resume here" : "Upload your resume"}
              </p>
              <p className="text-text-muted text-xs mt-1 font-inter">PDF, DOCX, or TXT · max 10 MB</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
