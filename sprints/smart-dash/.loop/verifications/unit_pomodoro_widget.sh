#!/usr/bin/env bash
# Verification: Pomodoro timer widget has all required controls and display elements
# PRD Reference: Widgets > Pomodoro Timer Widget
# Vision Goal: Visible timer for healthy work-break cadence
# Category: unit
set -euo pipefail

echo "=== Unit: Pomodoro Timer Widget Elements ==="

# This verification checks that:
# 1. Timer display exists and shows MM:SS format
# 2. Start, Pause, Reset buttons exist
# 3. Mode label (WORK/BREAK) exists
# 4. Completed pomodoro count display exists

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cat > /tmp/test_pomodoro.js << 'EOJS'
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    await page.goto('file://' + process.env.INDEX_PATH);

    // Check timer display
    const timerDisplay = await page.$('#timer-display');
    if (!timerDisplay) {
      console.error('FAIL: Timer display not found');
      process.exit(1);
    }

    const displayText = await page.textContent('#timer-display');
    const timeRegex = /^\d{1,2}:\d{2}$/; // MM:SS format
    if (!timeRegex.test(displayText)) {
      console.error(`FAIL: Timer display format incorrect. Expected MM:SS, got: ${displayText}`);
      process.exit(1);
    }

    // Check mode label
    const modeLabel = await page.$('#timer-mode');
    if (!modeLabel) {
      console.error('FAIL: Timer mode label not found');
      process.exit(1);
    }

    const modeText = await page.textContent('#timer-mode');
    if (!['WORK', 'BREAK'].includes(modeText)) {
      console.error(`FAIL: Mode label should be WORK or BREAK, got: ${modeText}`);
      process.exit(1);
    }

    // Check buttons exist
    const startBtn = await page.$('#timer-start');
    const pauseBtn = await page.$('#timer-pause');
    const resetBtn = await page.$('#timer-reset');

    if (!startBtn || !pauseBtn || !resetBtn) {
      console.error('FAIL: Not all timer control buttons found');
      process.exit(1);
    }

    // Check stats display
    const stats = await page.$('#timer-stats');
    if (!stats) {
      console.error('FAIL: Timer stats element not found');
      process.exit(1);
    }

    const statsText = await page.textContent('#timer-stats');
    if (!statsText.includes('pomodoro')) {
      console.error(`FAIL: Stats text should mention pomodoros, got: ${statsText}`);
      process.exit(1);
    }

    console.log('PASS: Pomodoro timer widget elements exist and are correctly formatted');
    console.log(`  Display: ${displayText}`);
    console.log(`  Mode: ${modeText}`);
    console.log(`  Stats: ${statsText}`);
    console.log('  Controls: Start, Pause, Reset ✓');

    await browser.close();
    process.exit(0);

  } catch (error) {
    console.error('FAIL: Error during pomodoro verification:', error.message);
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
node /tmp/test_pomodoro.js
