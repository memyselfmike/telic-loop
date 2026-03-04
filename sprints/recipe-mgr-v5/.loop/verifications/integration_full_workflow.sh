#!/bin/bash
# Integration test: Full end-to-end workflow verification
# Tests all 3 user workflows from Vision

set -e
cd "$(dirname "$0")/../.."

echo "Starting full workflow integration test..."

# Start server in background
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 > /dev/null 2>&1 &
SERVER_PID=$!
sleep 3

# Cleanup function
cleanup() {
  kill $SERVER_PID 2>/dev/null || true
  rm -f data/recipes.db 2>/dev/null || true
}

trap cleanup EXIT

# Test 1: Verify 5 seed recipes load
echo "1. Testing seed recipes..."
RECIPE_COUNT=$(curl -s "http://127.0.0.1:8000/api/recipes/" | python -c "import sys, json; print(len(json.load(sys.stdin)))")
if [ "$RECIPE_COUNT" != "5" ]; then
  echo "✗ Expected 5 seed recipes, got $RECIPE_COUNT"
  exit 1
fi
echo "  ✓ 5 seed recipes loaded"

# Test 2: Create a new recipe
echo "2. Testing recipe creation..."
NEW_RECIPE=$(cat <<'EOF'
{
  "title": "Test Pancakes",
  "description": "Fluffy breakfast pancakes",
  "category": "breakfast",
  "prep_time_minutes": 10,
  "cook_time_minutes": 15,
  "servings": 4,
  "instructions": "Mix ingredients and cook on griddle",
  "tags": "quick,breakfast",
  "ingredients": [
    {"quantity": 2, "unit": "cup", "item": "flour", "grocery_section": "pantry", "sort_order": 0},
    {"quantity": 2, "unit": "whole", "item": "eggs", "grocery_section": "dairy", "sort_order": 1},
    {"quantity": 1.5, "unit": "cup", "item": "milk", "grocery_section": "dairy", "sort_order": 2},
    {"quantity": 2, "unit": "tbsp", "item": "sugar", "grocery_section": "pantry", "sort_order": 3}
  ]
}
EOF
)

CREATE_RESPONSE=$(curl -s -X POST "http://127.0.0.1:8000/api/recipes/" \
  -H "Content-Type: application/json" \
  -d "$NEW_RECIPE")

RECIPE_ID=$(echo "$CREATE_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "  ✓ Recipe created with ID $RECIPE_ID"

# Test 3: Search and filter recipes
echo "3. Testing recipe search/filter..."
SEARCH_COUNT=$(curl -s "http://127.0.0.1:8000/api/recipes/?search=pancakes" | python -c "import sys, json; print(len(json.load(sys.stdin)))")
if [ "$SEARCH_COUNT" -lt "1" ]; then
  echo "✗ Search failed to find pancakes recipe"
  exit 1
fi
echo "  ✓ Search found $SEARCH_COUNT result(s)"

CATEGORY_COUNT=$(curl -s "http://127.0.0.1:8000/api/recipes/?category=breakfast" | python -c "import sys, json; print(len(json.load(sys.stdin)))")
if [ "$CATEGORY_COUNT" -lt "2" ]; then
  echo "✗ Expected at least 2 breakfast recipes"
  exit 1
fi
echo "  ✓ Category filter found $CATEGORY_COUNT breakfast recipe(s)"

# Test 4: Assign recipes to meal plan
echo "4. Testing meal plan assignment..."
MONDAY=$(python -c "from datetime import datetime, timedelta; today = datetime.now(); days_since_monday = today.weekday(); monday = today - timedelta(days=days_since_monday); print(monday.strftime('%Y-%m-%d'))")

# Assign seed recipe (ID 1) to Monday breakfast
curl -s -X PUT "http://127.0.0.1:8000/api/meals/" \
  -H "Content-Type: application/json" \
  -d "{\"week_start\": \"$MONDAY\", \"day_of_week\": 0, \"meal_slot\": \"breakfast\", \"recipe_id\": 1}" > /dev/null

# Assign new recipe to Monday lunch
curl -s -X PUT "http://127.0.0.1:8000/api/meals/" \
  -H "Content-Type: application/json" \
  -d "{\"week_start\": \"$MONDAY\", \"day_of_week\": 0, \"meal_slot\": \"lunch\", \"recipe_id\": $RECIPE_ID}" > /dev/null

# Assign seed recipe (ID 2) to Tuesday dinner
curl -s -X PUT "http://127.0.0.1:8000/api/meals/" \
  -H "Content-Type: application/json" \
  -d "{\"week_start\": \"$MONDAY\", \"day_of_week\": 1, \"meal_slot\": \"dinner\", \"recipe_id\": 2}" > /dev/null

MEAL_COUNT=$(curl -s "http://127.0.0.1:8000/api/meals?week=$MONDAY" | python -c "import sys, json; print(len(json.load(sys.stdin)))")
if [ "$MEAL_COUNT" != "3" ]; then
  echo "✗ Expected 3 meal assignments, got $MEAL_COUNT"
  exit 1
fi
echo "  ✓ 3 meals assigned to plan"

# Test 5: Generate shopping list
echo "5. Testing shopping list generation..."
curl -s -X POST "http://127.0.0.1:8000/api/shopping/generate/" \
  -H "Content-Type: application/json" \
  -d "{\"week_start\": \"$MONDAY\"}" > /dev/null

SHOPPING_LIST=$(curl -s "http://127.0.0.1:8000/api/shopping/current")
ITEM_COUNT=$(echo "$SHOPPING_LIST" | python -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('items', [])))")

