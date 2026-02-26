// Verification: User can export HTML file with inlined CSS
// PRD Reference: F5 HTML Export - Standalone file with inlined CSS
// Vision Goal: "clicks Export and receives a downloaded landing-page.html file"
// Category: value
const { test, expect } = require('@playwright/test');

test('Export button triggers HTML download with inlined CSS', async ({ page }) => {
  await page.goto('/');

  // Select a template
  await page.locator('.template-card', { hasText: 'SaaS Product' }).click();
  await page.waitForTimeout(500);

  // Set up download listener
  const downloadPromise = page.waitForEvent('download');

  // Click export button
  await page.locator('#export-btn').click();

  // Wait for download
  const download = await downloadPromise;

  // Verify filename
  expect(download.suggestedFilename()).toBe('landing-page.html');

  // Save and read the downloaded file
  const path = await download.path();
  const fs = require('fs');
  const content = fs.readFileSync(path, 'utf-8');

  // Verify it's valid HTML
  expect(content).toContain('<!DOCTYPE html>');
  expect(content).toContain('<html');
  expect(content).toContain('</html>');

  // Verify CSS is inlined (has <style> tag, not <link>)
  expect(content).toContain('<style>');
  expect(content).not.toContain('<link rel="stylesheet"');

  // Verify it contains section content
  expect(content).toContain('section-hero');
  expect(content).toContain('section-features');
  expect(content).toContain('section-testimonials');
  expect(content).toContain('section-pricing');
  expect(content).toContain('section-cta');

  // Verify it contains the actual content from the template
  expect(content).toContain('Ship Faster');

  // Verify accent color is included
  expect(content).toContain('--accent-color');

  // Verify no external dependencies (no script tags, no external CSS)
  expect(content).not.toContain('src="');
  expect(content).not.toContain('href="http');

  console.log('PASS: Export generates standalone HTML file with inlined CSS');
});
