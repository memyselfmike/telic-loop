// Verification: Section visibility toggle omits hidden sections from preview
// PRD Reference: F2 - Section Management - hidden sections omitted from DOM
// Vision Goal: Hidden sections disappear from preview entirely
// Category: integration

const { test, expect } = require('@playwright/test');

test('hidden sections are completely omitted from preview DOM', async ({ page }) => {
  console.log('=== Section Visibility Toggle - Preview Integration ===');

  await page.goto('/');
  await page.waitForSelector('#template-cards .template-card');

  // Load template
  await page.locator('#template-cards .template-card').first().click();
  await page.waitForTimeout(1000);

  // Count initial preview sections
  const initialCount = await page.locator('#preview-content .section').count();
  console.log(`Initial preview sections: ${initialCount}`);

  // Hide first section
  await page.locator('.eye-toggle').first().click();
  await page.waitForTimeout(500);

  // Count preview sections after hiding
  const newCount = await page.locator('#preview-content .section').count();
  console.log(`Preview sections after hiding: ${newCount}`);

  // Verify count decreased by 1
  expect(newCount).toBe(initialCount - 1);
  console.log('✓ Hidden section removed from preview DOM (not just hidden with CSS)');

  console.log('PASS: Hidden sections omitted from preview');
});

test('toggling visibility back shows section in preview again', async ({ page }) => {
  await page.goto('/');
  await page.waitForSelector('#template-cards .template-card');

  // Load template
  await page.locator('#template-cards .template-card').first().click();
  await page.waitForTimeout(1000);

  const initialCount = await page.locator('#preview-content .section').count();

  // Hide first section
  await page.locator('.eye-toggle').first().click();
  await page.waitForTimeout(500);

  const countAfterHide = await page.locator('#preview-content .section').count();
  expect(countAfterHide).toBe(initialCount - 1);

  // Show first section again
  await page.locator('.eye-toggle').first().click();
  await page.waitForTimeout(500);

  const countAfterShow = await page.locator('#preview-content .section').count();
  expect(countAfterShow).toBe(initialCount);
  console.log('✓ Toggling back to visible restores section in preview');

  console.log('PASS: Visibility toggle works bidirectionally');
});

test('hidden sections stay hidden after drag reorder', async ({ page }) => {
  await page.goto('/');
  await page.waitForSelector('#template-cards .template-card');

  // Load template
  await page.locator('#template-cards .template-card').first().click();
  await page.waitForTimeout(1000);

  // Hide second section
  await page.locator('.eye-toggle').nth(1).click();
  await page.waitForTimeout(500);

  const countAfterHide = await page.locator('#preview-content .section').count();

  // Drag first section to third position
  const firstSection = page.locator('#section-list .section-block').first();
  const thirdSection = page.locator('#section-list .section-block').nth(2);

  await firstSection.dragTo(thirdSection, {
    targetPosition: { x: 0, y: 60 }
  });

  await page.waitForTimeout(500);

  // Verify hidden section is still hidden
  const countAfterDrag = await page.locator('#preview-content .section').count();
  expect(countAfterDrag).toBe(countAfterHide);
  console.log('✓ Hidden section remains hidden after drag reorder');

  console.log('PASS: Visibility state persists through drag operations');
});
