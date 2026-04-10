import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Job, ParsedResume, ScrapeSession } from "@/types";

interface AppState {
  // Resume
  resumeFilename: string | null;
  parsedResume: ParsedResume | null;
  setResume: (filename: string, parsed: ParsedResume) => void;
  clearResume: () => void;

  // Active session
  activeSession: ScrapeSession | null;
  setActiveSession: (s: ScrapeSession | null) => void;

  // Selected job (for optimize / cover letter)
  selectedJobId: string | null;
  setSelectedJobId: (id: string | null) => void;

  // Full selected job object (for context display)
  selectedJob: Job | null;
  setSelectedJob: (job: Job | null) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      resumeFilename: null,
      parsedResume: null,
      setResume: (filename, parsed) =>
        set({ resumeFilename: filename, parsedResume: parsed }),
      clearResume: () => set({ resumeFilename: null, parsedResume: null }),

      activeSession: null,
      setActiveSession: (s) => set({ activeSession: s }),

      selectedJobId: null,
      setSelectedJobId: (id) => set({ selectedJobId: id }),

      selectedJob: null,
      setSelectedJob: (job) => set({ selectedJob: job }),
    }),
    {
      name: "jobhunt-store",
      partialize: (state) => ({
        resumeFilename: state.resumeFilename,
        parsedResume: state.parsedResume,
        selectedJob: state.selectedJob,
      }),
    }
  )
);
