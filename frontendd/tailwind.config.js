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
        signal: "#4f8ff0",
        signaldim: "#1e3a5f",
        warn: "#e8a662",
      },
      fontFamily: {
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
        sans: ["IBM Plex Sans", "sans-serif"],
      },
    },
  },
  plugins: [
    function ({ addVariant }) {
      // touch devices trigger :hover on tap — gate hover states to
      // devices that actually have a mouse, so taps don't get stuck
      // showing a hover state
      addVariant("hover-fine", "@media (hover: hover) and (pointer: fine) { &:hover }");
    },
  ],
};
