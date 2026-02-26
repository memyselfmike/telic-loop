// Verification: User can toggle between desktop and mobile preview
// PRD Reference: F4 Preview - Toggle between desktop (1200px) and mobile (375px)
// Vision Goal: "Toggle between desktop and mobile viewport previews"
// Category: value
const { test, expect } = require('@playwright/test');

test('User can toggle viewport between desktop and mobile', async ({ page }) => {
  await page.goto('/');

  // Select a template
  await page.locator('.template-card').first().click();
  await page.waitForTimeout(500);

  const previewFrame = page.locator('#preview-frame');
  const viewportToggle = page.locator('#toggle-viewport');

  // Initially should be desktop
  await expect(previewFrame).toHaveClass(/desktop/);
  await expect(viewportToggle).toContainText('Mobile');

  // Click to switch to mobile
  await viewportToggle.click();
  await page.waitForTimeout(200);

  // Should now be mobile
  await expect(previewFrame).toHaveClass(/mobile/);
  await expect(viewportToggle).toContainText('Desktop');

  // Click to switch back to desktop
  await viewportToggle.click();
  await page.waitForTimeout(200);

  // Should be desktop again
  await expect(previewFrame).toHaveClass(/desktop/);
  await expect(viewportToggle).toContainText('Mobile');

  console.log('PASS: User can toggle viewport between desktop and mobile');
});
