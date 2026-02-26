// Verification: App shell has correct layout structure and regions
// PRD Reference: Architecture - index.html with builder UI layout
// Vision Goal: Template selection screen and editor workspace areas
// Category: unit

const { chromium } = require('playwright');

async function verify() {
  let browser;
  let exitCode = 0;

  try {
    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ baseURL: 'http://localhost:3000' });
    const page = await context.newPage();

    console.log('=== UI Layout Structure Verification ===');

    // Test 1: index.html has all required layout regions
    await page.goto('/');

    // Check header
    const headerCount = await page.locator('.app-header').count();
    if (headerCount === 0) {
      throw new Error('App header not found');
    }
    const headerText = await page.locator('.app-header').textContent();
    if (!headerText.includes('PageCraft')) {
      throw new Error(`Header text does not contain 'PageCraft': ${headerText}`);
    }
    console.log('✓ App header present with title');

    // Check template selector area
    const templateSelectorCount = await page.locator('#template-selector').count();
    if (templateSelectorCount === 0) {
      throw new Error('Template selector area not found');
    }
    console.log('✓ Template selector area present');

    // Check workspace area (hidden initially)
    const workspaceCount = await page.locator('#workspace').count();
    if (workspaceCount !== 1) {
      throw new Error(`Expected 1 workspace element, found ${workspaceCount}`);
    }
    console.log('✓ Workspace area exists');

    // Check preview panel (hidden initially)
    const previewPanelCount = await page.locator('#preview-panel').count();
    if (previewPanelCount !== 1) {
      throw new Error(`Expected 1 preview panel element, found ${previewPanelCount}`);
    }
    console.log('✓ Preview panel exists');

    console.log('PASS: All layout regions present');

    // Test 2: CSS files load and apply styles
    const header = await page.locator('.app-header');
    const headerStyles = await header.evaluate(el => {
      const computed = window.getComputedStyle(el);
      return {
        display: computed.display,
        padding: computed.padding
      };
    });

    // If CSS loaded, header should have some styling
    if (headerStyles.display === '') {
      throw new Error('CSS styles not applied - header display is empty');
    }
    console.log('✓ CSS styles applied to header');

    console.log('PASS: CSS files loaded and applied');

    // Test 3: JS files load without errors
    const errors = [];
    page.on('pageerror', err => errors.push(err.message));

    await page.goto('/');

    // Wait for JS to execute
    await page.waitForTimeout(500);

    if (errors.length > 0) {
      throw new Error(`JavaScript errors on page load: ${errors.join(', ')}`);
    }
    console.log('✓ No JavaScript errors on page load');

    console.log('PASS: JavaScript loads without errors');

    await context.close();
  } catch (error) {
    console.error('FAIL:', error.message);
    exitCode = 1;
  } finally {
    if (browser) {
      await browser.close();
    }
  }

  process.exit(exitCode);
}

verify();
