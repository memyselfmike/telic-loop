// Verification: Template cards show visual thumbnail previews
// PRD Reference: F1 Template Selection - "Each card shows a thumbnail preview and template name"
// Vision Goal: "Pick from 3 starter templates displayed as visual cards with live previews"
// Category: value
const { test, expect } = require('@playwright/test');

test('Template cards display visual thumbnail previews', async ({ page }) => {
  await page.goto('/');

  // Verify template cards exist
  const templateCards = page.locator('.template-card');
  await expect(templateCards).toHaveCount(3);

  // Check each card for visual preview content
  for (let i = 0; i < 3; i++) {
    const card = templateCards.nth(i);
    const cardHTML = await card.innerHTML();

    // Look for visual preview indicators:
    // - img tags
    // - preview/thumbnail classes
    // - inline preview content (mini HTML rendering)
    // - SVG illustrations
    // - preview containers with background images

    const hasImage = cardHTML.includes('<img') || cardHTML.includes('background-image');
    const hasPreviewClass = cardHTML.includes('preview') || cardHTML.includes('thumbnail');
    const hasSVG = cardHTML.includes('<svg');
    const hasPreviewContainer = await card.locator('.preview, .thumbnail, .card-preview, .template-preview').count() > 0;

    const hasVisualPreview = hasImage || hasPreviewClass || hasSVG || hasPreviewContainer;

    if (!hasVisualPreview) {
      const cardText = await card.textContent();
      console.log(`FAIL: Card "${cardText.trim()}" has no visual preview element`);
      console.log(`Card HTML: ${cardHTML.substring(0, 200)}...`);
    }

    expect(hasVisualPreview).toBe(true);
  }

  console.log('PASS: All template cards have visual preview elements');
});

test('Template thumbnails show meaningful visual content', async ({ page }) => {
  await page.goto('/');

  const cards = page.locator('.template-card');

  for (let i = 0; i < 3; i++) {
    const card = cards.nth(i);
    const cardName = await card.locator('h3, .template-name, .card-title').textContent();

    // Check for preview content area
    const previewArea = card.locator('.preview, .thumbnail, .card-preview, .template-preview').first();

    if (await previewArea.count() === 0) {
      console.log(`FAIL: No preview area found in "${cardName}" card`);
      expect(await previewArea.count()).toBeGreaterThan(0);
      continue;
    }

    // Verify preview has non-trivial content (not just empty div)
    const previewHTML = await previewArea.innerHTML();
    const hasContent = previewHTML.length > 20; // More than just empty tags

    if (!hasContent) {
      console.log(`FAIL: Preview area in "${cardName}" is empty or trivial`);
      console.log(`Preview HTML: ${previewHTML}`);
    }

    expect(hasContent).toBe(true);
    console.log(`✓ "${cardName}" has thumbnail preview content (${previewHTML.length} chars)`);
  }

  console.log('PASS: Template thumbnails show meaningful visual content');
});

test('Template previews are visually distinguishable from each other', async ({ page }) => {
  await page.goto('/');

  const cards = page.locator('.template-card');
  const previewContents = [];

  // Capture preview content from all cards
  for (let i = 0; i < 3; i++) {
    const card = cards.nth(i);
    const preview = card.locator('.preview, .thumbnail, .card-preview, .template-preview').first();

    if (await preview.count() > 0) {
      const content = await preview.innerHTML();
      previewContents.push(content);
    }
  }

  // Verify we have 3 previews
  expect(previewContents.length).toBe(3);

  // Verify they're not all identical
  const uniquePreviews = new Set(previewContents).size;

  if (uniquePreviews === 1) {
    console.log('FAIL: All template preview thumbnails are identical');
    console.log('Preview 1:', previewContents[0].substring(0, 100));
    console.log('Preview 2:', previewContents[1].substring(0, 100));
    console.log('Preview 3:', previewContents[2].substring(0, 100));
  }

  expect(uniquePreviews).toBeGreaterThan(1);
  console.log(`PASS: Template previews are distinct (${uniquePreviews} unique thumbnails)`);
});
