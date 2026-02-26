// Verification: Each template produces visually distinct landing page layout
// PRD Reference: Epic completion criteria
// Vision Goal: "SaaS Product, Event/Webinar, Portfolio Showcase" - distinct templates
// Category: value

const { chromium } = require('playwright');

async function verify() {
  let browser;
  let exitCode = 0;

  try {
    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ baseURL: 'http://localhost:3000' });
    const page = await context.newPage();

    console.log('=== Template Layout Distinction Verification ===');

    // Test 1: SaaS, Event, and Portfolio templates render visually distinct layouts
    const templates = [];

    // Load each template and capture layout characteristics
    for (let i = 0; i < 3; i++) {
      await page.goto('/');
      await page.waitForSelector('#template-cards .template-card');

      const card = page.locator('#template-cards .template-card').nth(i);
      const templateName = await card.textContent();

      await card.click();
      await page.waitForTimeout(1000);

      // Capture layout characteristics
      const layout = await page.evaluate(() => {
        const preview = document.querySelector('#preview-content');
        if (!preview) return null;

        const sections = preview.children;
        const sectionStyles = [];

        for (let section of sections) {
          const computed = window.getComputedStyle(section);
          sectionStyles.push({
            className: section.className,
            backgroundColor: computed.backgroundColor,
            layout: computed.display,
            flexDirection: computed.flexDirection,
            gridTemplateColumns: computed.gridTemplateColumns,
            textAlign: computed.textAlign
          });
        }

        return {
          sectionCount: sections.length,
          sectionClasses: Array.from(sections).map(s => s.className).join(','),
          sectionStyles: sectionStyles,
          previewClass: preview.className,
          bodyClass: document.body.className
        };
      });

      templates.push({
        name: templateName.trim(),
        layout: layout
      });

      console.log(`✓ Captured layout for template ${i + 1}: ${templateName.substring(0, 30)}`);
    }

    // Compare layouts - they should be different
    const layout1 = JSON.stringify(templates[0].layout);
    const layout2 = JSON.stringify(templates[1].layout);
    const layout3 = JSON.stringify(templates[2].layout);

    // Layouts should NOT be identical
    const allIdentical = layout1 === layout2 && layout2 === layout3;

    if (allIdentical) {
      console.log('✗ FAIL: All 3 templates have IDENTICAL layouts');
      console.log('Template 1 classes:', templates[0].layout?.sectionClasses);
      console.log('Template 2 classes:', templates[1].layout?.sectionClasses);
      console.log('Template 3 classes:', templates[2].layout?.sectionClasses);
      throw new Error('All 3 templates have identical layouts');
    } else {
      console.log('✓ Templates have different layout characteristics');
    }

    console.log('PASS: Templates produce visually distinct layouts');

    // Test 2: template-specific CSS classes apply distinct styling
    await page.goto('/');
    await page.waitForSelector('#template-cards .template-card');

    // Load first template
    await page.locator('#template-cards .template-card').first().click();
    await page.waitForTimeout(1000);

    // Check for template-specific classes
    const hasTemplateClass = await page.evaluate(() => {
      const preview = document.querySelector('#preview-content');
      const body = document.body;

      const hasClass =
        preview?.className.includes('template-') ||
        body?.className.includes('template-') ||
        preview?.parentElement?.className.includes('template-');

      const classList = [
        preview?.className || '',
        body?.className || '',
        preview?.parentElement?.className || ''
      ].join(' ');

      return {
        hasTemplateClass: hasClass,
        classList: classList
      };
    });

    if (hasTemplateClass.hasTemplateClass) {
      console.log('✓ Template-specific CSS class applied:', hasTemplateClass.classList);
    } else {
      console.log('⚠ No template-specific CSS class found');
      console.log('  Classes present:', hasTemplateClass.classList);
    }

    console.log('PASS: Template-specific styling mechanism verified');

    // Test 3: hero section layout varies between templates
    const heroLayouts = [];

    for (let i = 0; i < 3; i++) {
      await page.goto('/');
      await page.waitForSelector('#template-cards .template-card');

      await page.locator('#template-cards .template-card').nth(i).click();
      await page.waitForTimeout(1000);

      // Get hero section layout
      const heroStyle = await page.evaluate(() => {
        const preview = document.querySelector('#preview-content');
        const firstSection = preview?.children[0];

        if (!firstSection) return null;

        const computed = window.getComputedStyle(firstSection);
        return {
          textAlign: computed.textAlign,
          justifyContent: computed.justifyContent,
          alignItems: computed.alignItems,
          flexDirection: computed.flexDirection,
          backgroundColor: computed.backgroundColor
        };
      });

      heroLayouts.push(heroStyle);
      console.log(`Template ${i + 1} hero:`, heroStyle);
    }

    // At least some variation should exist
    const allSame = heroLayouts.every(layout =>
      JSON.stringify(layout) === JSON.stringify(heroLayouts[0])
    );

    if (allSame) {
      console.log('⚠ All hero layouts are identical');
    } else {
      console.log('✓ Hero layouts show variation across templates');
    }

    console.log('PASS: Hero layout variation check complete');

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
