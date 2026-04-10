const PRESETS = [25, 50, 100, 250, 500];

interface Props {
  value: number;
  onChange: (km: number) => void;
  disabled?: boolean;
}

export default function DistanceSlider({ value, onChange, disabled = false }: Props) {
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <label className="text-[10px] font-manrope font-semibold text-text-muted uppercase tracking-[0.15em]">
          Radius
        </label>
        <span className="text-[10px] text-text-secondary font-inter">
          {disabled ? "Remote — distance not applicable" : `${value} km`}
        </span>
      </div>

      {!disabled && (
        <>
          <input
            type="range"
            min={25}
            max={500}
            step={25}
            value={value}
            onChange={(e) => onChange(Number(e.target.value))}
            className="w-full h-1 rounded-full appearance-none cursor-pointer"
            style={{ accentColor: "#7cd0ff" }}
          />
          <div className="flex gap-1.5 mt-2">
            {PRESETS.map((km) => (
              <button
                key={km}
                onClick={() => onChange(km)}
                className="flex-1 text-[10px] py-1 rounded font-inter transition-all"
                style={
                  value === km
                    ? { background: "rgba(124,208,255,0.12)", color: "#7cd0ff", border: "1px solid rgba(124,208,255,0.25)" }
                    : { background: "rgba(255,255,255,0.03)", color: "#6b6e72", border: "1px solid rgba(68,71,72,0.4)" }
                }
              >
                {km >= 1000 ? `${km / 1000}k` : km}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
