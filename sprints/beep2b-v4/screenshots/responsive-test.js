const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE = 'http://localhost:4321';
const OUT = path.join(__dirname, 'responsive-results');

// Ensure output directory exists
if (!fs.existsSync(OUT)) fs.mkdirSync(OUT, { recursive: true });

const VIEWPORTS = {
  tablet: { width: 768, height: 1024 },
  mobile: { width: 480, height: 844 },
};

const PAGES = [
  { name: 'home', path: '/' },
  { name: 'services', path: '/services' },
  { name: 'contact', path: '/contact' },
  { name: 'blog', path: '/blog' },
  { name: 'about', path: '/about' },
];

async function measureElement(page, selector) {
  try {
    return await page.evaluate((sel) => {
      const el = document.querySelector(sel);
      if (!el) return null;
      const rect = el.getBoundingClientRect();
      const style = window.getComputedStyle(el);
      return {
        width: rect.width,
        height: rect.height,
        top: rect.top,
        left: rect.left,
        right: rect.right,
        bottom: rect.bottom,
        fontSize: style.fontSize,
        display: style.display,
        overflow: style.overflow,
        padding: style.padding,
      };
    }, selector);
  } catch {
    return null;
  }
}

async function checkHorizontalOverflow(page) {
  return await page.evaluate(() => {
    const docWidth = document.documentElement.scrollWidth;
    const viewWidth = document.documentElement.clientWidth;
    const overflow = docWidth > viewWidth;
    return {
      overflow,
      docWidth,
      viewWidth,
      overflowPx: docWidth - viewWidth,
    };
  });
}

async function checkTapTargets(page) {
  return await page.evaluate(() => {
    const interactive = document.querySelectorAll('a, button, input, textarea, select, [role="button"]');
    const smallTargets = [];
    for (const el of interactive) {
      const rect = el.getBoundingClientRect();
      // Skip hidden elements
      if (rect.width === 0 && rect.height === 0) continue;
      const style = window.getComputedStyle(el);
      if (style.display === 'none' || style.visibility === 'hidden') continue;

      if (rect.width < 44 || rect.height < 44) {
        smallTargets.push({
          tag: el.tagName.toLowerCase(),
          text: (el.textContent || '').trim().slice(0, 40),
          width: Math.round(rect.width),
          height: Math.round(rect.height),
          href: el.href || '',
        });
      }
    }
    return smallTargets;
  });
}

async function checkOverlappingElements(page) {
  return await page.evaluate(() => {
    const elements = document.querySelectorAll('h1, h2, h3, p, a, button, img, .card, .btn, input, textarea');
    const rects = [];
    for (const el of elements) {
      const rect = el.getBoundingClientRect();
      if (rect.width === 0 && rect.height === 0) continue;
      const style = window.getComputedStyle(el);
      if (style.display === 'none' || style.visibility === 'hidden') continue;
      rects.push({
        tag: el.tagName.toLowerCase() + (el.className ? '.' + el.className.split(' ')[0] : ''),
        top: rect.top,
        left: rect.left,
        right: rect.right,
        bottom: rect.bottom,
        text: (el.textContent || '').trim().slice(0, 30),
      });
    }

    const overlaps = [];
    for (let i = 0; i < rects.length; i++) {
      for (let j = i + 1; j < rects.length; j++) {
        const a = rects[i], b = rects[j];
        // Check overlap only for elements at same visual level
        if (a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top) {
          const overlapArea = Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left)) *
                             Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
          const aArea = (a.right - a.left) * (a.bottom - a.top);
          const bArea = (b.right - b.left) * (b.bottom - b.top);
          const overlapRatio = overlapArea / Math.min(aArea, bArea);
          // Only report significant overlaps (>50% of smaller element)
          if (overlapRatio > 0.5 && overlapArea > 100) {
            overlaps.push({
              el1: `${a.tag}: "${a.text}"`,
              el2: `${b.tag}: "${b.text}"`,
              overlapRatio: Math.round(overlapRatio * 100) + '%',
            });
          }
        }
      }
    }
    return overlaps.slice(0, 10); // Limit to top 10
  });
}

