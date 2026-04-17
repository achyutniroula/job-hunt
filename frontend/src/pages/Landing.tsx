import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Search, Wifi, ChevronDown } from "lucide-react";
import toast from "react-hot-toast";
import ResumeDropzone from "@/components/ResumeDropzone";
import Spinner from "@/components/ui/Spinner";
import CitySelector from "@/components/CitySelector";
import DistanceSlider from "@/components/DistanceSlider";
import { startScrape } from "@/lib/api";
import { useAppStore } from "@/store/appStore";

const BOARD_GROUPS = [
  {
    label: "Job Boards",
    boards: ["linkedin", "indeed", "glassdoor", "ziprecruiter", "google", "eluta", "jobbank"],
  },
  {
    label: "Canadian Portals",
    description: "Direct ATS (Greenhouse · Lever · Ashby)",
    boards: ["canada-portals"],
  },
];

const ALL_BOARDS = [
  "linkedin", "indeed", "glassdoor", "ziprecruiter", "google", "eluta", "jobbank",
  "canada-portals",
];

const BOARD_LABELS: Record<string, string> = {
  linkedin: "LinkedIn", indeed: "Indeed", glassdoor: "Glassdoor",
  ziprecruiter: "ZipRecruiter", google: "Google Jobs",
  eluta: "Eluta.ca", jobbank: "JobBank.gc.ca",
  "canada-portals": "Canadian Portals",
};

const FADE_UP = {
  hidden: { opacity: 0, y: 24 },
  show:   { opacity: 1, y: 0 },
};

