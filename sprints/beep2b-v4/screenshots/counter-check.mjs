import { chromium } from 'playwright-core';

const BROWSER_PATH = 'C:/Program Files/Google/Chrome/Application/chrome.exe';

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function run() {
  const browser = await chromium.launch({
    executablePath: BROWSER_PATH,
    headless: true,
  });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  await page.goto('http://localhost:4321/', { waitUntil: 'networkidle' });
  await sleep(1000);

  // Scroll to trust bar to trigger counter animations
  await page.evaluate(() => window.scrollTo(0, 800));
  await sleep(3000); // Wait 3 seconds for counter animation (2s duration)

  // Get counter values
  const counters = await page.evaluate(() => {
    const els = document.querySelectorAll('[data-counter]');
    return Array.from(els).map(el => ({
      target: el.getAttribute('data-counter'),
      displayed: el.textContent,
    }));
  });
  console.log('Counter values after scrolling + 3s wait:', JSON.stringify(counters, null, 2));

  // Screenshot trust bar after animation completes
  await page.screenshot({ path: 'audit/trust_bar_animated.png' });

  // Check features grid - how many cards render?
  const featureInfo = await page.evaluate(() => {
    const grid = document.querySelector('.features-grid');
    if (!grid) return { error: 'No features-grid found' };
    const cards = grid.children;
    return {
      childCount: cards.length,
      gridCols: window.getComputedStyle(grid).gridTemplateColumns,
      children: Array.from(cards).map(c => c.textContent.trim().substring(0, 50)),
    };
  });
  console.log('Features grid:', JSON.stringify(featureInfo, null, 2));

  // Check "Book a Call" nav button styling
  const navCtaInfo = await page.evaluate(() => {
    const btn = document.querySelector('.nav-cta .btn');
    if (!btn) return { error: 'No nav CTA found' };
    const style = window.getComputedStyle(btn);
    return {
      text: btn.textContent.trim(),
      background: style.background.substring(0, 150),
      color: style.color,
      border: style.border,
      borderRadius: style.borderRadius,
      padding: style.padding,
    };
  });
  console.log('Nav CTA button:', JSON.stringify(navCtaInfo, null, 2));

  // Check footer Subscribe button
  const footerBtn = await page.evaluate(() => {
    const btns = document.querySelectorAll('button');
    const subscribe = Array.from(btns).find(b => b.textContent.trim() === 'Subscribe');
    if (!subscribe) return { error: 'No subscribe button found' };
    const style = window.getComputedStyle(subscribe);
    return {
      text: subscribe.textContent.trim(),
      background: style.background.substring(0, 150),
      color: style.color,
      border: style.border,
      borderRadius: style.borderRadius,
      fontFamily: style.fontFamily.substring(0, 80),
    };
  });
  console.log('Footer Subscribe button:', JSON.stringify(footerBtn, null, 2));

  await browser.close();
}

run().catch(console.error);
