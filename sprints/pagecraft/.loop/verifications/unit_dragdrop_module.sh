#!/usr/bin/env bash
# Verification: Drag-and-drop module initialization
# Category: unit
set -euo pipefail

cd "$(dirname "$0")/../.."
PORT="${PORT:-3000}" npx playwright test --config=playwright.config.js unit_dragdrop_module.spec.js
