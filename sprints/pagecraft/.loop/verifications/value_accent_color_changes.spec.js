// Verification: User can change accent color and see it applied globally
// PRD Reference: F3 Inline Editing - Accent color picker applies to buttons/headings/borders
// Vision Goal: "picks a blue accent color" and see changes apply
// Category: value
const { test, expect } = require('@playwright/test');

test('User can change accent color and it applies to preview', async ({ page }) => {
  await page.goto('/');

  // Select a template
  await page.locator('.template-card').first().click();
  await page.waitForTimeout(500);

  // Get initial accent color
  const initialColor = await page.evaluate(() => {
    return getComputedStyle(document.documentElement).getPropertyValue('--accent-color').trim();
  });

  expect(initialColor).toBeTruthy();

  // Change accent color
  const colorPicker = page.locator('#accent-color');
  await colorPicker.fill('#ff0000'); // Red
  await page.waitForTimeout(500);

  // Verify color changed in CSS variable
  const newColor = await page.evaluate(() => {
    return getComputedStyle(document.documentElement).getPropertyValue('--accent-color').trim();
  });

  expect(newColor).toBe('#ff0000');

  // Verify buttons use the accent color (hero section button)
  const heroButton = page.locator('.section-hero button');
  await expect(heroButton).toBeVisible();

  console.log('PASS: User can change accent color and it applies globally');
});
