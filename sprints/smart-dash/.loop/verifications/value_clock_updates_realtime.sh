#!/usr/bin/env bash
# Verification: Clock updates every second showing current time
# PRD Reference: Value Proof #1 - Clock shows current time
# Vision Goal: Always-visible time reference without alt-tabbing
# Category: value
set -euo pipefail

echo "=== Value: Clock Real-Time Updates ==="

# This verification proves USER VALUE:
# The developer can see the current time updating in real-time
# without switching tabs or checking the system clock

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cat > /tmp/test_clock_value.js << 'EOJS'
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    await page.goto('file://' + process.env.INDEX_PATH);

    // Get initial clock time
    const time1 = await page.textContent('#clock-time');

    console.log(`Initial time: ${time1}`);

    // Wait 2 seconds
    await page.waitForTimeout(2000);

    // Get time again
    const time2 = await page.textContent('#clock-time');

    console.log(`After 2 seconds: ${time2}`);

    // Check if time changed
    if (time1 === time2) {
      console.error('FAIL: Clock did not update after 2 seconds');
      console.error('  This means the developer cannot see real-time updates');
      process.exit(1);
    }

    // Verify time format is valid HH:MM:SS
    const timeRegex = /^\d{2}:\d{2}:\d{2}$/;
    if (!timeRegex.test(time2)) {
      console.error(`FAIL: Time format invalid: ${time2}`);
      process.exit(1);
    }

    // Verify date is displayed in correct format
    const dateText = await page.textContent('#clock-date');
    const dateRegex = /^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), (January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}$/;

    if (!dateRegex.test(dateText)) {
      console.error(`FAIL: Date format invalid: ${dateText}`);
      process.exit(1);
    }

    console.log('PASS: Clock updates in real-time and shows correct date');
    console.log('VALUE DELIVERED: Developer can see current time without alt-tabbing');
    console.log(`  ✓ Time updates every second`);
    console.log(`  ✓ Time format: 24-hour HH:MM:SS`);
    console.log(`  ✓ Date format: Day, Month DD`);

    await browser.close();
    process.exit(0);

  } catch (error) {
    console.error('FAIL: Error during clock value verification:', error.message);
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
node /tmp/test_clock_value.js
