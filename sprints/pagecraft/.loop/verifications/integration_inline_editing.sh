#!/usr/bin/env bash
# Verification: Inline editing state integration
# Category: integration
set -euo pipefail

cd "$(dirname "$0")/../.."
PORT="${PORT:-3000}" npx playwright test --config=playwright.config.js integration_inline_editing.spec.js
