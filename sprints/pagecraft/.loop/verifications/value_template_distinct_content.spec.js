// Verification: Each template loads with distinct, template-specific content
// PRD Reference: Task 1.1 - Distinct content per template
// Vision Goal: "Pick from 3 starter templates" with professional content
// Category: value
const { test, expect } = require('@playwright/test');

test('SaaS template has product-focused content', async ({ page }) => {
  await page.goto('/');

  await page.locator('.template-card', { hasText: 'SaaS Product' }).click();
  await page.waitForTimeout(500);

  const previewText = await page.locator('#preview-content').textContent();

  // SaaS should mention products, features, software-related terms
  const hasSaasTerms = /product|feature|software|ship|build|deploy/i.test(previewText);
  expect(hasSaasTerms).toBe(true);

  console.log('PASS: SaaS template has product-focused content');
});

test('Event template has event-focused content', async ({ page }) => {
  await page.goto('/');

  await page.locator('.template-card', { hasText: 'Event' }).click();
  await page.waitForTimeout(500);

  const previewText = await page.locator('#preview-content').textContent();

  // Event should mention events, webinars, conferences, dates, speakers
  const hasEventTerms = /event|webinar|conference|speaker|agenda|register|attend/i.test(previewText);
  expect(hasEventTerms).toBe(true);

  console.log('PASS: Event template has event-focused content');
});

test('Portfolio template has work/project-focused content', async ({ page }) => {
  await page.goto('/');

  await page.locator('.template-card', { hasText: 'Portfolio' }).click();
  await page.waitForTimeout(500);

  const previewText = await page.locator('#preview-content').textContent();

  // Portfolio should mention work, projects, showcase, portfolio
  const hasPortfolioTerms = /work|project|portfolio|showcase|design|creative/i.test(previewText);
  expect(hasPortfolioTerms).toBe(true);

  console.log('PASS: Portfolio template has work/project-focused content');
});

test('Templates have different hero headlines', async ({ page }) => {
  const headlines = [];

  // Get SaaS headline
  await page.goto('/');
  await page.locator('.template-card', { hasText: 'SaaS Product' }).click();
  await page.waitForTimeout(500);
  const saasHeadline = await page.locator('.section-hero h1').textContent();
  headlines.push(saasHeadline);

  // Get Event headline
  await page.goto('/');
  await page.locator('.template-card', { hasText: 'Event' }).click();
  await page.waitForTimeout(500);
  const eventHeadline = await page.locator('.section-hero h1').textContent();
  headlines.push(eventHeadline);

  // Get Portfolio headline
  await page.goto('/');
  await page.locator('.template-card', { hasText: 'Portfolio' }).click();
  await page.waitForTimeout(500);
  const portfolioHeadline = await page.locator('.section-hero h1').textContent();
  headlines.push(portfolioHeadline);

  // Verify all headlines are unique
  const uniqueHeadlines = new Set(headlines);
  expect(uniqueHeadlines.size).toBe(3);

  console.log('PASS: Templates have different hero headlines');
});
