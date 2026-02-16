#!/bin/bash
# Loop V2 Configuration - Colors, paths, and constants
#
# Dependencies: lib/_init.sh (for LOOP_ROOT)
#
# This configuration is SPRINT-AGNOSTIC. Override these defaults via:
# 1. Environment variables (e.g., LOOP_BACKEND_PORT=8080)
# 2. Project .env file
# 3. Sprint-specific config in {SPRINT_DIR}/loop-config.sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ═══════════════════════════════════════════════════════════════════════════
# SERVICE CONFIGURATION (Override via environment for different projects)
# ═══════════════════════════════════════════════════════════════════════════
#
# SERVICE DISCOVERY PRIORITY:
# 1. {SPRINT_DIR}/services.yaml - Explicit sprint service definitions
# 2. docker-compose.yml         - Docker Compose orchestration
# 3. Environment variables      - LOOP_*_PORT settings below
# 4. VISION.md keywords         - Fallback heuristic detection
#
# For complex projects, create services.yaml in your sprint folder.
# See: loop-v2/templates/services.yaml.template

# Use services v2 (extensible) or v1 (legacy npm-focused)
# Auto-detects: if docker-compose.yml or services.yaml exists, uses v2
LOOP_SERVICES_VERSION="${LOOP_SERVICES_VERSION:-auto}"

# Service startup timeout (seconds)
LOOP_SERVICE_TIMEOUT="${LOOP_SERVICE_TIMEOUT:-60}"

# Legacy port settings (used when no services.yaml or docker-compose)
LOOP_BACKEND_PORT="${LOOP_BACKEND_PORT:-3001}"
LOOP_BACKEND_HEALTH="${LOOP_BACKEND_HEALTH:-/api/health}"
LOOP_FRONTEND_PORT="${LOOP_FRONTEND_PORT:-3000}"
LOOP_FRONTEND_HEALTH="${LOOP_FRONTEND_HEALTH:-/}"
LOOP_CDP_PORT="${LOOP_CDP_PORT:-9222}"

# Export service config for prompts
export LOOP_SERVICES_VERSION LOOP_SERVICE_TIMEOUT
export LOOP_BACKEND_PORT LOOP_BACKEND_HEALTH
export LOOP_FRONTEND_PORT LOOP_FRONTEND_HEALTH
export LOOP_CDP_PORT

# ═══════════════════════════════════════════════════════════════════════════
# LOOP PROTECTION SETTINGS
# ═══════════════════════════════════════════════════════════════════════════

# Loop protection settings
MAX_TASK_ATTEMPTS=5
BLOCKER_CHECK_INTERVAL=3  # Run blocker check every N iterations

# Regression check settings
REGRESSION_CHECK_INTERVAL=5  # Run regression check every N fixes

# Random spot check settings
# These add unpredictability to regression detection - catching issues faster
SPOT_CHECK_PROBABILITY=30   # Percentage chance each iteration (0-100)
SPOT_CHECK_COUNT=2          # Number of random tests to check when triggered

# Max consecutive blocked before giving up
MAX_CONSECUTIVE_BLOCKED=5

# Protected branches that should not be worked on directly
PROTECTED_BRANCHES="main master develop"

# ═══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

# Safe grep -c: always returns a clean integer, never double-outputs.
# Usage: count=$(grepcount "pattern" "$file")
grepcount() {
    local result
    result=$(grep -c "$@" 2>/dev/null) || result=0
    # Strip Windows CRLF artifacts
    echo "${result}" | tr -d '\r\n'
}

# Export colors for subshells
export RED GREEN YELLOW BLUE PURPLE CYAN NC
