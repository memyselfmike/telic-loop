#!/usr/bin/env bash
# Setup: Install Playwright for E2E value verification
# This script is idempotent - safe to run multiple times
# Run this once before running value_* scripts

set -euo pipefail

SPRINT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERIF_DIR="$(dirname "${BASH_SOURCE[0]}")"
echo "=== Setup: Playwright E2E Test Environment ==="
echo ""

# Install Playwright in the sprint directory if not present
if [[ ! -d "$SPRINT_DIR/node_modules/@playwright" ]]; then
  echo "Installing Playwright..."
  cd "$SPRINT_DIR"
  npm install --save-dev @playwright/test 2>&1 | tail -5
  echo "Done."
else
  echo "Playwright already installed."
fi

# Install browser binaries if not present
echo ""
if npx playwright --version >/dev/null 2>&1; then
  echo "Installing Playwright browser binaries..."
  cd "$SPRINT_DIR"
  npx playwright install chromium 2>&1 | tail -5
  echo "Done."
fi

# Create playwright.config.ts in the sprint directory if not present
PLAYWRIGHT_CONFIG="$SPRINT_DIR/playwright.config.ts"
if [[ ! -f "$PLAYWRIGHT_CONFIG" ]]; then
  echo ""
  echo "Creating playwright.config.ts..."
  cat > "$PLAYWRIGHT_CONFIG" << 'EOF'
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: '.loop/verifications/playwright',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:4321',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'mobile',
      use: { ...devices['iPhone 13'] },
    },
  ],
  // Start Astro dev server automatically
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:4321',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
    env: {
      SANITY_PROJECT_ID: process.env.SANITY_PROJECT_ID || 'placeholder',
      SANITY_DATASET: process.env.SANITY_DATASET || 'production',
      SANITY_API_TOKEN: process.env.SANITY_API_TOKEN || 'placeholder',
      PUBLIC_FORM_ACTION: process.env.PUBLIC_FORM_ACTION || 'https://example.com/form',
    },
  },
});
EOF
  echo "Created: $PLAYWRIGHT_CONFIG"
fi

# Create playwright test directory
mkdir -p "$SPRINT_DIR/.loop/verifications/playwright"

echo ""
echo "Setup complete. Run value_* scripts to execute Playwright tests."
exit 0
