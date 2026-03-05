const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();
  const outDir = path.join(__dirname, 'audit');
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

  await page.goto('http://localhost:4321', { waitUntil: 'networkidle', timeout: 30000 });

  // Scroll through the entire page first to trigger ALL animations
  const pageHeight = await page.evaluate(() => document.body.scrollHeight);
  for (let y = 0; y < pageHeight; y += 300) {
    await page.evaluate((pos) => window.scrollTo(0, pos), y);
    await page.waitForTimeout(100);
  }
  // Wait extra for counters (2 second animation)
  await page.waitForTimeout(2500);

  // Now scroll back up and capture trust bar with completed counters
  const trustBar = await page.$('.trust-bar');
  if (trustBar) {
    await trustBar.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    await trustBar.screenshot({ path: path.join(outDir, '15-trust-bar-final.png') });
  }

  // Check the "Book a Call" nav CTA - zoom in on it
  const navCta = await page.$('.nav-cta');
  if (navCta) {
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(300);
    await navCta.screenshot({ path: path.join(outDir, '16-nav-cta-button.png') });
  }

  // Detailed CTA button analysis
  const ctaAnalysis = await page.evaluate(() => {
    const ctaLink = document.querySelector('.nav-cta a');
    if (!ctaLink) return { error: 'not found' };
    const cs = window.getComputedStyle(ctaLink);
    return {
      text: ctaLink.textContent.trim(),
      tagName: ctaLink.tagName,
      className: ctaLink.className,
      display: cs.display,
      padding: cs.padding,
      paddingTop: cs.paddingTop,
      paddingBottom: cs.paddingBottom,
      paddingLeft: cs.paddingLeft,
      paddingRight: cs.paddingRight,
      background: cs.background,
      backgroundColor: cs.backgroundColor,
      backgroundImage: cs.backgroundImage,
      border: cs.border,
      borderRadius: cs.borderRadius,
      color: cs.color,
      fontSize: cs.fontSize,
      fontWeight: cs.fontWeight,
      cursor: cs.cursor,
      textDecoration: cs.textDecoration,
      boxShadow: cs.boxShadow,
      width: cs.width,
      height: cs.height,
    };
  });
  console.log('CTA Button detailed analysis:');
  console.log(JSON.stringify(ctaAnalysis, null, 2));

  // Check the hero CTA buttons too
  const heroCtas = await page.evaluate(() => {
    const buttons = document.querySelectorAll('.hero-ctas .btn');
    return Array.from(buttons).map(btn => {
      const cs = window.getComputedStyle(btn);
      return {
        text: btn.textContent.trim(),
        className: btn.className,
        display: cs.display,
        padding: cs.padding,
        background: cs.background,
        backgroundColor: cs.backgroundColor,
        backgroundImage: cs.backgroundImage,
        border: cs.border,
        borderRadius: cs.borderRadius,
        color: cs.color,
        boxShadow: cs.boxShadow,
      };
    });
  });
  console.log('\nHero CTA buttons:');
  heroCtas.forEach((b, i) => {
    console.log(`\nButton ${i + 1}:`);
    console.log(JSON.stringify(b, null, 2));
  });

  // Zoom into hero CTA area
  const heroCTAArea = await page.$('.hero-ctas');
  if (heroCTAArea) {
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(300);
    await heroCTAArea.screenshot({ path: path.join(outDir, '17-hero-ctas.png') });
  }

  // Check section label alignment
  const sectionLabels = await page.evaluate(() => {
    const labels = document.querySelectorAll('.section-label');
    return Array.from(labels).map(l => {
      const cs = window.getComputedStyle(l);
      const rect = l.getBoundingClientRect();
      return {
        text: l.textContent.trim(),
        left: rect.left,
        textAlign: cs.textAlign,
        marginLeft: cs.marginLeft,
        paddingLeft: cs.paddingLeft,
        display: cs.display,
      };
    });
  });
  console.log('\nSection label positions:');
  sectionLabels.forEach(l => {
    console.log(`  "${l.text}" left=${l.left}px textAlign=${l.textAlign} display=${l.display}`);
  });

  // Check for the "background" prop on the BEEP Section
  const beepSection = await page.evaluate(() => {
    // The BEEP section has label "Our Methodology"
    const label = Array.from(document.querySelectorAll('.section-label')).find(l => l.textContent.includes('Our Methodology'));
    if (!label) return null;
    const section = label.closest('.section') || label.closest('section');
    if (!section) return null;
    const cs = window.getComputedStyle(section);
    return {
      background: cs.background,
      backgroundColor: cs.backgroundColor,
    };
  });
  console.log('\nBEEP section background:');
  console.log(JSON.stringify(beepSection, null, 2));

  // Check for the 'elevated' background variant
  // The Section component doesn't seem to handle background="elevated" prop
  // Let's check all section backgrounds
  const allSectionBgs = await page.evaluate(() => {
    const sections = document.querySelectorAll('.section');
    return Array.from(sections).map(s => {
      const cs = window.getComputedStyle(s);
      const label = s.querySelector('.section-label');
      return {
        label: label ? label.textContent.trim() : '(no label)',
        background: cs.background,
        backgroundColor: cs.backgroundColor,
      };
    });
  });
  console.log('\nAll section backgrounds:');
  allSectionBgs.forEach(s => {
    console.log(`  "${s.label}" bg=${s.backgroundColor}`);
  });

  // Check the overall visual spacing between sections
  const sectionSpacing = await page.evaluate(() => {
    const elements = [
      { name: 'Hero', sel: '.hero' },
      { name: 'Trust Section', sel: '.trust-bar' },
      { name: 'Divider 1', sel: '.section-divider' },
      { name: 'Features Section', sel: '.features-grid' },
    ];
    return elements.map(({ name, sel }) => {
      const el = document.querySelector(sel);
      if (!el) return { name, found: false };
      const rect = el.getBoundingClientRect();
      return { name, top: rect.top, bottom: rect.bottom, height: rect.height };
    });
  });
  console.log('\nSection spacing (from page top):');
  sectionSpacing.forEach(s => {
    if (!s.found) {
      console.log(`  ${s.name}: NOT FOUND`);
    } else {
      console.log(`  ${s.name}: top=${s.top.toFixed(0)} bottom=${s.bottom.toFixed(0)} height=${s.height.toFixed(0)}`);
    }
  });

  // Check if there's excessive whitespace between sections
  const dividerCount = await page.evaluate(() => document.querySelectorAll('.section-divider').length);
  console.log(`\nSection divider count: ${dividerCount}`);

  // Verify all font-size vars are resolved (not just fallbacks)
  const fontSizeCheck = await page.evaluate(() => {
    const results = [];
    const testCases = [
      { name: 'font-size-5xl', el: '.trust-number' },
      { name: 'font-size-4xl', el: '.section-heading' },
      { name: 'font-size-xl', el: '.feature-title' },
      { name: 'font-size-2xl', el: '.beep-step-title' },
      { name: 'font-size-lg', el: '.section-intro' },
    ];
    testCases.forEach(({ name, el: sel }) => {
      const el = document.querySelector(sel);
      if (!el) {
        results.push({ name, sel, found: false });
        return;
      }
      const cs = window.getComputedStyle(el);
      results.push({
        name,
        sel,
        found: true,
        fontSize: cs.fontSize,
        fontWeight: cs.fontWeight,
      });
    });
    return results;
  });
  console.log('\nFont size variable resolution:');
  fontSizeCheck.forEach(f => {
    if (!f.found) {
      console.log(`  ${f.name} (${f.sel}): NOT FOUND`);
    } else {
      console.log(`  ${f.name} (${f.sel}): ${f.fontSize} weight=${f.fontWeight}`);
    }
  });

  await browser.close();
  console.log('\nDone!');
})();
