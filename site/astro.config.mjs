import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  site: "https://pi-claude-code.ngoquochuy.com",
  output: "static",
  vite: { plugins: [tailwindcss()] },
});
