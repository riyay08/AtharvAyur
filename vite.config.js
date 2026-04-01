import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    // Listen on all interfaces so phones/tablets on the same Wi‑Fi can open the dev URL
    host: true,
    proxy: {
      // Use relative URLs in dev: fetch('/api/health') → FastAPI on 8000
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  preview: {
    host: true,
  },
});
