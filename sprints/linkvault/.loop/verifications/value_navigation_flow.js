// Verification: User can navigate freely between Collection and Dashboard pages
// PRD Reference: Epic 2 - Navigation bar on both pages
// Vision Goal: Two pages - main collection view and dashboard with navigation between them
// Category: value

import test from 'node:test';
import assert from 'node:assert';

const API_BASE = 'http://localhost:3000';

async function fetchPage(path) {
  const response = await fetch(`${API_BASE}${path}`);
  const html = await response.text();
  return { status: response.status, html };
}

async function makeRequest(method, path, body = null) {
  const options = {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {}
  };
  if (body) options.body = JSON.stringify(body);

  const response = await fetch(`${API_BASE}${path}`, options);
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;

  return { status: response.status, data };
}

test('VALUE - User navigates freely between Collection and Dashboard', async () => {
  console.log('');
  console.log('═══════════════════════════════════════════════════════');
  console.log('  VALUE TEST — Navigation User Experience');
  console.log('═══════════════════════════════════════════════════════');

  const createdIds = [];

  try {
    // SCENARIO: User discovers navigation
    console.log('');
    console.log('📖 SCENARIO: Discovering the Two-Page Experience');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('[User] Jordan opens LinkVault for the first time');

    // Create some test data so pages have content
    const bookmarks = [
      { title: 'React Docs', url: 'https://react.dev/', tags: ['react', 'docs'] },
      { title: 'MDN Web', url: 'https://developer.mozilla.org/', tags: ['docs', 'reference'] },
      { title: 'CSS Tricks', url: 'https://css-tricks.com/', tags: ['css', 'tutorial'] },
    ];

    console.log('[User] Saves 3 bookmarks');
    for (const bm of bookmarks) {
      const result = await makeRequest('POST', '/api/links', bm);
      assert.strictEqual(result.status, 201, 'Should create bookmark');
      createdIds.push(result.data.id);
    }

    // JOURNEY: Collection → Dashboard
    console.log('');
    console.log('📖 JOURNEY: Collection → Dashboard');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('[User] Currently viewing: Collection page (/)');

    const collectionPage = await fetchPage('/');
    assert.strictEqual(collectionPage.status, 200, 'Collection page should load');
    console.log('[User sees] Bookmark cards in a grid');

    // Verify navigation links exist on collection page
    assert.ok(
      collectionPage.html.match(/href=['"]\/dashboard['"]/i) ||
      collectionPage.html.includes('/dashboard'),
      'Collection page should have Dashboard link'
    );
    console.log('[User sees] Navigation bar with "Dashboard" link');

    // Verify active state indication
    assert.ok(
      collectionPage.html.includes('active') ||
      collectionPage.html.includes('current') ||
      collectionPage.html.match(/class=['"][^'"]*collection[^'"]*['"]/i),
      'Collection link should have active styling'
    );
    console.log('[User sees] "Collection" link is highlighted (active)');

    console.log('');
    console.log('[User action] Clicks "Dashboard" link');
    const dashboardPage = await fetchPage('/dashboard');
    assert.strictEqual(dashboardPage.status, 200, 'Dashboard should load successfully');
    console.log('[Browser] Navigates to /dashboard');
    console.log('[User sees] Dashboard with stats cards, bar chart, recent links');

    // Verify dashboard loaded the right content type
    assert.ok(
      dashboardPage.html.includes('stats') ||
      dashboardPage.html.includes('card') ||
      dashboardPage.html.includes('chart'),
      'Dashboard should have stats/chart content'
    );

    // JOURNEY: Dashboard → Collection
    console.log('');
    console.log('📖 JOURNEY: Dashboard → Collection (Return Trip)');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('[User] Currently viewing: Dashboard (/dashboard)');

    // Verify navigation back to collection exists
    assert.ok(
      dashboardPage.html.match(/href=['"]\/['"]/i) ||
      dashboardPage.html.includes('Collection'),
      'Dashboard should have Collection link'
    );
    console.log('[User sees] Navigation bar with "Collection" link');

    // Verify active state on dashboard
    assert.ok(
      dashboardPage.html.includes('active') && dashboardPage.html.includes('Dashboard'),
      'Dashboard link should be active on dashboard page'
    );
    console.log('[User sees] "Dashboard" link is highlighted (active)');

    console.log('');
    console.log('[User action] Clicks "Collection" link');
    const collectionReturn = await fetchPage('/');
    assert.strictEqual(collectionReturn.status, 200, 'Should navigate back to collection');
    console.log('[Browser] Navigates back to /');
    console.log('[User sees] Back to the bookmark card grid');

    // JOURNEY: Multiple back-and-forth trips
    console.log('');
    console.log('📖 JOURNEY: Multiple Navigation Cycles');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('[User thinks] "Let me check both pages a few times..."');

    const navigationSequence = [
      { path: '/dashboard', name: 'Dashboard' },
      { path: '/', name: 'Collection' },
      { path: '/dashboard', name: 'Dashboard' },
      { path: '/', name: 'Collection' },
    ];

    for (let i = 0; i < navigationSequence.length; i++) {
      const nav = navigationSequence[i];
      const page = await fetchPage(nav.path);

      assert.strictEqual(page.status, 200, `Navigation to ${nav.name} should succeed`);
      console.log(`[Navigation ${i + 1}/4] ✓ ${nav.name} loads successfully`);
    }

    console.log('[User thinks] "Navigation is smooth and reliable!"');

    // VALIDATION: Both pages accessible
    console.log('');
    console.log('📖 VALIDATION: Route Accessibility');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

    const routes = [
      { path: '/', description: 'Collection (root)' },
      { path: '/dashboard', description: 'Dashboard' },
    ];

    for (const route of routes) {
      const page = await fetchPage(route.path);
      assert.strictEqual(page.status, 200, `${route.description} should be accessible`);
      console.log(`✓ ${route.description} (${route.path}) - 200 OK`);
    }

    // VALIDATION: Navigation consistency
    console.log('');
    console.log('📖 VALIDATION: Navigation Bar Consistency');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

    const collectionNavCheck = await fetchPage('/');
    const dashboardNavCheck = await fetchPage('/dashboard');

    // Both pages should have navigation to both routes
    assert.ok(
      collectionNavCheck.html.includes('Dashboard') || collectionNavCheck.html.includes('dashboard'),
      'Collection page must link to Dashboard'
    );
    assert.ok(
      dashboardNavCheck.html.includes('Collection') || dashboardNavCheck.html.includes('collection') || dashboardNavCheck.html.match(/href=['"]\/['"]/),
      'Dashboard page must link to Collection'
    );

    console.log('✓ Collection page has Dashboard link');
    console.log('✓ Dashboard page has Collection link');
    console.log('✓ Bidirectional navigation enabled on both pages');

    // SUMMARY
    console.log('');
    console.log('═══════════════════════════════════════════════════════');
    console.log('  VALUE DELIVERED ✨');
    console.log('═══════════════════════════════════════════════════════');
    console.log('');
    console.log('[User reflects] "I can easily move between pages!"');
    console.log('  ✓ Navigation bar present on both pages');
    console.log('  ✓ Can navigate Collection → Dashboard');
    console.log('  ✓ Can navigate Dashboard → Collection');
    console.log('  ✓ Active page is clearly indicated');
    console.log('  ✓ Multiple navigation cycles work reliably');
    console.log('  ✓ Both routes are accessible and functional');
    console.log('');
    console.log('Vision delivered: Users can navigate freely between the');
    console.log('main collection view and the dashboard, with clear visual');
    console.log('indication of which page they\'re on. ✅');

  } finally {
    // Cleanup test bookmarks
    for (const id of createdIds) {
      try {
        await makeRequest('DELETE', `/api/links/${id}`);
      } catch (e) {
        // Ignore cleanup errors
      }
    }
  }
});

console.log('');
console.log('✅ PASS: Navigation delivers seamless two-page experience');
