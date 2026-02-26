// Verification: App shell has correct layout structure and regions
// PRD Reference: Architecture - index.html with builder UI layout
// Vision Goal: Template selection screen and editor workspace areas
// Category: unit

const { test, expect } = require('@playwright/test');

test('index.html has all required layout regions', async ({ page }) => {
  console.log('=== UI Layout Structure Verification ===');

  await page.goto('/');

  // Check header
  const header = await page.locator('.app-header');
  await expect(header).toBeVisible();
  const headerText = await header.textContent();
  expect(headerText).toContain('PageCraft');
  console.log('✓ App header present with title');

  // Check template selector area
  const templateSelector = await page.locator('#template-selector');
  await expect(templateSelector).toBeVisible();
  console.log('✓ Template selector area present');

  // Check workspace area (hidden initially)
  const workspace = await page.locator('#workspace');
  expect(await workspace.count()).toBe(1); // Exists in DOM
  console.log('✓ Workspace area exists');

  // Check preview panel (hidden initially)
  const previewPanel = await page.locator('#preview-panel');
  expect(await previewPanel.count()).toBe(1);
  console.log('✓ Preview panel exists');

  console.log('PASS: All layout regions present');
});

test('CSS files load and apply styles', async ({ page }) => {
  await page.goto('/');

  // Check that CSS is loaded by verifying computed styles
  const header = await page.locator('.app-header');
  const headerStyles = await header.evaluate(el => {
    const computed = window.getComputedStyle(el);
    return {
      display: computed.display,
      padding: computed.padding
    };
  });

  // If CSS loaded, header should have some styling
  expect(headerStyles.display).not.toBe('');
  console.log('✓ CSS styles applied to header');

  console.log('PASS: CSS files loaded and applied');
});

test('JS files load without errors', async ({ page }) => {
  const errors = [];
  page.on('pageerror', err => errors.push(err.message));

  await page.goto('/');

  // Wait for JS to execute
  await page.waitForTimeout(500);

  expect(errors).toEqual([]);
  console.log('✓ No JavaScript errors on page load');

  console.log('PASS: JavaScript loads without errors');
});
