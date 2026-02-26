#!/usr/bin/env bash
# Wrapper script for integration_state_management verification
# Executes standalone Node.js Playwright script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

node .loop/verifications/integration_state_management.js
