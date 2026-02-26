#!/usr/bin/env bash
# Verification: Inline text editing module
# Category: unit
set -euo pipefail

cd "$(dirname "$0")/../.."
PORT="${PORT:-3000}" npx playwright test --config=playwright.config.js unit_inline_editing.spec.js
