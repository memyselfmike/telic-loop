// Verification: Server starts on configured PORT and serves static files
// PRD Reference: Architecture - Express server serves static files
// Vision Goal: Foundation for the builder application
// Category: unit

const { test, expect } = require('@playwright/test');

test('server starts and responds to root path', async ({ page }) => {
  console.log('=== Server Start Verification ===');

  // Navigate to root - if server isn't running, this will fail
  const response = await page.goto('/');

  // Verify response is successful
  expect(response.status()).toBe(200);
  console.log('✓ Server responded with status 200');

  // Verify we get the index.html page
  const title = await page.title();
  expect(title).toBe('PageCraft - Landing Page Builder');
  console.log('✓ Index.html loaded with correct title');

  console.log('PASS: Server starts and serves index.html');
});

test('server serves static CSS files', async ({ page }) => {
  const baseURL = page.context()._options.baseURL;

  // Check app.css loads
  const appCssResponse = await page.goto(`${baseURL}/css/app.css`);
  expect(appCssResponse.status()).toBe(200);
  expect(appCssResponse.headers()['content-type']).toContain('css');
  console.log('✓ app.css loads successfully');

  // Check templates.css loads
  const templatesCssResponse = await page.goto(`${baseURL}/css/templates.css`);
  expect(templatesCssResponse.status()).toBe(200);
  expect(templatesCssResponse.headers()['content-type']).toContain('css');
  console.log('✓ templates.css loads successfully');

  console.log('PASS: All CSS files served correctly');
});

test('server serves static JS files', async ({ page }) => {
  const baseURL = page.context()._options.baseURL;

  // Check app.js loads
  const appJsResponse = await page.goto(`${baseURL}/js/app.js`);
  expect(appJsResponse.status()).toBe(200);
  console.log('✓ app.js loads successfully');

  // Check templates.js loads
  const templatesJsResponse = await page.goto(`${baseURL}/js/templates.js`);
  expect(templatesJsResponse.status()).toBe(200);
  console.log('✓ templates.js loads successfully');

  console.log('PASS: All JS files served correctly');
});
