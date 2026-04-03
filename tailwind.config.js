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
      keyframes: {
        "plan-card-exit": {
          to: {
            opacity: "0",
            transform: "translateX(calc(100% + 12px)) scale(0.94) rotate(1deg)",
          },
        },
        "plan-card-enter": {
          from: {
            opacity: "0",
            transform: "translateX(-32px) scale(0.97)",
          },
          to: {
            opacity: "1",
            transform: "translateX(0) scale(1)",
          },
        },
      },
      animation: {
        "plan-card-exit": "plan-card-exit 0.42s cubic-bezier(0.4, 0, 0.2, 1) forwards",
        "plan-card-enter": "plan-card-enter 0.5s cubic-bezier(0.22, 1, 0.36, 1) both",
      },
    },
  },
  plugins: [],
};
