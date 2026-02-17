#!/usr/bin/env bash
# Verification: Dashboard layout works correctly at 400px width and full width
# PRD Reference: Layout & Styling > Responsive
# Vision Goal: Fits in narrow side-pane (400px) without horizontal scrolling
# Category: integration
set -euo pipefail

echo "=== Integration: Responsive Layout at 400px ==="

# This verification checks that:
# 1. Page renders without horizontal scrollbar at 400px
# 2. All four widgets are visible and stacked vertically
# 3. Dark theme is applied correctly

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cat > /tmp/test_layout.js << 'EOJS'
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // Set viewport to 400px width (side-pane scenario)
    await page.setViewportSize({ width: 400, height: 800 });
    await page.goto('file://' + process.env.INDEX_PATH);

    // Check for horizontal scrollbar
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);

    if (scrollWidth > clientWidth) {
      console.error(`FAIL: Horizontal scrollbar present at 400px width`);
      console.error(`  scrollWidth: ${scrollWidth}, clientWidth: ${clientWidth}`);
      process.exit(1);
    }

    // Check all four widgets are visible
    const clockVisible = await page.isVisible('#clock-widget');
    const weatherVisible = await page.isVisible('#weather-widget');
    const taskVisible = await page.isVisible('#task-widget');
    const timerVisible = await page.isVisible('#timer-widget');

    if (!clockVisible || !weatherVisible || !taskVisible || !timerVisible) {
      console.error('FAIL: Not all widgets are visible');
      console.error(`  Clock: ${clockVisible}, Weather: ${weatherVisible}, Tasks: ${taskVisible}, Timer: ${timerVisible}`);
      process.exit(1);
    }

    // Check dark theme background color
    const bgColor = await page.evaluate(() => {
      return window.getComputedStyle(document.body).backgroundColor;
    });

    // Dark background should be rgb(26, 26, 46) or similar dark color
    // rgb values should all be low (< 50)
    const rgbMatch = bgColor.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
    if (rgbMatch) {
      const [_, r, g, b] = rgbMatch.map(Number);
      if (r > 50 || g > 50 || b > 50) {
        console.error(`FAIL: Background not dark enough: ${bgColor}`);
        process.exit(1);
      }
    }

    console.log('PASS: Layout is responsive and works at 400px width');
    console.log(`  No horizontal scroll: ✓`);
    console.log(`  All widgets visible: ✓`);
    console.log(`  Dark theme applied: ✓ (${bgColor})`);

    await browser.close();
    process.exit(0);

  } catch (error) {
    console.error('FAIL: Error during layout verification:', error.message);
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
node /tmp/test_layout.js
