// Tailwind CSS v4 configuration
// Note: In Tailwind v4, theme customisation is done via @theme in src/styles/global.css
// and the @tailwindcss/vite plugin is configured in astro.config.mjs.
// This file is kept for tooling compatibility (IDEs, shadcn/ui CLI, etc.).

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}',
    './sanity/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
