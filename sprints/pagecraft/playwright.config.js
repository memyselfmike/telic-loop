// Playwright Configuration for PageCraft
const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './.loop/verifications',
  testMatch: /value_.*\.spec\.js$/,
  timeout: 30000,
  retries: 0,
  workers: 1,
  use: {
    baseURL: `http://localhost:${process.env.PORT || 3000}`,
    headless: true,
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true,
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: process.platform === 'win32'
      ? `set PORT=${process.env.PORT || 3000} && node server.js`
      : `PORT=${process.env.PORT || 3000} node server.js`,
    port: parseInt(process.env.PORT || 3000),
    timeout: 10000,
    reuseExistingServer: !process.env.CI,
  },
});
