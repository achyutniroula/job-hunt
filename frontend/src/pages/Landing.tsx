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

const ALL_BOARDS = ["linkedin", "indeed", "glassdoor", "ziprecruiter", "google", "eluta", "jobbank"];

const BOARD_LABELS: Record<string, string> = {
  linkedin: "LinkedIn", indeed: "Indeed", glassdoor: "Glassdoor",
  ziprecruiter: "ZipRecruiter", google: "Google Jobs",
  eluta: "Eluta.ca", jobbank: "JobBank.gc.ca",
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
  const [showBoardPicker,setShowBoardPicker]= useState(false);
  const [loading,        setLoading]        = useState(false);

  const toggleBoard = (b: string) =>
    setSelectedBoards(prev => prev.includes(b) ? prev.filter(x => x !== b) : [...prev, b]);

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
    <main className="min-h-screen pt-24 pb-16 px-6 flex items-start justify-center">
      <motion.div
        className="w-full max-w-xl"
        variants={{ show: { transition: { staggerChildren: 0.1 } } }}
        initial="hidden"
        animate="show"
      >
        {/* Hero */}
        <motion.div variants={FADE_UP} className="text-center mb-10">
          <span className="badge mb-6 inline-flex">
            7 Canadian job boards · AI-powered matching
          </span>
          <h1 className="font-manrope font-light text-5xl sm:text-6xl text-text-primary leading-tight mt-4 tracking-tight section-glow">
            Find jobs that<br />
            <span className="rgb-text-gradient font-normal">actually fit.</span>
          </h1>
          <p className="text-text-secondary text-base mt-5 leading-relaxed max-w-md mx-auto font-light">
            Scrape LinkedIn, Indeed, Glassdoor and more — all at once.
            Upload your resume and get AI match scores for every result.
          </p>
        </motion.div>

        {/* Search Form */}
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

          {/* Board picker */}
          <div>
            <button
              onClick={() => setShowBoardPicker(v => !v)}
              className="flex items-center gap-2 text-xs text-text-muted hover:text-text-secondary transition-colors font-manrope tracking-wide"
            >
              <span>
                {selectedBoards.length === ALL_BOARDS.length
                  ? "All 7 boards selected"
                  : `${selectedBoards.length} board${selectedBoards.length !== 1 ? "s" : ""} selected`}
              </span>
              <ChevronDown className={`w-3.5 h-3.5 transition-transform ${showBoardPicker ? "rotate-180" : ""}`} />
            </button>

            {showBoardPicker && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                className="flex flex-wrap gap-2 mt-3"
              >
                {ALL_BOARDS.map(b => (
                  <button
                    key={b}
                    onClick={() => toggleBoard(b)}
                    className="badge cursor-pointer transition-all hover:border-[rgba(198,198,199,0.3)] hover:text-text-primary"
                    style={selectedBoards.includes(b) ? {
                      background: "rgba(198,198,199,0.1)",
                      color: "#e2e2e8",
                      border: "1px solid rgba(198,198,199,0.25)",
                    } : {}}
                  >
                    {BOARD_LABELS[b]}
                  </button>
                ))}
              </motion.div>
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
              <><Search className="w-4 h-4" />Search {selectedBoards.length} boards</>
            )}
          </button>
        </motion.div>

        {/* Resume Upload */}
        <motion.div variants={FADE_UP} className="mt-5">
          <p className="text-[10px] font-manrope font-semibold text-text-muted uppercase tracking-[0.15em] mb-3">
            Upload your resume for AI matching (optional but recommended)
          </p>
          <ResumeDropzone />
        </motion.div>

        {/* Feature chips */}
        <motion.div variants={FADE_UP} className="flex flex-wrap justify-center gap-2 mt-8">
          {["Semantic match scoring", "ATS optimization", "Human cover letters", "Real-time scraping"].map(f => (
            <span key={f} className="badge text-[11px]">{f}</span>
          ))}
        </motion.div>
      </motion.div>
    </main>
  );
}
