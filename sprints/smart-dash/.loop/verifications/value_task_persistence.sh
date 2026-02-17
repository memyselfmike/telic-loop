#!/usr/bin/env bash
# Verification: Tasks persist across page reload using localStorage
# PRD Reference: Value Proof #2 - Task persistence
# Vision Goal: Never lose task list when browser closes
# Category: value
set -euo pipefail

echo "=== Value: Task Persistence Across Reloads ==="

# This verification proves USER VALUE:
# The developer can add tasks, close the browser, and find them again
# This prevents the frustration of losing work lists

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cat > /tmp/test_task_persistence.js << 'EOJS'
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    await page.goto('file://' + process.env.INDEX_PATH);

    // Clear any existing tasks in localStorage
    await page.evaluate(() => localStorage.clear());
    await page.reload();

    // Add a unique test task
    const testTaskText = `Test task ${Date.now()}`;
    await page.fill('#task-input', testTaskText);
    await page.press('#task-input', 'Enter');

    console.log(`Added task: ${testTaskText}`);

    // Wait a moment for the task to be added
    await page.waitForTimeout(500);

    // Check if task appears in the list
    const taskItems = await page.$$('.task-item');
    if (taskItems.length === 0) {
      console.error('FAIL: Task was not added to the list');
      process.exit(1);
    }

    // Verify the task text is in the DOM
    const taskText = await page.textContent('.task-item span');
    if (!taskText.includes(testTaskText)) {
      console.error(`FAIL: Task text not found. Expected "${testTaskText}", got "${taskText}"`);
      process.exit(1);
    }

    console.log('✓ Task added successfully');

    // Check localStorage contains the task
    const localStorageData = await page.evaluate(() => {
      return localStorage.getItem('tasks') || localStorage.getItem('todoTasks') || null;
    });

    if (!localStorageData) {
      console.error('FAIL: No task data found in localStorage');
      process.exit(1);
    }

    console.log('✓ Task saved to localStorage');

    // Reload the page (simulating browser close/reopen)
    await page.reload();
    await page.waitForTimeout(500);

    // Check if the task is still there
    const taskItemsAfterReload = await page.$$('.task-item');
    if (taskItemsAfterReload.length === 0) {
      console.error('FAIL: Tasks not restored after page reload');
      process.exit(1);
    }

    const taskTextAfterReload = await page.textContent('.task-item span');
    if (!taskTextAfterReload.includes(testTaskText)) {
      console.error(`FAIL: Task not restored correctly. Expected "${testTaskText}", got "${taskTextAfterReload}"`);
      process.exit(1);
    }

    console.log('✓ Task persisted across reload');

    // Test complete/delete operations persist
    // Mark task as complete
    await page.click('.task-item input[type="checkbox"]');
    await page.waitForTimeout(300);

    // Check if completed style is applied
    const isCompleted = await page.evaluate(() => {
      const taskItem = document.querySelector('.task-item');
      return taskItem.classList.contains('completed');
    });

    if (!isCompleted) {
      console.error('FAIL: Task completion not applied');
      process.exit(1);
    }

    console.log('✓ Task marked as complete');

    // Reload and verify completion persists
    await page.reload();
    await page.waitForTimeout(500);

    const isStillCompleted = await page.evaluate(() => {
      const taskItem = document.querySelector('.task-item');
      return taskItem && taskItem.classList.contains('completed');
    });

    if (!isStillCompleted) {
      console.error('FAIL: Task completion did not persist across reload');
      process.exit(1);
    }

    console.log('✓ Task completion persisted across reload');

    console.log('\nPASS: Task persistence works correctly');
    console.log('VALUE DELIVERED: Developer never loses their task list when browser closes');
    console.log('  ✓ Tasks saved to localStorage');
    console.log('  ✓ Tasks restored on page reload');
    console.log('  ✓ Task completion state persists');

    // Cleanup
    await page.evaluate(() => localStorage.clear());

    await browser.close();
    process.exit(0);

  } catch (error) {
    console.error('FAIL: Error during task persistence verification:', error.message);
    await browser.close();
    process.exit(1);
  }
})();
EOJS

if ! command -v node &> /dev/null; then
    echo "SKIP: Node.js not found"
    exit 0
fi

export INDEX_PATH="$PROJECT_ROOT/index.html"
node /tmp/test_task_persistence.js
