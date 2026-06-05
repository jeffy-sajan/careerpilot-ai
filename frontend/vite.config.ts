import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom", "react-router-dom"],
          sentry: ["@sentry/react"],
          recharts: ["recharts"],
          ui: ["lucide-react"],
        },
      },
    },
  },
  server: {
    host: true, // Needed for docker
    port: 5173,
    watch: {
      usePolling: true, // Needed for hot reload in docker
    },
  },
});
