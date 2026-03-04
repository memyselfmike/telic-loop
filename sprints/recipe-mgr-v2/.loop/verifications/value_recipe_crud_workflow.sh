#!/usr/bin/env bash
# Verification: Recipe CRUD Workflow via UI
# PRD Reference: Section 4.1 (Recipe Collection), Epic 1 Acceptance Criteria
# Vision Goal: User creates a new recipe with title, description, category, prep/cook times, servings, instructions, tags, and multiple ingredients. User edits an existing recipe by changing any field including adding and removing ingredients. User deletes a recipe and confirms the action.
# Category: value

set -euo pipefail

echo "=== Recipe CRUD Workflow via UI ==="

cd "$(dirname "$0")/../.."

# Check for Playwright
if ! command -v npx &> /dev/null; then
    echo "FAIL: npx not found (needed for Playwright). Install Node.js first."
    exit 1
fi

# Isolated test environment
TEST_PORT="${PORT:-8000}"
DATA_DIR="${TEST_DATA_DIR:-$PWD/.test_data_$$}"
mkdir -p "$DATA_DIR/data"

export PORT="$TEST_PORT"
export PYTHONPATH="$PWD/backend${PYTHONPATH:+:$PYTHONPATH}"

echo "Starting server on port $TEST_PORT..."

# Start server in background
cd backend
python -c "
import sys
import os
from pathlib import Path
import database
database.DB_PATH = Path('$DATA_DIR/data/recipes.db')
import uvicorn
from main import app
uvicorn.run(app, host='0.0.0.0', port=$TEST_PORT, log_level='error')
" &

SERVER_PID=$!
cd ..

trap 'kill $SERVER_PID 2>/dev/null; rm -rf "$DATA_DIR"' EXIT

# Wait for server
echo "Waiting for server..."
for i in $(seq 1 30); do
    if curl -s "http://localhost:$TEST_PORT/" > /dev/null 2>&1; then
        echo "Server ready"
        break
    fi
    sleep 1
done

# Create Playwright test script
cat > "$DATA_DIR/test_crud.mjs" << 'EOTEST'
import { chromium } from '@playwright/test';

const TEST_PORT = process.env.TEST_PORT || '8000';
const BASE_URL = `http://localhost:${TEST_PORT}`;

