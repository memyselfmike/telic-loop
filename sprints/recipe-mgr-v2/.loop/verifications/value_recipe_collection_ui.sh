#!/usr/bin/env bash
# Verification: Recipe Collection UI - Browse, Search, Filter
# PRD Reference: Section 4.1 (Recipe Collection View)
# Vision Goal: User opens localhost:8000 and sees 5 seed recipes displayed as cards with title, category badge, prep+cook time, and tag chips in a dark-themed grid layout. User filters recipes by category dropdown, searches by title or ingredient name, and filters by tag.
# Category: value

set -euo pipefail

echo "=== Recipe Collection UI - Browse, Search, Filter ==="

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
cat > "$DATA_DIR/test_ui.mjs" << 'EOTEST'
import { chromium } from '@playwright/test';

const TEST_PORT = process.env.TEST_PORT || '8000';
const BASE_URL = `http://localhost:${TEST_PORT}`;

(async () => {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ viewport: { width: 1024, height: 768 } });
    const page = await context.newPage();

    try {
        console.log('\nTest 1: User opens localhost and sees 5 seed recipes displayed as cards');
        await page.goto(BASE_URL, { waitUntil: 'networkidle' });

        // Wait for recipes to load
        await page.waitForSelector('.recipe-card', { timeout: 5000 });

        // Count recipe cards
        const recipeCards = await page.locator('.recipe-card').count();
        if (recipeCards !== 5) {
            throw new Error(`Expected 5 recipe cards, found ${recipeCards}`);
        }
        console.log('PASS: Found 5 recipe cards');

        // Verify card structure (title, category, time, tags)
        const firstCard = page.locator('.recipe-card').first();
        const hasTitle = await firstCard.locator('.recipe-title, .card-title').count() > 0;
        const hasCategory = await firstCard.locator('.recipe-category, .category-badge').count() > 0;
        const hasTime = await firstCard.locator('.recipe-time, .prep-time, .cook-time').count() > 0;

        if (!hasTitle || !hasCategory || !hasTime) {
            throw new Error('Recipe card missing required elements (title, category, or time)');
        }
        console.log('PASS: Recipe cards contain title, category badge, and time info');

        console.log('\nTest 2: User searches by title');
        await page.fill('#recipe-search', 'Oatmeal');
        await page.waitForTimeout(500); // Wait for debounce

        const searchResults = await page.locator('.recipe-card').count();
        if (searchResults === 0) {
            throw new Error('Search for "Oatmeal" returned no results');
        }

        // Verify the result contains Oatmeal in title
        const resultText = await page.locator('.recipe-card .recipe-title, .recipe-card .card-title').first().textContent();
        if (!resultText.includes('Oatmeal')) {
            throw new Error(`Expected "Oatmeal" in search result, got: ${resultText}`);
        }
        console.log('PASS: Search by title filters correctly');

        // Clear search
        await page.fill('#recipe-search', '');
        await page.waitForTimeout(500);

        console.log('\nTest 3: User filters by category');
        await page.selectOption('#recipe-category', 'breakfast');
        await page.waitForTimeout(500);

        const categoryResults = await page.locator('.recipe-card').count();
        if (categoryResults === 0) {
            throw new Error('Category filter for "breakfast" returned no results');
        }
        console.log(`PASS: Category filter shows ${categoryResults} breakfast recipe(s)`);

        // Reset category
        await page.selectOption('#recipe-category', '');
        await page.waitForTimeout(500);

        console.log('\nTest 4: User filters by tag');
        await page.fill('#recipe-tag', 'quick');
        await page.waitForTimeout(500);

        const tagResults = await page.locator('.recipe-card').count();
        if (tagResults === 0) {
            throw new Error('Tag filter for "quick" returned no results');
        }
        console.log(`PASS: Tag filter shows ${tagResults} recipe(s) tagged "quick"`);

        console.log('\nTest 5: Verify dark theme is applied');
        const bodyBg = await page.evaluate(() => {
            return window.getComputedStyle(document.body).backgroundColor;
        });

        // Dark theme should have dark background (rgb values < 128)
        const rgbMatch = bodyBg.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
        if (rgbMatch) {
            const [_, r, g, b] = rgbMatch.map(Number);
            if (r > 128 || g > 128 || b > 128) {
                throw new Error(`Background too light for dark theme: ${bodyBg}`);
            }
            console.log('PASS: Dark theme applied (dark background detected)');
        } else {
            console.log('WARN: Could not verify dark theme background color');
        }

        console.log('\n=== All UI Tests Passed ===');
        await browser.close();
        process.exit(0);

    } catch (error) {
        console.error('\nFAIL:', error.message);
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

node test_ui.mjs
cd -

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "PASS: All recipe collection UI verifications passed"
else
    echo ""
    echo "FAIL: Some UI verifications failed"
fi

exit $exit_code
