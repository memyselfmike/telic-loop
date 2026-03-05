import { chromium } from 'playwright';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ssDir = path.join(__dirname, '..'); // save screenshots to sprint root

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();

  // Collect console errors
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });

  // Step 1: Check the API to confirm server is running and DB is connected
  console.log('=== Step 1: Check API health ===');
  try {
    const apiResponse = await page.goto('http://localhost:3000/api/posts', { waitUntil: 'networkidle', timeout: 10000 });
    const apiText = await page.textContent('body');
    console.log('API /posts response status:', apiResponse?.status());
    console.log('API /posts body (first 500 chars):', apiText?.substring(0, 500));
  } catch (e) {
    console.log('API check failed:', e.message);
  }

  // Step 2: Try to login via API first
  console.log('\n=== Step 2: Login via API ===');
  try {
    const loginResponse = await page.evaluate(async () => {
      const res = await fetch('http://localhost:3000/api/users/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'admin@beep2b.com', password: 'changeme' }),
      });
      return { status: res.status, body: await res.json() };
    });
    console.log('Login response:', JSON.stringify(loginResponse, null, 2).substring(0, 500));
  } catch (e) {
    console.log('API login failed:', e.message);
  }

  // Step 3: Navigate to admin login page and try to dismiss error overlay
  console.log('\n=== Step 3: Navigate to /admin/login ===');
  await page.goto('http://localhost:3000/admin/login', { waitUntil: 'domcontentloaded', timeout: 15000 }).catch(() => {});
  await sleep(3000);

  // Try to dismiss the Next.js error overlay
  // Press escape or click close button
  await page.keyboard.press('Escape').catch(() => {});
  await sleep(500);

  // Try clicking the close button on the error overlay
  const closeBtn = await page.$('button[aria-label="Close"]') || await page.$('[data-nextjs-errors-dialog-left-right-close-button]');
  if (closeBtn) {
    await closeBtn.click();
    console.log('Dismissed error overlay via close button');
  }

  // Try pressing Escape again
  await page.keyboard.press('Escape').catch(() => {});
  await sleep(1000);

  await page.screenshot({ path: path.join(ssDir, 'admin_after_dismiss.png'), fullPage: false });

  // Check what the page HTML looks like underneath
  const pageHTML = await page.content();
  console.log('Page HTML length:', pageHTML.length);

  // Look for login form elements by checking the full DOM
  const inputs = await page.$$eval('input', els => els.map(e => ({ type: e.type, name: e.name, id: e.id, placeholder: e.placeholder })));
  console.log('All inputs on page:', JSON.stringify(inputs));

  // Try checking if the error is only client-side - see page source
  console.log('\n=== Step 4: Check page source for form elements ===');
  const hasForm = pageHTML.includes('<form');
  const hasEmailInput = pageHTML.includes('email');
  const hasPasswordInput = pageHTML.includes('password');
  console.log('Has form:', hasForm);
  console.log('Has email references:', hasEmailInput);
  console.log('Has password references:', hasPasswordInput);

  // Check if Payload (payload) route group works
  console.log('\n=== Step 5: Try (payload) route group ===');
  // In Payload v3 with Next.js, the admin panel might be at /admin but served through (payload) route group
  // The error "Cannot destructure property 'config'" suggests the config import is failing

  // Try the GraphQL endpoint
  try {
    const gqlResponse = await page.evaluate(async () => {
      const res = await fetch('http://localhost:3000/api/graphql', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: '{ Posts { docs { title } } }' }),
      });
      return { status: res.status, body: await res.json() };
    });
    console.log('GraphQL response:', JSON.stringify(gqlResponse, null, 2).substring(0, 500));
  } catch (e) {
    console.log('GraphQL failed:', e.message);
  }

  // Check collections via REST API
  console.log('\n=== Step 6: Check all collections via REST API ===');
  for (const collection of ['posts', 'categories', 'testimonials', 'form-submissions', 'media', 'users']) {
    try {
      const response = await page.evaluate(async (col) => {
        const res = await fetch(`http://localhost:3000/api/${col}?limit=100`);
        const data = await res.json();
        return { status: res.status, totalDocs: data.totalDocs, docs: data.docs?.length };
      }, collection);
      console.log(`  ${collection}: status=${response.status}, totalDocs=${response.totalDocs}, returned=${response.docs}`);
    } catch (e) {
      console.log(`  ${collection}: ERROR - ${e.message}`);
    }
  }

  // Step 7: Login via API, set cookie, then try admin panel
  console.log('\n=== Step 7: Login via API and try admin ===');
  try {
    const loginResult = await page.evaluate(async () => {
      const res = await fetch('http://localhost:3000/api/users/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'admin@beep2b.com', password: 'changeme' }),
        credentials: 'include',
      });
      return { status: res.status, body: await res.json() };
    });
    console.log('Login result:', JSON.stringify(loginResult).substring(0, 300));

    if (loginResult.body.token) {
      // Set the auth cookie
      await context.addCookies([{
        name: 'payload-token',
        value: loginResult.body.token,
        domain: 'localhost',
        path: '/',
      }]);
      console.log('Set payload-token cookie');

      // Now try admin panel
      await page.goto('http://localhost:3000/admin', { waitUntil: 'domcontentloaded', timeout: 15000 }).catch(() => {});
      await sleep(3000);

      // Dismiss error overlay again
      await page.keyboard.press('Escape').catch(() => {});
      await sleep(500);
      await page.keyboard.press('Escape').catch(() => {});
      await sleep(1000);

      await page.screenshot({ path: path.join(ssDir, 'admin_after_api_login.png'), fullPage: false });
      console.log('Current URL:', page.url());
      console.log('Screenshot: admin_after_api_login.png');
    }
  } catch (e) {
    console.log('API login + admin error:', e.message);
  }

  // Console errors
  console.log('\n=== Console Errors ===');
  consoleErrors.forEach(e => console.log('  ', e.substring(0, 200)));

  await browser.close();
  console.log('\n=== Done ===');
})();
