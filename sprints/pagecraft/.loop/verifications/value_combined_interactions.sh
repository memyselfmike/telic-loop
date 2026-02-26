#!/usr/bin/env bash
# Verification: All Epic 2 features work together
# Category: value
set -euo pipefail

cd "$(dirname "$0")/../.."
PORT="${PORT:-3000}" npx playwright test --config=playwright.config.js value_combined_interactions.spec.js
