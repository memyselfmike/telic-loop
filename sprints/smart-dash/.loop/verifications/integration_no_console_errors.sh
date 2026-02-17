#!/usr/bin/env bash
# Verification: Page loads without console errors (except acceptable network failures)
# PRD Reference: Acceptance Criteria #1
# Vision Goal: Clean, error-free dashboard experience
# Category: integration
set -euo pipefail

echo "=== Integration: No Console Errors on Load ==="

# This verification checks that:
# 1. Page loads without JavaScript errors
# 2. Acceptable exceptions: weather API network failures

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cat > /tmp/test_console_errors.js << 'EOJS'
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  const consoleErrors = [];
  const pageErrors = [];

  // Capture console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });

  // Capture page errors
  page.on('pageerror', error => {
    pageErrors.push(error.message);
  });

  try {
    await page.goto('file://' + process.env.INDEX_PATH);

    // Wait for page to fully initialize
    await page.waitForTimeout(3000);

    // Interact with page to trigger any lazy-loaded errors
    await page.click('#task-input'); // Focus task input

    // Filter out acceptable errors
    const unacceptableErrors = [...consoleErrors, ...pageErrors].filter(err => {
      // Network errors for weather API are acceptable
      if (err.includes('net::ERR') || err.includes('Failed to fetch')) return false;
      if (err.includes('openweathermap')) return false;
      return true;
    });

    if (unacceptableErrors.length > 0) {
      console.error('FAIL: Unacceptable console/page errors detected:');
      unacceptableErrors.forEach(err => console.error(`  - ${err}`));
      process.exit(1);
    }

    console.log('PASS: No unacceptable console errors');
    console.log(`  Console errors: ${consoleErrors.length} (all acceptable)`);
    console.log(`  Page errors: ${pageErrors.length} (all acceptable)`);

    await browser.close();
    process.exit(0);

  } catch (error) {
    console.error('FAIL: Error during console error check:', error.message);
    await browser.close();
    process.exit(1);
  }
})();
EOJS

if ! command -v node &> /dev/null; then
    echo "SKIP: Node.js not found"
    exit 0
fi

export INDEX_PATH="$PROJECT_ROOT/index.html"
node /tmp/test_console_errors.js
