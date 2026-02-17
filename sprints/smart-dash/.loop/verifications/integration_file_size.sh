#!/usr/bin/env bash
# Verification: Total file size of index.html is under 15KB
# PRD Reference: Technical Constraints > Single file, Acceptance Criteria #5
# Vision Goal: Lightweight single-file dashboard
# Category: integration
set -euo pipefail

echo "=== Integration: File Size Constraint ==="

# This verification checks that:
# 1. index.html exists
# 2. File size is under 15KB (15360 bytes)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
INDEX_FILE="$PROJECT_ROOT/index.html"

if [ ! -f "$INDEX_FILE" ]; then
    echo "FAIL: index.html not found at $INDEX_FILE"
    exit 1
fi

# Get file size in bytes (cross-platform)
if [[ "$OSTYPE" == "darwin"* ]]; then
    FILE_SIZE=$(stat -f%z "$INDEX_FILE")
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    # Windows - use wc or fallback to ls
    FILE_SIZE=$(wc -c < "$INDEX_FILE" 2>/dev/null || ls -l "$INDEX_FILE" | awk '{print $5}')
else
    FILE_SIZE=$(stat -c%s "$INDEX_FILE" 2>/dev/null || wc -c < "$INDEX_FILE")
fi

MAX_SIZE=15360  # 15KB in bytes

# Calculate KB using arithmetic (no bc needed)
SIZE_KB=$((FILE_SIZE / 1024))
SIZE_KB_DECIMAL=$((FILE_SIZE * 100 / 1024 % 100))

if [ "$FILE_SIZE" -gt "$MAX_SIZE" ]; then
    EXCESS=$((FILE_SIZE - MAX_SIZE))
    EXCESS_KB=$((EXCESS / 1024))
    echo "FAIL: File size exceeds 15KB limit"
    echo "  Current size: ${SIZE_KB}.${SIZE_KB_DECIMAL}KB ($FILE_SIZE bytes)"
    echo "  Maximum size: 15KB ($MAX_SIZE bytes)"
    echo "  Excess: ${EXCESS_KB}KB"
    exit 1
fi

REMAINING=$((MAX_SIZE - FILE_SIZE))
REMAINING_KB=$((REMAINING / 1024))

echo "PASS: File size is within 15KB limit"
echo "  File size: ${SIZE_KB}.${SIZE_KB_DECIMAL}KB ($FILE_SIZE bytes)"
echo "  Limit: 15KB ($MAX_SIZE bytes)"
echo "  Remaining: ${REMAINING_KB}KB"

exit 0
