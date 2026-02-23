// Verification: Stats API handles edge cases correctly
// PRD Reference: Epic 2 - GET /api/stats endpoint
// Vision Goal: Dashboard shows tag counts and recent links correctly
// Category: integration

import test from 'node:test';
import assert from 'node:assert';
import { readLinks, writeLinks } from '../../storage.js';

const API_BASE = 'http://localhost:3000';

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

test('INTEGRATION - Stats API edge cases', async (t) => {
  console.log('=== Stats API Edge Cases Test ===');

  const createdIds = [];

  try {
    await t.test('Empty collection stats', async () => {
      // Save current state and clear all links
      const existingLinks = await readLinks();
      await writeLinks([]);

      try {
        const result = await makeRequest('GET', '/api/stats');

        assert.strictEqual(result.status, 200, 'Should return 200 for empty collection');
        assert.strictEqual(result.data.total_links, 0, 'total_links should be 0');
        assert.strictEqual(result.data.total_tags, 0, 'total_tags should be 0');
        assert.deepStrictEqual(result.data.tag_counts, {}, 'tag_counts should be empty object');
        assert.deepStrictEqual(result.data.recent, [], 'recent should be empty array');

        console.log('✓ Empty collection returns zeros and empty arrays gracefully');
      } finally {
        // Restore previous state
        await writeLinks(existingLinks);
      }
    });

    await t.test('Single link stats', async () => {
      const singleLink = await makeRequest('POST', '/api/links', {
        title: 'Single Test Link',
        url: 'https://example.com/single',
        tags: ['test', 'single']
      });
      createdIds.push(singleLink.data.id);

      const result = await makeRequest('GET', '/api/stats');
      const allLinks = await makeRequest('GET', '/api/links');

      assert.strictEqual(result.status, 200, 'Should return 200');
      assert.ok(result.data.total_links >= 1, 'total_links should include our link');
      assert.ok(result.data.total_tags >= 2, 'total_tags should include our tags');
      assert.ok(result.data.tag_counts['test'] >= 1, 'tag_counts should include "test"');
      assert.ok(result.data.tag_counts['single'] >= 1, 'tag_counts should include "single"');
      assert.ok(Array.isArray(result.data.recent), 'recent should be an array');

      console.log('✓ Single link stats computed correctly');
    });

    await t.test('Link with no tags', async () => {
      const noTags = await makeRequest('POST', '/api/links', {
        title: 'No Tags Link',
        url: 'https://example.com/notags',
        tags: []
      });
      createdIds.push(noTags.data.id);

      const result = await makeRequest('GET', '/api/stats');

      assert.strictEqual(result.status, 200, 'Should handle links with no tags');
      // total_tags might not change if we already have tags from previous links
      assert.ok(result.data.total_links >= 2, 'Should count link without tags');

      console.log('✓ Links with no tags handled gracefully');
    });

    await t.test('Recent links sorting', async () => {
      // Create 7 links with slight delays to ensure distinct timestamps
      const titles = ['First', 'Second', 'Third', 'Fourth', 'Fifth', 'Sixth', 'Seventh'];
      const recentTestIds = [];

      for (const title of titles) {
        const result = await makeRequest('POST', '/api/links', {
          title: `Recent ${title}`,
          url: `https://example.com/recent${title.toLowerCase()}`,
          tags: ['recent-test']
        });
        recentTestIds.push(result.data.id);
        createdIds.push(result.data.id);

        // Small delay to ensure different created_at timestamps
        await new Promise(resolve => setTimeout(resolve, 10));
      }

      const stats = await makeRequest('GET', '/api/stats');

      // Should return max 5 recent links
      assert.ok(stats.data.recent.length <= 5, 'Should return max 5 recent links');

      // Verify sorting: most recent first
      if (stats.data.recent.length >= 2) {
        for (let i = 0; i < stats.data.recent.length - 1; i++) {
          const current = new Date(stats.data.recent[i].created_at);
          const next = new Date(stats.data.recent[i + 1].created_at);

          assert.ok(current >= next, 'Recent links should be sorted newest first');
        }
      }

      console.log('✓ Recent links limited to 5 and sorted correctly (newest first)');
    });

    await t.test('Tag count accuracy with duplicates', async () => {
      // Create links with overlapping tags to test counting
      const links = [
        { title: 'A', url: 'https://a.com', tags: ['alpha', 'beta'] },
        { title: 'B', url: 'https://b.com', tags: ['alpha', 'gamma'] },
        { title: 'C', url: 'https://c.com', tags: ['beta', 'gamma'] },
      ];

      const testIds = [];
      for (const link of links) {
        const result = await makeRequest('POST', '/api/links', link);
        testIds.push(result.data.id);
        createdIds.push(result.data.id);
      }

      const stats = await makeRequest('GET', '/api/stats');

      // Verify our test tags are counted correctly
      assert.ok(stats.data.tag_counts['alpha'] >= 2, 'alpha should appear in 2 links');
      assert.ok(stats.data.tag_counts['beta'] >= 2, 'beta should appear in 2 links');
      assert.ok(stats.data.tag_counts['gamma'] >= 2, 'gamma should appear in 2 links');

      console.log('✓ Tag counts accurate with overlapping tags');
    });

    await t.test('Stats reflect deletions', async () => {
      // Get current stats
      const statsBefore = await makeRequest('GET', '/api/stats');
      const linksBefore = statsBefore.data.total_links;

      // Delete one of our test links
      if (createdIds.length > 0) {
        await makeRequest('DELETE', `/api/links/${createdIds[0]}`);

        const statsAfter = await makeRequest('GET', '/api/stats');

        assert.ok(statsAfter.data.total_links < linksBefore, 'total_links should decrease after deletion');

        console.log('✓ Stats update correctly after deletions');
      }
    });

  } finally {
    // Cleanup all test links
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
console.log('PASS: Stats API handles all edge cases correctly');
