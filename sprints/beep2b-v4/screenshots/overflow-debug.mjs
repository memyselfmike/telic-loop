import { chromium } from 'playwright';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = join(__dirname, 'responsive');

(async () => {
  const browser = await chromium.launch({ headless: true });

  // Debug horizontal overflow at 768px
  for (const width of [768, 480]) {
    console.log(`\n=== Debugging overflow at ${width}px ===`);
    const ctx = await browser.newContext({ viewport: { width, height: 800 } });
    const page = await ctx.newPage();
    await page.goto('http://localhost:4321/', { waitUntil: 'networkidle', timeout: 30000 });

    const overflowInfo = await page.evaluate(() => {
      const docWidth = document.documentElement.scrollWidth;
      const viewWidth = document.documentElement.clientWidth;
      const overflow = docWidth - viewWidth;

      // Find elements causing overflow
      const offenders = [];
      const all = document.querySelectorAll('*');
      for (const el of all) {
        const rect = el.getBoundingClientRect();
        if (rect.right > viewWidth + 5) {
          const tag = el.tagName.toLowerCase();
          const cls = el.className ? `.${String(el.className).split(' ').join('.')}` : '';
          const id = el.id ? `#${el.id}` : '';
          offenders.push({
            selector: `${tag}${id}${cls}`.slice(0, 120),
            right: Math.round(rect.right),
            width: Math.round(rect.width),
            overflow: Math.round(rect.right - viewWidth),
          });
        }
      }

      // Deduplicate and sort by overflow amount
      const seen = new Set();
      const unique = offenders.filter(o => {
        if (seen.has(o.selector)) return false;
        seen.add(o.selector);
        return true;
      });
      unique.sort((a, b) => b.overflow - a.overflow);

      return {
        docWidth,
        viewWidth,
        overflow,
        topOffenders: unique.slice(0, 15),
      };
    });

    console.log(`  Document width: ${overflowInfo.docWidth}px, Viewport: ${overflowInfo.viewWidth}px, Overflow: ${overflowInfo.overflow}px`);
    console.log('  Top overflow offenders:');
    for (const o of overflowInfo.topOffenders) {
      console.log(`    ${o.selector}: right=${o.right}px, width=${o.width}px, overflow=${o.overflow}px`);
    }

    // Also check if the nav menu is open by default
    const navState = await page.evaluate(() => {
      const nav = document.querySelector('nav');
      if (!nav) return 'No nav found';
      const style = window.getComputedStyle(nav);
      const navLinks = nav.querySelectorAll('a');
      const visibleLinks = [];
      for (const a of navLinks) {
        const rect = a.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
          visibleLinks.push({ text: a.textContent.trim(), left: Math.round(rect.left), right: Math.round(rect.right) });
        }
      }
      return { display: style.display, position: style.position, visibleLinks };
    });
    console.log(`  Nav state: ${JSON.stringify(navState)}`);

    await ctx.close();
  }

  await browser.close();
  console.log('\nDone.');
})();
