// Board badges use tonal shifts within the Obsidian Ether palette — no bright neons
const BOARD_COLORS: Record<string, { bg: string; color: string; border: string }> = {
  linkedin:     { bg: "rgba(124,208,255,0.07)", color: "#7cd0ff", border: "rgba(124,208,255,0.2)" },
  indeed:       { bg: "rgba(214,186,255,0.07)", color: "#d6baff", border: "rgba(214,186,255,0.2)" },
  glassdoor:    { bg: "rgba(74,222,128,0.07)",  color: "#4ade80", border: "rgba(74,222,128,0.2)"  },
  ziprecruiter: { bg: "rgba(255,200,124,0.07)", color: "#ffc87c", border: "rgba(255,200,124,0.2)" },
  google:       { bg: "rgba(248,113,113,0.07)", color: "#f87171", border: "rgba(248,113,113,0.2)" },
  eluta:        { bg: "rgba(255,200,124,0.07)", color: "#ffc87c", border: "rgba(255,200,124,0.2)" },
  jobbank:      { bg: "rgba(214,186,255,0.07)", color: "#d6baff", border: "rgba(214,186,255,0.2)" },
};

const BOARD_LABELS: Record<string, string> = {
  linkedin: "LinkedIn", indeed: "Indeed", glassdoor: "Glassdoor",
  ziprecruiter: "ZipRecruiter", google: "Google Jobs",
  eluta: "Eluta.ca", jobbank: "JobBank",
};

export default function BoardBadge({ board }: { board: string }) {
  const style = BOARD_COLORS[board];
  return (
    <span
      className="badge"
      style={style ? {
        background: style.bg,
        color: style.color,
        border: `1px solid ${style.border}`,
      } : {}}
    >
      {BOARD_LABELS[board] ?? board}
    </span>
  );
}
