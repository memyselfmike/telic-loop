// Verification: Section visibility toggle (eye icon) functionality
// PRD Reference: F2 - Section Management - hide/show sections
// Vision Goal: Users can hide sections they don't want in their landing page
// Category: unit

const { test, expect } = require('@playwright/test');

test('eye icon toggle buttons render on each section', async ({ page }) => {
  console.log('=== Section Visibility Toggle ===');

  await page.goto('/');
  await page.waitForSelector('#template-cards .template-card');

  // Load template
  await page.locator('#template-cards .template-card').first().click();
  await page.waitForTimeout(1000);

  // Check for eye toggle buttons
  const eyeToggles = await page.locator('.eye-toggle, .toggle-visibility, button[title*="Hide"], button[title*="Show"]');
  const toggleCount = await eyeToggles.count();

  expect(toggleCount).toBeGreaterThan(0);
  console.log(`✓ Found ${toggleCount} visibility toggle buttons (eye icons)`);

  // Verify each section has a toggle
  const sectionCount = await page.locator('#section-list .section-block').count();
  expect(toggleCount).toBe(sectionCount);
  console.log(`✓ Each section (${sectionCount}) has a visibility toggle`);

  console.log('PASS: Eye icon toggles render correctly');
});

test('clicking eye toggle changes visibility state', async ({ page }) => {
  await page.goto('/');
  await page.waitForSelector('#template-cards .template-card');

  // Load template
  await page.locator('#template-cards .template-card').first().click();
  await page.waitForTimeout(1000);

  const eyeToggle = page.locator('.eye-toggle').first();

  // Get initial state
  const initialClass = await eyeToggle.getAttribute('class');
  console.log(`Initial eye toggle class: ${initialClass}`);

  // Click toggle
  await eyeToggle.click();
  await page.waitForTimeout(300);

  // Get new state
  const newClass = await eyeToggle.getAttribute('class');
  console.log(`New eye toggle class: ${newClass}`);

  // Verify class changed (indicating state change)
  expect(newClass).not.toBe(initialClass);
  console.log('✓ Eye toggle visual state changed on click');

  console.log('PASS: Visibility toggle changes state');
});

test('hidden sections are visually indicated', async ({ page }) => {
  await page.goto('/');
  await page.waitForSelector('#template-cards .template-card');

  // Load template
  await page.locator('#template-cards .template-card').first().click();
  await page.waitForTimeout(1000);

  // Hide first section
  await page.locator('.eye-toggle').first().click();
  await page.waitForTimeout(300);

  // Check if toggle has hidden class or different icon
  const firstToggle = page.locator('.eye-toggle').first();
  const hasHiddenIndicator = await page.evaluate(() => {
    const toggle = document.querySelector('.eye-toggle');
    return toggle?.classList.contains('eye-hidden') ||
           toggle?.textContent?.includes('🗨️') ||
           toggle?.style.opacity === '0.5';
  });

  expect(hasHiddenIndicator).toBeTruthy();
  console.log('✓ Hidden section has visual indicator (crossed eye or dimmed)');

  console.log('PASS: Hidden sections are visually indicated');
});
