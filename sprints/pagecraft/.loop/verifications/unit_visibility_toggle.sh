#!/usr usr/bin/env bash
# Verification: Section visibility toggle
# Category: unit
set -euo pipefail

cd "$(dirname "$0")/../.."
PORT="${PORT:-3000}" npx playwright test --config=playwright.config.js unit_visibility_toggle.spec.js
