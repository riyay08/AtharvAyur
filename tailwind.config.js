/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        vata: "#7EC8E3",
        pitta: "#D98C6B",
        kapha: "#8FAF7A",
      },
      boxShadow: {
        wellness: "0 12px 30px rgba(15, 23, 42, 0.08)",
      },
    },
  },
  plugins: [],
};
