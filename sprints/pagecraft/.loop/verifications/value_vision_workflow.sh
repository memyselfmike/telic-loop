#!/usr/bin/env bash
# Verification: Complete Vision workflow end-to-end
# Category: value
set -euo pipefail

cd "$(dirname "$0")/../.."
PORT="${PORT:-3000}" npx playwright test --config=playwright.config.js value_vision_workflow.spec.js
