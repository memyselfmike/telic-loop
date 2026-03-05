import { chromium } from 'playwright';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = join(__dirname, 'responsive');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();

  // Collect console errors
  const errors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') errors.push(msg.text());
  });
  page.on('pageerror', err => {
    errors.push(`PAGE ERROR: ${err.message}`);
  });

  console.log('=== Navigating to /admin/login ===');
  await page.goto('http://localhost:3000/admin/login', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(5000);
  console.log(`  URL: ${page.url()}`);

  await page.screenshot({ path: join(OUT, 'cms_login_direct.png') });
  console.log('  -> cms_login_direct.png');

  const bodyText = await page.evaluate(() => document.body.innerText.slice(0, 500));
  console.log(`  Body text: ${bodyText.slice(0, 300)}`);

  console.log(`  Console errors: ${errors.length}`);
  for (const e of errors.slice(0, 10)) {
    console.log(`    ${e.slice(0, 200)}`);
  }

  // Try API login
  console.log('\n=== Trying API login ===');
  const loginResp = await page.evaluate(async () => {
    try {
      const resp = await fetch('http://localhost:3000/api/users/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'admin@beep2b.com', password: 'changeme' }),
      });
      const data = await resp.json();
      return { status: resp.status, data };
    } catch (e) {
      return { error: e.message };
    }
  });
  console.log(`  Login response: ${JSON.stringify(loginResp).slice(0, 500)}`);

  // If login succeeded, try navigating to admin with the cookie
  if (loginResp.data && loginResp.data.token) {
    console.log('  Login succeeded! Navigating to admin...');
    await page.goto('http://localhost:3000/admin', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(5000);
    await page.screenshot({ path: join(OUT, 'cms_admin_loggedin.png') });
    console.log(`  -> cms_admin_loggedin.png (URL: ${page.url()})`);

    const bodyText2 = await page.evaluate(() => document.body.innerText.slice(0, 500));
    console.log(`  Body text: ${bodyText2.slice(0, 300)}`);
  }

  await browser.close();
  console.log('\nDone.');
})();
