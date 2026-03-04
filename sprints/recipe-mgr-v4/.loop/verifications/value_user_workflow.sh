#!/usr/bin/bash
# Value Delivery Verification
# Verifies user-visible value: can they actually use the app to plan meals and shop?

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_DIR"

echo "=== VALUE CHECK: User Workflow Verification ==="

# Start server
echo "Starting server..."
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8002 > /tmp/value_server.log 2>&1 &
SERVER_PID=$!
sleep 3

cleanup() {
    kill $SERVER_PID 2>/dev/null || true
}
trap cleanup EXIT

# Value Proof 1: User sees seed recipes immediately
echo "VALUE 1: User opens app and sees recipes immediately..."
RECIPES=$(curl -s http://localhost:8002/api/recipes)
RECIPE_COUNT=$(echo "$RECIPES" | python -c "import sys, json; print(len(json.load(sys.stdin)))")
if [ "$RECIPE_COUNT" -ge 5 ]; then
    echo "  ✓ User sees $RECIPE_COUNT recipes (including 5 seed recipes)"
else
    echo "  ✗ FAIL: User would see empty app"
    exit 1
fi

# Value Proof 2: Frontend loads
echo "VALUE 2: Frontend loads and serves HTML..."
HOMEPAGE=$(curl -s http://localhost:8002/)
if [[ "$HOMEPAGE" == *"Recipe Manager"* ]]; then
    echo "  ✓ User can open the app in browser"
else
    echo "  ✗ FAIL: Frontend doesn't load"
    exit 1
fi

# Value Proof 3: Can create recipe with ingredients
echo "VALUE 3: User can create their own recipe..."
CREATE_RESULT=$(curl -s -X POST http://localhost:8002/api/recipes -H "Content-Type: application/json" -d '{
  "title": "My Recipe",
  "description": "A test recipe",
  "category": "dinner",
  "prep_time_minutes": 15,
  "cook_time_minutes": 30,
  "servings": 4,
  "instructions": "Cook it",
  "tags": "easy,quick",
  "ingredients": [
    {"quantity": 2, "unit": "cup", "item": "flour", "grocery_section": "pantry"},
    {"quantity": 1, "unit": "tsp", "item": "salt", "grocery_section": "pantry"}
  ]
}')
NEW_ID=$(echo "$CREATE_RESULT" | python -c "import sys, json; print(json.load(sys.stdin)['id'])")
if [ -n "$NEW_ID" ]; then
    echo "  ✓ User can add their own recipes (ID: $NEW_ID)"
else
    echo "  ✗ FAIL: User can't create recipes"
    exit 1
fi

# Value Proof 4: Can plan weekly meals
echo "VALUE 4: User can plan their weekly meals..."
WEEK=$(python -c "from datetime import datetime, timedelta; print((datetime.now() - timedelta(days=datetime.now().weekday())).strftime('%Y-%m-%d'))")
PLAN_RESULT=$(curl -s -X PUT http://localhost:8002/api/meals -H "Content-Type: application/json" -d "{\"week_start\":\"$WEEK\",\"day_of_week\":1,\"meal_slot\":\"dinner\",\"recipe_id\":$NEW_ID}")
if [[ "$PLAN_RESULT" == *"$NEW_ID"* ]]; then
    echo "  ✓ User can assign recipes to meal slots"
else
    echo "  ✗ FAIL: Meal planning broken"
    exit 1
fi

# Value Proof 5: Get aggregated shopping list
echo "VALUE 5: User gets auto-generated shopping list..."
SHOPPING=$(curl -s -X POST http://localhost:8002/api/shopping/generate -H "Content-Type: application/json" -d "{\"week_start\":\"$WEEK\"}")
ITEMS=$(echo "$SHOPPING" | python -c "import sys, json; items = json.load(sys.stdin)['items']; print(len(items))")
if [ "$ITEMS" -gt 0 ]; then
    echo "  ✓ User gets shopping list with $ITEMS items (aggregated ingredients)"
else
    echo "  ✗ FAIL: Shopping list generation broken"
    exit 1
fi

# Value Proof 6: Data persists
echo "VALUE 6: User's data persists in database..."
if [ -f "data/recipes.db" ]; then
    DB_SIZE=$(stat -c%s "data/recipes.db" 2>/dev/null || stat -f%z "data/recipes.db" 2>/dev/null || echo "0")
    if [ "$DB_SIZE" -gt 1000 ]; then
        echo "  ✓ SQLite database exists and contains data ($DB_SIZE bytes)"
    else
        echo "  ✗ FAIL: Database too small or empty"
        exit 1
    fi
else
    echo "  ✗ FAIL: Database file missing"
    exit 1
fi

echo ""
echo "=== ALL VALUE CHECKS PASSED ==="
echo "✓ User can browse recipes"
echo "✓ User can create recipes with ingredients"
echo "✓ User can plan weekly meals"
echo "✓ User can generate shopping lists"
echo "✓ User's data persists"
echo ""
echo "The app delivers the promised value from the Vision!"

exit 0