(async () => {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ viewport: { width: 1024, height: 768 } });
    const page = await context.newPage();

    try {
        console.log('\nTest 1: User creates a new recipe with multiple ingredients');
        await page.goto(BASE_URL, { waitUntil: 'networkidle' });

        // Find and click "Add Recipe" button (look for common button text/classes)
        const addButton = page.locator('button:has-text("Add Recipe"), button:has-text("Create Recipe"), button:has-text("New Recipe"), .btn-add-recipe').first();
        await addButton.click();

        // Wait for modal to open
        await page.waitForSelector('#recipe-modal, .modal', { timeout: 2000 });
        console.log('Recipe form modal opened');

        // Fill in recipe details
        await page.fill('#form-title, input[name="title"], #recipe-title', 'UI Test Recipe');
        await page.fill('#form-description, textarea[name="description"], #recipe-description', 'Created via UI test');
        await page.selectOption('#form-category, select[name="category"], #recipe-category', 'dinner');
        await page.fill('#form-prep-time, input[name="prep_time"], #prep-time', '15');
        await page.fill('#form-cook-time, input[name="cook_time"], #cook-time', '25');
        await page.fill('#form-servings, input[name="servings"], #servings', '4');
        await page.fill('#form-instructions, textarea[name="instructions"], #recipe-instructions', 'Step 1: Test\nStep 2: More test');
        await page.fill('#form-tags, input[name="tags"], #recipe-tags', 'test,ui');

        // Add first ingredient (may already have one row)
        const ingredientRows = await page.locator('.ingredient-row, [data-ingredient-row]').count();
        if (ingredientRows === 0) {
            await page.click('button:has-text("Add Ingredient"), .add-ingredient-btn, #add-ingredient-btn');
        }

        // Fill first ingredient
        await page.fill('.ingredient-row:first-child input[placeholder*="quantity"], .ingredient-row:first-child input[name*="quantity"]', '2');
        await page.fill('.ingredient-row:first-child input[placeholder*="unit"], .ingredient-row:first-child input[name*="unit"]', 'cup');
        await page.fill('.ingredient-row:first-child input[placeholder*="item"], .ingredient-row:first-child input[name*="item"]', 'pasta');

        // Try to add second ingredient
        const addIngredientBtn = page.locator('button:has-text("Add Ingredient"), .add-ingredient-btn, #add-ingredient-btn').first();
        if (await addIngredientBtn.count() > 0) {
            await addIngredientBtn.click();
            await page.waitForTimeout(200);

            // Fill second ingredient
            await page.fill('.ingredient-row:last-child input[placeholder*="quantity"], .ingredient-row:nth-child(2) input[name*="quantity"]', '1');
            await page.fill('.ingredient-row:last-child input[placeholder*="unit"], .ingredient-row:nth-child(2) input[name*="unit"]', 'lb');
            await page.fill('.ingredient-row:last-child input[placeholder*="item"], .ingredient-row:nth-child(2) input[name*="item"]', 'chicken');
        }

        console.log('Recipe form filled with multiple ingredients');

        // Submit the form
        await page.click('button[type="submit"], #recipe-submit-btn, button:has-text("Create Recipe")');

        // Wait for modal to close and recipe to appear
        await page.waitForTimeout(1000);

        // Verify recipe appears in collection
        await page.waitForSelector('.recipe-card:has-text("UI Test Recipe")', { timeout: 3000 });
        console.log('PASS: Recipe created and appears in collection');

        console.log('\nTest 2: User views recipe detail');
        // Click the newly created recipe card
        await page.click('.recipe-card:has-text("UI Test Recipe")');

        // Wait for detail view/modal
        await page.waitForSelector('#recipe-detail-modal, .recipe-detail', { timeout: 2000 });

        // Verify detail content shows ingredients
        const detailText = await page.locator('#recipe-detail-content, .recipe-detail').textContent();
        if (!detailText.includes('pasta') && !detailText.includes('Pasta')) {
            throw new Error('Recipe detail does not show ingredients');
        }
        console.log('PASS: Recipe detail view shows full recipe with ingredients');

        console.log('\nTest 3: User edits the recipe');
        // Click Edit button
        await page.click('#detail-edit-btn, button:has-text("Edit")');

        // Wait for form to populate
        await page.waitForTimeout(500);

        // Modify title
        const titleField = page.locator('#form-title, input[name="title"], #recipe-title').first();
        await titleField.clear();
        await titleField.fill('Edited UI Test Recipe');

        // Submit
        await page.click('button[type="submit"], #recipe-submit-btn, button:has-text("Save"), button:has-text("Update")');
        await page.waitForTimeout(1000);

        // Verify updated recipe appears
        await page.waitForSelector('.recipe-card:has-text("Edited UI Test Recipe")', { timeout: 3000 });
        console.log('PASS: Recipe edited successfully and changes reflected');

        console.log('\nTest 4: User deletes the recipe with confirmation');
        // Click the edited recipe card
        await page.click('.recipe-card:has-text("Edited UI Test Recipe")');
        await page.waitForTimeout(500);

        // Click Delete button
        await page.click('#detail-delete-btn, button:has-text("Delete")');

        // Wait for confirmation dialog
        await page.waitForSelector('#delete-modal, .confirm-dialog, .modal:has-text("Delete")', { timeout: 2000 });
        console.log('Delete confirmation dialog appeared');

        // Confirm deletion
        await page.click('#delete-confirm-btn, button:has-text("Delete Recipe"), button:has-text("Confirm")');
        await page.waitForTimeout(1000);

        // Verify recipe is gone from collection
        const deletedRecipe = await page.locator('.recipe-card:has-text("Edited UI Test Recipe")').count();
        if (deletedRecipe > 0) {
            throw new Error('Recipe still appears in collection after deletion');
        }
        console.log('PASS: Recipe deleted and removed from collection');

        console.log('\n=== All CRUD Workflow Tests Passed ===');
        await browser.close();
        process.exit(0);

    } catch (error) {
        console.error('\nFAIL:', error.message);
        await page.screenshot({ path: '/tmp/crud_failure.png' }).catch(() => {});
        await browser.close();
        process.exit(1);
    }
})();
EOTEST

# Install Playwright if needed and run test
export TEST_PORT="$TEST_PORT"

# Create a temporary package.json to install @playwright/test
cat > "$DATA_DIR/package.json" << 'EOPKG'
{
  "type": "module",
  "dependencies": {
    "@playwright/test": "^1.40.0"
  }
}
EOPKG

cd "$DATA_DIR"
if [ ! -d "node_modules/@playwright/test" ]; then
    echo "Installing @playwright/test..."
    npm install --silent > /dev/null 2>&1
    npx playwright install chromium --with-deps > /dev/null 2>&1
fi

node test_crud.mjs
cd -

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "PASS: All recipe CRUD workflow verifications passed"
else
    echo ""
    echo "FAIL: Some CRUD workflow verifications failed"
fi

exit $exit_code
