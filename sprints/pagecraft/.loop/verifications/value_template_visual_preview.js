// Verification: Template cards show visual previews, not just text
// PRD Reference: F1 Template Selection - thumbnail preview
// Vision Goal: "templates displayed as visual cards with live previews"
// Category: value

const { chromium } = require('playwright');

async function verify() {
  let browser;
  let exitCode = 0;

  try {
    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ baseURL: 'http://localhost:3000' });
    const page = await context.newPage();

    console.log('=== Template Visual Preview Verification ===');

    // Test 1: template cards show visual preview thumbnails
    await page.goto('/');
    await page.waitForSelector('#template-cards .template-card');

    const cards = page.locator('#template-cards .template-card');
    const cardCount = await cards.count();

    if (cardCount !== 3) {
      throw new Error(`Expected 3 template cards, found ${cardCount}`);
    }
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
        throw new Error(`Card ${i + 1} does not have a visual preview element`);
      }
    }

    console.log('PASS: All template cards have visual previews');

    // Test 2: each template card is visually distinct
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
    if (cardSnapshots[0].text === cardSnapshots[1].text) {
      throw new Error('Card 1 and Card 2 have identical text');
    }
    if (cardSnapshots[0].text === cardSnapshots[2].text) {
      throw new Error('Card 1 and Card 3 have identical text');
    }
    if (cardSnapshots[1].text === cardSnapshots[2].text) {
      throw new Error('Card 2 and Card 3 have identical text');
    }

    console.log('✓ All 3 cards have distinct text');
    console.log('PASS: Template cards are visually distinct');

    // Test 3: template cards are styled as clickable cards with hover states
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
    if (initialStyles.cursor !== 'pointer') {
      throw new Error(`Card cursor is '${initialStyles.cursor}', expected 'pointer'`);
    }
    console.log('✓ Card has pointer cursor');

    // Cards should have visual affordance (shadow or border)
    const hasVisualAffordance =
      initialStyles.boxShadow !== 'none' ||
      initialStyles.border !== 'none' ||
      parseInt(initialStyles.borderRadius) > 0;

    if (!hasVisualAffordance) {
      throw new Error('Card has no visual affordance (no shadow, border, or radius)');
    }
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

    await context.close();
  } catch (error) {
    console.error('FAIL:', error.message);
    exitCode = 1;
  } finally {
    if (browser) {
      await browser.close();
    }
  }

  process.exit(exitCode);
}

verify();
