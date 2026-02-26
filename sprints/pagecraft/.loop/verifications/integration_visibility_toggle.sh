#!/usr/bin/env bash
# Verification: Section visibility toggle preview integration
# Category: integration
set -euo pipefail

cd "$(dirname "$0")/../.."
PORT="${PORT:-3000}" npx playwright test --config=playwright.config.js integration_visibility_toggle.spec.js