async function testMobileNav(page, viewport) {
  const results = {};

  // Check hamburger visibility
  const hamburger = await measureElement(page, '.mobile-toggle');
  results.hamburgerVisible = hamburger && hamburger.display !== 'none';
  results.hamburgerSize = hamburger ? `${Math.round(hamburger.width)}x${Math.round(hamburger.height)}` : 'N/A';

  // Check nav-links initial state
  const navLinks = await measureElement(page, '.nav-links');
  results.navLinksHidden = navLinks ? (navLinks.left >= viewport.width || navLinks.display === 'none') : true;

  if (results.hamburgerVisible) {
    // Click hamburger
    try {
      await page.click('#mobile-toggle');
      await page.waitForTimeout(500); // Wait for animation

      // Take screenshot with menu open
      await page.screenshot({
        path: path.join(OUT, `nav-open-${viewport.width}px.png`),
        fullPage: false,
      });

      const navOpen = await measureElement(page, '.nav-links');
      results.menuOpened = navOpen && navOpen.left < viewport.width;
      results.menuWidth = navOpen ? Math.round(navOpen.width) : 0;

      // Check if nav links are accessible (font size, tap targets)
      const navLinkMeasure = await page.evaluate(() => {
        const links = document.querySelectorAll('.nav-links a');
        return Array.from(links).map(a => {
          const rect = a.getBoundingClientRect();
          const style = window.getComputedStyle(a);
          return {
            text: a.textContent.trim(),
            width: Math.round(rect.width),
            height: Math.round(rect.height),
            fontSize: style.fontSize,
          };
        });
      });
      results.navLinkDetails = navLinkMeasure;

      // Close via Escape
      await page.keyboard.press('Escape');
      await page.waitForTimeout(400);

      const navClosed = await measureElement(page, '.nav-links');
      results.menuClosedViaEscape = navClosed ? (navClosed.left >= viewport.width) : true;

    } catch (e) {
      results.menuError = e.message;
    }
  }

  return results;
}

