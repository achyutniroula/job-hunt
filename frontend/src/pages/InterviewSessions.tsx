import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, Trash2, ExternalLink, BriefcaseBusiness } from "lucide-react";
import toast from "react-hot-toast";
import { listInterviewSessions, deleteInterviewSession } from "@/lib/api";

interface SessionSummary {
  id: string;
  job_title: string;
  company_name: string;
  created_at: string;
}

export default function InterviewSessions() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    listInterviewSessions()
      .then(setSessions)
      .catch(() => toast.error("Failed to load sessions"))
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this interview session and all its data?")) return;
    setDeleting(id);
    try {
      await deleteInterviewSession(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
      toast.success("Session deleted");
    } catch {
      toast.error("Failed to delete session");
    } finally {
      setDeleting(null);
    }
  };

  return (
    <main className="pt-20 pb-16 px-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <BriefcaseBusiness className="w-5 h-5 text-text-muted" />
          <h1 className="font-manrope font-light text-2xl text-text-primary">Job Module</h1>
        </div>
        <button
          className="btn-primary flex items-center gap-2 text-sm px-4 py-2"
          onClick={() => navigate("/interview/new")}
        >
          <Plus className="w-4 h-4" />
          New Session
        </button>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="skeleton h-16 rounded-lg" />
          ))}
        </div>
      ) : sessions.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <BriefcaseBusiness className="w-10 h-10 text-text-muted mx-auto mb-4" />
          <p className="text-text-secondary font-light text-lg mb-6">No interview sessions yet</p>
          <button
            className="btn-primary px-6 py-2.5"
            onClick={() => navigate("/interview/new")}
          >
            Start your first session
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {sessions.map((s) => (
            <div key={s.id} className="glass-card p-5 flex items-center justify-between gap-4">
              <div className="flex-1 min-w-0">
                <p className="font-manrope font-medium text-text-primary truncate">{s.job_title}</p>
                <p className="text-text-muted text-sm mt-0.5">{s.company_name}</p>
                <p className="text-text-muted text-xs mt-1">
                  {new Date(s.created_at).toLocaleDateString("en-CA", {
                    year: "numeric",
                    month: "short",
                    day: "numeric",
                  })}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <button
                  className="btn-ghost flex items-center gap-1.5 text-sm px-3 py-1.5"
                  onClick={() => navigate(`/interview/${s.id}`)}
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  Open
                </button>
                <button
                  className="p-2 rounded-lg transition-colors text-text-muted hover:text-danger"
                  style={{ background: "transparent" }}
                  onClick={() => handleDelete(s.id)}
                  disabled={deleting === s.id}
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
