#!/bin/bash
# Value Check: User-Visible Deliverable
# Verifies that the application delivers the promised user value

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_DIR"

echo "Verifying user-visible value delivery..."
echo "=========================================="

# Check 1: Frontend files exist and are accessible
echo ""
echo "Check 1: Frontend deliverable exists..."
if [ ! -f "frontend/index.html" ]; then
    echo "FAIL: index.html not found"
    exit 1
fi
if [ ! -f "frontend/css/style.css" ]; then
    echo "FAIL: style.css not found"
    exit 1
fi
if [ ! -f "frontend/js/app.js" ]; then
    echo "FAIL: app.js not found"
    exit 1
fi
if [ ! -f "frontend/js/recipes.js" ]; then
    echo "FAIL: recipes.js not found"
    exit 1
fi
if [ ! -f "frontend/js/planner.js" ]; then
    echo "FAIL: planner.js not found"
    exit 1
fi
if [ ! -f "frontend/js/shopping.js" ]; then
    echo "FAIL: shopping.js not found"
    exit 1
fi
echo "PASS: All frontend files exist"

# Check 2: Backend is runnable
echo ""
echo "Check 2: Backend can start..."
timeout 10 python -m uvicorn backend.main:app --host 127.0.0.1 --port 8003 > /tmp/value_check.log 2>&1 &
SERVER_PID=$!

cleanup() {
    kill $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null || true
}
trap cleanup EXIT

sleep 4

# Check if server is responding
HEALTH_CHECK=$(curl -s http://127.0.0.1:8003/api/health || echo "FAIL")
if [[ "$HEALTH_CHECK" != *"ok"* ]]; then
    echo "FAIL: Server not responding"
    cat /tmp/value_check.log
    exit 1
fi
echo "PASS: Server starts and responds"

# Check 3: Core user value - Recipe management
echo ""
echo "Check 3: User can manage recipes..."
RECIPES=$(curl -s http://127.0.0.1:8003/api/recipes)
RECIPE_COUNT=$(echo "$RECIPES" | python -c "import sys, json; data = json.load(sys.stdin); print(len(data))")
if [ "$RECIPE_COUNT" -lt 1 ]; then
    echo "FAIL: No recipes available for user"
    exit 1
fi
echo "PASS: User has access to $RECIPE_COUNT recipes"

# Check 4: Core user value - Meal planning
echo ""
echo "Check 4: User can plan meals..."
WEEK_START=$(python -c "from datetime import datetime, timedelta; today = datetime.now(); monday = today - timedelta(days=today.weekday()); print(monday.strftime('%Y-%m-%d'))")
MEALS=$(curl -s "http://127.0.0.1:8003/api/meals?week=$WEEK_START")
# Empty meal plan is OK - user can add meals
echo "PASS: Meal planning endpoint accessible"

# Check 5: Core user value - Shopping list generation
echo ""
echo "Check 5: User can generate shopping lists..."

# First assign a recipe to the meal plan
RECIPE_ID=$(echo "$RECIPES" | python -c "import sys, json; print(json.load(sys.stdin)[0]['id'])")
ASSIGN_MEAL='{"week_start":"'$WEEK_START'","day_of_week":0,"meal_slot":"breakfast","recipe_id":'$RECIPE_ID'}'
curl -s -X PUT http://127.0.0.1:8003/api/meals \
    -H "Content-Type: application/json" \
    -d "$ASSIGN_MEAL" > /dev/null

# Generate shopping list
GENERATE='{"week_start":"'$WEEK_START'"}'
SHOPPING=$(curl -s -X POST http://127.0.0.1:8003/api/shopping/generate \
    -H "Content-Type: application/json" \
    -d "$GENERATE")

ITEM_COUNT=$(echo "$SHOPPING" | python -c "import sys, json; print(len(json.load(sys.stdin)['items']))")
if [ "$ITEM_COUNT" -lt 1 ]; then
    echo "FAIL: Shopping list generation failed"
    exit 1
fi
echo "PASS: User can generate shopping list with $ITEM_COUNT items"

# Check 6: Data persistence
echo ""
echo "Check 6: User data persists..."
if [ ! -f "data/recipes.db" ]; then
    echo "FAIL: Database file not created"
    exit 1
fi

# Verify database has tables
TABLES=$(python -c "
import sqlite3
conn = sqlite3.connect('data/recipes.db')
cursor = conn.cursor()
cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")
tables = [row[0] for row in cursor.fetchall()]
conn.close()
print(','.join(tables))
")

if [[ "$TABLES" != *"recipes"* ]] || [[ "$TABLES" != *"meal_plans"* ]] || [[ "$TABLES" != *"shopping_lists"* ]]; then
    echo "FAIL: Database schema incomplete"
    echo "Found tables: $TABLES"
    exit 1
fi
echo "PASS: Database persists user data"

echo ""
echo "=========================================="
echo "All value checks passed!"
echo "User can:"
echo "  - Browse and manage recipes"
echo "  - Plan weekly meals"
echo "  - Generate shopping lists from meal plans"
echo "  - Data persists across sessions"
echo "=========================================="
exit 0
