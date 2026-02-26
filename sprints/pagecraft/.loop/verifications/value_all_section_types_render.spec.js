// Verification: All 5 section types render with correct content in preview
// PRD Reference: F2 Section Management - 5 section types with distinct visuals
// Vision Goal: Professional landing pages with all section types
// Category: value
const { test, expect } = require('@playwright/test');

test('All 5 section types render correctly in preview', async ({ page }) => {
  await page.goto('/');

  // Select SaaS template
  await page.locator('.template-card', { hasText: 'SaaS Product' }).click();
  await page.waitForTimeout(500);

  const previewContent = page.locator('#preview-content');

  // Verify hero section
  const heroSection = previewContent.locator('.section-hero');
  await expect(heroSection).toBeVisible();
  await expect(heroSection.locator('h1')).toBeVisible();
  await expect(heroSection.locator('button')).toBeVisible();

  // Verify features section
  const featuresSection = previewContent.locator('.section-features');
  await expect(featuresSection).toBeVisible();
  await expect(featuresSection.locator('.features-grid')).toBeVisible();
  await expect(featuresSection.locator('.feature-card')).toHaveCount(3);

  // Verify testimonials section
  const testimonialsSection = previewContent.locator('.section-testimonials');
  await expect(testimonialsSection).toBeVisible();
  await expect(testimonialsSection.locator('.testimonials-grid')).toBeVisible();
  await expect(testimonialsSection.locator('.testimonial-card')).toHaveCount(3);

  // Verify pricing section
  const pricingSection = previewContent.locator('.section-pricing');
  await expect(pricingSection).toBeVisible();
  await expect(pricingSection.locator('.pricing-grid')).toBeVisible();
  await expect(pricingSection.locator('.pricing-card')).toHaveCount(3);

  // Verify CTA section
  const ctaSection = previewContent.locator('.section-cta');
  await expect(ctaSection).toBeVisible();
  await expect(ctaSection.locator('h2')).toBeVisible();
  await expect(ctaSection.locator('button')).toBeVisible();

  console.log('PASS: All 5 section types render correctly in preview');
});

test('Section content matches template JSON data', async ({ page }) => {
  await page.goto('/');

  // Select SaaS template
  await page.locator('.template-card', { hasText: 'SaaS Product' }).click();
  await page.waitForTimeout(500);

  const previewContent = page.locator('#preview-content');

  // Check hero headline matches template
  const heroHeadline = await previewContent.locator('.section-hero h1').textContent();
  expect(heroHeadline).toContain('Ship Faster');

  // Check features count
  const featureCards = previewContent.locator('.feature-card');
  await expect(featureCards).toHaveCount(3);

  // Check pricing tiers
  const pricingCards = previewContent.locator('.pricing-card');
  await expect(pricingCards).toHaveCount(3);

  console.log('PASS: Section content matches template JSON data');
});
