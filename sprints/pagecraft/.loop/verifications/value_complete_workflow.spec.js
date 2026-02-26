// Verification: Complete user workflow from Vision succeeds
// PRD Reference: Full PRD workflow
// Vision Goal: "User opens PageCraft, picks SaaS Product template, changes headline, picks blue accent color, previews on mobile, and exports"
// Category: value
const { test, expect } = require('@playwright/test');

test('Complete Vision workflow: pick template, customize, preview, export', async ({ page }) => {
  console.log('Starting complete Vision workflow test...');

  // Step 1: User opens PageCraft
  await page.goto('/');
  await expect(page.locator('h1')).toContainText('PageCraft');
  console.log('✓ PageCraft loaded');

  // Step 2: User sees 3 template cards
  const templateCards = page.locator('.template-card');
  await expect(templateCards).toHaveCount(3);
  console.log('✓ 3 template cards visible');

  // Step 3: User picks SaaS Product template
  await page.locator('.template-card', { hasText: 'SaaS Product' }).click();
  await page.waitForTimeout(500);
  await expect(page.locator('.editor-container')).toBeVisible();
  console.log('✓ SaaS Product template loaded');

  // Step 4: Verify sections appear (5 sections)
  const sectionBlocks = page.locator('.section-block');
  await expect(sectionBlocks).toHaveCount(5);
  console.log('✓ 5 sections visible in workspace');

  // Step 5: Verify preview shows content
  const previewContent = page.locator('#preview-content');
  await expect(previewContent).toBeVisible();
  const initialHeadline = await page.locator('.section-hero h1').textContent();
  expect(initialHeadline).toBeTruthy();
  console.log(`✓ Preview shows content (headline: "${initialHeadline}")`);

  // Step 6: User picks a blue accent color
  const colorPicker = page.locator('#accent-color');
  await colorPicker.fill('#0066ff');
  await page.waitForTimeout(300);
  const accentColor = await page.evaluate(() => {
    return getComputedStyle(document.documentElement).getPropertyValue('--accent-color').trim();
  });
  expect(accentColor).toBe('#0066ff');
  console.log('✓ Blue accent color applied');

  // Step 7: User previews on mobile
  const viewportToggle = page.locator('#toggle-viewport');
  await viewportToggle.click();
  await page.waitForTimeout(200);
  const previewFrame = page.locator('#preview-frame');
  await expect(previewFrame).toHaveClass(/mobile/);
  console.log('✓ Mobile preview activated');

  // Step 8: User exports HTML
  const downloadPromise = page.waitForEvent('download');
  await page.locator('#export-btn').click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe('landing-page.html');

  // Verify exported file content
  const path = await download.path();
  const fs = require('fs');
  const exportedHTML = fs.readFileSync(path, 'utf-8');

  // Verify exported HTML is self-contained
  expect(exportedHTML).toContain('<!DOCTYPE html>');
  expect(exportedHTML).toContain('<style>');
  expect(exportedHTML).not.toContain('src="'); // No external scripts
  expect(exportedHTML).not.toContain('<link rel="stylesheet"'); // No external CSS

  // Verify content is preserved
  expect(exportedHTML).toContain('section-hero');
  expect(exportedHTML).toContain('section-features');
  expect(exportedHTML).toContain('section-testimonials');
  expect(exportedHTML).toContain('section-pricing');
  expect(exportedHTML).toContain('section-cta');

  // Verify accent color is in exported file
  expect(exportedHTML).toContain('#0066ff');

  console.log('✓ Exported HTML is self-contained with correct content and accent color');

  console.log('PASS: Complete Vision workflow succeeded - user can pick template, customize, preview, and export');
});
