import { chromium } from 'playwright';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ssDir = path.join(__dirname, '..'); // save screenshots to sprint root

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();

  // Step 1: Navigate to /admin - should redirect to login
  console.log('=== Step 1: Navigate to /admin ===');
  try {
    await page.goto('http://localhost:3000/admin', { waitUntil: 'networkidle', timeout: 15000 });
  } catch (e) {
    console.log('Navigation timeout, continuing anyway...');
  }
  await sleep(2000);
  console.log('Current URL:', page.url());
  await page.screenshot({ path: path.join(ssDir, 'admin_login.png'), fullPage: false });
  console.log('Screenshot: admin_login.png');

  // Step 2: Log in
  console.log('\n=== Step 2: Log in with admin@beep2b.com / changeme ===');
  try {
    // Wait for the login form
    await page.waitForSelector('input[name="email"], input[id="field-email"]', { timeout: 10000 });

    // Find and fill email
    const emailInput = await page.$('input[name="email"]') || await page.$('input[id="field-email"]');
    if (emailInput) {
      await emailInput.fill('admin@beep2b.com');
      console.log('Filled email');
    } else {
      console.log('Could not find email input');
    }

    // Find and fill password
    const pwInput = await page.$('input[name="password"]') || await page.$('input[id="field-password"]');
    if (pwInput) {
      await pwInput.fill('changeme');
      console.log('Filled password');
    } else {
      console.log('Could not find password input');
    }

    // Click login button
    const loginBtn = await page.$('button[type="submit"]');
    if (loginBtn) {
      await loginBtn.click();
      console.log('Clicked login button');
    }

    // Wait for navigation after login
    await sleep(3000);
    try {
      await page.waitForURL('**/admin', { timeout: 10000 });
    } catch(e) {
      console.log('URL after login attempt:', page.url());
    }
  } catch (e) {
    console.log('Login error:', e.message);
  }

  // Step 3: Dashboard screenshot
  console.log('\n=== Step 3: Dashboard ===');
  console.log('Current URL:', page.url());
  await sleep(2000);
  await page.screenshot({ path: path.join(ssDir, 'admin_dashboard.png'), fullPage: false });
  console.log('Screenshot: admin_dashboard.png');

  // Get page content to understand layout
  const dashboardTitle = await page.title();
  console.log('Page title:', dashboardTitle);

  // Step 4: Navigate to Posts collection
  console.log('\n=== Step 4: Posts collection ===');
  await page.goto('http://localhost:3000/admin/collections/posts', { waitUntil: 'networkidle', timeout: 15000 }).catch(() => {});
  await sleep(2000);
  console.log('Current URL:', page.url());

  // Count rows in the posts table
  const postRows = await page.$$('table tbody tr');
  console.log('Post rows found in table:', postRows.length);

  // Try to get post titles
  const postTexts = await page.$$eval('table tbody tr td:first-child', cells => cells.map(c => c.textContent?.trim()));
  console.log('Post titles:', postTexts);

  // Also check if there's a different list layout
  const listItems = await page.$$('.collection-list__item, [class*="list"] [class*="row"]');
  console.log('List items found:', listItems.length);

  await page.screenshot({ path: path.join(ssDir, 'admin_posts.png'), fullPage: false });
  console.log('Screenshot: admin_posts.png');

  // Step 5: Navigate to Categories
  console.log('\n=== Step 5: Categories collection ===');
  await page.goto('http://localhost:3000/admin/collections/categories', { waitUntil: 'networkidle', timeout: 15000 }).catch(() => {});
  await sleep(2000);
  console.log('Current URL:', page.url());

  const catRows = await page.$$('table tbody tr');
  console.log('Category rows found:', catRows.length);

  const catTexts = await page.$$eval('table tbody tr td:first-child', cells => cells.map(c => c.textContent?.trim()));
  console.log('Category names:', catTexts);

  await page.screenshot({ path: path.join(ssDir, 'admin_categories.png'), fullPage: false });
  console.log('Screenshot: admin_categories.png');

  // Step 6: Navigate to Testimonials
  console.log('\n=== Step 6: Testimonials collection ===');
  await page.goto('http://localhost:3000/admin/collections/testimonials', { waitUntil: 'networkidle', timeout: 15000 }).catch(() => {});
  await sleep(2000);
  console.log('Current URL:', page.url());

  const testRows = await page.$$('table tbody tr');
  console.log('Testimonial rows found:', testRows.length);

  const testTexts = await page.$$eval('table tbody tr td:first-child', cells => cells.map(c => c.textContent?.trim()));
  console.log('Testimonial names:', testTexts);

  await page.screenshot({ path: path.join(ssDir, 'admin_testimonials.png'), fullPage: false });
  console.log('Screenshot: admin_testimonials.png');

  // Step 7: Navigate to Form Submissions
  console.log('\n=== Step 7: Form Submissions collection ===');
  await page.goto('http://localhost:3000/admin/collections/form-submissions', { waitUntil: 'networkidle', timeout: 15000 }).catch(() => {});
  await sleep(2000);
  console.log('Current URL:', page.url());

  const formRows = await page.$$('table tbody tr');
  console.log('Form submission rows found:', formRows.length);

  await page.screenshot({ path: path.join(ssDir, 'admin_form_submissions.png'), fullPage: false });
  console.log('Screenshot: admin_form_submissions.png');

  // Step 8: Check Media collection
  console.log('\n=== Step 8: Media collection ===');
  await page.goto('http://localhost:3000/admin/collections/media', { waitUntil: 'networkidle', timeout: 15000 }).catch(() => {});
  await sleep(2000);
  console.log('Current URL:', page.url());

  const mediaItems = await page.$$('table tbody tr');
  console.log('Media items found:', mediaItems.length);

  // Check for grid/card layout too
  const mediaCards = await page.$$('[class*="thumbnail"], [class*="card"], [class*="upload"]');
  console.log('Media cards/thumbnails:', mediaCards.length);

  await page.screenshot({ path: path.join(ssDir, 'admin_media.png'), fullPage: false });
  console.log('Screenshot: admin_media.png');

  // Step 9: Try editing a post
  console.log('\n=== Step 9: Edit a post ===');
  await page.goto('http://localhost:3000/admin/collections/posts', { waitUntil: 'networkidle', timeout: 15000 }).catch(() => {});
  await sleep(2000);

  // Click on the first post
  const firstPostLink = await page.$('table tbody tr:first-child td:first-child a') || await page.$('table tbody tr:first-child a');
  if (firstPostLink) {
    await firstPostLink.click();
    console.log('Clicked first post');
  } else {
    // Try clicking the row itself
    const firstRow = await page.$('table tbody tr:first-child');
    if (firstRow) {
      await firstRow.click();
      console.log('Clicked first row');
    } else {
      console.log('Could not find any post to click');
      // Try alternative selectors
      const anyLink = await page.$('a[href*="/admin/collections/posts/"]');
      if (anyLink) {
        await anyLink.click();
        console.log('Clicked a post link');
      }
    }
  }

  await sleep(3000);
  console.log('Current URL after clicking post:', page.url());
  await page.screenshot({ path: path.join(ssDir, 'admin_edit_post.png'), fullPage: false });
  console.log('Screenshot: admin_edit_post.png');

  // Check for rich text editor
  const richTextEditor = await page.$('[class*="rich-text"], [class*="richText"], .lexical-editor, [data-lexical-editor], [contenteditable="true"], .ql-editor');
  console.log('Rich text editor found:', richTextEditor !== null);

  // Scroll down to see more of the editor
  await page.evaluate(() => window.scrollBy(0, 500));
  await sleep(1000);
  await page.screenshot({ path: path.join(ssDir, 'admin_edit_post_scrolled.png'), fullPage: false });
  console.log('Screenshot: admin_edit_post_scrolled.png');

  // Check for all visible fields on the edit page
  const labels = await page.$$eval('label', els => els.map(e => e.textContent?.trim()).filter(Boolean));
  console.log('Form labels found:', labels);

  // Check for the rich text toolbar
  const toolbar = await page.$$('[class*="toolbar"], [role="toolbar"]');
  console.log('Toolbars found:', toolbar.length);

  await browser.close();
  console.log('\n=== Done ===');
})();
