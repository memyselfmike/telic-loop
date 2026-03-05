import { chromium } from 'playwright-core';

const BROWSER_PATH = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE_URL = 'http://localhost:4321';
const VIEWPORT = { width: 1440, height: 900 };

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function run() {
  const browser = await chromium.launch({
    executablePath: BROWSER_PATH,
    headless: true,
  });
  const context = await browser.newContext({ viewport: VIEWPORT });
  const page = await context.newPage();

  // ── PART 1: Full homepage scroll-through ──
  console.log('=== HOMEPAGE FULL SCROLL AUDIT ===');
  await page.goto(BASE_URL + '/', { waitUntil: 'networkidle' });
  await sleep(2000); // Let animations settle

  // Get total page height
  const totalHeight = await page.evaluate(() => document.body.scrollHeight);
  console.log(`Page total height: ${totalHeight}px`);

  // Screenshot at y=0 (Hero section)
  await page.screenshot({ path: 'audit/01_hero.png' });
  console.log('Captured: Hero section (y=0)');

  // Scroll down in 800px increments
  const scrollPositions = [
    { y: 800, name: '02_trust_bar' },
    { y: 1600, name: '03_features_top' },
    { y: 2400, name: '04_features_bottom' },
    { y: 3200, name: '05_beep_methodology' },
    { y: 4000, name: '06_beep_bottom' },
    { y: 4800, name: '07_testimonials' },
    { y: 5600, name: '08_cta_banner' },
    { y: 6400, name: '09_footer' },
    { y: 7200, name: '10_extra1' },
    { y: 8000, name: '11_extra2' },
  ];

  for (const pos of scrollPositions) {
    if (pos.y >= totalHeight) break;
    await page.evaluate(y => window.scrollTo(0, y), pos.y);
    await sleep(500);
    await page.screenshot({ path: `audit/${pos.name}.png` });
    console.log(`Captured: ${pos.name} (y=${pos.y})`);
  }

  // Also capture bottom of page
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await sleep(500);
  await page.screenshot({ path: 'audit/12_page_bottom.png' });
  console.log('Captured: Page bottom');

  // ── PART 2: Header inspection ──
  console.log('\n=== HEADER INSPECTION ===');
  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(300);

  const headerInfo = await page.evaluate(() => {
    const header = document.querySelector('header');
    if (!header) return { error: 'No header found' };
    const links = header.querySelectorAll('a');
    const linkData = Array.from(links).map(a => ({
      text: a.textContent.trim(),
      href: a.getAttribute('href'),
    }));
    const style = window.getComputedStyle(header);
    return {
      position: style.position,
      backgroundColor: style.backgroundColor,
      linkCount: links.length,
      links: linkData,
    };
  });
  console.log('Header info:', JSON.stringify(headerInfo, null, 2));

  // Check header stickiness by scrolling
  await page.evaluate(() => window.scrollTo(0, 500));
  await sleep(500);
  await page.screenshot({ path: 'audit/13_header_sticky.png' });
  console.log('Captured: Header sticky state at y=500');

  // ── PART 3: Navigate to each page ──
  console.log('\n=== NAVIGATION TEST ===');
  const navLinks = [
    { name: 'Home', path: '/' },
    { name: 'About', path: '/about' },
    { name: 'Services', path: '/services' },
    { name: 'How It Works', path: '/how-it-works' },
    { name: 'Blog', path: '/blog' },
    { name: 'Contact', path: '/contact' },
  ];

  // First, get actual nav links from the page
  await page.goto(BASE_URL + '/', { waitUntil: 'networkidle' });
  const actualNavLinks = await page.evaluate(() => {
    const nav = document.querySelector('nav');
    if (!nav) return [];
    return Array.from(nav.querySelectorAll('a')).map(a => ({
      text: a.textContent.trim(),
      href: a.getAttribute('href'),
    }));
  });
  console.log('Actual nav links:', JSON.stringify(actualNavLinks, null, 2));

  // Navigate to each link
  for (const link of actualNavLinks) {
    try {
      const url = link.href.startsWith('http') ? link.href : BASE_URL + link.href;
      const response = await page.goto(url, { waitUntil: 'networkidle', timeout: 10000 });
      const status = response ? response.status() : 'unknown';
      const title = await page.title();
      const safeName = link.text.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase();
      await page.screenshot({ path: `audit/nav_${safeName}.png` });
      console.log(`  ${link.text} (${link.href}) -> Status: ${status}, Title: "${title}"`);
    } catch (err) {
      console.log(`  ${link.text} (${link.href}) -> ERROR: ${err.message}`);
    }
  }

  // ── PART 4: Detailed section analysis ──
  console.log('\n=== SECTION DETAIL ANALYSIS ===');
  await page.goto(BASE_URL + '/', { waitUntil: 'networkidle' });
  await sleep(1500);

  const sectionAnalysis = await page.evaluate(() => {
    const results = {};

    // Body/page background
    const bodyStyle = window.getComputedStyle(document.body);
    results.bodyBackground = bodyStyle.backgroundColor;

    // All sections
    const sections = document.querySelectorAll('section');
    results.sectionCount = sections.length;
    results.sections = Array.from(sections).map((sec, i) => {
      const style = window.getComputedStyle(sec);
      const rect = sec.getBoundingClientRect();
      return {
        index: i,
        id: sec.id || '(none)',
        className: sec.className.substring(0, 100),
        top: Math.round(rect.top + window.scrollY),
        height: Math.round(rect.height),
        background: style.backgroundColor,
        firstHeading: sec.querySelector('h1,h2,h3')?.textContent?.trim().substring(0, 80) || '(none)',
      };
    });

    // Cards analysis
    const cards = document.querySelectorAll('[class*="card"], [class*="Card"]');
    results.cardCount = cards.length;
    if (cards.length > 0) {
      const firstCard = cards[0];
      const cardStyle = window.getComputedStyle(firstCard);
      results.cardSample = {
        background: cardStyle.backgroundColor,
        backdropFilter: cardStyle.backdropFilter || cardStyle.webkitBackdropFilter,
        border: cardStyle.border,
        borderRadius: cardStyle.borderRadius,
        boxShadow: cardStyle.boxShadow,
      };
    }

    // Buttons analysis
    const buttons = document.querySelectorAll('button, a[class*="btn"], a[class*="button"], [class*="Button"]');
    results.buttonCount = buttons.length;
    results.buttons = Array.from(buttons).slice(0, 10).map(btn => {
      const style = window.getComputedStyle(btn);
      return {
        text: btn.textContent.trim().substring(0, 50),
        background: style.background.substring(0, 150),
        backgroundImage: style.backgroundImage.substring(0, 150),
        color: style.color,
        border: style.border,
        borderRadius: style.borderRadius,
        padding: style.padding,
      };
    });

    // Counters / trust bar
    const counters = document.querySelectorAll('[class*="counter"], [class*="Counter"], [class*="stat"], [class*="Stat"], [class*="trust"], [class*="Trust"]');
    results.counterElements = counters.length;

    return results;
  });
  console.log('Section analysis:', JSON.stringify(sectionAnalysis, null, 2));

  await browser.close();
  console.log('\n=== AUDIT COMPLETE ===');
}

run().catch(console.error);
