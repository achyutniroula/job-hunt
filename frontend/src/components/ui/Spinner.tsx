import clsx from "clsx";

interface SpinnerProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizes = { sm: "w-4 h-4", md: "w-6 h-6", lg: "w-10 h-10" };

export default function Spinner({ size = "md", className }: SpinnerProps) {
  return (
    <div
      className={clsx("animate-spin rounded-full", sizes[size], className)}
      style={{ border: "2px solid rgba(68,71,72,0.3)", borderTopColor: "#7cd0ff" }}
    />
  );
}
