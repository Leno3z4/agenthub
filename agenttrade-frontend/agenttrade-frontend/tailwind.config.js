/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,jsx}", "./components/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        void: "#0b0f14",
        surface: "#131a22",
        surface2: "#171f29",
        line: "#263140",
        dim: "#6b7889",
        signal: "#49d6c8",
        signaldim: "#1f4a47",
        warn: "#e8a662",
      },
      fontFamily: {
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
        sans: ["IBM Plex Sans", "sans-serif"],
      },
    },
  },
  plugins: [],
};