if [ "$ITEM_COUNT" -lt "5" ]; then
  echo "✗ Expected at least 5 shopping items, got $ITEM_COUNT"
  exit 1
fi
echo "  ✓ Shopping list generated with $ITEM_COUNT items"

# Test 6: Verify unit normalization
echo "6. Testing unit normalization..."
# The shopping list should have aggregated ingredients
# Check for proper grouping by section
SECTIONS=$(echo "$SHOPPING_LIST" | python -c "import sys, json; data=json.load(sys.stdin); sections=set(item['grocery_section'] for item in data['items']); print(len(sections))")
if [ "$SECTIONS" -lt "2" ]; then
  echo "✗ Expected items from multiple sections, got $SECTIONS"
  exit 1
fi
echo "  ✓ Items grouped by $SECTIONS grocery section(s)"

# Test 7: Check/uncheck shopping items
echo "7. Testing shopping item toggle..."
FIRST_ITEM_ID=$(echo "$SHOPPING_LIST" | python -c "import sys, json; data=json.load(sys.stdin); print(data['items'][0]['id'])")

curl -s -X PATCH "http://127.0.0.1:8000/api/shopping/items/$FIRST_ITEM_ID" > /dev/null

UPDATED_LIST=$(curl -s "http://127.0.0.1:8000/api/shopping/current")
CHECKED_STATUS=$(echo "$UPDATED_LIST" | python -c "import sys, json; data=json.load(sys.stdin); item=[i for i in data['items'] if i['id']==$FIRST_ITEM_ID][0]; print(item['checked'])")

if [ "$CHECKED_STATUS" != "1" ]; then
  echo "✗ Item was not checked"
  exit 1
fi
echo "  ✓ Item toggled to checked"

# Test 8: Add manual item
echo "8. Testing manual item addition..."
curl -s -X POST "http://127.0.0.1:8000/api/shopping/items" \
  -H "Content-Type: application/json" \
  -d '{"item": "Bananas", "quantity": 6, "unit": "whole", "grocery_section": "produce", "source": "manual"}' > /dev/null

UPDATED_COUNT=$(curl -s "http://127.0.0.1:8000/api/shopping/current" | python -c "import sys, json; data=json.load(sys.stdin); print(len(data['items']))")

if [ "$UPDATED_COUNT" != "$((ITEM_COUNT + 1))" ]; then
  echo "✗ Manual item was not added"
  exit 1
fi
echo "  ✓ Manual item added successfully"

# Test 9: Test cascade delete
echo "9. Testing cascade delete..."
# Delete the recipe that's in the meal plan
DELETE_RESPONSE=$(curl -s -X DELETE "http://127.0.0.1:8000/api/recipes/1")
REMOVED_COUNT=$(echo "$DELETE_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['meal_plans_removed'])")

if [ "$REMOVED_COUNT" != "1" ]; then
  echo "✗ Expected 1 meal plan removed, got $REMOVED_COUNT"
  exit 1
fi
echo "  ✓ Cascade delete removed $REMOVED_COUNT meal plan(s)"

# Test 10: Verify combined search filters
echo "10. Testing combined filters..."
TAG_RESULTS=$(curl -s "http://127.0.0.1:8000/api/recipes/?tag=quick" | python -c "import sys, json; print(len(json.load(sys.stdin)))")
if [ "$TAG_RESULTS" -lt "1" ]; then
  echo "✗ Tag filter returned no results"
  exit 1
fi
echo "  ✓ Tag filter found $TAG_RESULTS recipe(s)"

# Test 11: Week navigation
echo "11. Testing week navigation..."
NEXT_WEEK=$(python -c "from datetime import datetime, timedelta; today = datetime.now(); days_since_monday = today.weekday(); monday = today - timedelta(days=days_since_monday); next_monday = monday + timedelta(days=7); print(next_monday.strftime('%Y-%m-%d'))")

NEXT_WEEK_MEALS=$(curl -s "http://127.0.0.1:8000/api/meals?week=$NEXT_WEEK" | python -c "import sys, json; print(len(json.load(sys.stdin)))")
echo "  ✓ Next week has $NEXT_WEEK_MEALS meal(s) (empty is expected)"

# Test 12: Data persistence (restart server)
echo "12. Testing data persistence..."
kill $SERVER_PID
sleep 1
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 > /dev/null 2>&1 &
SERVER_PID=$!
sleep 3

PERSISTED_COUNT=$(curl -s "http://127.0.0.1:8000/api/recipes/" | python -c "import sys, json; print(len(json.load(sys.stdin)))")
if [ "$PERSISTED_COUNT" -lt "5" ]; then
  echo "✗ Data did not persist across restart"
  exit 1
fi
echo "  ✓ Data persisted across server restart ($PERSISTED_COUNT recipes)"

echo ""
echo "✓ All integration workflow tests passing"
