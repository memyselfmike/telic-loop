// Verification: User can return to template selector from editor
// PRD Reference: F1 Template Selection - "User can switch templates (warns about losing changes)"
// Vision Goal: User workflow includes ability to switch templates during editing
// Category: value
const { test, expect } = require('@playwright/test');

test('Change Template button exists and is visible in editor', async ({ page }) => {
  await page.goto('/');

  // Load a template
  const templateCard = page.locator('.template-card').first();
  await templateCard.click();
  await page.waitForTimeout(500);

  // Editor should be visible
  await expect(page.locator('.editor-container')).toBeVisible();

  // Look for Change Template, Back, or similar button
  const changeTemplateButton = page.locator('button, a, .btn').filter({
    hasText: /change template|back|switch template|templates|select template/i
  });

  const buttonCount = await changeTemplateButton.count();

  if (buttonCount === 0) {
    console.log('FAIL: No Change Template or Back button found in editor view');
    console.log('Available buttons:', await page.locator('button').allTextContents());
  }

  expect(buttonCount).toBeGreaterThan(0);
  console.log('PASS: Change Template button exists in editor');
});

test('Change Template button returns user to template selector', async ({ page }) => {
  await page.goto('/');

  // Load a template
  await page.locator('.template-card').first().click();
  await page.waitForTimeout(500);

  // Verify editor is showing
  await expect(page.locator('.editor-container')).toBeVisible();
  await expect(page.locator('#template-selector')).toBeHidden();

  // Find and click the change template button
  const changeButton = page.locator('button, a, .btn').filter({
    hasText: /change template|back|switch template|templates|select template/i
  }).first();

  // Set up dialog handler for confirmation
  let dialogShown = false;
  page.on('dialog', async dialog => {
    dialogShown = true;
    expect(dialog.message()).toMatch(/switch|change|lose|lost/i);
    await dialog.accept();
  });

  await changeButton.click();
  await page.waitForTimeout(500);

  // Template selector should be visible again
  await expect(page.locator('#template-selector')).toBeVisible();

  // Editor may remain visible or may be hidden - both are acceptable
  // The key requirement is that template selector is accessible

  console.log('PASS: Change Template button returns user to template selector');
});

test('Change Template shows confirmation dialog about losing changes', async ({ page }) => {
  await page.goto('/');

  // Load a template
  await page.locator('.template-card').first().click();
  await page.waitForTimeout(500);

  // Make a change (edit some text or change color)
  const accentPicker = page.locator('#accent-color');
  if (await accentPicker.count() > 0) {
    await accentPicker.fill('#ff0000');
    await page.waitForTimeout(200);
  }

  // Find change template button
  const changeButton = page.locator('button, a, .btn').filter({
    hasText: /change template|back|switch template|templates|select template/i
  }).first();

  // Set up dialog handler
  let dialogMessage = '';
  page.on('dialog', async dialog => {
    dialogMessage = dialog.message();
    await dialog.dismiss(); // Dismiss to test cancellation
  });

  await changeButton.click();
  await page.waitForTimeout(500);

  // Verify dialog was shown with appropriate warning
  if (!dialogMessage) {
    console.log('FAIL: No confirmation dialog shown when changing templates');
  }

  expect(dialogMessage).toMatch(/switch|change|lose|lost|discard/i);
  console.log(`PASS: Confirmation dialog shown: "${dialogMessage}"`);

  // Verify dismissal keeps user in editor
  await expect(page.locator('.editor-container')).toBeVisible();
});

test('Change Template button works from all three templates', async ({ page }) => {
  const templates = ['SaaS Product', 'Event', 'Portfolio'];

  for (const templateName of templates) {
    await page.goto('/');
    await page.waitForTimeout(300);

    // Load template
    const card = page.locator('.template-card', { hasText: templateName });
    await card.click();
    await page.waitForTimeout(500);

    // Find change button
    const changeButton = page.locator('button, a, .btn').filter({
      hasText: /change template|back|switch template|templates|select template/i
    }).first();

    if (await changeButton.count() === 0) {
      console.log(`FAIL: No Change Template button found after loading "${templateName}"`);
      expect(await changeButton.count()).toBeGreaterThan(0);
      continue;
    }

    // Handle dialog
    page.on('dialog', async dialog => {
      await dialog.accept();
    });

    await changeButton.click();
    await page.waitForTimeout(500);

    // Should return to template selector
    await expect(page.locator('#template-selector')).toBeVisible();

    console.log(`✓ Change Template works from "${templateName}"`);
  }

  console.log('PASS: Change Template button works from all templates');
});