export default function Landing() {
  const navigate = useNavigate();
  const { setActiveSession } = useAppStore();

  const [keywords,       setKeywords]       = useState("");
  const [city,           setCity]           = useState("Toronto");
  const [cityProvince,   setCityProvince]   = useState("Ontario");
  const [distanceKm,     setDistanceKm]     = useState(100);
  const [remoteOnly,     setRemoteOnly]     = useState(false);
  const [selectedBoards, setSelectedBoards] = useState<string[]>(ALL_BOARDS);
  const [showBoards,     setShowBoards]     = useState(false);
  const [loading,        setLoading]        = useState(false);

  const toggleBoard = (b: string) => {
    if (selectedBoards.includes(b) && selectedBoards.length === 1) return;
    setSelectedBoards(prev => prev.includes(b) ? prev.filter(x => x !== b) : [...prev, b]);
  };

  const handleSearch = async () => {
    if (!keywords.trim()) { toast.error("Enter a job title or keywords"); return; }
    if (selectedBoards.length === 0) { toast.error("Select at least one job board"); return; }
    setLoading(true);
    try {
      const resolvedLocation = remoteOnly ? "Canada" : `${city}, ${cityProvince}, Canada`;
      const session = await startScrape({
        keywords: keywords.trim(),
        location: resolvedLocation,
        remote_only: remoteOnly,
        boards: selectedBoards,
        city: remoteOnly ? undefined : city,
        distance_km: remoteOnly ? undefined : distanceKm,
      });
      setActiveSession(session);
      navigate(`/dashboard/${session.id}`);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to start search");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen pt-20 pb-16 px-8 flex items-center justify-center">
      <div className="w-full max-w-6xl">
        <div className="grid grid-cols-1 md:grid-cols-[55fr_45fr] gap-12 items-start">

          {/* ── LEFT: Hero + feature chips ─────────────────────────────── */}
          <motion.div
            className="space-y-10"
            variants={{ show: { transition: { staggerChildren: 0.1 } } }}
            initial="hidden" animate="show"
          >
            <motion.div variants={FADE_UP}>
              <span className="badge mb-5 inline-flex">
                7 job boards + Canadian portals · AI-powered matching
              </span>
              <h1 className="font-manrope font-light text-5xl sm:text-6xl text-text-primary leading-tight mt-4 tracking-tight section-glow">
                Find jobs that<br />
                <span className="rgb-text-gradient font-normal">actually fit.</span>
              </h1>
              <p className="text-text-secondary text-xl mt-6 leading-relaxed font-light max-w-lg">
                Scrape LinkedIn, Indeed, Glassdoor and more — plus Canadian company portals on Greenhouse, Lever, and Ashby — all at once.
                Upload your resume and get AI match scores and grades for every result.
              </p>
            </motion.div>

            <motion.div variants={FADE_UP} className="flex flex-wrap gap-2">
              {["Semantic match scoring", "ATS optimization", "Human cover letters", "Real-time scraping"].map(f => (
                <span key={f} className="badge text-[11px]">{f}</span>
              ))}
            </motion.div>
          </motion.div>

          {/* ── RIGHT: Search form + resume upload ─────────────────────── */}
          <motion.div
            className="space-y-4"
            variants={{ show: { transition: { staggerChildren: 0.1 } } }}
            initial="hidden" animate="show"
          >
            <motion.div variants={FADE_UP} className="glass-card-static p-6 space-y-4">
              {/* Keywords */}
              <div>
                <label className="text-[10px] font-manrope font-semibold text-text-muted uppercase tracking-[0.15em] mb-2 block">
                  Job title / keywords
                </label>
                <div className="relative">
                  <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <input
                    type="text"
                    className="input-base pl-10"
                    placeholder="e.g. Senior React Developer, Data Scientist"
                    value={keywords}
                    onChange={e => setKeywords(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && handleSearch()}
                  />
                </div>
              </div>

              {/* Remote toggle */}
              <div className="flex justify-end">
                <button
                  onClick={() => setRemoteOnly(v => !v)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-inter transition-all duration-200 ${
                    remoteOnly ? "text-success" : "text-text-muted hover:text-text-secondary"
                  }`}
                  style={{
                    background: remoteOnly ? "rgba(74,222,128,0.08)" : "rgba(255,255,255,0.04)",
                    border: `1px solid ${remoteOnly ? "rgba(74,222,128,0.25)" : "rgba(68,71,72,0.5)"}`,
                  }}
                >
                  <Wifi className="w-4 h-4" />
                  Remote only
                </button>
              </div>

              {/* City selector */}
              <CitySelector
                city={remoteOnly ? "Remote" : city}
                onChange={(c, p) => { setCity(c); setCityProvince(p); }}
              />

              {/* Distance slider */}
              <DistanceSlider
                value={distanceKm}
                onChange={setDistanceKm}
                disabled={remoteOnly || city === "Remote"}
              />

              {/* Board picker — dropdown */}
              <div className="relative">
                <button
                  onClick={() => setShowBoards(v => !v)}
                  className="w-full flex items-center justify-between input-base text-left"
                >
                  <span className="text-sm text-text-secondary">
                    {selectedBoards.length === ALL_BOARDS.length
                      ? "All sources (7 boards + Canadian portals)"
                      : `${selectedBoards.length} source${selectedBoards.length !== 1 ? "s" : ""} selected`}
                  </span>
                  <ChevronDown className={`w-4 h-4 text-text-muted transition-transform ${showBoards ? "rotate-180" : ""}`} />
                </button>
                {showBoards && (
                  <div className="absolute z-20 mt-1 w-full rounded-xl p-3 space-y-3"
                    style={{ background: "#16181c", border: "1px solid rgba(68,71,72,0.5)" }}>
                    {BOARD_GROUPS.map(group => (
                      <div key={group.label}>
                        <p className="text-[9px] font-manrope uppercase tracking-widest text-text-dim mb-1.5">
                          {group.label}
                          {group.description && <span className="ml-1 normal-case tracking-normal opacity-60">{group.description}</span>}
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {group.boards.map(b => (
                            <button
                              key={b}
                              onClick={() => toggleBoard(b)}
                              className="badge cursor-pointer transition-all"
                              style={selectedBoards.includes(b) ? {
                                background: "rgba(110,231,183,0.1)",
                                color: "#6ee7b7",
                                border: "1px solid rgba(110,231,183,0.3)",
                              } : {}}
                            >
                              {BOARD_LABELS[b]}
                            </button>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <button
                className="btn-primary w-full text-sm py-3"
                onClick={handleSearch}
                disabled={loading}
              >
                {loading ? (
                  <><Spinner size="sm" />Starting search…</>
                ) : (
                  <><Search className="w-4 h-4" />Search {selectedBoards.length === ALL_BOARDS.length ? "all sources" : `${selectedBoards.length} source${selectedBoards.length !== 1 ? "s" : ""}`}</>
                )}
              </button>
            </motion.div>

            {/* Resume Upload */}
            <motion.div variants={FADE_UP}>
              <p className="text-[10px] font-manrope font-semibold text-text-muted uppercase tracking-[0.15em] mb-3">
                Upload your resume for AI matching (optional but recommended)
              </p>
              <ResumeDropzone />
            </motion.div>
          </motion.div>

        </div>
      </div>
    </main>
  );
}
