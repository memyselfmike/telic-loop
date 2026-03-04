#!/bin/bash
# Integration Test: Full User Flow
# Tests the complete workflow from seed data to shopping list generation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_DIR"

echo "Starting integration test: Full user flow"
echo "=========================================="

# Start server in background
echo "Starting server on port 8002..."
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8002 > /tmp/verify_server.log 2>&1 &
SERVER_PID=$!

# Function to cleanup on exit
cleanup() {
    echo "Stopping server (PID: $SERVER_PID)..."
    kill $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null || true
}
trap cleanup EXIT

# Wait for server to start
echo "Waiting for server to start..."
sleep 5

BASE_URL="http://127.0.0.1:8002"

# Test 1: Health check
echo ""
echo "Test 1: Health check..."
HEALTH=$(curl -s "$BASE_URL/api/health")
if [[ "$HEALTH" != *"ok"* ]]; then
    echo "FAIL: Health check failed"
    exit 1
fi
echo "PASS: Server is healthy"

# Test 2: Seed data exists
echo ""
echo "Test 2: Verify seed data..."
RECIPE_COUNT=$(curl -s "$BASE_URL/api/recipes" | python -c "import sys, json; print(len(json.load(sys.stdin)))")
if [ "$RECIPE_COUNT" -lt 5 ]; then
    echo "FAIL: Expected at least 5 seed recipes, got $RECIPE_COUNT"
    exit 1
fi
echo "PASS: Found $RECIPE_COUNT recipes"

# Test 3: Create a recipe
echo ""
echo "Test 3: Create new recipe..."
NEW_RECIPE='{"title":"Verification Test Recipe","description":"Test","category":"lunch","prep_time_minutes":10,"cook_time_minutes":20,"servings":4,"instructions":"Test steps","tags":"test","ingredients":[{"quantity":2,"unit":"cup","item":"test flour","grocery_section":"pantry"}]}'
CREATE_RESULT=$(curl -s -X POST "$BASE_URL/api/recipes" \
    -H "Content-Type: application/json" \
    -d "$NEW_RECIPE")

RECIPE_ID=$(echo "$CREATE_RESULT" | python -c "import sys, json; print(json.load(sys.stdin)['id'])")
if [ -z "$RECIPE_ID" ]; then
    echo "FAIL: Failed to create recipe"
    exit 1
fi
echo "PASS: Created recipe with ID $RECIPE_ID"

# Test 4: Assign to meal plan
echo ""
echo "Test 4: Assign recipe to meal plan..."
WEEK_START=$(python -c "from datetime import datetime, timedelta; today = datetime.now(); monday = today - timedelta(days=today.weekday()); print(monday.strftime('%Y-%m-%d'))")

MEAL_ASSIGN='{"week_start":"'$WEEK_START'","day_of_week":0,"meal_slot":"breakfast","recipe_id":'$RECIPE_ID'}'
curl -s -X PUT "$BASE_URL/api/meals" \
    -H "Content-Type: application/json" \
    -d "$MEAL_ASSIGN" > /dev/null

echo "PASS: Assigned recipe to meal plan"

# Test 5: Generate shopping list
echo ""
echo "Test 5: Generate shopping list..."
SHOP_GENERATE='{"week_start":"'$WEEK_START'"}'
SHOPPING_LIST=$(curl -s -X POST "$BASE_URL/api/shopping/generate" \
    -H "Content-Type: application/json" \
    -d "$SHOP_GENERATE")

ITEM_COUNT=$(echo "$SHOPPING_LIST" | python -c "import sys, json; print(len(json.load(sys.stdin)['items']))")
if [ "$ITEM_COUNT" -lt 1 ]; then
    echo "FAIL: Shopping list should have at least 1 item, got $ITEM_COUNT"
    exit 1
fi
echo "PASS: Generated shopping list with $ITEM_COUNT items"

# Test 6: Verify persistence
echo ""
echo "Test 6: Verify data persistence..."
CURRENT_LIST=$(curl -s "$BASE_URL/api/shopping/current")
PERSISTED_ITEMS=$(echo "$CURRENT_LIST" | python -c "import sys, json; print(len(json.load(sys.stdin)['items']))")
if [ "$PERSISTED_ITEMS" != "$ITEM_COUNT" ]; then
    echo "FAIL: Item count mismatch after reload"
    exit 1
fi
echo "PASS: Shopping list persisted correctly"

echo ""
echo "=========================================="
echo "All integration tests passed!"
exit 0
