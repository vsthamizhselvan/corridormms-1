/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        vfx: {
          darkest: "#0e0e10",
          base: "#141416",
          surface: "#1a1a1e",
          elevated: "#222226",
          panel: "#1e1e22",
          border: "#2c2c32",
          "border-subtle": "#24242a",
          "border-focus": "#3b82f6",
          accent: "#2563eb",
          "accent-hover": "#1d4ed8",
          text: "#f4f4f6",
          "text-muted": "#90909a",
          "text-dim": "#60606a",
          track: "#0d9488",
          "track-audio": "#0284c7",
          playhead: "#ef4444",
          indicator: "#10b981",
        },
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "Inter",
          "sans-serif",
        ],
        mono: [
          "JetBrains Mono",
          "SF Mono",
          "Consolas",
          "monospace",
        ],
      },
    },
  },
  plugins: [],
};
