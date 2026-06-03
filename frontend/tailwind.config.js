/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans:    ["Hind", "ui-sans-serif", "system-ui", "-apple-system", "sans-serif"],
        display: ["Archivo Black", "Hind", "ui-sans-serif", "sans-serif"],
        mono:    ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      colors: {
        // Background & Surfaces
        background:    "oklch(0.965 0.008 85)",
        foreground:    "oklch(0.18 0.005 270)",
        surface:       "oklch(0.98 0.006 85)",
        "surface-muted": "oklch(0.93 0.01 85)",
        paper:         "oklch(0.965 0.008 85)",
        "paper-2":     "oklch(0.93 0.01 85)",
        ink:           "oklch(0.18 0.005 270)",
        "ink-2":       "oklch(0.28 0.005 270)",
        card:          "oklch(0.985 0.005 85)",
        // Primary
        primary:           "oklch(0.18 0.005 270)",
        "primary-foreground": "oklch(0.965 0.008 85)",
        "primary-soft":    "oklch(0.91 0.01 85)",
        // Muted
        muted:             "oklch(0.93 0.01 85)",
        "muted-foreground": "oklch(0.45 0.008 270)",
        // Semantic
        success:           "oklch(0.5 0.12 150)",
        "success-foreground": "oklch(0.98 0.006 85)",
        "success-soft":    "oklch(0.92 0.04 150)",
        warning:           "oklch(0.7 0.14 70)",
        "warning-foreground": "oklch(0.25 0.05 70)",
        "warning-soft":    "oklch(0.93 0.06 80)",
        destructive:       "oklch(0.55 0.2 27)",
        "destructive-foreground": "oklch(0.98 0.006 85)",
        "destructive-soft": "oklch(0.93 0.04 27)",
        // Border
        border:            "oklch(0.82 0.012 85)",
        "border-strong":   "oklch(0.18 0.005 270)",
        input:             "oklch(0.82 0.012 85)",
        ring:              "oklch(0.18 0.005 270)",
        // Sidebar
        sidebar:                    "oklch(0.18 0.005 270)",
        "sidebar-foreground":        "oklch(0.88 0.008 85)",
        "sidebar-primary":           "oklch(0.965 0.008 85)",
        "sidebar-primary-foreground": "oklch(0.18 0.005 270)",
        "sidebar-accent":            "oklch(0.26 0.005 270)",
        "sidebar-accent-foreground": "oklch(0.98 0.006 85)",
        "sidebar-border":            "oklch(0.28 0.005 270)",
      },
      boxShadow: {
        card:     "0 1px 0 0 rgb(13 13 13 / 0.04)",
        elevated: "0 1px 0 0 rgb(13 13 13 / 0.06), 0 12px 32px -16px rgb(13 13 13 / 0.12)",
      },
    },
  },
  plugins: [],
}

