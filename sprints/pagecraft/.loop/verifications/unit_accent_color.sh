#!/usr/bin/env bash
# Verification: Accent color picker module
# Category: unit
set -euo pipefail

cd "$(dirname "$0")/../.."
PORT="${PORT:-3000}" npx playwright test --config=playwright.config.js unit_accent_color.spec.js
