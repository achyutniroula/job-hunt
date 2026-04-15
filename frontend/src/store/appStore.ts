import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { ATSOptimizeResponse, CoverLetterResponse, Job, ParsedResume, ScrapeSession } from "@/types";

interface AppState {
  // Resume
  resumeFilename: string | null;
  parsedResume: ParsedResume | null;
  setResume: (filename: string, parsed: ParsedResume) => void;
  clearResume: () => void;

  // Active session
  activeSession: ScrapeSession | null;
  setActiveSession: (s: ScrapeSession | null) => void;

  // Selected job
  selectedJobId: string | null;
  setSelectedJobId: (id: string | null) => void;
  selectedJob: Job | null;
  setSelectedJob: (job: Job | null) => void;

  // Optimize results
  optimizeResult: ATSOptimizeResponse | null;
  setOptimizeResult: (r: ATSOptimizeResponse | null) => void;
  optimizePassNum: number;
  setOptimizePassNum: (n: number) => void;

  // Cover letter results
  coverLetterResult: CoverLetterResponse | null;
  setCoverLetterResult: (r: CoverLetterResponse | null) => void;
  coverLetterEdited: string;
  setCoverLetterEdited: (s: string) => void;

  // Interview prep
  activeInterviewSessionId: string | null;
  setActiveInterviewSession: (id: string | null) => void;
  activeBrainstormThreadId: string | null;
  setActiveBrainstormThread: (id: string | null) => void;
  interviewNavModule: "resume" | "job" | "links" | "qa" | "github" | "brainstorm" | "optimize";
  setInterviewNavModule: (m: "resume" | "job" | "links" | "qa" | "github" | "brainstorm" | "optimize") => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      resumeFilename: null,
      parsedResume: null,
      setResume: (filename, parsed) => set({ resumeFilename: filename, parsedResume: parsed }),
      clearResume: () => set({ resumeFilename: null, parsedResume: null }),

      activeSession: null,
      setActiveSession: (s) => set({ activeSession: s }),

      selectedJobId: null,
      setSelectedJobId: (id) => set({ selectedJobId: id }),
      selectedJob: null,
      setSelectedJob: (job) => set({ selectedJob: job }),

      optimizeResult: null,
      setOptimizeResult: (r) => set({ optimizeResult: r }),
      optimizePassNum: 1,
      setOptimizePassNum: (n) => set({ optimizePassNum: n }),

      coverLetterResult: null,
      setCoverLetterResult: (r) => set({ coverLetterResult: r }),
      coverLetterEdited: "",
      setCoverLetterEdited: (s) => set({ coverLetterEdited: s }),

      activeInterviewSessionId: null,
      setActiveInterviewSession: (id) => set({ activeInterviewSessionId: id }),
      activeBrainstormThreadId: null,
      setActiveBrainstormThread: (id) => set({ activeBrainstormThreadId: id }),
      interviewNavModule: "qa",
      setInterviewNavModule: (m) => set({ interviewNavModule: m }),
    }),
    {
      name: "jobhunt-store",
      partialize: (state) => ({
        resumeFilename: state.resumeFilename,
        parsedResume: state.parsedResume,
        selectedJob: state.selectedJob,
        optimizeResult: state.optimizeResult,
        optimizePassNum: state.optimizePassNum,
        coverLetterResult: state.coverLetterResult,
        coverLetterEdited: state.coverLetterEdited,
      }),
    }
  )
);
