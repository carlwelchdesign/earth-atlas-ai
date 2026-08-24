/// <reference types="vitest/config" />

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  test: {
    coverage: {
      provider: "v8",
      reporter: ["text"],
    },
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
  },
});
