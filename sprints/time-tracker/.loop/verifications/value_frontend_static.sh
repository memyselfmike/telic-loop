#!/usr/bin/env bash
# Verification: Frontend is served as a static SPA with dark theme
# PRD Reference: Section 4.6 (Visual Design), Section 1.1 (Static file serving)
# Vision Goal: Professional dark-themed dashboard that freelancer trusts for daily use
# Category: value
set -euo pipefail

SPRINT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
echo "=== Value: Frontend Static Serving ==="
echo "Checking that the app serves a real dark-themed SPA from the FastAPI server"
echo ""

PYTHON="${PYTHON:-python}"
PORT=19876

# Start server
cd "$SPRINT_DIR"
"$PYTHON" -m uvicorn backend.main:app --port $PORT --host 127.0.0.1 &
SERVER_PID=$!
trap "kill $SERVER_PID 2>/dev/null; wait $SERVER_PID 2>/dev/null; exit" EXIT

# Wait for server
for i in $(seq 1 30); do
    if curl -s "http://127.0.0.1:$PORT/api/timer" > /dev/null 2>&1; then
        echo "Server started on port $PORT (pid=$SERVER_PID)"
        break
    fi
    sleep 0.3
    if [ $i -eq 30 ]; then
        echo "FAIL: Server did not start within timeout"
        exit 1
    fi
done

# Test 1: GET / serves HTML
HTML=$(curl -s "http://127.0.0.1:$PORT/")
if echo "$HTML" | grep -qi "<!DOCTYPE html\|<html"; then
    echo "PASS: GET / serves HTML document"
else
    echo "FAIL: GET / did not return HTML"
    exit 1
fi

# Test 2: Dark theme colors present
if echo "$HTML" | grep -q "#0d1117\|0d1117"; then
    echo "PASS: Dark theme background color #0d1117 present"
else
    echo "FAIL: Dark theme background color #0d1117 missing from HTML/CSS"
    exit 1
fi

# Test 3: Navigation tabs present (Timer, Weekly, Projects, Reports)
MISSING_TABS=()
for tab in "Timer" "Weekly" "Projects" "Reports"; do
    if ! echo "$HTML" | grep -qi "$tab"; then
        MISSING_TABS+=("$tab")
    fi
done
if [ ${#MISSING_TABS[@]} -eq 0 ]; then
    echo "PASS: All 4 navigation tabs present (Timer, Weekly, Projects, Reports)"
else
    echo "FAIL: Missing navigation tabs: ${MISSING_TABS[*]}"
    exit 1
fi

# Test 4: GET /api/timer works
TIMER_RESP=$(curl -s "http://127.0.0.1:$PORT/api/timer")
if echo "$TIMER_RESP" | python -c "import sys,json; json.load(sys.stdin); sys.exit(0)" 2>/dev/null; then
    echo "PASS: GET /api/timer returns valid JSON"
else
    echo "FAIL: GET /api/timer did not return valid JSON: $TIMER_RESP"
    exit 1
fi

# Test 5: Static CSS is served (check for style.css or inline styles)
if curl -s "http://127.0.0.1:$PORT/style.css" | grep -q "color\|background\|font" 2>/dev/null; then
    echo "PASS: style.css is served with CSS content"
elif echo "$HTML" | grep -q "<style"; then
    echo "PASS: Styles are embedded in index.html"
else
    echo "WARN: Could not verify CSS delivery (may be okay if all inline)"
fi

echo ""
echo "=== FRONTEND STATIC SERVING VALUE PROOF PASSED ==="
exit 0
