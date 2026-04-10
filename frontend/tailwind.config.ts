import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Obsidian Ether — surface hierarchy
        bg: {
          DEFAULT: "#111317",
          surface: "#1a1c20",
          elevated: "#1e2024",
          high: "#282a2e",
          highest: "#333539",
          lowest: "#0c0e12",
          bright: "#37393e",
          border: "#444748",
        },
        // Accent — silver-gray as the interactive secondary
        accent: {
          DEFAULT: "#c6c6c7",   // silver-gray (metallic, not blue)
          light: "#d6baff",     // purple — decorative only
          blue: "#7cd0ff",      // blue — glow decorations only
          amber: "#ffc87c",     // amber — glow decorations only
          glow: "rgba(198,198,199,0.15)",
        },
        text: {
          primary: "#e0dbd2",   // vintage warm white — body text
          secondary: "#bfbab2", // warm muted
          muted: "#8a8680",     // warm gray
          dim: "#5c5a56",
        },
        success: "#4ade80",
        warning: "#ffc87c",
        danger: "#f87171",
      },
      fontFamily: {
        serif:   ['"Manrope"', "sans-serif"],
        sans:    ['"Inter"', "system-ui", "sans-serif"],
        mono:    ['"JetBrains Mono"', '"Fira Code"', "monospace"],
        manrope: ['"Manrope"', "sans-serif"],
        inter:   ['"Inter"', "sans-serif"],
      },
      borderRadius: {
        DEFAULT: "0.5rem",
        lg: "1rem",
        xl: "1.5rem",
        full: "9999px",
      },
      boxShadow: {
        glow:     "0 0 20px rgba(198,198,199,0.12), 0 0 40px rgba(214,186,255,0.06)",
        "glow-lg":"0 0 30px rgba(198,198,199,0.2),  0 0 60px rgba(214,186,255,0.08)",
        card:     "0 4px 24px rgba(0,0,0,0.4)",
        ambient:  "0px 24px 48px rgba(0,0,0,0.5)",
      },
      animation: {
        "fade-in":  "fadeIn 0.4s ease-out",
        "slide-up": "slideUp 0.4s ease-out",
        pulse:      "pulse 2s cubic-bezier(0.4,0,0.6,1) infinite",
      },
      keyframes: {
        fadeIn:  { "0%": { opacity: "0" }, "100%": { opacity: "1" } },
        slideUp: { "0%": { opacity: "0", transform: "translateY(16px)" }, "100%": { opacity: "1", transform: "translateY(0)" } },
      },
    },
  },
  plugins: [],
};

export default config;
