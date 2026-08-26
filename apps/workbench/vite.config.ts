/// <reference types="vitest/config" />

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ["maplibre-gl"],
  },
  server: {
    proxy: {
      "/v1": process.env.ECHOATLAS_API_ORIGIN ?? "http://127.0.0.1:8000",
    },
  },
  test: {
    coverage: {
      provider: "v8",
      reporter: ["text"],
    },
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
  },
});
