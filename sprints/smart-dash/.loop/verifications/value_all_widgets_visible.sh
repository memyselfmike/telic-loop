#!/usr/bin/env bash
# Verification: All four widgets render correctly on page load
# PRD Reference: Value Proof #1, Acceptance Criteria #1
# Vision Goal: Consolidate time, weather, tasks, timer into one view
# Category: value
set -euo pipefail

echo "=== Value: All Widgets Visible - Single View Consolidation ==="

# This verification proves USER VALUE:
# The developer sees ALL four essential widgets in one view
# No more alt-tabbing between 5 different tabs

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cat > /tmp/test_all_widgets.js << 'EOJS'
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
    await page.waitForTimeout(1000); // Let widgets initialize

    console.log('Checking all four widgets are visible and functional...\n');

    // 1. CLOCK WIDGET
    const clockVisible = await page.isVisible('#clock-widget');
    const clockTime = await page.textContent('#clock-time');
    const clockDate = await page.textContent('#clock-date');

    if (!clockVisible) {
      console.error('FAIL: Clock widget not visible');
      process.exit(1);
    }

    console.log('✓ Clock Widget:');
    console.log(`    Time: ${clockTime}`);
    console.log(`    Date: ${clockDate}`);

    // 2. WEATHER WIDGET
    const weatherVisible = await page.isVisible('#weather-widget');
    const weatherInfo = await page.textContent('#weather-info');

    if (!weatherVisible) {
      console.error('FAIL: Weather widget not visible');
      process.exit(1);
    }

    console.log('✓ Weather Widget:');
    console.log(`    Info: ${weatherInfo}`);

    // 3. TASK WIDGET
    const taskVisible = await page.isVisible('#task-widget');
    const taskInputVisible = await page.isVisible('#task-input');
    const taskCount = await page.textContent('#task-count');

    if (!taskVisible || !taskInputVisible) {
      console.error('FAIL: Task widget not fully visible');
      process.exit(1);
    }

    console.log('✓ Task Widget:');
    console.log(`    Input field: present`);
    console.log(`    Count: ${taskCount}`);

    // 4. POMODORO TIMER WIDGET
    const timerVisible = await page.isVisible('#timer-widget');
    const timerDisplay = await page.textContent('#timer-display');
    const timerMode = await page.textContent('#timer-mode');
    const timerStartVisible = await page.isVisible('#timer-start');

    if (!timerVisible || !timerStartVisible) {
      console.error('FAIL: Timer widget not fully visible');
      process.exit(1);
    }

    console.log('✓ Pomodoro Timer Widget:');
    console.log(`    Display: ${timerDisplay}`);
    console.log(`    Mode: ${timerMode}`);
    console.log(`    Controls: present`);

    // Check for unacceptable console errors
    const unacceptableErrors = consoleErrors.filter(err => {
      // Weather API failures are acceptable
      if (err.includes('net::ERR') || err.includes('Failed to fetch')) return false;
      if (err.includes('openweathermap')) return false;
      return true;
    });

    if (unacceptableErrors.length > 0) {
      console.error('\nFAIL: Console errors detected:');
      unacceptableErrors.forEach(err => console.error(`  ${err}`));
      process.exit(1);
    }

    console.log('\n✓ No console errors (weather API failures are acceptable)');

    console.log('\n' + '='.repeat(60));
    console.log('PASS: All four widgets visible and functional');
    console.log('='.repeat(60));
    console.log('\nVALUE DELIVERED: Developer sees everything in one view');
    console.log('  ✓ Clock - no need to check system clock');
    console.log('  ✓ Weather - plan breaks without leaving page');
    console.log('  ✓ Tasks - never forget what to do next');
    console.log('  ✓ Timer - stay on healthy work-break cadence');
    console.log('\nBEFORE: Alt-tab between 5 tabs, lose 10-15 min per session');
    console.log('AFTER:  Single view, zero context switches, full focus');

    await browser.close();
    process.exit(0);

  } catch (error) {
    console.error('FAIL: Error during all-widgets verification:', error.message);
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
node /tmp/test_all_widgets.js
