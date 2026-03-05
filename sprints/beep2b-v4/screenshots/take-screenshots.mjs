import { chromium } from 'playwright';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

const pages = [
  { url: 'http://localhost:4321/', name: 'home.png' },
  { url: 'http://localhost:4321/how-it-works', name: 'how-it-works.png' },
  { url: 'http://localhost:4321/services', name: 'services.png' },
  { url: 'http://localhost:4321/about', name: 'about.png' },
  { url: 'http://localhost:4321/blog', name: 'blog.png' },
  { url: 'http://localhost:4321/contact', name: 'contact.png' },
  { url: 'http://localhost:4321/blog/the-anatomy-of-a-high-converting-linkedin-profile', name: 'blog-post.png' },
];

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1280, height: 900 },
  });

  for (const { url, name } of pages) {
    const page = await context.newPage();
    console.log(`Navigating to ${url} ...`);
    await page.goto(url, { waitUntil: 'networkidle' });
    const outPath = join(__dirname, name);
    await page.screenshot({ path: outPath, fullPage: true });
    console.log(`  -> saved ${name}`);
    await page.close();
  }

  await browser.close();
  console.log('Done. All screenshots saved.');
})();
