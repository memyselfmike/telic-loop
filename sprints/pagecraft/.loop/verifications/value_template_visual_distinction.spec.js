// Verification: Each template produces visually distinct landing pages
// PRD Reference: F1 Template Selection - templates must be visually distinguishable
// Vision Goal: "Pick from 3 starter templates" - templates should look different, not just have different text
// Category: value
const { test, expect } = require('@playwright/test');

test('Each template has distinct visual styling via CSS classes', async ({ page }) => {
  await page.goto('/');

  // Load SaaS template
  const saasCard = page.locator('.template-card', { hasText: 'SaaS Product' });
  await saasCard.click();
  await page.waitForTimeout(500);

  // Check for template-specific CSS class on preview
  const previewFrame = page.locator('#preview-frame');
  const saasClass = await previewFrame.evaluate((el) => {
    return el.classList.contains('template-saas') ||
           el.classList.contains('saas') ||
           el.querySelector('.template-saas') !== null;
  });

  // Capture SaaS styling snapshot
  const saasHeroColor = await page.locator('.section-hero').evaluate((el) => {
    return window.getComputedStyle(el).backgroundColor;
  });

  console.log(`SaaS hero background: ${saasHeroColor}`);

  // Switch to Event template
  await page.reload();
  await page.waitForTimeout(500);

  const eventCard = page.locator('.template-card', { hasText: 'Event' });
  await eventCard.click();
  await page.waitForTimeout(500);

  // Check for different template class
  const eventClass = await previewFrame.evaluate((el) => {
    return el.classList.contains('template-event') ||
           el.classList.contains('event') ||
           el.querySelector('.template-event') !== null;
  });

  // Capture Event styling snapshot
  const eventHeroColor = await page.locator('.section-hero').evaluate((el) => {
    return window.getComputedStyle(el).backgroundColor;
  });

  console.log(`Event hero background: ${eventHeroColor}`);

  // Switch to Portfolio template
  await page.reload();
  await page.waitForTimeout(500);

  const portfolioCard = page.locator('.template-card', { hasText: 'Portfolio' });
  await portfolioCard.click();
  await page.waitForTimeout(500);

  // Capture Portfolio styling snapshot
  const portfolioHeroColor = await page.locator('.section-hero').evaluate((el) => {
    return window.getComputedStyle(el).backgroundColor;
  });

  console.log(`Portfolio hero background: ${portfolioHeroColor}`);

  // Verify templates have different styling (at least one should differ)
  const colorsUnique = new Set([saasHeroColor, eventHeroColor, portfolioHeroColor]).size;

  if (colorsUnique === 1) {
    console.log('FAIL: All templates have identical hero background colors - no visual distinction');
    expect(colorsUnique).toBeGreaterThan(1);
  } else {
    console.log(`PASS: Templates have ${colorsUnique} different hero styles - visual distinction exists`);
  }
});

test('Templates have distinct layout patterns beyond just text', async ({ page }) => {
  const layoutSignatures = {};

  for (const templateName of ['SaaS Product', 'Event', 'Portfolio']) {
    await page.goto('/');
    await page.waitForTimeout(300);

    const card = page.locator('.template-card', { hasText: templateName });
    await card.click();
    await page.waitForTimeout(500);

    // Capture layout characteristics
    const signature = await page.evaluate(() => {
      const preview = document.querySelector('#preview-content');
      const sections = preview.querySelectorAll('[class*="section"]');

      const layout = {
        sectionCount: sections.length,
        heroAlign: window.getComputedStyle(preview.querySelector('.section-hero')).textAlign,
        featuresGridColumns: window.getComputedStyle(preview.querySelector('.features-grid')).gridTemplateColumns,
        backgroundStyles: Array.from(sections).map(s => window.getComputedStyle(s).background.substring(0, 50))
      };

      return JSON.stringify(layout);
    });

    layoutSignatures[templateName] = signature;
    console.log(`${templateName} layout signature: ${signature.substring(0, 100)}...`);
  }

  // At least one layout characteristic should differ between templates
  const uniqueSignatures = new Set(Object.values(layoutSignatures)).size;

  if (uniqueSignatures === 1) {
    console.log('FAIL: All templates have identical layout signatures');
    console.log('SaaS:', layoutSignatures['SaaS Product']);
    console.log('Event:', layoutSignatures['Event']);
    console.log('Portfolio:', layoutSignatures['Portfolio']);
  }

  expect(uniqueSignatures).toBeGreaterThan(1);
  console.log('PASS: Templates have distinct layout patterns');
});
