#!/usr/bin/env bash
# Verification: Accent color global coverage
# Category: integration
set -euo pipefail

cd "$(dirname "$0")/../.."
PORT="${PORT:-3000}" npx playwright test --config=playwright.config.js integration_accent_color_coverage.spec.js
