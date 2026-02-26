// Verification: All 3 template JSON files are valid and contain required structure
// PRD Reference: F1 Template Selection, F2 Section Management
// Vision Goal: Templates with distinct content for SaaS, Event, Portfolio
// Category: unit

const { chromium } = require('playwright');

const REQUIRED_SECTION_TYPES = ['hero', 'features', 'testimonials', 'pricing', 'cta'];
const TEMPLATES = ['saas', 'event', 'portfolio'];

async function verify() {
  let browser;
  let exitCode = 0;

  try {
    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ baseURL: 'http://localhost:3000' });
    const page = await context.newPage();

    console.log('=== Template JSON Validation ===');

    // Test 1: all template JSON files exist and are valid JSON
    for (const templateName of TEMPLATES) {
      const response = await page.goto(`/templates/${templateName}.json`);
      if (response.status() !== 200) {
        throw new Error(`Template ${templateName}.json returned status ${response.status()}, expected 200`);
      }

      const jsonText = await response.text();
      let template;
      try {
        template = JSON.parse(jsonText);
      } catch (err) {
        throw new Error(`Template ${templateName}.json is not valid JSON: ${err.message}`);
      }

      if (!template.name) {
        throw new Error(`Template ${templateName}.json missing 'name' property`);
      }
      if (!template.sections) {
        throw new Error(`Template ${templateName}.json missing 'sections' property`);
      }
      if (!Array.isArray(template.sections)) {
        throw new Error(`Template ${templateName}.json 'sections' is not an array`);
      }

      console.log(`✓ ${templateName}.json is valid JSON with required structure`);
    }

    console.log('PASS: All template JSON files are valid');

    // Test 2: each template has all 5 required section types
    for (const templateName of TEMPLATES) {
      const response = await page.goto(`/templates/${templateName}.json`);
      const template = await response.json();

      if (template.sections.length !== 5) {
        throw new Error(`Template ${templateName}.json has ${template.sections.length} sections, expected 5`);
      }

      const sectionTypes = template.sections.map(s => s.type);
      for (const requiredType of REQUIRED_SECTION_TYPES) {
        if (!sectionTypes.includes(requiredType)) {
          throw new Error(`Template ${templateName}.json missing required section type: ${requiredType}`);
        }
      }

      console.log(`✓ ${templateName}.json has all 5 required section types`);
    }

    console.log('PASS: All templates have required sections');

    // Test 3: each section has unique id and content object
    for (const templateName of TEMPLATES) {
      const response = await page.goto(`/templates/${templateName}.json`);
      const template = await response.json();

      const ids = new Set();

      for (const section of template.sections) {
        if (!section.id) {
          throw new Error(`Template ${templateName}.json has section without 'id' property`);
        }
        if (!section.type) {
          throw new Error(`Template ${templateName}.json has section without 'type' property`);
        }
        if (!section.content) {
          throw new Error(`Template ${templateName}.json has section without 'content' property`);
        }
        if (typeof section.content !== 'object') {
          throw new Error(`Template ${templateName}.json section.content is not an object`);
        }

        // Check for unique IDs
        if (ids.has(section.id)) {
          throw new Error(`Template ${templateName}.json has duplicate section id: ${section.id}`);
        }
        ids.add(section.id);
      }

      console.log(`✓ ${templateName}.json: all sections have unique id and content`);
    }

    console.log('PASS: All sections properly structured');

    // Test 4: templates have distinct content (not copy-paste)
    const templates = {};
    for (const templateName of TEMPLATES) {
      const response = await page.goto(`/templates/${templateName}.json`);
      templates[templateName] = await response.json();
    }

    // Check hero headlines are different
    const saasHero = templates.saas.sections.find(s => s.type === 'hero').content.headline;
    const eventHero = templates.event.sections.find(s => s.type === 'hero').content.headline;
    const portfolioHero = templates.portfolio.sections.find(s => s.type === 'hero').content.headline;

    if (saasHero === eventHero) {
      throw new Error('SaaS and Event templates have identical hero headlines');
    }
    if (saasHero === portfolioHero) {
      throw new Error('SaaS and Portfolio templates have identical hero headlines');
    }
    if (eventHero === portfolioHero) {
      throw new Error('Event and Portfolio templates have identical hero headlines');
    }

    console.log('✓ SaaS hero:', saasHero);
    console.log('✓ Event hero:', eventHero);
    console.log('✓ Portfolio hero:', portfolioHero);

    console.log('PASS: Templates have distinct content');

    await context.close();
  } catch (error) {
    console.error('FAIL:', error.message);
    exitCode = 1;
  } finally {
    if (browser) {
      await browser.close();
    }
  }

  process.exit(exitCode);
}

verify();
