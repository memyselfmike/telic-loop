// Verification: Server starts on configured PORT and serves static files
// PRD Reference: Architecture - Express server serves static files
// Vision Goal: Foundation for the builder application
// Category: unit
// NOTE: Standalone Node.js script (not Playwright test DSL)

const { chromium } = require('playwright');

async function verify() {
  let browser;
  let exitCode = 0;

  try {
    console.log('=== Server Start Verification ===');

    // Launch browser
    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ baseURL: 'http://localhost:3000' });
    const page = await context.newPage();

    // Test 1: Server starts and responds to root path
    console.log('\nTest 1: Server starts and responds to root path');
    const response = await page.goto('/');

    if (response.status() !== 200) {
      throw new Error(`Expected status 200, got ${response.status()}`);
    }
    console.log('✓ Server responded with status 200');

    const title = await page.title();
    if (title !== 'PageCraft - Landing Page Builder') {
      throw new Error(`Expected title "PageCraft - Landing Page Builder", got "${title}"`);
    }
    console.log('✓ Index.html loaded with correct title');
    console.log('PASS: Server starts and serves index.html');

    // Test 2: Server serves static CSS files
    console.log('\nTest 2: Server serves static CSS files');
    const appCssResponse = await page.goto('http://localhost:3000/css/app.css');
    if (appCssResponse.status() !== 200) {
      throw new Error(`app.css returned status ${appCssResponse.status()}`);
    }
    const appCssType = appCssResponse.headers()['content-type'];
    if (!appCssType || !appCssType.includes('css')) {
      throw new Error(`app.css has wrong content-type: ${appCssType}`);
    }
    console.log('✓ app.css loads successfully');

    const templatesCssResponse = await page.goto('http://localhost:3000/css/templates.css');
    if (templatesCssResponse.status() !== 200) {
      throw new Error(`templates.css returned status ${templatesCssResponse.status()}`);
    }
    const templatesCssType = templatesCssResponse.headers()['content-type'];
    if (!templatesCssType || !templatesCssType.includes('css')) {
      throw new Error(`templates.css has wrong content-type: ${templatesCssType}`);
    }
    console.log('✓ templates.css loads successfully');
    console.log('PASS: All CSS files served correctly');

    // Test 3: Server serves static JS files
    console.log('\nTest 3: Server serves static JS files');
    const appJsResponse = await page.goto('http://localhost:3000/js/app.js');
    if (appJsResponse.status() !== 200) {
      throw new Error(`app.js returned status ${appJsResponse.status()}`);
    }
    console.log('✓ app.js loads successfully');

    const templatesJsResponse = await page.goto('http://localhost:3000/js/templates.js');
    if (templatesJsResponse.status() !== 200) {
      throw new Error(`templates.js returned status ${templatesJsResponse.status()}`);
    }
    console.log('✓ templates.js loads successfully');
    console.log('PASS: All JS files served correctly');

    console.log('\n=== ALL TESTS PASSED ===');

  } catch (error) {
    console.error('\n❌ VERIFICATION FAILED:');
    console.error(error.message);
    if (error.stack) {
      console.error(error.stack);
    }
    exitCode = 1;
  } finally {
    if (browser) {
      await browser.close();
    }
  }

  process.exit(exitCode);
}

verify();
