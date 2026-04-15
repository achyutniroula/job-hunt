import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  FileText,
  Briefcase,
  Link2,
  MessageSquare,
  Lightbulb,
  Github,
  Sparkles,
  ArrowLeft,
} from "lucide-react";
import toast from "react-hot-toast";
import { getInterviewSession } from "@/lib/api";
import { useAppStore } from "@/store/appStore";
import ResumePreview from "@/components/interview/ResumePreview";
import JobDetails from "@/components/interview/JobDetails";
import CompanyLinks from "@/components/interview/CompanyLinks";
import InterviewQA from "@/components/interview/InterviewQA";
import BrainstormChat from "@/components/interview/BrainstormChat";
import GitHubRepos from "@/components/interview/GitHubRepos";
import ResumeOptimizer from "@/components/interview/ResumeOptimizer";
import NewInterviewSession from "@/pages/NewInterviewSession";

type Module = "resume" | "job" | "links" | "qa" | "github" | "brainstorm" | "optimize";

const NAV_ITEMS: { id: Module; label: string; icon: React.ElementType }[] = [
  { id: "resume",     label: "Resume",       icon: FileText },
  { id: "optimize",   label: "Optimizer",    icon: Sparkles },
  { id: "job",        label: "Job Details",  icon: Briefcase },
  { id: "links",      label: "Company",      icon: Link2 },
  { id: "qa",         label: "Chat",         icon: MessageSquare },
  { id: "github",     label: "GitHub",       icon: Github },
  { id: "brainstorm", label: "Brainstorm",   icon: Lightbulb },
];

interface Session {
  id: string;
  job_title: string;
  job_description: string;
  company_name: string;
  company_website?: string | null;
  company_careers_url?: string | null;
  company_glassdoor_url?: string | null;
  company_linkedin_url?: string | null;
  company_indeed_url?: string | null;
  resume_pdf_path?: string | null;
  resume_text?: string | null;
  github_url?: string | null;
  salary_info?: string | null;
  location?: string | null;
  seniority?: string | null;
  created_at: string;
  updated_at: string;
}

export default function InterviewPrep() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { interviewNavModule, setInterviewNavModule } = useAppStore();

  const [session, setSession] = useState<Session | null>(null);
  const [resumeText, setResumeText] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [activeModule, setActiveModule] = useState<Module>(interviewNavModule ?? "qa");

  // "new" is a special route to create a session
  const isNew = sessionId === "new";

  useEffect(() => {
    if (isNew || !sessionId) {
      setLoading(false);
      return;
    }
    getInterviewSession(sessionId)
      .then((s) => { setSession(s); setResumeText(s.resume_text ?? ""); })
      .catch(() => toast.error("Session not found"))
      .finally(() => setLoading(false));
  }, [sessionId, isNew]);

  const switchModule = (m: Module) => {
    setActiveModule(m);
    setInterviewNavModule(m);
  };

  if (isNew) {
    return <NewInterviewSession />;
  }

  if (loading) {
    return (
      <div className="interview-page flex items-center justify-center min-h-screen">
        <div className="flex flex-col items-center gap-4 text-text-muted">
          <span className="typing-dot" />
          <p className="text-sm">Loading session…</p>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="interview-page flex items-center justify-center min-h-screen">
        <div className="text-center text-text-muted">
          <p>Session not found.</p>
          <button className="btn-primary mt-4" onClick={() => navigate("/interview")}>
            Back to sessions
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="interview-page flex h-screen overflow-hidden bg-bg">
      {/* Left nav pane */}
      <aside
        className="w-56 shrink-0 flex flex-col py-6 z-20"
        style={{
          background: "rgba(17,19,23,0.92)",
          backdropFilter: "blur(12px)",
          borderRight: "1px solid rgba(255,255,255,0.05)",
          height: "100vh",
        }}
      >
        <div className="px-5 mb-6">
          <button
            className="flex items-center gap-2 text-text-muted hover:text-text-primary transition-colors text-sm mb-4"
            onClick={() => navigate("/interview")}
          >
            <ArrowLeft className="w-4 h-4" /> Sessions
          </button>
          <p className="text-text-primary font-manrope font-light truncate text-base">
            {session.job_title}
          </p>
          <p className="text-text-muted text-sm truncate mt-0.5">{session.company_name}</p>
        </div>

        <nav className="flex-1 space-y-0.5">
          {NAV_ITEMS.map(({ id, label, icon: Icon }) => {
            const active = activeModule === id;
            return (
              <button
                key={id}
                onClick={() => switchModule(id)}
                className="w-full flex items-center px-6 py-3 text-sm transition-all text-left group"
                style={
                  active
                    ? { borderLeft: "2px solid rgba(198,198,199,0.6)", color: "#e2e2e8", background: "rgba(255,255,255,0.04)" }
                    : { borderLeft: "2px solid transparent", color: "rgba(198,198,199,0.4)" }
                }
              >
                <Icon className="w-4 h-4 mr-3 shrink-0" />
                <span className="font-manrope">{label}</span>
              </button>
            );
          })}
        </nav>
      </aside>

      {/* Right panel */}
      <main className="flex-1 min-w-0 overflow-y-auto px-6 py-8" style={{ height: "100vh" }}>
        <div
          key={activeModule}
          className="interview-panel-enter interview-panel-enter-active min-w-0 max-w-full"
          style={{ willChange: "transform" }}
        >
          {activeModule === "resume" && (
            <ResumePreview
              resumeText={resumeText}
              sessionId={session.id}
              onUpdate={(t) => setResumeText(t)}
            />
          )}
          {activeModule === "optimize" && (
            <ResumeOptimizer
              sessionId={session.id}
              hasGithub={!!session.github_url}
              onApply={(t) => setResumeText(t)}
            />
          )}
          {activeModule === "job" && <JobDetails session={session} />}
          {activeModule === "links" && <CompanyLinks session={session} />}
          {activeModule === "qa" && <InterviewQA sessionId={session.id} jobTitle={session.job_title} />}
          {activeModule === "github" && <GitHubRepos sessionId={session.id} githubUrl={session.github_url} />}
          {activeModule === "brainstorm" && <BrainstormChat sessionId={session.id} />}
        </div>
      </main>
    </div>
  );
}
