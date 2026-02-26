// Verification: User can select a template and see it load into the editor
// PRD Reference: F1 Template Selection - Task 1.7 end-to-end flow
// Vision Goal: "Choose a template — Pick from 3 starter templates displayed as visual cards"
// Category: value
const { test, expect } = require('@playwright/test');

test('User sees 3 template cards and can select one to load', async ({ page }) => {
  await page.goto('/');

  // Verify page loads
  await expect(page.locator('h1')).toContainText('PageCraft');

  // Verify 3 template cards are visible
  const templateCards = page.locator('.template-card');
  await expect(templateCards).toHaveCount(3);

  // Verify card text content
  const cardTexts = await templateCards.allTextContents();
  expect(cardTexts.some(text => text.includes('SaaS Product'))).toBe(true);
  expect(cardTexts.some(text => text.includes('Event'))).toBe(true);
  expect(cardTexts.some(text => text.includes('Portfolio'))).toBe(true);

  // Click the first template card (SaaS Product)
  const saasCard = page.locator('.template-card', { hasText: 'SaaS Product' });
  await saasCard.click();

  // Wait for template to load
  await page.waitForTimeout(500);

  // Verify template selector is hidden
  await expect(page.locator('#template-selector')).toBeHidden();

  // Verify editor container is visible
  await expect(page.locator('.editor-container')).toBeVisible();

  // Verify sections appear in workspace
  const sectionBlocks = page.locator('.section-block');
  await expect(sectionBlocks).toHaveCount(5);

  // Verify preview panel shows content
  const previewContent = page.locator('#preview-content');
  await expect(previewContent).toBeVisible();
  await expect(previewContent).not.toBeEmpty();

  console.log('PASS: User can select a template and it loads into the editor');
});

test('User can switch templates with confirmation', async ({ page }) => {
  await page.goto('/');

  // Select first template
  await page.locator('.template-card').first().click();
  await page.waitForTimeout(500);

  // Try to select a different template
  page.on('dialog', async dialog => {
    expect(dialog.message()).toContain('Switch template');
    await dialog.accept();
  });

  // Click a different template card
  const templateCards = page.locator('.template-card');
  const secondCard = templateCards.nth(1);
  await secondCard.click();

  await page.waitForTimeout(500);

  // Verify new template loaded
  await expect(page.locator('.editor-container')).toBeVisible();

  console.log('PASS: User can switch templates with confirmation');
});
