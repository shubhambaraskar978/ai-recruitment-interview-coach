/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#172421",
        muted: "#697873",
        paper: "#f6f8f5",
        line: "#e3e9e4",
        forest: "#176b5b",
        lime: "#d5ed72",
      },
      fontFamily: {
        sans: ["DM Sans", "sans-serif"],
        display: ["Manrope", "sans-serif"],
      },
    },
  },
  plugins: [],
};
