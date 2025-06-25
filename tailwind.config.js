/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        netflix: ["'Netflix Sans'", "Helvetica Neue", "Segoe UI", "Roboto", "Ubuntu", "sans-serif"],
        slab: ["'Roboto Slab'", "serif"],
      },
      colors: {
        netflixRed: "#e50914",
        darkBg: "#141414",
        darkCard: "#1f1f1f",
        textLight: "#e5e5e5",
        textMuted: "#b3b3b3",
      },
      boxShadow: {
        netflix: "0 4px 10px rgba(0, 0, 0, 0.5)",
      },
    },
  },
  plugins: [],
};