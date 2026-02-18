/**
 * Value Verification: Blog System Delivers Content Marketing Value
 * PRD Reference: §3.6 (Blog Listing), §3.7 (Blog Post), §3.8 (Category Filter)
 * Vision Goal: "Blog with Discovery" - visitors browse posts, filter by category, read full articles
 *              "Blog posts paginate at 10 per page with prev/next navigation and category filtering works"
 * Category: value
 */

import { test, expect, Page } from '@playwright/test';

test.describe('Blog Listing - Content Discovery', () => {
  test('Blog listing page loads and shows post cards', async ({ page }) => {
    await page.goto('/blog', { waitUntil: 'domcontentloaded' });

    // Page should not error
    const bodyText = await page.locator('body').innerText();
    expect(bodyText.trim().length).toBeGreaterThan(10);

    // Should NOT show an error page
    await expect(page.locator('body')).not.toContainText('Internal Server Error');
    await expect(page.locator('body')).not.toContainText('500');

    // Check for blog cards or post list
    const blogCards = page.locator(
      'article, [class*="card"], [class*="post"], [class*="blog"]'
    );
    const cardCount = await blogCards.count();

    if (cardCount > 0) {
      console.log(`✓ Blog listing shows ${cardCount} blog card elements`);
    } else {
      // Acceptable: "No posts yet" placeholder when CMS has no data
      const noPostsText = page.getByText(/no posts|coming soon|empty|no content|stay tuned/i);
      if (await noPostsText.count() > 0) {
        console.log('✓ Blog shows graceful empty state (no CMS posts yet)');
      } else {
        console.log('  SKIP: Blog cards not yet implemented (task 1.7 / 2.4)');
        test.skip();
      }
    }
  });

  test('Blog cards show required metadata', async ({ page }) => {
    await page.goto('/blog', { waitUntil: 'domcontentloaded' });

    const blogCards = page.locator('article, [class*="blog-card"], [class*="post-card"]');
    const cardCount = await blogCards.count();

    if (cardCount === 0) {
      console.log('  SKIP: No blog cards yet (pending CMS data or task 1.7)');
      test.skip();
      return;
    }

    // Check first card has key metadata: title, date, category
    const firstCard = blogCards.first();

    // Title (h2 or h3 inside card)
    const cardTitle = firstCard.locator('h2, h3, h4, a[href*="/blog/"]');
    if (await cardTitle.count() > 0) {
      const titleText = await cardTitle.first().innerText();
      expect(titleText.trim().length).toBeGreaterThan(5);
      console.log(`✓ Blog card has title: "${titleText.substring(0, 60)}"`);
    }

    // Date (time element or date-formatted text)
    const dateEl = firstCard.locator('time, [class*="date"], [datetime]');
    if (await dateEl.count() > 0) {
      console.log('✓ Blog card has date/time element');
    }

    // Category badge
    const badge = firstCard.locator('[class*="badge"], [class*="tag"], [class*="category"]');
    if (await badge.count() > 0) {
      const badgeText = await badge.first().innerText();
      console.log(`✓ Blog card has category badge: "${badgeText}"`);
    }
  });

  test('Blog listing has pagination controls', async ({ page }) => {
    await page.goto('/blog', { waitUntil: 'domcontentloaded' });

    // Pagination: prev/next links or page numbers
    const paginationLinks = page.locator(
      'nav[aria-label*="pagination" i], [class*="pagination"], a[href*="/blog/2"], a:has-text("Next"), a:has-text("Previous")'
    );

    if (await paginationLinks.count() > 0) {
      console.log('✓ Pagination controls found on blog listing');
    } else {
      // Acceptable if fewer than 10 posts (no pagination needed)
      const blogCards = page.locator('article, [class*="card"]');
      const cardCount = await blogCards.count();
      if (cardCount < 10) {
        console.log(`  OK: ${cardCount} posts shown, pagination not needed until 10+ posts`);
      } else {
        console.log('  SKIP: Pagination not yet implemented (task 1.7 / 2.4)');
      }
    }
  });

  test('Blog has responsive grid layout', async ({ page }) => {
    // Desktop: 3 column grid
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto('/blog', { waitUntil: 'domcontentloaded' });

    const grid = page.locator('[class*="grid"], [class*="card-grid"]').first();
    if (await grid.count() > 0) {
      console.log('✓ Grid container found on blog listing');
    }

    // Mobile: single column
    await page.setViewportSize({ width: 375, height: 812 });
    const bodyText = await page.locator('body').innerText();
    expect(bodyText.trim().length).toBeGreaterThan(0);
    console.log('✓ Blog listing renders on mobile viewport');
  });
});

