export interface Job {
  id: string;
  session_id: string;
  title: string;
  company: string | null;
  location: string | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string | null;
  salary_interval: string | null;
  description: string | null;
  skills: string[];
  seniority_level: string | null;
  employment_type: string | null;
  is_remote: boolean;
  board: string;
  job_url: string | null;
  posted_at: string | null;
  match_score: number | null;
  created_at: string;
}

export interface ScrapeSession {
  id: string;
  keywords: string;
  location: string;
  remote_only: boolean;
  boards: string[] | null;
  status: "pending" | "running" | "done" | "failed";
  job_count: number;
  error: string | null;
  resume_filename: string | null;
  created_at: string;
  finished_at: string | null;
}

export interface ParsedResume {
  raw_text: string;
  skills: string[];
  tech_stack: string[];
  soft_skills: string[];
  experience_years: number | null;
  seniority_level: string | null;
  job_titles: string[];
  education: string[];
  certifications: string[];
  languages: string[];
}

export interface ResumeUploadResponse {
  filename: string;
  parsed: ParsedResume;
}

export interface ChangeItem {
  category: "verb" | "keyword" | "title" | "skill" | "metric" | "reframe" | "removed" | "restructure";
  text: string;
}

export interface ATSOptimizeResponse {
  original_text: string;
  optimized_text: string;
  latex_text: string | null;
  changes_summary: string[];
  change_items: ChangeItem[];
  ats_score_before: number | null;
  ats_score_after: number | null;
  matched_keywords: string[];
  missing_keywords: string[];
  improvements: string[];
  transparency_report: string;
  interview_prep: string;
  gap_analysis: string;
  linkedin_unavailable: boolean;
}

export interface FetchUrlResponse {
  title: string | null;
  company: string | null;
  description: string;
  source: string;
}

export interface CoverLetterResponse {
  cover_letter: string;
  word_count: number;
}

export interface ScrapeRequest {
  keywords: string;
  location: string;
  remote_only: boolean;
  boards?: string[] | null;
  city?: string;
  distance_km?: number;
}
