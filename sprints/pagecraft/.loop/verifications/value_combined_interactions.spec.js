// Verification: All Epic 2 features work together without conflicts
// PRD Reference: F2 + F3 combined functionality
// Vision Goal: User workflow from template selection through full customization
// Category: value

const { test, expect } = require('@playwright/test');

test('user can drag-reorder then inline-edit without losing order', async ({ page }) => {
  console.log('=== Combined Interactive Editor Features ===');

  await page.goto('/');
  await page.waitForSelector('#template-cards .template-card');

  // Load template
  await page.locator('#template-cards .template-card').first().click();
  await page.waitForTimeout(1000);

  // 1. Drag-reorder sections
  const firstSection = page.locator('#section-list .section-block').first();
  const thirdSection = page.locator('#section-list .section-block').nth(2);
  await firstSection.dragTo(thirdSection, { targetPosition: { x: 0, y: 60 } });
  await page.waitForTimeout(500);

  const orderAfterDrag = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('#section-list .section-block'))
      .map(b => b.querySelector('strong')?.textContent);
  });

  console.log(`Order after drag: ${orderAfterDrag.join(', ')}`);

  // 2. Inline edit headline
  const headline = page.locator('#preview-content [data-field]').first();
  await headline.click();
  await page.waitForTimeout(200);
  await headline.fill('');
  await headline.type('Combined Test Headline');
  await page.locator('#preview-frame').click();
  await page.waitForTimeout(500);

  // 3. Verify order didn't reset
  const orderAfterEdit = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('#section-list .section-block'))
      .map(b => b.querySelector('strong')?.textContent);
  });

  expect(orderAfterEdit).toEqual(orderAfterDrag);
  console.log('✓ Section order preserved after inline edit');

  // 4. Verify edit persisted
  const editedText = await headline.textContent();
  expect(editedText).toContain('Combined Test Headline');
  console.log('✓ Inline edit preserved after drag operation');

  console.log('PASS: Drag-reorder + inline-edit work together');
});

test('inline edits persist through drag-reorder operations', async ({ page }) => {
  await page.goto('/');
  await page.waitForSelector('#template-cards .template-card');

  // Load template
  await page.locator('#template-cards .template-card').first().click();
  await page.waitForTimeout(1000);

  // 1. Edit text first
  const headline = page.locator('#preview-content [data-field]').first();
  await headline.click();
  await page.waitForTimeout(200);
  await headline.fill('');
  await headline.type('Persistent Text Through Reorder');
  await page.locator('#preview-frame').click();
  await page.waitForTimeout(500);

  // 2. Then drag-reorder
  const firstSection = page.locator('#section-list .section-block').first();
  const secondSection = page.locator('#section-list .section-block').nth(1);
  await firstSection.dragTo(secondSection, { targetPosition: { x: 0, y: 60 } });
  await page.waitForTimeout(500);

  // 3. Verify text still shows edited value
  const textAfterDrag = await headline.textContent();
  expect(textAfterDrag).toContain('Persistent Text Through Reorder');
  console.log('✓ Edited text persisted through drag-reorder');

  console.log('PASS: Inline edits persist through drag operations');
});

test('hidden sections remain hidden after accent color change', async ({ page }) => {
  await page.goto('/');
  await page.waitForSelector('#template-cards .template-card');

  // Load template
  await page.locator('#template-cards .template-card').first().click();
  await page.waitForTimeout(1000);

  // 1. Hide a section
  await page.locator('.eye-toggle').nth(1).click();
  await page.waitForTimeout(500);

  const countAfterHide = await page.locator('#preview-content .section').count();
  console.log(`Sections in preview after hiding: ${countAfterHide}`);

  // 2. Change accent color
  const colorPicker = page.locator('#accent-color, input[type="color"]');
  await colorPicker.fill('#00ff00');
  await page.waitForTimeout(500);

  // 3. Verify hidden section is still hidden
  const countAfterColor = await page.locator('#preview-content .section').count();
  expect(countAfterColor).toBe(countAfterHide);
  console.log('✓ Hidden section remained hidden after color change');

  console.log('PASS: Visibility state persists through accent color changes');
});

test('all 4 features work in combination without conflicts', async ({ page }) => {
  await page.goto('/');
  await page.waitForSelector('#template-cards .template-card');

  // Load template
  await page.locator('#template-cards .template-card').first().click();
  await page.waitForTimeout(1000);

  console.log('Testing combined workflow: drag + edit + toggle + color...');

  // 1. Drag-reorder
  const firstSection = page.locator('#section-list .section-block').first();
  const thirdSection = page.locator('#section-list .section-block').nth(2);
  await firstSection.dragTo(thirdSection, { targetPosition: { x: 0, y: 60 } });
  await page.waitForTimeout(500);
  console.log('✓ Step 1: Reordered sections');

  // 2. Hide a section
  await page.locator('.eye-toggle').nth(1).click();
  await page.waitForTimeout(500);
  const countAfterHide = await page.locator('#preview-content .section').count();
  console.log(`✓ Step 2: Hidden section (${countAfterHide} visible)`);

  // 3. Edit text
  const headline = page.locator('#preview-content [data-field]').first();
  await headline.click();
  await page.waitForTimeout(200);
  await headline.fill('');
  await headline.type('Full Workflow Test');
  await page.locator('#preview-frame').click();
  await page.waitForTimeout(500);
  console.log('✓ Step 3: Edited headline');

  // 4. Change color
  const colorPicker = page.locator('#accent-color, input[type="color"]');
  await colorPicker.fill('#ff00ff');
  await page.waitForTimeout(500);
  console.log('✓ Step 4: Changed accent color');

  // Verify all changes persisted
  const finalCount = await page.locator('#preview-content .section').count();
  expect(finalCount).toBe(countAfterHide);

  const finalText = await headline.textContent();
  expect(finalText).toContain('Full Workflow Test');

  const finalColor = await page.evaluate(() => {
    return getComputedStyle(document.documentElement).getPropertyValue('--accent-color').trim();
  });
  expect(finalColor).toBe('#ff00ff');

  console.log('✓ All 4 changes persisted correctly');
  console.log('PASS: All interactive editor features work together');
});

test('editing text inside draggable section works without triggering drag', async ({ page }) => {
  await page.goto('/');
  await page.waitForSelector('#template-cards .template-card');

  // Load template
  await page.locator('#template-cards .template-card').first().click();
  await page.waitForTimeout(1000);

  // Get initial order
  const initialOrder = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('#section-list .section-block'))
      .map(b => b.querySelector('strong')?.textContent);
  });

  // Click and edit text in preview (should not trigger drag on workspace)
  const editableInPreview = page.locator('#preview-content [data-field]').first();
  await editableInPreview.click();
  await page.waitForTimeout(200);
  await editableInPreview.fill('');
  await editableInPreview.type('Edited Without Drag');
  await page.locator('#preview-frame').click();
  await page.waitForTimeout(500);

  // Verify order unchanged (edit didn't accidentally trigger drag)
  const finalOrder = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('#section-list .section-block'))
      .map(b => b.querySelector('strong')?.textContent);
  });

  expect(finalOrder).toEqual(initialOrder);
  console.log('✓ Inline editing did not accidentally trigger drag operations');

  console.log('PASS: Edit and drag event handlers do not conflict');
});
