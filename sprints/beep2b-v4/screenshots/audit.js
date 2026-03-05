const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();
  const outDir = path.join(__dirname, 'audit');

  // Create output directory
  const fs = require('fs');
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

  // Navigate to the page
  console.log('Navigating to http://localhost:4321 ...');
  await page.goto('http://localhost:4321', { waitUntil: 'networkidle', timeout: 30000 });

  // Wait a moment for animations to potentially start
  await page.waitForTimeout(1500);

  // 1. Full page screenshot (initial load, top of page)
  console.log('1. Taking full-page initial screenshot...');
  await page.screenshot({ path: path.join(outDir, '01-full-page-top.png'), fullPage: false });

  // 2. Full page screenshot (entire page)
  console.log('2. Taking full-page screenshot...');
  await page.screenshot({ path: path.join(outDir, '02-full-page-all.png'), fullPage: true });

  // 3. Hero section (should be visible on initial load)
  console.log('3. Screenshotting hero section...');
  const hero = await page.$('.hero');
  if (hero) {
    await hero.screenshot({ path: path.join(outDir, '03-hero.png') });
  } else {
    console.log('  WARNING: .hero element not found');
  }

  // 4. Header / nav
  console.log('4. Screenshotting header...');
  const header = await page.$('.header');
  if (header) {
    await header.screenshot({ path: path.join(outDir, '04-header.png') });
  } else {
    console.log('  WARNING: .header element not found');
  }

  // 5. Trust bar - scroll to it first to trigger animations
  console.log('5. Scrolling to and screenshotting trust bar...');
  const trustBar = await page.$('.trust-bar');
  if (trustBar) {
    await trustBar.scrollIntoViewIfNeeded();
    await page.waitForTimeout(800);
    await trustBar.screenshot({ path: path.join(outDir, '05-trust-bar.png') });
  } else {
    console.log('  WARNING: .trust-bar element not found');
  }

  // 6. Features grid
  console.log('6. Scrolling to and screenshotting features grid...');
  const featuresGrid = await page.$('.features-grid');
  if (featuresGrid) {
    await featuresGrid.scrollIntoViewIfNeeded();
    await page.waitForTimeout(800);
    await featuresGrid.screenshot({ path: path.join(outDir, '06-features-grid.png') });
  } else {
    console.log('  WARNING: .features-grid element not found');
  }

  // Also get the section heading above the features grid
  const featureHeading = await page.$('text=Systematic B2B Lead Generation');
  if (featureHeading) {
    // Get parent section
    const featureSection = await featureHeading.evaluate(el => {
      let parent = el.closest('section') || el.parentElement;
      return parent ? parent.getBoundingClientRect() : null;
    });
  }

  // 7. BEEP preview section
  console.log('7. Scrolling to and screenshotting BEEP preview...');
  const beepSteps = await page.$('.beep-steps');
  if (beepSteps) {
    await beepSteps.scrollIntoViewIfNeeded();
    await page.waitForTimeout(800);
    await beepSteps.screenshot({ path: path.join(outDir, '07-beep-steps.png') });
  } else {
    console.log('  WARNING: .beep-steps element not found');
  }

  // 8. Testimonials
  console.log('8. Scrolling to and screenshotting testimonials...');
  const testimonials = await page.$('.testimonials-grid');
  if (testimonials) {
    await testimonials.scrollIntoViewIfNeeded();
    await page.waitForTimeout(800);
    await testimonials.screenshot({ path: path.join(outDir, '08-testimonials.png') });
  } else {
    console.log('  WARNING: .testimonials-grid element not found');
    // Check if the heading exists at least
    const testHeading = await page.$('text=Real Results from Real Clients');
    if (testHeading) {
      console.log('  NOTE: Heading exists but grid is empty (no testimonials loaded from CMS)');
      await testHeading.scrollIntoViewIfNeeded();
      await page.waitForTimeout(500);
      await page.screenshot({ path: path.join(outDir, '08-testimonials-area.png'), fullPage: false });
    }
  }

  // 9. CTA banner
  console.log('9. Scrolling to and screenshotting CTA banner...');
  const ctaBanner = await page.$('.cta-banner');
  if (ctaBanner) {
    await ctaBanner.scrollIntoViewIfNeeded();
    await page.waitForTimeout(800);
    await ctaBanner.screenshot({ path: path.join(outDir, '09-cta-banner.png') });
  } else {
    console.log('  WARNING: .cta-banner element not found');
  }

  // 10. Footer
  console.log('10. Scrolling to and screenshotting footer...');
  const footer = await page.$('.footer');
  if (footer) {
    await footer.scrollIntoViewIfNeeded();
    await page.waitForTimeout(800);
    await footer.screenshot({ path: path.join(outDir, '10-footer.png') });
  } else {
    console.log('  WARNING: .footer element not found');
  }

  // 11. Now scroll back to top and check header stickiness
  console.log('11. Scrolling back to top, checking sticky header...');
  // First scroll down a bit
  await page.evaluate(() => window.scrollTo(0, 500));
  await page.waitForTimeout(500);
  await page.screenshot({ path: path.join(outDir, '11-header-sticky-scrolled.png'), fullPage: false });

  // 12. Scroll to top
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(500);
  await page.screenshot({ path: path.join(outDir, '12-header-at-top.png'), fullPage: false });

  // 13. Check for animation states - scroll through page slowly to trigger all animations
  console.log('13. Checking animation trigger states...');
  const pageHeight = await page.evaluate(() => document.body.scrollHeight);
  const viewportHeight = 900;
  let scrollPos = 0;
  let shotIdx = 13;

  // Scroll in chunks to trigger animations
  while (scrollPos < pageHeight) {
    scrollPos += viewportHeight * 0.6; // 60% viewport overlap
    await page.evaluate((y) => window.scrollTo(0, y), scrollPos);
    await page.waitForTimeout(400);
  }

  // Now go back through and check which elements got animated
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(300);

  // Check animated state of elements
  const animationStates = await page.evaluate(() => {
    const results = [];
    document.querySelectorAll('[data-animate]').forEach(el => {
      results.push({
        tag: el.tagName,
        text: el.textContent.trim().substring(0, 50),
        animated: el.classList.contains('animated'),
        opacity: window.getComputedStyle(el).opacity,
        transform: window.getComputedStyle(el).transform,
      });
    });
    return results;
  });
  console.log('\nAnimation states after full scroll:');
  animationStates.forEach(s => {
    console.log(`  [${s.animated ? 'ANIMATED' : 'NOT-ANIMATED'}] <${s.tag}> "${s.text}" opacity=${s.opacity} transform=${s.transform}`);
  });

  // Check stagger animation states
  const staggerStates = await page.evaluate(() => {
    const results = [];
    document.querySelectorAll('[data-stagger] > *').forEach(el => {
      results.push({
        tag: el.tagName,
        text: el.textContent.trim().substring(0, 50),
        animated: el.classList.contains('stagger-animated'),
        opacity: window.getComputedStyle(el).opacity,
      });
    });
    return results;
  });
  console.log('\nStagger animation states:');
  staggerStates.forEach(s => {
    console.log(`  [${s.animated ? 'ANIMATED' : 'NOT-ANIMATED'}] <${s.tag}> "${s.text}" opacity=${s.opacity}`);
  });

  // 14. Counter states
  const counterStates = await page.evaluate(() => {
    const results = [];
    document.querySelectorAll('[data-counter]').forEach(el => {
      results.push({
        target: el.dataset.counter,
        currentText: el.textContent.trim(),
      });
    });
    return results;
  });
  console.log('\nCounter states:');
  counterStates.forEach(s => {
    console.log(`  target=${s.target} current="${s.currentText}"`);
  });

  // 15. Check nav links
  const navLinks = await page.evaluate(() => {
    const links = document.querySelectorAll('.nav-links a');
    return Array.from(links).map(a => ({
      text: a.textContent.trim(),
      href: a.href,
      classes: a.className,
    }));
  });
  console.log('\nNav links:');
  navLinks.forEach(l => {
    console.log(`  "${l.text}" -> ${l.href} [${l.classes}]`);
  });

  // 16. Check Book a Call CTA button
  const ctaButton = await page.evaluate(() => {
    const btn = document.querySelector('.nav-cta .btn');
    if (!btn) return null;
    const styles = window.getComputedStyle(btn);
    return {
      text: btn.textContent.trim(),
      display: styles.display,
      padding: styles.padding,
      background: styles.background,
      backgroundColor: styles.backgroundColor,
      borderRadius: styles.borderRadius,
      color: styles.color,
      cursor: styles.cursor,
    };
  });
  console.log('\nCTA Button styles:');
  console.log(JSON.stringify(ctaButton, null, 2));

  // 17. Header glass-morphism check
  const headerStyles = await page.evaluate(() => {
    const header = document.querySelector('.header');
    if (!header) return null;
    const styles = window.getComputedStyle(header);
    return {
      position: styles.position,
      background: styles.background,
      backgroundColor: styles.backgroundColor,
      backdropFilter: styles.backdropFilter,
      webkitBackdropFilter: styles.webkitBackdropFilter,
      zIndex: styles.zIndex,
      borderBottom: styles.borderBottom,
      top: styles.top,
    };
  });
  console.log('\nHeader styles (glass-morphism check):');
  console.log(JSON.stringify(headerStyles, null, 2));

  // 18. Card glass-morphism check
  const cardStyles = await page.evaluate(() => {
    const card = document.querySelector('.card');
    if (!card) return null;
    const styles = window.getComputedStyle(card);
    return {
      background: styles.background,
      backgroundColor: styles.backgroundColor,
      backdropFilter: styles.backdropFilter,
      webkitBackdropFilter: styles.webkitBackdropFilter,
      border: styles.border,
      borderRadius: styles.borderRadius,
    };
  });
  console.log('\nCard glass-morphism check:');
  console.log(JSON.stringify(cardStyles, null, 2));

  // 19. Text contrast analysis
  const contrastData = await page.evaluate(() => {
    const results = [];
    // Check key text elements
    const selectors = [
      { name: 'Hero headline', sel: '.hero-headline' },
      { name: 'Hero subtitle', sel: '.hero-subtitle' },
      { name: 'Trust number', sel: '.trust-number' },
      { name: 'Trust label', sel: '.trust-label' },
      { name: 'Section heading', sel: '.section-heading' },
      { name: 'Feature title', sel: '.feature-title' },
      { name: 'Feature description', sel: '.feature-description' },
      { name: 'BEEP step title', sel: '.beep-step-title' },
      { name: 'BEEP step description', sel: '.beep-step-description' },
      { name: 'CTA heading', sel: '.cta-heading' },
      { name: 'CTA text', sel: '.cta-text' },
      { name: 'Footer tagline', sel: '.footer-tagline' },
      { name: 'Footer copyright', sel: '.footer-copyright' },
      { name: 'Nav links', sel: '.nav-links a' },
      { name: 'Section label', sel: '.section-label' },
    ];

    selectors.forEach(({ name, sel }) => {
      const el = document.querySelector(sel);
      if (el) {
        const styles = window.getComputedStyle(el);
        results.push({
          name,
          color: styles.color,
          backgroundColor: styles.backgroundColor,
          fontSize: styles.fontSize,
          fontWeight: styles.fontWeight,
          webkitTextFillColor: styles.webkitTextFillColor,
        });
      }
    });
    return results;
  });
  console.log('\nText contrast data:');
  contrastData.forEach(d => {
    console.log(`  ${d.name}: color=${d.color} bg=${d.backgroundColor} size=${d.fontSize} weight=${d.fontWeight} fill=${d.webkitTextFillColor}`);
  });

  // 20. Check if any images failed to load
  const brokenImages = await page.evaluate(() => {
    const imgs = document.querySelectorAll('img');
    return Array.from(imgs).filter(img => !img.complete || img.naturalWidth === 0).map(img => ({
      src: img.src,
      alt: img.alt,
    }));
  });
  console.log('\nBroken images:');
  if (brokenImages.length === 0) {
    console.log('  None found (or no images on page)');
  } else {
    brokenImages.forEach(img => console.log(`  BROKEN: ${img.src} alt="${img.alt}"`));
  }

  // 21. Check overall page dimensions and section visibility
  const sectionInfo = await page.evaluate(() => {
    const sections = [
      { name: 'Hero', sel: '.hero' },
      { name: 'Trust Bar', sel: '.trust-bar' },
      { name: 'Features Grid', sel: '.features-grid' },
      { name: 'BEEP Steps', sel: '.beep-steps' },
      { name: 'Testimonials', sel: '.testimonials-grid' },
      { name: 'CTA Banner', sel: '.cta-banner' },
      { name: 'Footer', sel: '.footer' },
    ];

    return sections.map(({ name, sel }) => {
      const el = document.querySelector(sel);
      if (!el) return { name, found: false };
      const rect = el.getBoundingClientRect();
      const style = window.getComputedStyle(el);
      return {
        name,
        found: true,
        width: rect.width,
        height: rect.height,
        display: style.display,
        visibility: style.visibility,
        overflow: style.overflow,
        childCount: el.children.length,
      };
    });
  });
  console.log('\nSection dimensions and visibility:');
  sectionInfo.forEach(s => {
    if (!s.found) {
      console.log(`  ${s.name}: NOT FOUND`);
    } else {
      console.log(`  ${s.name}: ${s.width}x${s.height} display=${s.display} vis=${s.visibility} overflow=${s.overflow} children=${s.childCount}`);
    }
  });

  // 22. Take a final full-page screenshot after all scrolling (animations triggered)
  console.log('\n22. Taking final full-page screenshot with animations triggered...');
  // Scroll through entire page one more time to ensure all animations fire
  for (let y = 0; y < pageHeight; y += 300) {
    await page.evaluate((pos) => window.scrollTo(0, pos), y);
    await page.waitForTimeout(150);
  }
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(500);
  await page.screenshot({ path: path.join(outDir, '14-final-full-animated.png'), fullPage: true });

  console.log('\nDone! Screenshots saved to:', outDir);
  await browser.close();
})();