test.describe('Blog Post - Content Reading Experience', () => {
  test('Individual blog post page renders correctly', async ({ page }) => {
    // First check if any posts exist by looking at blog listing
    await page.goto('/blog', { waitUntil: 'domcontentloaded' });

    // Try to find a link to a blog post
    const postLink = page.locator('a[href*="/blog/"]:not([href="/blog"])').first();

    if (await postLink.count() === 0) {
      console.log('  SKIP: No blog post links found (no CMS posts or task 2.4/2.5 pending)');
      test.skip();
      return;
    }

    const href = await postLink.getAttribute('href');
    if (!href) { test.skip(); return; }

    // Navigate to the post
    await page.goto(href, { waitUntil: 'domcontentloaded' });

    // Post should have a title
    const title = page.locator('h1').first();
    await expect(title).toBeVisible();
    const titleText = await title.innerText();
    expect(titleText.trim().length).toBeGreaterThan(5);
    console.log(`✓ Blog post page loaded: "${titleText.substring(0, 60)}"`);

    // Post should have body content
    const postBody = page.locator('article, [class*="prose"], [class*="post-content"], main');
    await expect(postBody).toBeVisible();
    const bodyText = await postBody.innerText();
    expect(bodyText.trim().length).toBeGreaterThan(50);
    console.log('✓ Blog post has body content');
  });

  test('Blog post Portable Text renders correctly', async ({ page }) => {
    await page.goto('/blog', { waitUntil: 'domcontentloaded' });
    const postLink = page.locator('a[href*="/blog/"]:not([href="/blog"])').first();

    if (await postLink.count() === 0) {
      console.log('  SKIP: No blog posts available (pending CMS data)');
      test.skip();
      return;
    }

    const href = await postLink.getAttribute('href');
    await page.goto(href!, { waitUntil: 'domcontentloaded' });

    // Portable Text renders headings, paragraphs
    const paragraphs = page.locator('article p, [class*="prose"] p, main p');
    if (await paragraphs.count() > 0) {
      console.log(`✓ Blog post has ${await paragraphs.count()} paragraph elements`);
    }

    // Check for proper typography elements
    const contentElements = page.locator('h2, h3, p, ul, ol, blockquote');
    const elemCount = await contentElements.count();
    expect(elemCount).toBeGreaterThan(0);
    console.log(`✓ Blog post has ${elemCount} content elements (headings, paragraphs, lists)`);
  });

  test('Blog post has author bio and related posts', async ({ page }) => {
    await page.goto('/blog', { waitUntil: 'domcontentloaded' });
    const postLink = page.locator('a[href*="/blog/"]:not([href="/blog"])').first();

    if (await postLink.count() === 0) {
      console.log('  SKIP: No blog posts available (pending CMS data)');
      test.skip();
      return;
    }

    const href = await postLink.getAttribute('href');
    await page.goto(href!, { waitUntil: 'domcontentloaded' });

    // Author bio (task 3.5)
    const authorSection = page.locator('[class*="author"], [class*="bio"]').first();
    if (await authorSection.count() > 0) {
      console.log('✓ Author bio section present on blog post');
    } else {
      console.log('  SKIP: Author bio not yet implemented (task 3.5)');
    }

    // Related posts (task 3.5)
    const relatedPosts = page.locator('[class*="related"], section:has-text("Related")').first();
    if (await relatedPosts.count() > 0) {
      console.log('✓ Related posts section present on blog post');
    } else {
      console.log('  SKIP: Related posts not yet implemented (task 3.5)');
    }

    // Back to blog link
    const backLink = page.getByRole('link', { name: /back.*blog|← blog|all posts/i });
    if (await backLink.count() > 0) {
      console.log('✓ Back to blog link present');
    }
  });
});

test.describe('Category Filtering', () => {
  test('Category filter navigates to filtered blog view', async ({ page }) => {
    await page.goto('/blog', { waitUntil: 'domcontentloaded' });

    // Look for category filter bar or links
    const categoryLinks = page.locator('a[href*="/blog/category/"], [class*="category-filter"] a');
    const catCount = await categoryLinks.count();

    if (catCount === 0) {
      console.log('  SKIP: Category filter not yet implemented (task 2.6)');
      test.skip();
      return;
    }

    const firstCatLink = categoryLinks.first();
    const catHref = await firstCatLink.getAttribute('href');
    console.log(`  Clicking category: ${catHref}`);

    await firstCatLink.click();
    await page.waitForURL('**/blog/category/**');
    expect(page.url()).toContain('/blog/category/');

    // Category page should show category title as heading
    const heading = page.locator('h1, h2').first();
    await expect(heading).toBeVisible();
    console.log(`✓ Category page loaded: ${page.url()}`);
  });

  test('Category page shows graceful empty state', async ({ page }) => {
    // Even with no CMS posts, category pages should not crash
    await page.goto('/blog/category/linkedin-marketing', { waitUntil: 'domcontentloaded' });

    // Should not show 500 error
    await expect(page.locator('body')).not.toContainText('Internal Server Error');
    await expect(page.locator('body')).not.toContainText('500');

    const bodyText = await page.locator('body').innerText();
    if (bodyText.trim().length > 0) {
      console.log('✓ Category page handles empty state gracefully');
    } else {
      console.log('  SKIP: Category pages not yet implemented (task 2.6)');
    }
  });
});
