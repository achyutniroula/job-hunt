// Board badges use tonal shifts within the Obsidian Ether palette — no bright neons

const STATIC_COLORS: Record<string, { bg: string; color: string; border: string }> = {
  linkedin:     { bg: "rgba(124,208,255,0.07)", color: "#7cd0ff", border: "rgba(124,208,255,0.2)" },
  indeed:       { bg: "rgba(214,186,255,0.07)", color: "#d6baff", border: "rgba(214,186,255,0.2)" },
  glassdoor:    { bg: "rgba(74,222,128,0.07)",  color: "#4ade80", border: "rgba(74,222,128,0.2)"  },
  ziprecruiter: { bg: "rgba(255,200,124,0.07)", color: "#ffc87c", border: "rgba(255,200,124,0.2)" },
  google:       { bg: "rgba(248,113,113,0.07)", color: "#f87171", border: "rgba(248,113,113,0.2)" },
  eluta:        { bg: "rgba(255,200,124,0.07)", color: "#ffc87c", border: "rgba(255,200,124,0.2)" },
  jobbank:      { bg: "rgba(214,186,255,0.07)", color: "#d6baff", border: "rgba(214,186,255,0.2)" },
};

// Canadian portal ATS types get a distinct teal/mint style
const ATS_COLORS: Record<string, { bg: string; color: string; border: string; ats: string }> = {
  greenhouse: { bg: "rgba(52,211,153,0.07)", color: "#34d399", border: "rgba(52,211,153,0.2)",  ats: "Greenhouse" },
  lever:      { bg: "rgba(167,139,250,0.07)", color: "#a78bfa", border: "rgba(167,139,250,0.2)", ats: "Lever" },
  ashby:      { bg: "rgba(251,191,36,0.07)",  color: "#fbbf24", border: "rgba(251,191,36,0.2)",  ats: "Ashby" },
  custom:     { bg: "rgba(156,163,175,0.07)", color: "#9ca3af", border: "rgba(156,163,175,0.2)", ats: "Direct" },
};

const STATIC_LABELS: Record<string, string> = {
  linkedin: "LinkedIn", indeed: "Indeed", glassdoor: "Glassdoor",
  ziprecruiter: "ZipRecruiter", google: "Google Jobs",
  eluta: "Eluta.ca", jobbank: "JobBank",
};

export default function BoardBadge({ board }: { board: string }) {
  // Handle "ats:CompanyName" format from Canadian portal scanner
  const colonIdx = board.indexOf(":");
  if (colonIdx !== -1) {
    const atsKey = board.slice(0, colonIdx);
    const companyName = board.slice(colonIdx + 1);
    const atsStyle = ATS_COLORS[atsKey];
    if (atsStyle) {
      return (
        <span
          className="badge flex items-center gap-1"
          style={{ background: atsStyle.bg, color: atsStyle.color, border: `1px solid ${atsStyle.border}` }}
          title={`Posted via ${atsStyle.ats}`}
        >
          {companyName}
          <span style={{ opacity: 0.55, fontSize: "0.65em" }}>· {atsStyle.ats}</span>
        </span>
      );
    }
  }

  // Standard job boards
  const style = STATIC_COLORS[board];
  return (
    <span
      className="badge"
      style={style ? { background: style.bg, color: style.color, border: `1px solid ${style.border}` } : {}}
    >
      {STATIC_LABELS[board] ?? board}
    </span>
  );
}