async function testPage(page, pageDef, viewportName, viewport) {
  console.log(`\n  Testing ${pageDef.name} at ${viewport.width}px...`);

  await page.goto(`${BASE}${pageDef.path}`, { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(500);

  // Full page screenshot
  await page.screenshot({
    path: path.join(OUT, `${viewportName}-${pageDef.name}.png`),
    fullPage: true,
  });

  // Viewport-only screenshot
  await page.screenshot({
    path: path.join(OUT, `${viewportName}-${pageDef.name}-viewport.png`),
    fullPage: false,
  });

  const results = {
    page: pageDef.name,
    viewport: `${viewport.width}x${viewport.height}`,
  };

  // 1. Horizontal overflow check
  results.overflow = await checkHorizontalOverflow(page);

  // 2. Tap targets
  results.smallTapTargets = await checkTapTargets(page);

  // 3. Overlapping elements
  results.overlaps = await checkOverlappingElements(page);

  // 4. Page-specific checks
  if (pageDef.name === 'home') {
    results.heroHeadline = await measureElement(page, '.hero-headline');
    results.featuresGrid = await measureElement(page, '.features-grid');
    results.beepSteps = await measureElement(page, '.beep-steps');
    results.trustBar = await measureElement(page, '.trust-bar');

    // Check grid column count
    results.featuresGridCols = await page.evaluate(() => {
      const grid = document.querySelector('.features-grid');
      if (!grid) return null;
      return window.getComputedStyle(grid).gridTemplateColumns;
    });
    results.beepStepsCols = await page.evaluate(() => {
      const grid = document.querySelector('.beep-steps');
      if (!grid) return null;
      return window.getComputedStyle(grid).gridTemplateColumns;
    });
    results.trustBarCols = await page.evaluate(() => {
      const grid = document.querySelector('.trust-bar');
      if (!grid) return null;
      return window.getComputedStyle(grid).gridTemplateColumns;
    });
  }

  if (pageDef.name === 'services') {
    results.serviceHeader = await measureElement(page, '.service-header');
    results.serviceHeaderCols = await page.evaluate(() => {
      const grid = document.querySelector('.service-header');
      if (!grid) return null;
      return window.getComputedStyle(grid).gridTemplateColumns;
    });
    results.serviceCta = await measureElement(page, '.service-cta');
    results.serviceCtaDirection = await page.evaluate(() => {
      const el = document.querySelector('.service-cta');
      if (!el) return null;
      return window.getComputedStyle(el).flexDirection;
    });
  }

  if (pageDef.name === 'contact') {
    results.contactContainer = await measureElement(page, '.contact-container');
    results.contactContainerCols = await page.evaluate(() => {
      const grid = document.querySelector('.contact-container');
      if (!grid) return null;
      return window.getComputedStyle(grid).gridTemplateColumns;
    });
    results.faqGrid = await measureElement(page, '.faq-grid');
    results.faqGridCols = await page.evaluate(() => {
      const grid = document.querySelector('.faq-grid');
      if (!grid) return null;
      return window.getComputedStyle(grid).gridTemplateColumns;
    });
  }

  if (pageDef.name === 'blog') {
    results.postsGrid = await measureElement(page, '.posts-grid');
    results.postsGridCols = await page.evaluate(() => {
      const grid = document.querySelector('.posts-grid');
      if (!grid) return null;
      return window.getComputedStyle(grid).gridTemplateColumns;
    });
    results.filterButtons = await measureElement(page, '.filter-buttons');
    results.filterDirection = await page.evaluate(() => {
      const el = document.querySelector('.filter-buttons');
      if (!el) return null;
      return window.getComputedStyle(el).flexDirection;
    });
  }

  if (pageDef.name === 'about') {
    results.timeline = await measureElement(page, '.timeline');
    results.timelineItemCols = await page.evaluate(() => {
      const item = document.querySelector('.timeline-item');
      if (!item) return null;
      return window.getComputedStyle(item).gridTemplateColumns;
    });
    results.valuesGrid = await measureElement(page, '.values-grid');
    results.valuesGridCols = await page.evaluate(() => {
      const grid = document.querySelector('.values-grid');
      if (!grid) return null;
      return window.getComputedStyle(grid).gridTemplateColumns;
    });
    results.statsContainer = await measureElement(page, '.stats-container');
    results.statsContainerCols = await page.evaluate(() => {
      const grid = document.querySelector('.stats-container');
      if (!grid) return null;
      return window.getComputedStyle(grid).gridTemplateColumns;
    });
  }

  // Footer check (all pages)
  results.footerGrid = await measureElement(page, '.footer-grid');
  results.footerGridCols = await page.evaluate(() => {
    const grid = document.querySelector('.footer-grid');
    if (!grid) return null;
    return window.getComputedStyle(grid).gridTemplateColumns;
  });

  return results;
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const allResults = {};

  for (const [vpName, vp] of Object.entries(VIEWPORTS)) {
    console.log(`\n=== Testing ${vpName} (${vp.width}x${vp.height}) ===`);

    const context = await browser.newContext({
      viewport: vp,
      deviceScaleFactor: 2,
    });
    const page = await context.newPage();

    allResults[vpName] = { viewport: vp, pages: {}, nav: {} };

    // Test nav on home page first
    await page.goto(BASE, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(500);
    allResults[vpName].nav = await testMobileNav(page, vp);

    // Test each page
    for (const pageDef of PAGES) {
      allResults[vpName].pages[pageDef.name] = await testPage(page, pageDef, vpName, vp);
    }

    await context.close();
  }

  // Write JSON results
  fs.writeFileSync(
    path.join(OUT, 'results.json'),
    JSON.stringify(allResults, null, 2)
  );

  // Print summary
  console.log('\n\n========================================');
  console.log('RESPONSIVE LAYOUT TEST RESULTS');
  console.log('========================================');

  for (const [vpName, vpData] of Object.entries(allResults)) {
    console.log(`\n--- ${vpName.toUpperCase()} (${vpData.viewport.width}x${vpData.viewport.height}) ---`);

    // Nav results
    const nav = vpData.nav;
    console.log(`\n  Mobile Nav:`);
    console.log(`    Hamburger visible: ${nav.hamburgerVisible}`);
    console.log(`    Hamburger size: ${nav.hamburgerSize}`);
    console.log(`    Menu opens on click: ${nav.menuOpened}`);
    console.log(`    Menu closes on Escape: ${nav.menuClosedViaEscape}`);
    if (nav.navLinkDetails) {
      console.log(`    Nav link sizes:`);
      for (const link of nav.navLinkDetails) {
        console.log(`      "${link.text}" - ${link.width}x${link.height}px, font: ${link.fontSize}`);
      }
    }

    // Per-page results
    for (const [pageName, pageData] of Object.entries(vpData.pages)) {
      console.log(`\n  ${pageName.toUpperCase()} page:`);

      // Overflow
      const ov = pageData.overflow;
      console.log(`    Horizontal overflow: ${ov.overflow ? `YES (+${ov.overflowPx}px)` : 'NONE'}`);

      // Small tap targets
      if (pageData.smallTapTargets.length > 0) {
        console.log(`    Small tap targets (< 44px): ${pageData.smallTapTargets.length}`);
        for (const t of pageData.smallTapTargets.slice(0, 5)) {
          console.log(`      <${t.tag}> "${t.text}" - ${t.width}x${t.height}px`);
        }
        if (pageData.smallTapTargets.length > 5) {
          console.log(`      ... and ${pageData.smallTapTargets.length - 5} more`);
        }
      } else {
        console.log(`    Small tap targets: NONE (all >= 44px)`);
      }

      // Overlaps
      if (pageData.overlaps && pageData.overlaps.length > 0) {
        console.log(`    Overlapping elements: ${pageData.overlaps.length}`);
        for (const o of pageData.overlaps) {
          console.log(`      ${o.el1} overlaps ${o.el2} (${o.overlapRatio})`);
        }
      } else {
        console.log(`    Overlapping elements: NONE`);
      }

      // Page-specific
      if (pageName === 'home') {
        if (pageData.heroHeadline) {
          console.log(`    Hero headline font-size: ${pageData.heroHeadline.fontSize}`);
          console.log(`    Hero headline width: ${Math.round(pageData.heroHeadline.width)}px`);
        }
        console.log(`    Features grid columns: ${pageData.featuresGridCols || 'N/A'}`);
        console.log(`    BEEP steps columns: ${pageData.beepStepsCols || 'N/A'}`);
        console.log(`    Trust bar columns: ${pageData.trustBarCols || 'N/A'}`);
      }

      if (pageName === 'services') {
        console.log(`    Service header columns: ${pageData.serviceHeaderCols || 'N/A'}`);
        console.log(`    Service CTA direction: ${pageData.serviceCtaDirection || 'N/A'}`);
      }

      if (pageName === 'contact') {
        console.log(`    Contact container columns: ${pageData.contactContainerCols || 'N/A'}`);
        console.log(`    FAQ grid columns: ${pageData.faqGridCols || 'N/A'}`);
      }

      if (pageName === 'blog') {
        console.log(`    Posts grid columns: ${pageData.postsGridCols || 'N/A'}`);
        console.log(`    Filter direction: ${pageData.filterDirection || 'N/A'}`);
      }

      if (pageName === 'about') {
        console.log(`    Timeline item columns: ${pageData.timelineItemCols || 'N/A'}`);
        console.log(`    Values grid columns: ${pageData.valuesGridCols || 'N/A'}`);
        console.log(`    Stats container columns: ${pageData.statsContainerCols || 'N/A'}`);
      }

      // Footer (all pages, but only report once per viewport from home)
      if (pageName === 'home') {
        console.log(`    Footer grid columns: ${pageData.footerGridCols || 'N/A'}`);
      }
    }
  }

  console.log('\n\nScreenshots saved to:', OUT);
  console.log('JSON results saved to:', path.join(OUT, 'results.json'));

  await browser.close();
})();
