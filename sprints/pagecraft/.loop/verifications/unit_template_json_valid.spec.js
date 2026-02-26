// Verification: All 3 template JSON files are valid and contain required structure
// PRD Reference: F1 Template Selection, F2 Section Management
// Vision Goal: Templates with distinct content for SaaS, Event, Portfolio
// Category: unit

const { test, expect } = require('@playwright/test');

const REQUIRED_SECTION_TYPES = ['hero', 'features', 'testimonials', 'pricing', 'cta'];
const TEMPLATES = ['saas', 'event', 'portfolio'];

test('all template JSON files exist and are valid JSON', async ({ page }) => {
  console.log('=== Template JSON Validation ===');

  const baseURL = page.context()._options.baseURL;

  for (const templateName of TEMPLATES) {
    const response = await page.goto(`${baseURL}/templates/${templateName}.json`);
    expect(response.status()).toBe(200);

    const jsonText = await response.text();
    const template = JSON.parse(jsonText); // Will throw if invalid

    expect(template).toHaveProperty('name');
    expect(template).toHaveProperty('sections');
    expect(Array.isArray(template.sections)).toBe(true);

    console.log(`✓ ${templateName}.json is valid JSON with required structure`);
  }

  console.log('PASS: All template JSON files are valid');
});

test('each template has all 5 required section types', async ({ page }) => {
  const baseURL = page.context()._options.baseURL;

  for (const templateName of TEMPLATES) {
    const response = await page.goto(`${baseURL}/templates/${templateName}.json`);
    const template = await response.json();

    expect(template.sections.length).toBe(5);

    const sectionTypes = template.sections.map(s => s.type);
    for (const requiredType of REQUIRED_SECTION_TYPES) {
      expect(sectionTypes).toContain(requiredType);
    }

    console.log(`✓ ${templateName}.json has all 5 required section types`);
  }

  console.log('PASS: All templates have required sections');
});

test('each section has unique id and content object', async ({ page }) => {
  const baseURL = page.context()._options.baseURL;

  for (const templateName of TEMPLATES) {
    const response = await page.goto(`${baseURL}/templates/${templateName}.json`);
    const template = await response.json();

    const ids = new Set();

    for (const section of template.sections) {
      expect(section).toHaveProperty('id');
      expect(section).toHaveProperty('type');
      expect(section).toHaveProperty('content');
      expect(typeof section.content).toBe('object');

      // Check for unique IDs
      expect(ids.has(section.id)).toBe(false);
      ids.add(section.id);
    }

    console.log(`✓ ${templateName}.json: all sections have unique id and content`);
  }

  console.log('PASS: All sections properly structured');
});

test('templates have distinct content (not copy-paste)', async ({ page }) => {
  const baseURL = page.context()._options.baseURL;

  const templates = {};
  for (const templateName of TEMPLATES) {
    const response = await page.goto(`${baseURL}/templates/${templateName}.json`);
    templates[templateName] = await response.json();
  }

  // Check hero headlines are different
  const saasHero = templates.saas.sections.find(s => s.type === 'hero').content.headline;
  const eventHero = templates.event.sections.find(s => s.type === 'hero').content.headline;
  const portfolioHero = templates.portfolio.sections.find(s => s.type === 'hero').content.headline;

  expect(saasHero).not.toBe(eventHero);
  expect(saasHero).not.toBe(portfolioHero);
  expect(eventHero).not.toBe(portfolioHero);

  console.log('✓ SaaS hero:', saasHero);
  console.log('✓ Event hero:', eventHero);
  console.log('✓ Portfolio hero:', portfolioHero);

  console.log('PASS: Templates have distinct content');
});
