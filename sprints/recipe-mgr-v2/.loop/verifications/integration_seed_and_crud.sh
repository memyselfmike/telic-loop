#!/usr/bin/env bash
# Verification: Database Initialization and Recipe CRUD Integration
# PRD Reference: Section 2.3 (Seed Data), Section 3.1 (Recipe Endpoints)
# Vision Goal: "Trust the Data" - SQLite persistence with proper relationships
# Category: integration

set -euo pipefail

echo "=== Database Initialization and Recipe CRUD Integration ==="

cd "$(dirname "$0")/../.."

# Isolated test environment
TEST_PORT="${PORT:-8000}"
DATA_DIR="${TEST_DATA_DIR:-$PWD/.test_data_$$}"
mkdir -p "$DATA_DIR/data"

# Export environment for FastAPI
export PORT="$TEST_PORT"
export PYTHONPATH="$PWD/backend:${PYTHONPATH:-}"
export TEST_DB_PATH="$DATA_DIR/data/recipes.db"

echo "Starting server on port $TEST_PORT with isolated database..."

# Start server in background
cd backend
python -c "
import sys
import os
from pathlib import Path

# Monkey-patch DB_PATH to use test directory
import database
database.DB_PATH = Path(os.environ['TEST_DB_PATH'])

# Start server
import uvicorn
from main import app

uvicorn.run(app, host='0.0.0.0', port=$TEST_PORT, log_level='error')
" &

SERVER_PID=$!
cd ..

# Cleanup on exit
trap 'kill $SERVER_PID 2>/dev/null; rm -rf "$DATA_DIR"' EXIT

# Wait for server to be ready
echo "Waiting for server to start..."
for i in $(seq 1 30); do
    if curl -s "http://localhost:$TEST_PORT/" > /dev/null 2>&1; then
        echo "Server ready"
        break
    fi
    sleep 1
done

# Verify server is responding
if ! curl -s "http://localhost:$TEST_PORT/" > /dev/null 2>&1; then
    echo "FAIL: Server did not start on port $TEST_PORT"
    exit 1
fi

echo ""
echo "Test 1: Verify seed data exists (5 recipes with ingredients)"
response=$(curl -s "http://localhost:$TEST_PORT/api/recipes")
recipe_count=$(echo "$response" | python -c "import sys, json; data=json.load(sys.stdin); print(len(data))")

if [ "$recipe_count" != "5" ]; then
    echo "FAIL: Expected 5 seed recipes, got $recipe_count"
    echo "Response: $response"
    exit 1
fi
echo "PASS: Found 5 seed recipes"

# Verify specific seed recipe titles
echo "$response" | python -c "
import sys, json
recipes = json.load(sys.stdin)
titles = {r['title'] for r in recipes}
expected = {'Classic Oatmeal', 'Grilled Chicken Salad', 'Beef Stir Fry', 'Trail Mix', 'Chocolate Mug Cake'}
if titles == expected:
    print('PASS: All seed recipe titles present')
    sys.exit(0)
else:
    print(f'FAIL: Missing seed recipes. Expected {expected}, got {titles}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

echo ""
echo "Test 2: Create new recipe via POST"
create_response=$(curl -s -w "\n%{http_code}" -X POST "http://localhost:$TEST_PORT/api/recipes" \
    -H "Content-Type: application/json" \
    -d '{
        "title": "Integration Test Recipe",
        "description": "Created by integration test",
        "category": "lunch",
        "prep_time_minutes": 10,
        "cook_time_minutes": 15,
        "servings": 2,
        "instructions": "Test instructions",
        "tags": "test,integration",
        "ingredients": [
            {"quantity": 1.0, "unit": "cup", "item": "test ingredient", "grocery_section": "pantry"}
        ]
    }')

http_code=$(echo "$create_response" | tail -n1)
response_body=$(echo "$create_response" | head -n-1)

if [ "$http_code" != "201" ]; then
    echo "FAIL: Expected 201 Created, got $http_code"
    echo "Response: $response_body"
    exit 1
fi
echo "PASS: Recipe created with status 201"

# Extract recipe ID
recipe_id=$(echo "$response_body" | python -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Created recipe ID: $recipe_id"

echo ""
echo "Test 3: Retrieve created recipe by ID"
get_response=$(curl -s -w "\n%{http_code}" "http://localhost:$TEST_PORT/api/recipes/$recipe_id")
http_code=$(echo "$get_response" | tail -n1)
response_body=$(echo "$get_response" | head -n-1)

if [ "$http_code" != "200" ]; then
    echo "FAIL: Expected 200 OK, got $http_code"
    exit 1
fi

echo "$response_body" | python -c "
import sys, json
recipe = json.load(sys.stdin)
assert recipe['title'] == 'Integration Test Recipe', 'Title mismatch'
assert recipe['category'] == 'lunch', 'Category mismatch'
assert len(recipe['ingredients']) == 1, 'Ingredient count mismatch'
assert recipe['ingredients'][0]['item'] == 'test ingredient', 'Ingredient item mismatch'
print('PASS: Recipe retrieved with correct data and ingredients')
"

if [ $? -ne 0 ]; then
    exit 1
fi

echo ""
echo "Test 4: Update recipe via PUT"
update_response=$(curl -s -w "\n%{http_code}" -X PUT "http://localhost:$TEST_PORT/api/recipes/$recipe_id" \
    -H "Content-Type: application/json" \
    -d '{
        "title": "Updated Test Recipe",
        "description": "Updated description",
        "category": "dinner",
        "prep_time_minutes": 20,
        "cook_time_minutes": 30,
        "servings": 4,
        "instructions": "Updated instructions",
        "tags": "updated,test",
        "ingredients": [
            {"quantity": 2.0, "unit": "cup", "item": "new ingredient", "grocery_section": "produce"}
        ]
    }')

http_code=$(echo "$update_response" | tail -n1)
response_body=$(echo "$update_response" | head -n-1)

if [ "$http_code" != "200" ]; then
    echo "FAIL: Expected 200 OK for update, got $http_code"
    echo "Response: $response_body"
    exit 1
fi

echo "$response_body" | python -c "
import sys, json
recipe = json.load(sys.stdin)
assert recipe['title'] == 'Updated Test Recipe', 'Title not updated'
assert recipe['category'] == 'dinner', 'Category not updated'
assert recipe['prep_time_minutes'] == 20, 'Prep time not updated'
assert len(recipe['ingredients']) == 1, 'Ingredients not replaced'
assert recipe['ingredients'][0]['item'] == 'new ingredient', 'Ingredient not updated'
print('PASS: Recipe updated successfully')
"

if [ $? -ne 0 ]; then
    exit 1
fi

echo ""
echo "Test 5: Delete recipe via DELETE"
delete_response=$(curl -s -w "\n%{http_code}" -X DELETE "http://localhost:$TEST_PORT/api/recipes/$recipe_id")
http_code=$(echo "$delete_response" | tail -n1)

if [ "$http_code" != "204" ]; then
    echo "FAIL: Expected 204 No Content for delete, got $http_code"
    exit 1
fi
echo "PASS: Recipe deleted with status 204"

# Verify recipe is gone
verify_response=$(curl -s -w "\n%{http_code}" "http://localhost:$TEST_PORT/api/recipes/$recipe_id")
http_code=$(echo "$verify_response" | tail -n1)

if [ "$http_code" != "404" ]; then
    echo "FAIL: Expected 404 after deletion, got $http_code"
    exit 1
fi
echo "PASS: Recipe no longer accessible (404)"

echo ""
echo "=== All Integration Tests Passed ==="
exit 0
