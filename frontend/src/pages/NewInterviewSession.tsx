import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Loader2 } from "lucide-react";
import toast from "react-hot-toast";
import { createInterviewSession } from "@/lib/api";
import { useAppStore } from "@/store/appStore";

export default function NewInterviewSession() {
  const navigate = useNavigate();
  const { optimizeResult, parsedResume } = useAppStore();

  const [jobTitle, setJobTitle] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [resumeText, setResumeText] = useState(
    optimizeResult?.optimized_text ?? parsedResume?.raw_text ?? ""
  );
  const [githubUrl, setGithubUrl] = useState(parsedResume?.raw_text ? "" : "");
  const [salaryInfo, setSalaryInfo] = useState("");
  const [location, setLocation] = useState("");
  const [seniority, setSeniority] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!jobTitle.trim() || !jobDescription.trim() || !companyName.trim()) {
      toast.error("Job title, description, and company are required");
      return;
    }
    setSubmitting(true);
    try {
      const session = await createInterviewSession({
        job_title: jobTitle.trim(),
        job_description: jobDescription.trim(),
        company_name: companyName.trim(),
        resume_text: resumeText.trim(),
        github_url: githubUrl.trim() || undefined,
        salary_info: salaryInfo.trim() || undefined,
        location: location.trim() || undefined,
        seniority: seniority.trim() || undefined,
      });
      toast.success("Session created — generating Q&A in background");
      navigate(`/interview/${session.id}`);
    } catch {
      toast.error("Failed to create session");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="interview-page min-h-screen py-10 px-6 max-w-3xl mx-auto">
      <button
        className="flex items-center gap-2 text-text-muted hover:text-text-primary transition-colors text-sm mb-8"
        onClick={() => navigate("/interview")}
      >
        <ArrowLeft className="w-4 h-4" /> Back
      </button>

      <h1 className="font-manrope font-light text-text-primary mb-8">New Interview Session</h1>

      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div>
            <label className="block text-text-muted text-sm mb-1.5">Job Title *</label>
            <input
              className="input-base w-full"
              placeholder="e.g. Senior Software Engineer"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block text-text-muted text-sm mb-1.5">Company *</label>
            <input
              className="input-base w-full"
              placeholder="e.g. Acme Corp"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block text-text-muted text-sm mb-1.5">Location</label>
            <input
              className="input-base w-full"
              placeholder="e.g. Toronto, ON"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-text-muted text-sm mb-1.5">Seniority</label>
            <input
              className="input-base w-full"
              placeholder="e.g. Mid, Senior"
              value={seniority}
              onChange={(e) => setSeniority(e.target.value)}
            />
          </div>
          <div className="sm:col-span-2">
            <label className="block text-text-muted text-sm mb-1.5">Salary Info</label>
            <input
              className="input-base w-full"
              placeholder="e.g. $90,000 – $120,000"
              value={salaryInfo}
              onChange={(e) => setSalaryInfo(e.target.value)}
            />
          </div>
          <div className="sm:col-span-2">
            <label className="block text-text-muted text-sm mb-1.5">
              GitHub Profile
              <span className="ml-2 text-xs text-text-muted opacity-60">(optional — adds repo context to chat)</span>
            </label>
            <input
              className="input-base w-full"
              placeholder="e.g. https://github.com/username or just username"
              value={githubUrl}
              onChange={(e) => setGithubUrl(e.target.value)}
            />
          </div>
        </div>

        <div>
          <label className="block text-text-muted text-sm mb-1.5">Job Description *</label>
          <textarea
            className="input-base w-full resize-y"
            rows={8}
            placeholder="Paste the full job description here…"
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            required
          />
        </div>

        <div>
          <label className="block text-text-muted text-sm mb-1.5">
            Resume Text
            {optimizeResult?.optimized_text && (
              <span className="ml-2 text-xs text-success">(pre-filled from optimizer)</span>
            )}
          </label>
          <textarea
            className="input-base w-full resize-y"
            rows={8}
            placeholder="Paste your resume text here…"
            value={resumeText}
            onChange={(e) => setResumeText(e.target.value)}
          />
        </div>

        <button
          type="submit"
          className="btn-primary py-3 flex items-center justify-center gap-2"
          disabled={submitting}
        >
          {submitting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Creating session…
            </>
          ) : (
            "Create Session"
          )}
        </button>
      </form>
    </div>
  );
}
