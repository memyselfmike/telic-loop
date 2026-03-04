#!/bin/bash
# Integration verification: Test full recipe -> meal plan -> shopping list workflow
# Verifies end-to-end data flow through all 3 major API subsystems

set -e
cd "$(dirname "$0")/../.."

# Start server in background
echo "Starting FastAPI server..."
python -m uvicorn backend.main:app --port 8003 > /tmp/server.log 2>&1 &
SERVER_PID=$!
sleep 3

# Trap to ensure server cleanup
trap "kill $SERVER_PID 2>/dev/null || true" EXIT

# Helper for API calls
api_call() {
    local method=$1
    local path=$2
    local data=$3

    if [ -n "$data" ]; then
        curl -s -X "$method" "http://localhost:8003$path" \
            -H "Content-Type: application/json" \
            -d "$data"
    else
        curl -s -X "$method" "http://localhost:8003$path"
    fi
}

echo "Testing full workflow..."

# 1. Verify seed recipes exist
echo "1. Checking seed recipes..."
RECIPES=$(api_call GET "/api/recipes/")
RECIPE_COUNT=$(echo "$RECIPES" | python -c "import sys, json; print(len(json.load(sys.stdin)))")
if [ "$RECIPE_COUNT" -ne 5 ]; then
    echo "✗ Expected 5 seed recipes, found $RECIPE_COUNT"
    exit 1
fi
echo "  ✓ 5 seed recipes loaded"

# 2. Create a new recipe
echo "2. Creating test recipe..."
NEW_RECIPE=$(api_call POST "/api/recipes/" '{
    "title": "Verification Recipe",
    "category": "lunch",
    "ingredients": [
        {"quantity": 2.0, "unit": "cup", "item": "rice", "grocery_section": "pantry"},
        {"quantity": 1.0, "unit": "lb", "item": "chicken", "grocery_section": "meat"}
    ]
}')
RECIPE_ID=$(echo "$NEW_RECIPE" | python -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "  ✓ Recipe created with ID $RECIPE_ID"

# 3. Assign recipes to meal plan
echo "3. Assigning recipes to meal plan..."
api_call PUT "/api/meals/" '{
    "week_start": "2026-03-02",
    "day_of_week": 0,
    "meal_slot": "lunch",
    "recipe_id": 1
}' > /dev/null
api_call PUT "/api/meals/" "{
    \"week_start\": \"2026-03-02\",
    \"day_of_week\": 1,
    \"meal_slot\": \"dinner\",
    \"recipe_id\": $RECIPE_ID
}" > /dev/null
echo "  ✓ 2 meals assigned"

# 4. Generate shopping list
echo "4. Generating shopping list..."
SHOPPING_LIST=$(api_call POST "/api/shopping/generate" '{"week_start": "2026-03-02"}')
ITEM_COUNT=$(echo "$SHOPPING_LIST" | python -c "import sys, json; print(len(json.load(sys.stdin)['items']))")
if [ "$ITEM_COUNT" -lt 1 ]; then
    echo "✗ Shopping list is empty"
    exit 1
fi
echo "  ✓ Shopping list generated with $ITEM_COUNT items"

# 5. Verify unit normalization
echo "5. Testing unit normalization..."
# Create recipe with 4 tsp (should normalize to 1.3 tbsp)
NORM_RECIPE=$(api_call POST "/api/recipes/" '{
    "title": "Unit Norm Test",
    "category": "snack",
    "ingredients": [{"quantity": 4.0, "unit": "tsp", "item": "sugar", "grocery_section": "pantry"}]
}')
NORM_ID=$(echo "$NORM_RECIPE" | python -c "import sys, json; print(json.load(sys.stdin)['id'])")

# Clear old meal plans and assign new recipe
api_call POST "/api/shopping/generate" '{"week_start": "2026-03-09"}' > /dev/null
api_call PUT "/api/meals/" "{
    \"week_start\": \"2026-03-09\",
    \"day_of_week\": 0,
    \"meal_slot\": \"breakfast\",
    \"recipe_id\": $NORM_ID
}" > /dev/null

# Generate new shopping list
NORM_LIST=$(api_call POST "/api/shopping/generate" '{"week_start": "2026-03-09"}')
SUGAR_UNIT=$(echo "$NORM_LIST" | python -c "
import sys, json
items = json.load(sys.stdin)['items']
sugar = next((i for i in items if i['item'] == 'sugar'), None)
print(sugar['unit'] if sugar else 'NOT_FOUND')
")

if [ "$SUGAR_UNIT" != "tbsp" ]; then
    echo "✗ Unit normalization failed: expected tbsp, got $SUGAR_UNIT"
    exit 1
fi
echo "  ✓ Unit normalization working (4 tsp -> tbsp)"

# 6. Test cascade delete
echo "6. Testing cascade delete..."
api_call DELETE "/api/recipes/$RECIPE_ID" > /dev/null
MEALS_AFTER=$(api_call GET "/api/meals/?week=2026-03-02")
MEAL_COUNT=$(echo "$MEALS_AFTER" | python -c "import sys, json; print(len(json.load(sys.stdin)))")
if [ "$MEAL_COUNT" -ne 1 ]; then
    echo "✗ Cascade delete failed"
    exit 1
fi
echo "  ✓ Cascade delete working"

echo ""
echo "✓ All integration workflow tests passing"
exit 0
