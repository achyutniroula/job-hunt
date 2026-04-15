import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ChevronUp, Eye, BookOpen, MessageSquare } from "lucide-react";

interface Props {
  transparencyReport: string;
  gapAnalysis: string;
  interviewPrep: string;
}

const TABS = [
  { key: "changes",   label: "What Changed",      icon: Eye },
  { key: "gaps",      label: "Gaps & Study Plan",  icon: BookOpen },
  { key: "interview", label: "Interview Prep",     icon: MessageSquare },
] as const;

type Tab = typeof TABS[number]["key"];

export default function TransparencyReport({ transparencyReport, gapAnalysis, interviewPrep }: Props) {
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState<Tab>("changes");

  const content: Record<Tab, string> = {
    changes:   transparencyReport,
    gaps:      gapAnalysis,
    interview: interviewPrep,
  };

  if (!transparencyReport && !gapAnalysis && !interviewPrep) return null;

  return (
    <div className="rounded-xl overflow-hidden"
      style={{ background: "rgba(14,16,20,0.7)", border: "1px solid rgba(124,208,255,0.12)" }}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-5 py-3.5 text-left transition-colors hover:bg-white/[0.02]"
      >
        <div className="flex items-center gap-2.5">
          <Eye className="w-3.5 h-3.5" style={{ color: "#7cd0ff" }} />
          <span className="text-sm font-manrope font-semibold uppercase tracking-[0.15em]"
            style={{ color: "#7cd0ff" }}>
            Behind the Scenes
          </span>
        </div>
        {open ? <ChevronUp className="w-3.5 h-3.5 text-text-muted" /> : <ChevronDown className="w-3.5 h-3.5 text-text-muted" />}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div style={{ borderTop: "1px solid rgba(124,208,255,0.1)" }}>
              {/* Tabs */}
              <div className="flex px-4 pt-3 gap-1">
                {TABS.map(({ key, label, icon: Icon }) => (
                  <button
                    key={key}
                    onClick={() => setTab(key)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-manrope uppercase tracking-wide transition-all"
                    style={tab === key
                      ? { background: "rgba(124,208,255,0.1)", color: "#7cd0ff", border: "1px solid rgba(124,208,255,0.2)" }
                      : { color: "#6b6e72" }}
                  >
                    <Icon className="w-3 h-3" />{label}
                  </button>
                ))}
              </div>

              {/* Content */}
              <div className="px-5 py-4 max-h-80 overflow-y-auto no-scrollbar">
                <pre className="text-sm text-text-secondary font-inter leading-relaxed whitespace-pre-wrap">
                  {content[tab] || "No data available for this section."}
                </pre>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
