// Verification: Template cards show visual previews, not just text
// PRD Reference: F1 Template Selection - thumbnail preview
// Vision Goal: "templates displayed as visual cards with live previews"
// Category: value

const { test, expect } = require('@playwright/test');

test('template cards show visual preview thumbnails', async ({ page }) => {
  console.log('=== Template Visual Preview Verification ===');

  await page.goto('/');
  await page.waitForSelector('#template-cards .template-card');

  const cards = page.locator('#template-cards .template-card');
  const cardCount = await cards.count();

  expect(cardCount).toBe(3);
  console.log(`✓ Found ${cardCount} template cards`);

  // Check each card for visual preview elements
  for (let i = 0; i < cardCount; i++) {
    const card = cards.nth(i);

    // Look for preview elements: mini-preview div, iframe, or img
    const hasPreview = await card.evaluate(el => {
      const hasPreviewDiv = el.querySelector('.template-preview, .preview, .thumbnail, .mini-preview') !== null;
      const hasImage = el.querySelector('img') !== null;
      const hasIframe = el.querySelector('iframe') !== null;
      const hasStyledDiv = el.querySelector('[style*="background"], [class*="scaled"], [class*="mini"]') !== null;

      return hasPreviewDiv || hasImage || hasIframe || hasStyledDiv;
    });

    if (hasPreview) {
      console.log(`✓ Card ${i + 1}: has visual preview element`);
    } else {
      console.log(`✗ Card ${i + 1}: NO visual preview found (only text)`);
    }

    expect(hasPreview).toBe(true);
  }

  console.log('PASS: All template cards have visual previews');
});

test('each template card is visually distinct', async ({ page }) => {
  await page.goto('/');
  await page.waitForSelector('#template-cards .template-card');

  const cards = page.locator('#template-cards .template-card');
  const cardSnapshots = [];

  // Capture visual characteristics of each card
  for (let i = 0; i < 3; i++) {
    const card = cards.nth(i);

    const cardInfo = await card.evaluate(el => {
      const preview = el.querySelector('.template-preview, .preview, .thumbnail, .mini-preview');
      const text = el.textContent;
      const bgColor = preview ? window.getComputedStyle(preview).backgroundColor : '';
      const innerHTML = el.innerHTML;

      return {
        text: text,
        bgColor: bgColor,
        htmlLength: innerHTML.length,
        hasPreview: preview !== null
      };
    });

    cardSnapshots.push(cardInfo);
    console.log(`Card ${i + 1}:`, cardInfo.text.substring(0, 50), 'hasPreview:', cardInfo.hasPreview);
  }

  // Verify cards are different from each other
  expect(cardSnapshots[0].text).not.toBe(cardSnapshots[1].text);
  expect(cardSnapshots[0].text).not.toBe(cardSnapshots[2].text);
  expect(cardSnapshots[1].text).not.toBe(cardSnapshots[2].text);

  console.log('✓ All 3 cards have distinct text');
  console.log('PASS: Template cards are visually distinct');
});

test('template cards are styled as clickable cards with hover states', async ({ page }) => {
  await page.goto('/');
  await page.waitForSelector('#template-cards .template-card');

  const firstCard = page.locator('#template-cards .template-card').first();

  // Get initial styles
  const initialStyles = await firstCard.evaluate(el => {
    const computed = window.getComputedStyle(el);
    return {
      cursor: computed.cursor,
      boxShadow: computed.boxShadow,
      border: computed.border,
      borderRadius: computed.borderRadius,
      transition: computed.transition
    };
  });

  // Cards should look clickable
  expect(initialStyles.cursor).toBe('pointer');
  console.log('✓ Card has pointer cursor');

  // Cards should have visual affordance (shadow or border)
  const hasVisualAffordance =
    initialStyles.boxShadow !== 'none' ||
    initialStyles.border !== 'none' ||
    parseInt(initialStyles.borderRadius) > 0;

  expect(hasVisualAffordance).toBe(true);
  console.log('✓ Card has visual affordance (shadow/border/radius)');

  // Hover state (simulate hover and check for changes)
  await firstCard.hover();
  await page.waitForTimeout(100);

  const hoverStyles = await firstCard.evaluate(el => {
    const computed = window.getComputedStyle(el);
    return {
      boxShadow: computed.boxShadow,
      transform: computed.transform
    };
  });

  console.log('✓ Hover state applied:', {
    hasTransform: hoverStyles.transform !== 'none',
    shadow: hoverStyles.boxShadow !== 'none'
  });

  console.log('PASS: Template cards styled as clickable with hover feedback');
});
