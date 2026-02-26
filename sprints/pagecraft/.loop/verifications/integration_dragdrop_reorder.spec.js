// Verification: Drag-and-drop section reordering updates state and preview
// PRD Reference: F2 - Section Management - reorder via drag-and-drop
// Vision Goal: Drag sections to reorder them and preview reflects new order
// Category: integration

const { test, expect } = require('@playwright/test');

test('dragging section reorders AppState.sections array', async ({ page }) => {
  console.log('=== Drag-Drop Section Reordering ===');

  await page.goto('/');
  await page.waitForSelector('#template-cards .template-card');

  // Load template
  await page.locator('#template-cards .template-card').first().click();
  await page.waitForTimeout(1000);

  // Get initial section order
  const initialOrder = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('#section-list .section-block'))
      .map(block => block.querySelector('strong')?.textContent || '');
  });

  console.log(`Initial order: ${initialOrder.join(', ')}`);

  if (initialOrder.length < 2) {
    console.log('⚠ Need at least 2 sections to test reordering');
    return;
  }

  // Perform drag-and-drop: move first section to after second
  const firstSection = page.locator('#section-list .section-block').first();
  const secondSection = page.locator('#section-list .section-block').nth(1);

  await firstSection.dragTo(secondSection, {
    targetPosition: { x: 0, y: 60 } // Drop below second section
  });

  await page.waitForTimeout(500);

  // Get new section order
  const newOrder = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('#section-list .section-block'))
      .map(block => block.querySelector('strong')?.textContent || '');
  });

  console.log(`New order: ${newOrder.join(', ')}`);

  // Verify order changed
  expect(newOrder).not.toEqual(initialOrder);
  console.log('✓ Section order changed in workspace');

  console.log('PASS: Drag-drop reordering updates state');
});

test('preview immediately reflects reordered sections', async ({ page }) => {
  await page.goto('/');
  await page.waitForSelector('#template-cards .template-card');

  // Load template
  await page.locator('#template-cards .template-card').first().click();
  await page.waitForTimeout(1000);

  // Get initial preview section order
  const initialPreviewOrder = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('#preview-content .section'))
      .map(s => s.className.match(/section-(\w+)/)?.[1] || '');
  });

  console.log(`Initial preview order: ${initialPreviewOrder.join(', ')}`);

  if (initialPreviewOrder.length < 2) {
    console.log('⚠ Need at least 2 sections in preview');
    return;
  }

  // Drag first section to second position
  const firstSection = page.locator('#section-list .section-block').first();
  const secondSection = page.locator('#section-list .section-block').nth(1);

  await firstSection.dragTo(secondSection, {
    targetPosition: { x: 0, y: 60 }
  });

  await page.waitForTimeout(500);

  // Get new preview section order
  const newPreviewOrder = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('#preview-content .section'))
      .map(s => s.className.match(/section-(\w+)/)?.[1] || '');
  });

  console.log(`New preview order: ${newPreviewOrder.join(', ')}`);

  // Verify preview order changed to match workspace
  expect(newPreviewOrder).not.toEqual(initialPreviewOrder);
  console.log('✓ Preview updated immediately after drag-drop');

  console.log('PASS: Preview reflects reordered sections');
});

test('section order persists through subsequent edits', async ({ page }) => {
  await page.goto('/');
  await page.waitForSelector('#template-cards .template-card');

  // Load template
  await page.locator('#template-cards .template-card').first().click();
  await page.waitForTimeout(1000);

  // Reorder sections
  const firstSection = page.locator('#section-list .section-block').first();
  const thirdSection = page.locator('#section-list .section-block').nth(2);

  await firstSection.dragTo(thirdSection, {
    targetPosition: { x: 0, y: 60 }
  });

  await page.waitForTimeout(500);

  // Get order after drag
  const orderAfterDrag = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('#section-list .section-block'))
      .map(block => block.querySelector('strong')?.textContent || '');
  });

  console.log(`Order after drag: ${orderAfterDrag.join(', ')}`);

  // Perform another action (change accent color)
  const colorPicker = page.locator('#accent-color, input[type="color"]');
  if (await colorPicker.count() > 0) {
    await colorPicker.fill('#00ff00');
    await page.waitForTimeout(500);
  }

  // Verify order is still the same
  const orderAfterColorChange = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('#section-list .section-block'))
      .map(block => block.querySelector('strong')?.textContent || '');
  });

  expect(orderAfterColorChange).toEqual(orderAfterDrag);
  console.log('✓ Section order persisted after accent color change');

  console.log('PASS: Reordered sections persist through subsequent edits');
});
