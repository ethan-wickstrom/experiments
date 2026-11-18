import preact from "@preact/preset-vite";
import { defineConfig } from "vite";

export default defineConfig({
  base: "./",
  plugins: [preact()],
  worker: { format: "es" },
  server: { host: true, allowedHosts: true },
  preview: { host: true, allowedHosts: true },
});
