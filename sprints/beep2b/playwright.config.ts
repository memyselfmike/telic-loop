import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: '.loop/verifications/playwright',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:4321',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'mobile',
      use: { ...devices['iPhone 13'] },
    },
  ],
  // Start Astro dev server automatically
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:4321',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
    env: {
      SANITY_PROJECT_ID: process.env.SANITY_PROJECT_ID || 'placeholder',
      SANITY_DATASET: process.env.SANITY_DATASET || 'production',
      SANITY_API_TOKEN: process.env.SANITY_API_TOKEN || 'placeholder',
      PUBLIC_FORM_ACTION: process.env.PUBLIC_FORM_ACTION || 'https://example.com/form',
    },
  },
});
