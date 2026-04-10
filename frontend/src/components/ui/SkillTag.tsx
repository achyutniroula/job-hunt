interface SkillTagProps {
  label: string;
  highlighted?: boolean;
}

export default function SkillTag({ label, highlighted = false }: SkillTagProps) {
  return (
    <span
      className="badge"
      style={highlighted ? {
        background: "rgba(198,198,199,0.1)",
        color: "#e2e2e8",
        border: "1px solid rgba(198,198,199,0.25)",
      } : {}}
    >
      {label}
    </span>
  );
}
