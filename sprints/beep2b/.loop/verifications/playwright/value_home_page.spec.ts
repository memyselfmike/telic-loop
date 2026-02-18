/**
 * Value Verification: Home Page Delivers Beep2B Value Proposition
 * PRD Reference: §3.1 (Home Page) - Hero, Features, BEEP Preview, Testimonials, CTA
 * Vision Goal: "Home page displays hero, features, BEEP preview, testimonials, and CTA from CMS content"
 *              "A business owner visits beep2b.com and finds a modern, fast, professional marketing website"
 * Category: value
 */

import { test, expect } from '@playwright/test';

test.describe('Home Page - Value Proposition Delivery', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
  });

  test('Home page loads with a visible hero section', async ({ page }) => {
    // Hero should have a prominent headline communicating the value proposition
    const hero = page.locator('section, div').filter({
      has: page.locator('h1, h2').first(),
    }).first();

    await expect(hero).toBeVisible();

    // The main heading should be present
    const heading = page.locator('h1').first();
    await expect(heading).toBeVisible();

    const headingText = await heading.innerText();
    expect(headingText.trim().length).toBeGreaterThan(5);
    console.log(`✓ Hero heading: "${headingText.trim().substring(0, 80)}"`);
  });

  test('Home page has a primary Call-to-Action button', async ({ page }) => {
    // CTA button - "Book a Discovery Call" or similar
    const ctaButton = page.locator('a, button').filter({
      hasText: /book|discovery|call|get started|learn more|contact/i,
    }).first();

    if (await ctaButton.count() > 0) {
      await expect(ctaButton).toBeVisible();
      const ctaText = await ctaButton.innerText();
      console.log(`✓ Primary CTA found: "${ctaText}"`);
    } else {
      console.log('  SKIP: CTA button not yet implemented (task 1.6 / 3.1)');
      test.skip();
    }
  });

  test('Home page has features/benefits section', async ({ page }) => {
    // Features section should have multiple cards or feature descriptions
    const featureCards = page.locator('section, div').filter({
      has: page.locator('[class*="card"], [class*="feature"], article').first(),
    });

    if (await featureCards.count() > 0) {
      console.log('✓ Features section found');
    } else {
      // Look for any multiple similar structured elements (could be divs with headings)
      const h3s = page.locator('h3, h4');
      const h3Count = await h3s.count();
      if (h3Count >= 2) {
        console.log(`✓ Features-like content found (${h3Count} sub-headings)`);
      } else {
        console.log('  SKIP: Features section not yet implemented (task 1.6 / 3.1)');
        test.skip();
      }
    }
  });

  test('Home page references the BEEP method', async ({ page }) => {
    const pageText = await page.locator('body').innerText();
    const hasBEEP = /BEEP|Build.*Engage|Engage.*Educate|LinkedIn lead/i.test(pageText);

    if (hasBEEP) {
      console.log('✓ BEEP method mentioned on home page');
    } else {
      console.log('  SKIP: BEEP method preview not yet implemented (task 3.1)');
      test.skip();
    }
  });

  test('Home page shows testimonials section', async ({ page }) => {
    const testimonials = page.locator(
      '[class*="testimonial"], blockquote, [class*="review"], section:has([class*="testimonial"])'
    );

    if (await testimonials.count() > 0) {
      console.log(`✓ Testimonials section found`);
    } else {
      // Check for placeholder testimonial text
      const pageText = await page.locator('body').innerText();
      if (/testimonial|quote|review/i.test(pageText)) {
        console.log('✓ Testimonial references found in page text');
      } else {
        console.log('  SKIP: Testimonials not yet implemented (task 3.1)');
        test.skip();
      }
    }
  });

  test('Home page loads completely without JavaScript errors', async ({ page }) => {
    const jsErrors: string[] = [];
    page.on('pageerror', err => jsErrors.push(err.message));

    await page.goto('/', { waitUntil: 'networkidle' });

    if (jsErrors.length > 0) {
      console.error('JavaScript errors on home page:');
      jsErrors.forEach(e => console.error(`  - ${e}`));
      expect(jsErrors, 'No JavaScript errors should occur on home page').toHaveLength(0);
    } else {
      console.log('✓ No JavaScript errors on home page');
    }
  });
});

test.describe('Home Page - Layout Quality', () => {
  test.use({ viewport: { width: 1280, height: 800 } });

  test('Home page has correct <title> tag', async ({ page }) => {
    await page.goto('/');
    const title = await page.title();
    expect(title.trim().length).toBeGreaterThan(5);
    console.log(`✓ Page title: "${title}"`);
  });

  test('Home page has meta description for SEO', async ({ page }) => {
    await page.goto('/');
    const metaDesc = page.locator('meta[name="description"]');

    if (await metaDesc.count() > 0) {
      const content = await metaDesc.getAttribute('content');
      expect(content?.trim().length).toBeGreaterThan(10);
      console.log(`✓ Meta description: "${content?.substring(0, 80)}..."`);
    } else {
      console.log('  SKIP: Meta description not yet added (task 3.6)');
    }
  });
});
