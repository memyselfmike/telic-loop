#!/usr/bin/env bash
# Verification: Weather widget shows fallback text when no API key, or real data with valid key
# PRD Reference: Widgets > Weather Widget
# Vision Goal: Shows weather at a glance for break planning
# Category: unit
set -euo pipefail

echo "=== Unit: Weather Widget Display ==="

# This verification checks that:
# 1. Weather widget element exists
# 2. Shows fallback text "Weather unavailable" when no API key
# 3. Or shows temperature and conditions with valid API key
# 4. No console errors on failure (graceful degradation)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cat > /tmp/test_weather.js << 'EOJS'
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  // Collect console errors
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });

  try {
    await page.goto('file://' + process.env.INDEX_PATH);

    // Check weather element exists
    const weatherElement = await page.$('#weather-info');
    if (!weatherElement) {
      console.error('FAIL: Weather widget element not found');
      process.exit(1);
    }

    // Wait a moment for weather to load or show fallback
    await page.waitForTimeout(2000);

    const weatherText = await page.textContent('#weather-info');

    // Valid states:
    // 1. "Loading weather..." (initial state)
    // 2. "Weather unavailable" (no API key or error)
    // 3. "XX°C, Condition" (success with API key)

    const validStates = [
      /Loading weather\.\.\./,
      /Weather unavailable/,
      /\d+°C, \w+/,  // e.g., "15°C, Cloudy"
    ];

    const isValid = validStates.some(regex => regex.test(weatherText));

    if (!isValid) {
      console.error(`FAIL: Weather text in unexpected format: ${weatherText}`);
      process.exit(1);
    }

    // Check for console errors related to weather (except expected network failures)
    const weatherErrors = consoleErrors.filter(err =>
      !err.includes('net::ERR') && // Network errors are acceptable
      !err.includes('Failed to fetch') // Fetch failures are acceptable
    );

    if (weatherErrors.length > 0) {
      console.error('FAIL: Unexpected console errors:', weatherErrors);
      process.exit(1);
    }

    console.log('PASS: Weather widget displays correctly');
    console.log(`  Weather text: ${weatherText}`);
    console.log(`  Console errors (excluding network): ${weatherErrors.length}`);

    await browser.close();
    process.exit(0);

  } catch (error) {
    console.error('FAIL: Error during weather verification:', error.message);
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
node /tmp/test_weather.js
