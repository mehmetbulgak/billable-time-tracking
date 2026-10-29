import { fileURLToPath, URL } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": { target: backendUrl, changeOrigin: true },
      "/ws": { target: backendUrl.replace(/^http/, "ws"), ws: true },
    },
  },
  build: {
    sourcemap: true,
    rolldownOptions: {
      output: {
        codeSplitting: {
          groups: [
            {
              name: "react",
              test: /node_modules[\\/](react|react-dom|react-router|scheduler)[\\/]/,
            },
            {
              name: "redux",
              test: /node_modules[\\/](@reduxjs|react-redux|redux|immer|reselect)[\\/]/,
            },
            {
              name: "mui",
              test: /node_modules[\\/](@mui[\\/](material|system|styled-engine|utils|private-theming|core-downloads-tracker)|@emotion)[\\/]/,
            },
          ],
        },
      },
    },
  },
  test: {
    environment: "jsdom",
    env: { VITE_API_URL: "http://localhost/api/v1", TZ: "Europe/Istanbul" },
    setupFiles: ["./src/test/setup.ts"],
    css: false,
    restoreMocks: true,
  },
});
