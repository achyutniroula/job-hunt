interface ScoreRingProps {
  score: number | null;
  size?: number;
}

export default function ScoreRing({ score, size = 52 }: ScoreRingProps) {
  if (score === null || score === undefined) {
    return (
      <div
        className="flex items-center justify-center rounded-full text-text-muted font-manrope text-xs"
        style={{ width: size, height: size, background: "rgba(30,32,36,0.8)", border: "1px solid rgba(68,71,72,0.3)" }}
      >
        —
      </div>
    );
  }

  const radius = (size - 6) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;

  // Semantic: silver-gray (high) → amber (mid) → soft red (low)
  const color =
    score >= 70 ? "#c6c6c7" :
    score >= 45 ? "#ffc87c" :
                  "#f87171";

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="rgba(68,71,72,0.3)" strokeWidth={3} />
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke={color} strokeWidth={3}
          strokeDasharray={circumference} strokeDashoffset={circumference - progress} strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.6s ease-out", filter: `drop-shadow(0 0 3px ${color}60)` }} />
      </svg>
      <span className="absolute font-manrope font-light" style={{ fontSize: size * 0.22, color }}>
        {Math.round(score)}
      </span>
    </div>
  );
}
