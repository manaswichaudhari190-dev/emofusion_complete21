/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        display: ["'Syne'", "sans-serif"],
        body: ["'DM Sans'", "sans-serif"],
      },
      colors: {
        brand: {
          50: "#f0f4ff",
          100: "#dde8ff",
          400: "#7aa2f7",
          500: "#5a8dee",
          600: "#3d74e8",
          700: "#2558d4",
          900: "#0a1628",
        },
        surface: {
          dark: "#0d1117",
          card: "#161b22",
          border: "#21262d",
        },
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-out",
        "slide-up": "slideUp 0.4s ease-out",
        "pulse-glow": "pulseGlow 2s ease-in-out infinite",
        "bar-grow": "barGrow 0.8s ease-out forwards",
      },
      keyframes: {
        fadeIn: { "0%": { opacity: 0 }, "100%": { opacity: 1 } },
        slideUp: { "0%": { opacity: 0, transform: "translateY(16px)" }, "100%": { opacity: 1, transform: "translateY(0)" } },
        pulseGlow: { "0%,100%": { boxShadow: "0 0 0 0 rgba(90,141,238,0.4)" }, "50%": { boxShadow: "0 0 0 12px rgba(90,141,238,0)" } },
        barGrow: { "0%": { width: "0%" }, "100%": { width: "var(--bar-width)" } },
      },
    },
  },
  plugins: [],
};
