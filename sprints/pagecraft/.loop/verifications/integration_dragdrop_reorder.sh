#!/usr/bin/env bash
# Verification: Drag-and-drop section reordering
# Category: integration
set -euo pipefail

cd "$(dirname "$0")/../.."
PORT="${PORT:-3000}" npx playwright test --config=playwright.config.js integration_dragdrop_reorder.spec.js
