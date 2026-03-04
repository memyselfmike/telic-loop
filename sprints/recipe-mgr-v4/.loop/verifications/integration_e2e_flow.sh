#!/usr/bin/bash
# End-to-End Integration Test
# Tests complete user workflow: create recipe -> plan meals -> generate shopping list

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_DIR"

# Start server in background
echo "Starting server..."
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 > /tmp/e2e_server.log 2>&1 &
SERVER_PID=$!
sleep 3

# Cleanup function
cleanup() {
    echo "Stopping server..."
    kill $SERVER_PID 2>/dev/null || true
    rm -f /tmp/e2e_test.db
}
trap cleanup EXIT

# Test 1: Health check
echo "Test 1: Health check..."
HEALTH=$(curl -s http://localhost:8001/api/health)
if [[ "$HEALTH" != *"ok"* ]]; then
    echo "FAIL: Health check failed"
    exit 1
fi

# Test 2: Seed recipes present
echo "Test 2: Seed recipes present..."
RECIPE_COUNT=$(curl -s http://localhost:8001/api/recipes | python -c "import sys, json; print(len(json.load(sys.stdin)))")
if [ "$RECIPE_COUNT" -lt 5 ]; then
    echo "FAIL: Expected at least 5 seed recipes, got $RECIPE_COUNT"
    exit 1
fi

# Test 3: Create new recipe
echo "Test 3: Create new recipe..."
RECIPE_JSON='{"title":"E2E Test Recipe","description":"Test","category":"dinner","prep_time_minutes":10,"cook_time_minutes":20,"servings":4,"instructions":"Test instructions","tags":"test","ingredients":[{"quantity":1,"unit":"cup","item":"test ingredient","grocery_section":"pantry"}]}'
NEW_RECIPE=$(curl -s -X POST http://localhost:8001/api/recipes -H "Content-Type: application/json" -d "$RECIPE_JSON")
RECIPE_ID=$(echo "$NEW_RECIPE" | python -c "import sys, json; print(json.load(sys.stdin)['id'])")
if [ -z "$RECIPE_ID" ]; then
    echo "FAIL: Recipe creation failed"
    exit 1
fi

# Test 4: Assign to meal plan
echo "Test 4: Assign recipe to meal plan..."
WEEK_START=$(python -c "from datetime import datetime, timedelta; today = datetime.now(); monday = today - timedelta(days=today.weekday()); print(monday.strftime('%Y-%m-%d'))")
MEAL_JSON="{\"week_start\":\"$WEEK_START\",\"day_of_week\":1,\"meal_slot\":\"lunch\",\"recipe_id\":$RECIPE_ID}"
MEAL_RESULT=$(curl -s -X PUT http://localhost:8001/api/meals -H "Content-Type: application/json" -d "$MEAL_JSON")
if [[ "$MEAL_RESULT" != *"$RECIPE_ID"* ]]; then
    echo "FAIL: Meal plan assignment failed"
    exit 1
fi

# Test 5: Generate shopping list
echo "Test 5: Generate shopping list..."
SHOPPING_JSON="{\"week_start\":\"$WEEK_START\"}"
SHOPPING_LIST=$(curl -s -X POST http://localhost:8001/api/shopping/generate -H "Content-Type: application/json" -d "$SHOPPING_JSON")
ITEM_COUNT=$(echo "$SHOPPING_LIST" | python -c "import sys, json; print(len(json.load(sys.stdin)['items']))")
if [ "$ITEM_COUNT" -lt 1 ]; then
    echo "FAIL: Shopping list generation failed"
    exit 1
fi

# Test 6: Toggle shopping item
echo "Test 6: Toggle shopping item..."
ITEM_ID=$(echo "$SHOPPING_LIST" | python -c "import sys, json; print(json.load(sys.stdin)['items'][0]['id'])")
TOGGLE_RESULT=$(curl -s -X PATCH http://localhost:8001/api/shopping/items/$ITEM_ID -H "Content-Type: application/json" -d '{"checked":true}')
if [[ "$TOGGLE_RESULT" != *"true"* ]]; then
    echo "FAIL: Toggle shopping item failed"
    exit 1
fi

echo "All E2E tests passed!"
exit 0
