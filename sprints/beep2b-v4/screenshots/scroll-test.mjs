import { chromium } from 'playwright';
import path from 'path';
import { fileURLToPath } from 'url';
const __dirname = path.dirname(fileURLToPath(import.meta.url));

(async () => {
  const browser = await chromium.launch();
  
  // Test 1: Homepage with scrolling to trigger animations
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await page.goto('http://localhost:4321/', { waitUntil: 'networkidle', timeout: 30000 });
  
  // Scroll slowly to trigger all animations
  for (let i = 0; i < 20; i++) {
    await page.evaluate(() => window.scrollBy(0, 400));
    await page.waitForTimeout(300);
  }
  // Scroll back to top
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(500);
  
  await page.screenshot({ path: path.join(__dirname, 'home-scrolled.png'), fullPage: true });
  console.log('Saved home-scrolled.png');

  // Test 2: Mobile homepage (480px)
  const mobilePage = await browser.newPage({ viewport: { width: 480, height: 844 } });
  await mobilePage.goto('http://localhost:4321/', { waitUntil: 'networkidle', timeout: 30000 });
  for (let i = 0; i < 20; i++) {
    await mobilePage.evaluate(() => window.scrollBy(0, 300));
    await mobilePage.waitForTimeout(200);
  }
  await mobilePage.evaluate(() => window.scrollTo(0, 0));
  await mobilePage.waitForTimeout(500);
  await mobilePage.screenshot({ path: path.join(__dirname, 'home-mobile.png'), fullPage: true });
  console.log('Saved home-mobile.png');

  // Test 3: Tablet (768px)
  const tabletPage = await browser.newPage({ viewport: { width: 768, height: 1024 } });
  await tabletPage.goto('http://localhost:4321/', { waitUntil: 'networkidle', timeout: 30000 });
  for (let i = 0; i < 20; i++) {
    await tabletPage.evaluate(() => window.scrollBy(0, 300));
    await tabletPage.waitForTimeout(200);
  }
  await tabletPage.evaluate(() => window.scrollTo(0, 0));
  await tabletPage.waitForTimeout(500);
  await tabletPage.screenshot({ path: path.join(__dirname, 'home-tablet.png'), fullPage: true });
  console.log('Saved home-tablet.png');

  // Test 4: Blog page with scrolling
  const blogPage = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await blogPage.goto('http://localhost:4321/blog', { waitUntil: 'networkidle', timeout: 30000 });
  for (let i = 0; i < 10; i++) {
    await blogPage.evaluate(() => window.scrollBy(0, 400));
    await blogPage.waitForTimeout(200);
  }
  await blogPage.evaluate(() => window.scrollTo(0, 0));
  await blogPage.waitForTimeout(500);
  await blogPage.screenshot({ path: path.join(__dirname, 'blog-scrolled.png'), fullPage: true });
  console.log('Saved blog-scrolled.png');

  // Test 5: Contact page with scrolling
  const contactPage = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await contactPage.goto('http://localhost:4321/contact', { waitUntil: 'networkidle', timeout: 30000 });
  for (let i = 0; i < 10; i++) {
    await contactPage.evaluate(() => window.scrollBy(0, 400));
    await contactPage.waitForTimeout(200);
  }
  await contactPage.evaluate(() => window.scrollTo(0, 0));
  await contactPage.waitForTimeout(500);
  await contactPage.screenshot({ path: path.join(__dirname, 'contact-scrolled.png'), fullPage: true });
  console.log('Saved contact-scrolled.png');

  // Test 6: Services page with scrolling
  const servicesPage = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await servicesPage.goto('http://localhost:4321/services', { waitUntil: 'networkidle', timeout: 30000 });
  for (let i = 0; i < 10; i++) {
    await servicesPage.evaluate(() => window.scrollBy(0, 400));
    await servicesPage.waitForTimeout(200);
  }
  await servicesPage.evaluate(() => window.scrollTo(0, 0));
  await servicesPage.waitForTimeout(500);
  await servicesPage.screenshot({ path: path.join(__dirname, 'services-scrolled.png'), fullPage: true });
  console.log('Saved services-scrolled.png');
  
  // Test 7: Blog post with scrolling
  const postPage = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await postPage.goto('http://localhost:4321/blog/the-anatomy-of-a-high-converting-linkedin-profile', { waitUntil: 'networkidle', timeout: 30000 });
  for (let i = 0; i < 10; i++) {
    await postPage.evaluate(() => window.scrollBy(0, 400));
    await postPage.waitForTimeout(200);
  }
  await postPage.evaluate(() => window.scrollTo(0, 0));
  await postPage.waitForTimeout(500);
  await postPage.screenshot({ path: path.join(__dirname, 'blog-post-scrolled.png'), fullPage: true });
  console.log('Saved blog-post-scrolled.png');

  await browser.close();
  console.log('All scroll tests complete!');
})();
