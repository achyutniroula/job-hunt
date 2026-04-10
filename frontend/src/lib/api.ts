import axios from "axios";
import type {
  ATSOptimizeResponse,
  CoverLetterResponse,
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

export default api;
