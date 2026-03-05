import { chromium } from 'playwright';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = join(__dirname, 'responsive');

import { mkdirSync } from 'fs';
mkdirSync(OUT, { recursive: true });

async function screenshot(page, name) {
  const path = join(OUT, name);
  await page.screenshot({ path });
  console.log(`  -> ${name}`);
  return path;
}

async function scrollToSection(page, selector, name) {
  const el = await page.$(selector);
  if (el) {
    await el.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    await screenshot(page, name);
    return true;
  } else {
    console.log(`  !! Section not found: ${selector} for ${name}`);
    return false;
  }
}

(async () => {
  const browser = await chromium.launch({ headless: true });

  // ============================================================
  // PART 1: 768px (Tablet) - Homepage
  // ============================================================
  console.log('\n=== 768px TABLET: Homepage ===');
  {
    const ctx = await browser.newContext({ viewport: { width: 768, height: 1024 } });
    const page = await ctx.newPage();
    await page.goto('http://localhost:4321/', { waitUntil: 'networkidle', timeout: 30000 });

    // Full page
    await page.screenshot({ path: join(OUT, '768_home_full.png'), fullPage: true });
    console.log('  -> 768_home_full.png');

    // Hero (top of page)
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(300);
    await screenshot(page, '768_home_hero.png');

    // Features grid
    await scrollToSection(page, 'section:has(h2)', '768_home_section2.png');

    // Try to find features/BEEP/testimonials by text
    const sections = await page.$$('section');
    console.log(`  Found ${sections.length} sections on homepage`);
    for (let i = 0; i < sections.length; i++) {
      try {
        const text = await sections[i].textContent();
        const preview = text.replace(/\s+/g, ' ').trim().slice(0, 80);
        const isVisible = await sections[i].isVisible();
        console.log(`  Section ${i} (visible=${isVisible}): ${preview}`);
        if (isVisible) {
          await sections[i].scrollIntoViewIfNeeded({ timeout: 3000 });
          await page.waitForTimeout(300);
          await screenshot(page, `768_home_section_${i}.png`);
        } else {
          console.log(`    Skipping hidden section ${i}`);
        }
      } catch (e) {
        console.log(`    Error on section ${i}: ${e.message.slice(0, 100)}`);
      }
    }

    // Footer
    const footer = await page.$('footer');
    if (footer) {
      try {
        await footer.scrollIntoViewIfNeeded({ timeout: 3000 });
        await page.waitForTimeout(300);
        await screenshot(page, '768_home_footer.png');
      } catch (e) {
        console.log(`  Footer scroll error: ${e.message.slice(0, 100)}`);
      }
    }

    // Check for hamburger menu - use broader selectors
    const hamburgerSels = [
      'button[aria-label*="menu" i]',
      'button[class*="hamburger" i]',
      'button[class*="mobile" i]',
      '.mobile-menu-toggle',
      '[data-mobile-menu]',
      'header button',
      'nav button',
    ];
    let hamburgerInfo = 'No hamburger menu detected';
    for (const sel of hamburgerSels) {
      const btn = await page.$(sel);
      if (btn) {
        const visible = await btn.isVisible();
        hamburgerInfo = `Found with "${sel}", visible=${visible}`;
        break;
      }
    }
    console.log(`  Hamburger menu: ${hamburgerInfo}`);

    // Check horizontal overflow
    const hasOverflow = await page.evaluate(() => {
      return document.documentElement.scrollWidth > document.documentElement.clientWidth;
    });
    console.log(`  Horizontal overflow at 768px: ${hasOverflow}`);

    await ctx.close();
  }

  // ============================================================
  // PART 2: 768px - /services
  // ============================================================
  console.log('\n=== 768px TABLET: /services ===');
  {
    const ctx = await browser.newContext({ viewport: { width: 768, height: 1024 } });
    const page = await ctx.newPage();
    await page.goto('http://localhost:4321/services', { waitUntil: 'networkidle', timeout: 30000 });
    await page.screenshot({ path: join(OUT, '768_services_full.png'), fullPage: true });
    console.log('  -> 768_services_full.png');
    await screenshot(page, '768_services_top.png');

    const hasOverflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
    console.log(`  Horizontal overflow: ${hasOverflow}`);
    await ctx.close();
  }

  // ============================================================
  // PART 3: 768px - /blog
  // ============================================================
  console.log('\n=== 768px TABLET: /blog ===');
  {
    const ctx = await browser.newContext({ viewport: { width: 768, height: 1024 } });
    const page = await ctx.newPage();
    await page.goto('http://localhost:4321/blog', { waitUntil: 'networkidle', timeout: 30000 });
    await page.screenshot({ path: join(OUT, '768_blog_full.png'), fullPage: true });
    console.log('  -> 768_blog_full.png');
    await screenshot(page, '768_blog_top.png');

    const hasOverflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
    console.log(`  Horizontal overflow: ${hasOverflow}`);
    await ctx.close();
  }

  // ============================================================
  // PART 4: 480px (Mobile) - Homepage
  // ============================================================
  console.log('\n=== 480px MOBILE: Homepage ===');
  {
    const ctx = await browser.newContext({ viewport: { width: 480, height: 800 } });
    const page = await ctx.newPage();
    await page.goto('http://localhost:4321/', { waitUntil: 'networkidle', timeout: 30000 });

    // Full page
    await page.screenshot({ path: join(OUT, '480_home_full.png'), fullPage: true });
    console.log('  -> 480_home_full.png');

    // Hero
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(300);
    await screenshot(page, '480_home_hero.png');

    // All sections
    const sections = await page.$$('section');
    console.log(`  Found ${sections.length} sections`);
    for (let i = 0; i < sections.length; i++) {
      try {
        const text = await sections[i].textContent();
        const preview = text.replace(/\s+/g, ' ').trim().slice(0, 80);
        const isVisible = await sections[i].isVisible();
        console.log(`  Section ${i} (visible=${isVisible}): ${preview}`);
        if (isVisible) {
          await sections[i].scrollIntoViewIfNeeded({ timeout: 3000 });
          await page.waitForTimeout(300);
          await screenshot(page, `480_home_section_${i}.png`);
        } else {
          console.log(`    Skipping hidden section ${i}`);
        }
      } catch (e) {
        console.log(`    Error on section ${i}: ${e.message.slice(0, 100)}`);
      }
    }

    // Footer
    const footer = await page.$('footer');
    if (footer) {
      try {
        await footer.scrollIntoViewIfNeeded({ timeout: 3000 });
        await page.waitForTimeout(300);
        await screenshot(page, '480_home_footer.png');
      } catch (e) {
        console.log(`  Footer scroll error: ${e.message.slice(0, 100)}`);
      }
    }

    // Check horizontal overflow
    const hasOverflow = await page.evaluate(() => {
      return document.documentElement.scrollWidth > document.documentElement.clientWidth;
    });
    console.log(`  Horizontal overflow at 480px: ${hasOverflow}`);

    // Check text sizes
    const textInfo = await page.evaluate(() => {
      const body = window.getComputedStyle(document.body);
      const h1 = document.querySelector('h1');
      const h1Style = h1 ? window.getComputedStyle(h1) : null;
      return {
        bodyFontSize: body.fontSize,
        h1FontSize: h1Style ? h1Style.fontSize : 'no h1',
        viewportWidth: window.innerWidth,
      };
    });
    console.log(`  Body font: ${textInfo.bodyFontSize}, H1 font: ${textInfo.h1FontSize}`);

    await ctx.close();
  }

  // ============================================================
  // PART 5: 480px - Hamburger Menu Test
  // ============================================================
  console.log('\n=== 480px MOBILE: Hamburger Menu ===');
  {
    const ctx = await browser.newContext({ viewport: { width: 480, height: 800 } });
    const page = await ctx.newPage();
    await page.goto('http://localhost:4321/', { waitUntil: 'networkidle', timeout: 30000 });

    // Find hamburger button - try multiple selectors
    const selectors = [
      'button[aria-label*="menu" i]',
      'button[class*="hamburger" i]',
      'button[class*="mobile" i]',
      '.mobile-menu-toggle',
      '[data-mobile-menu]',
      'header button',
      'nav button',
      '.menu-toggle',
      '#menu-toggle',
      'button:has(.hamburger)',
      'button:has(svg[class*="menu"])',
    ];

    let hamburgerFound = false;
    for (const sel of selectors) {
      const btn = await page.$(sel);
      if (btn) {
        const visible = await btn.isVisible();
        if (visible) {
          console.log(`  Found hamburger with selector: ${sel}`);
          await screenshot(page, '480_menu_before_click.png');

          // Click hamburger
          await btn.click();
          await page.waitForTimeout(800);
          await screenshot(page, '480_menu_after_click.png');

          // Check for visible nav links
          const allNavLinks = await page.$$('nav a, .mobile-nav a, [class*="mobile-menu"] a, header a');
          const navLinks = [];
          for (const link of allNavLinks) {
            if (await link.isVisible()) navLinks.push(link);
          }
          console.log(`  Nav links visible after click: ${navLinks.length}`);

          // Try clicking a nav link
          if (navLinks.length > 0) {
            const linkText = await navLinks[0].textContent();
            const linkHref = await navLinks[0].getAttribute('href');
            console.log(`  Clicking link: "${linkText}" -> ${linkHref}`);
            await navLinks[0].click();
            await page.waitForTimeout(1000);
            console.log(`  Navigated to: ${page.url()}`);
            await screenshot(page, '480_menu_after_nav.png');
          }

          hamburgerFound = true;
          break;
        }
      }
    }

    if (!hamburgerFound) {
      console.log('  No visible hamburger button found at 480px!');
      // Dump header HTML for debugging
      const headerHTML = await page.evaluate(() => {
        const h = document.querySelector('header') || document.querySelector('nav');
        return h ? h.outerHTML.slice(0, 2000) : 'No header/nav found';
      });
      console.log(`  Header HTML: ${headerHTML.slice(0, 500)}`);
      await screenshot(page, '480_no_hamburger_debug.png');
    }

    await ctx.close();
  }

  // ============================================================
  // PART 6: 480px - /contact form
  // ============================================================
  console.log('\n=== 480px MOBILE: /contact ===');
  {
    const ctx = await browser.newContext({ viewport: { width: 480, height: 800 } });
    const page = await ctx.newPage();
    await page.goto('http://localhost:4321/contact', { waitUntil: 'networkidle', timeout: 30000 });

    await page.screenshot({ path: join(OUT, '480_contact_full.png'), fullPage: true });
    console.log('  -> 480_contact_full.png');
    await screenshot(page, '480_contact_top.png');

    // Find form and check layout
    const formInfo = await page.evaluate(() => {
      const form = document.querySelector('form');
      if (!form) return { found: false };
      const inputs = form.querySelectorAll('input, textarea, select');
      const inputData = [];
      for (const inp of inputs) {
        const rect = inp.getBoundingClientRect();
        inputData.push({
          type: inp.type || inp.tagName.toLowerCase(),
          name: inp.name,
          width: rect.width,
          left: rect.left,
          top: rect.top,
        });
      }
      return {
        found: true,
        formWidth: form.getBoundingClientRect().width,
        inputs: inputData,
      };
    });
    console.log(`  Form found: ${formInfo.found}`);
    if (formInfo.found) {
      console.log(`  Form width: ${formInfo.formWidth}px`);
      for (const inp of formInfo.inputs) {
        console.log(`    ${inp.type}[${inp.name}]: width=${inp.width.toFixed(0)}px, left=${inp.left.toFixed(0)}px`);
      }
    }

    // Scroll to form
    const form = await page.$('form');
    if (form) {
      await form.scrollIntoViewIfNeeded();
      await page.waitForTimeout(300);
      await screenshot(page, '480_contact_form.png');
    }

    const hasOverflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
    console.log(`  Horizontal overflow: ${hasOverflow}`);

    await ctx.close();
  }

  // ============================================================
  // PART 7: CMS Admin Panel
  // ============================================================
  console.log('\n=== CMS Admin Panel ===');
  {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    const page = await ctx.newPage();
    await page.goto('http://localhost:3000/admin', { waitUntil: 'networkidle', timeout: 30000 });
    console.log(`  URL after navigation: ${page.url()}`);
    await screenshot(page, 'cms_admin_initial.png');

    // Check what's on the page
    const pageTitle = await page.title();
    console.log(`  Page title: ${pageTitle}`);

    // Check for login form
    const loginForm = await page.$('form');
    const emailField = await page.$('input[type="email"], input[name="email"]');
    const passwordField = await page.$('input[type="password"], input[name="password"]');

    if (emailField && passwordField) {
      console.log('  Login form detected. Attempting login...');
      await emailField.fill('admin@beep2b.com');
      await passwordField.fill('changeme');
      await screenshot(page, 'cms_admin_login_filled.png');

      // Find and click submit button
      const submitBtn = await page.$('button[type="submit"], input[type="submit"], button:has-text("Log in"), button:has-text("Login"), button:has-text("Sign in")');
      if (submitBtn) {
        await submitBtn.click();
        await page.waitForTimeout(3000);
        await page.waitForLoadState('networkidle').catch(() => {});
        console.log(`  URL after login: ${page.url()}`);
        await screenshot(page, 'cms_admin_after_login.png');

        // Check for dashboard or error
        const bodyText = await page.evaluate(() => document.body.innerText.slice(0, 500));
        console.log(`  Page content: ${bodyText.slice(0, 200)}`);

        // Try navigating to Posts
        const postsLink = await page.$('a[href*="posts" i], nav a:has-text("Posts")');
        if (postsLink) {
          await postsLink.click();
          await page.waitForTimeout(2000);
          await screenshot(page, 'cms_admin_posts.png');
          console.log('  -> Posts page loaded');
        }

        // Try Categories
        await page.goto('http://localhost:3000/admin/collections/categories', { waitUntil: 'networkidle', timeout: 15000 }).catch(() => {});
        await screenshot(page, 'cms_admin_categories.png');
        console.log(`  Categories URL: ${page.url()}`);

        // Try Testimonials
        await page.goto('http://localhost:3000/admin/collections/testimonials', { waitUntil: 'networkidle', timeout: 15000 }).catch(() => {});
        await screenshot(page, 'cms_admin_testimonials.png');
        console.log(`  Testimonials URL: ${page.url()}`);
      } else {
        console.log('  No submit button found');
      }
    } else {
      console.log('  No login form detected. Checking page content...');
      const bodyText = await page.evaluate(() => document.body.innerText.slice(0, 500));
      console.log(`  Content: ${bodyText.slice(0, 300)}`);

      // Maybe already logged in? Check for admin nav
      const navItems = await page.$$eval('nav a', links => links.map(l => ({ text: l.textContent, href: l.href })));
      console.log(`  Nav items: ${JSON.stringify(navItems.slice(0, 10))}`);
    }

    await ctx.close();
  }

  await browser.close();
  console.log('\n=== ALL TESTS COMPLETE ===');
})();
