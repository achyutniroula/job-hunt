import axios from "axios";
import type {
  ATSOptimizeResponse,
  CoverLetterResponse,
  FetchUrlResponse,
  Job,
  ParsedResume,
  ResumeUploadResponse,
  ScrapeRequest,
  ScrapeSession,
} from "@/types";

const api = axios.create({
  baseURL: "/api",
  timeout: 120_000, // scraping can take a while
});

// ── Jobs ──────────────────────────────────────────────────────────────────────

export const startScrape = (body: ScrapeRequest): Promise<ScrapeSession> =>
  api.post("/jobs/scrape", body).then((r) => r.data);

export const getSession = (sessionId: string): Promise<ScrapeSession> =>
  api.get(`/jobs/session/${sessionId}`).then((r) => r.data);

export const getJobs = (
  sessionId: string,
  params?: {
    min_score?: number;
    remote_only?: boolean;
    boards?: string;
    seniority?: string;
    sort_by?: "match_score" | "posted_at";
    limit?: number;
    offset?: number;
  }
): Promise<Job[]> =>
  api.get(`/jobs/${sessionId}`, { params }).then((r) => r.data);

export const matchJobsToResume = (
  sessionId: string,
  resumeFilename: string
): Promise<Job[]> =>
  api
    .post(`/jobs/${sessionId}/match`, null, {
      params: { resume_filename: resumeFilename },
    })
    .then((r) => r.data);

export const getJob = (jobId: string): Promise<Job> =>
  api.get(`/jobs/detail/${jobId}`).then((r) => r.data);

// ── Resume ────────────────────────────────────────────────────────────────────

export const uploadResume = (file: File): Promise<ResumeUploadResponse> => {
  const form = new FormData();
  form.append("file", file);
  return api
    .post("/resume/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then((r) => r.data);
};

export const getParsedResume = (filename: string): Promise<ParsedResume> =>
  api.get(`/resume/${filename}/parsed`).then((r) => r.data);

// ── Generate ──────────────────────────────────────────────────────────────────

export const optimizeResume = (body: {
  resume_filename: string;
  job_id?: string;
  job_description?: string;
  previous_optimized?: string;
  previous_improvements?: string[];
  github_urls?: string[];
  linkedin_url?: string;
}): Promise<ATSOptimizeResponse> =>
  api.post("/generate/optimize", body).then((r) => r.data);

export const generateCoverLetter = (body: {
  resume_filename: string;
  job_id?: string;
  job_description?: string;
  company_name?: string;
  job_title?: string;
  extra_notes?: string;
}): Promise<CoverLetterResponse> =>
  api.post("/generate/cover-letter", body).then((r) => r.data);

export const fetchJobUrl = (url: string): Promise<FetchUrlResponse> =>
  api.post("/generate/fetch-url", { url }).then((r) => r.data);

export const downloadCoverLetterDocx = (text: string, company: string): Promise<Blob> =>
  api
    .post("/generate/cover-letter-docx", { text, company }, { responseType: "blob" })
    .then((r) => r.data);

// ── Interview ─────────────────────────────────────────────────────────────────

export const createInterviewSession = (body: {
  job_title: string;
  job_description: string;
  company_name: string;
  resume_text: string;
  github_url?: string;
  salary_info?: string;
  location?: string;
  seniority?: string;
}) => api.post("/interview/session", body).then((r) => r.data);

export const getInterviewGitHub = (sessionId: string) =>
  api.get(`/interview/session/${sessionId}/github`).then((r) => r.data);

export const explainGitHubRepo = (sessionId: string, repoName: string) =>
  api.get(`/interview/session/${sessionId}/github/${repoName}/explain`).then((r) => r.data);

export const getInterviewSession = (sessionId: string) =>
  api.get(`/interview/session/${sessionId}`).then((r) => r.data);

export const listInterviewSessions = () =>
  api.get("/interview/sessions").then((r) => r.data);

export const deleteInterviewSession = (sessionId: string) =>
  api.delete(`/interview/session/${sessionId}`).then((r) => r.data);

export const updateSessionResume = (sessionId: string, resume_text: string) =>
  api.patch(`/interview/session/${sessionId}/resume`, { resume_text }).then((r) => r.data);

export const optimizeSessionResume = (sessionId: string) =>
  api.post(`/interview/session/${sessionId}/optimize`, {}).then((r) => r.data);

export const getSessionOptimizeResult = (sessionId: string) =>
  api.get(`/interview/session/${sessionId}/optimize`).then((r) => r.data);

export const getInterviewQA = (sessionId: string) =>
  api.get(`/interview/session/${sessionId}/qa`).then((r) => r.data);

export const sendInterviewChat = (sessionId: string, message: string) =>
  api.post(`/interview/${sessionId}/chat`, { message }).then((r) => r.data);

export const getInterviewChat = (sessionId: string) =>
  api.get(`/interview/${sessionId}/chat`).then((r) => r.data);

export const deleteInterviewChatMessage = (sessionId: string, messageId: string) =>
  api.delete(`/interview/${sessionId}/chat/${messageId}`).then((r) => r.data);

export const clearInterviewChat = (sessionId: string) =>
  api.delete(`/interview/${sessionId}/chat`).then((r) => r.data);

export const createBrainstormThread = (sessionId: string, title: string) =>
  api.post(`/interview/${sessionId}/brainstorm/thread`, { title }).then((r) => r.data);

export const listBrainstormThreads = (sessionId: string) =>
  api.get(`/interview/${sessionId}/brainstorm/threads`).then((r) => r.data);

export const renameBrainstormThread = (sessionId: string, threadId: string, title: string) =>
  api.patch(`/interview/${sessionId}/brainstorm/thread/${threadId}`, { title }).then((r) => r.data);

export const deleteBrainstormThread = (sessionId: string, threadId: string) =>
  api.delete(`/interview/${sessionId}/brainstorm/thread/${threadId}`).then((r) => r.data);

export const sendBrainstormMessage = (sessionId: string, threadId: string, message: string) =>
  api
    .post(`/interview/${sessionId}/brainstorm/thread/${threadId}/message`, { message })
    .then((r) => r.data);

export const getBrainstormMessages = (sessionId: string, threadId: string) =>
  api.get(`/interview/${sessionId}/brainstorm/thread/${threadId}/messages`).then((r) => r.data);

export default api;
