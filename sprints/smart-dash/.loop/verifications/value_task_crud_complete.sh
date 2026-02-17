#!/usr/bin/env bash
# Verification: Complete task CRUD workflow with count accuracy
# PRD Reference: Value Proof #6 - Task count accuracy
# Vision Goal: Simple task list that prevents forgetting what to do next
# Category: value
set -euo pipefail

echo "=== Value: Complete Task Management Workflow ==="

# This verification proves USER VALUE:
# The developer can manage their task list completely
# Add multiple tasks, mark some complete, delete others, see accurate count

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cat > /tmp/test_task_crud.js << 'EOJS'
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    await page.goto('file://' + process.env.INDEX_PATH);

    // Clear localStorage
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.waitForTimeout(500);

    console.log('Starting with clean slate...\n');

    // Initial state: 0 tasks
    let taskCount = await page.textContent('#task-count');
    if (!taskCount.includes('0 tasks') && !taskCount.includes('0 done')) {
      console.error(`FAIL: Initial count should be "0 tasks, 0 done", got: ${taskCount}`);
      process.exit(1);
    }
    console.log(`✓ Initial state: ${taskCount}`);

    // Add first task
    await page.fill('#task-input', 'Implement authentication');
    await page.press('#task-input', 'Enter');
    await page.waitForTimeout(300);

    taskCount = await page.textContent('#task-count');
    if (!taskCount.includes('1 task')) {
      console.error(`FAIL: After adding 1 task, count should show "1 task", got: ${taskCount}`);
      process.exit(1);
    }
    console.log(`✓ After add: ${taskCount}`);

    // Add second task
    await page.fill('#task-input', 'Write unit tests');
    await page.press('#task-input', 'Enter');
    await page.waitForTimeout(300);

    taskCount = await page.textContent('#task-count');
    if (!taskCount.includes('2 tasks')) {
      console.error(`FAIL: After adding 2 tasks, count should show "2 tasks", got: ${taskCount}`);
      process.exit(1);
    }
    console.log(`✓ After 2nd add: ${taskCount}`);

    // Add third task
    await page.fill('#task-input', 'Update documentation');
    await page.press('#task-input', 'Enter');
    await page.waitForTimeout(300);

    taskCount = await page.textContent('#task-count');
    if (!taskCount.includes('3 tasks')) {
      console.error(`FAIL: After adding 3 tasks, count should show "3 tasks", got: ${taskCount}`);
      process.exit(1);
    }
    console.log(`✓ After 3rd add: ${taskCount}`);

    // Mark first task as complete
    const checkboxes = await page.$$('.task-item input[type="checkbox"]');
    if (checkboxes.length < 1) {
      console.error('FAIL: No checkboxes found');
      process.exit(1);
    }

    await checkboxes[0].click();
    await page.waitForTimeout(300);

    taskCount = await page.textContent('#task-count');
    if (!taskCount.includes('3 tasks') || !taskCount.includes('1 done')) {
      console.error(`FAIL: After completing 1 task, count should show "3 tasks, 1 done", got: ${taskCount}`);
      process.exit(1);
    }
    console.log(`✓ After completing 1: ${taskCount}`);

    // Verify strikethrough is applied
    const completedTasks = await page.$$('.task-item.completed');
    if (completedTasks.length !== 1) {
      console.error('FAIL: Expected 1 completed task with strikethrough style');
      process.exit(1);
    }
    console.log('✓ Strikethrough style applied to completed task');

    // Mark second task as complete
    const checkboxes2 = await page.$$('.task-item input[type="checkbox"]');
    await checkboxes2[1].click();
    await page.waitForTimeout(300);

    taskCount = await page.textContent('#task-count');
    if (!taskCount.includes('3 tasks') || !taskCount.includes('2 done')) {
      console.error(`FAIL: After completing 2 tasks, count should show "3 tasks, 2 done", got: ${taskCount}`);
      process.exit(1);
    }
    console.log(`✓ After completing 2: ${taskCount}`);

    // Delete a task
    const deleteButtons = await page.$$('.task-item button');
    if (deleteButtons.length < 1) {
      console.error('FAIL: No delete buttons found');
      process.exit(1);
    }

    await deleteButtons[0].click();
    await page.waitForTimeout(300);

    taskCount = await page.textContent('#task-count');
    // After deleting one task, should have 2 tasks (and if we deleted a completed one, 1 done)
    if (!taskCount.includes('2 tasks')) {
      console.error(`FAIL: After deleting 1 task, count should show "2 tasks", got: ${taskCount}`);
      process.exit(1);
    }
    console.log(`✓ After delete: ${taskCount}`);

    // Verify task list has correct number of items
    const remainingTasks = await page.$$('.task-item');
    if (remainingTasks.length !== 2) {
      console.error(`FAIL: Expected 2 tasks in list, found ${remainingTasks.length}`);
      process.exit(1);
    }
    console.log('✓ Task list reflects correct count');

    console.log('\n' + '='.repeat(60));
    console.log('PASS: Complete task management workflow');
    console.log('='.repeat(60));
    console.log('\nVALUE DELIVERED: Developer has a fully functional task manager');
    console.log('  ✓ Add tasks via Enter key');
    console.log('  ✓ Mark complete with checkbox (strikethrough applied)');
    console.log('  ✓ Delete tasks with × button');
    console.log('  ✓ Task count is always accurate');
    console.log('  ✓ No server or account needed');
    console.log('\nUSER BENEFIT: Never forget what to do next during focus session');

    // Cleanup
    await page.evaluate(() => localStorage.clear());

    await browser.close();
    process.exit(0);

  } catch (error) {
    console.error('FAIL: Error during task CRUD verification:', error.message);
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
node /tmp/test_task_crud.js
