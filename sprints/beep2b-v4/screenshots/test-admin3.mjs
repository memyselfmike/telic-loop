import { chromium } from 'playwright';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ssDir = path.join(__dirname, '..');

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();

  // Collect ALL console messages
  const consoleLogs = [];
  page.on('console', msg => {
    consoleLogs.push({ type: msg.type(), text: msg.text() });
  });

  // Track page errors
  const pageErrors = [];
  page.on('pageerror', err => {
    pageErrors.push(err.message);
  });

  // Navigate to admin
  console.log('=== Navigate to /admin ===');
  await page.goto('http://localhost:3000/admin', { waitUntil: 'domcontentloaded', timeout: 15000 }).catch(() => {});
  await sleep(5000);

  // Print all console messages
  console.log('\n=== Console Messages ===');
  consoleLogs.forEach(l => console.log(`  [${l.type}] ${l.text.substring(0, 300)}`));

  console.log('\n=== Page Errors ===');
  pageErrors.forEach(e => console.log(`  ${e.substring(0, 500)}`));

  // Check for 500 errors from server - try fetching admin page directly
  console.log('\n=== Server-side admin page check ===');
  try {
    const resp = await page.evaluate(async () => {
      const r = await fetch('/admin', { headers: { 'Accept': 'text/html' } });
      const text = await r.text();
      return { status: r.status, bodyLen: text.length, first1000: text.substring(0, 1000), last500: text.substring(text.length - 500) };
    });
    console.log('Status:', resp.status);
    console.log('Body length:', resp.bodyLen);
    console.log('First 1000 chars:', resp.first1000);
  } catch (e) {
    console.log('Error:', e.message);
  }

  // Check what scripts are loaded
  const scripts = await page.$$eval('script', els => els.map(s => ({ src: s.src, type: s.type, innerLen: s.innerHTML.length })));
  console.log('\n=== Scripts on page ===');
  scripts.forEach(s => console.log(`  src=${s.src || '(inline)'}, type=${s.type}, len=${s.innerLen}`));

  // Check for specific Payload errors in the HTML
  const html = await page.content();

  // Look for error boundary text
  if (html.includes('Cannot destructure')) {
    const idx = html.indexOf('Cannot destructure');
    console.log('\n=== Error in HTML ===');
    console.log(html.substring(Math.max(0, idx - 200), idx + 200));
  }

  // Check _next data
  const nextDataScripts = await page.$$eval('script#__NEXT_DATA__', els => els.map(s => s.textContent));
  if (nextDataScripts.length > 0) {
    console.log('\n=== __NEXT_DATA__ ===');
    console.log(nextDataScripts[0]?.substring(0, 500));
  }

  await browser.close();
  console.log('\n=== Done ===');
})();
