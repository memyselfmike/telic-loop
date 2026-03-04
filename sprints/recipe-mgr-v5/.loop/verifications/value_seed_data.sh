#!/bin/bash
# Value verification: Ensure seed data loads on fresh database
# Tests Value Proof #1: "User opens localhost:8000 and sees 5 seed recipes immediately"

set -e
cd "$(dirname "$0")/../.."

echo "Testing seed data loading..."

# Remove database to test fresh initialization
rm -f data/recipes.db

# Start server to initialize database (will keep running for API tests below)
echo "Initializing fresh database..."
python -m uvicorn backend.main:app --port 8004 > /tmp/server_seed.log 2>&1 &
SERVER_PID=$!
trap "kill $SERVER_PID 2>/dev/null || true" EXIT

# Give server time to fully start and initialize database
sleep 5

# Verify database was created and seeded
if [ ! -f "data/recipes.db" ]; then
    echo "✗ Database file not created"
    cat /tmp/server_seed.log
    exit 1
fi

# Check seed recipes via API (server already running from above)
RECIPES=$(curl -s http://localhost:8004/api/recipes/)
RECIPE_COUNT=$(echo "$RECIPES" | python -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")

if [ "$RECIPE_COUNT" -ne 5 ]; then
    echo "✗ Expected 5 seed recipes, found $RECIPE_COUNT"
    exit 1
fi

# Verify all categories are covered
CATEGORIES=$(echo "$RECIPES" | python -c "
import sys, json
recipes = json.load(sys.stdin)
cats = set(r['category'] for r in recipes)
print(','.join(sorted(cats)))
")

EXPECTED="breakfast,dessert,dinner,lunch,snack"
if [ "$CATEGORIES" != "$EXPECTED" ]; then
    echo "✗ Missing categories. Expected: $EXPECTED, Got: $CATEGORIES"
    exit 1
fi

echo "✓ Fresh database initialized with 5 seed recipes covering all categories"
exit 0
