"""
Test Task List Widget functionality
Verifies task addition, completion, deletion, persistence, and count accuracy
"""
import pytest
from playwright.sync_api import Page, expect


def test_task_widget_add_task(page: Page):
    """Verify that a user can add a task by typing text and pressing Enter"""
    page.goto("http://localhost:8000/index.html")

    # Wait for the page to load
    expect(page.locator("#task-widget")).to_be_visible()

    # Get the input field
    task_input = page.locator("#task-input")

    # Add a task
    task_input.fill("Write unit tests")
    task_input.press("Enter")

    # Verify the task appears in the list
    task_list = page.locator("#task-list")
    expect(task_list.locator(".task-item")).to_have_count(1)
    expect(task_list.locator(".task-item span")).to_have_text("Write unit tests")

    # Verify the input is cleared
    expect(task_input).to_have_value("")

    # Verify task count
    task_count = page.locator("#task-count")
    expect(task_count).to_have_text("1 task, 0 done")


def test_task_widget_complete_task(page: Page):
    """Verify that checking the checkbox applies strikethrough style"""
    page.goto("http://localhost:8000/index.html")

    # Add a task
    task_input = page.locator("#task-input")
    task_input.fill("Review pull request")
    task_input.press("Enter")

    # Get the task item
    task_item = page.locator(".task-item").first
    checkbox = task_item.locator("input[type='checkbox']")

    # Verify initial state: not completed
    expect(task_item).not_to_have_class("completed")

    # Check the checkbox
    checkbox.check()

    # Verify the task has completed class and strikethrough
    expect(task_item).to_have_class("task-item completed")

    # Verify task count updates
    task_count = page.locator("#task-count")
    expect(task_count).to_have_text("1 task, 1 done")


def test_task_widget_delete_task(page: Page):
    """Verify that clicking the x button removes the task"""
    page.goto("http://localhost:8000/index.html")

    # Add two tasks
    task_input = page.locator("#task-input")
    task_input.fill("Task 1")
    task_input.press("Enter")
    task_input.fill("Task 2")
    task_input.press("Enter")

    # Verify we have 2 tasks
    task_list = page.locator("#task-list")
    expect(task_list.locator(".task-item")).to_have_count(2)

    # Delete the first task
    delete_button = task_list.locator(".task-item").first.locator("button")
    delete_button.click()

    # Verify we have 1 task left
    expect(task_list.locator(".task-item")).to_have_count(1)
    expect(task_list.locator(".task-item span")).to_have_text("Task 2")

    # Verify task count updates
    task_count = page.locator("#task-count")
    expect(task_count).to_have_text("1 task, 0 done")


def test_task_widget_persistence(page: Page):
    """Verify that tasks persist after page refresh and restore completion state"""
    page.goto("http://localhost:8000/index.html")

    # Add three tasks
    task_input = page.locator("#task-input")
    task_input.fill("Persistent task 1")
    task_input.press("Enter")
    task_input.fill("Persistent task 2")
    task_input.press("Enter")
    task_input.fill("Persistent task 3")
    task_input.press("Enter")

    # Complete the second task
    task_list = page.locator("#task-list")
    second_task = task_list.locator(".task-item").nth(1)
    second_task.locator("input[type='checkbox']").check()

    # Verify state before refresh
    expect(task_list.locator(".task-item")).to_have_count(3)
    expect(second_task).to_have_class("task-item completed")

    # Refresh the page
    page.reload()

    # Wait for page to load
    expect(page.locator("#task-widget")).to_be_visible()

    # Verify all tasks are still there
    task_list = page.locator("#task-list")
    expect(task_list.locator(".task-item")).to_have_count(3)

    # Verify task content
    expect(task_list.locator(".task-item").nth(0).locator("span")).to_have_text("Persistent task 1")
    expect(task_list.locator(".task-item").nth(1).locator("span")).to_have_text("Persistent task 2")
    expect(task_list.locator(".task-item").nth(2).locator("span")).to_have_text("Persistent task 3")

    # Verify the second task is still completed
    second_task_after_reload = task_list.locator(".task-item").nth(1)
    expect(second_task_after_reload).to_have_class("task-item completed")
    expect(second_task_after_reload.locator("input[type='checkbox']")).to_be_checked()

    # Verify task count is accurate
    task_count = page.locator("#task-count")
    expect(task_count).to_have_text("3 tasks, 1 done")


def test_task_widget_count_accuracy(page: Page):
    """Verify that task count updates accurately after all operations"""
    page.goto("http://localhost:8000/index.html")

    # Initially should show 0 tasks
    task_count = page.locator("#task-count")
    expect(task_count).to_have_text("0 tasks, 0 done")

    # Add three tasks
    task_input = page.locator("#task-input")
    task_input.fill("Task A")
    task_input.press("Enter")
    task_input.fill("Task B")
    task_input.press("Enter")
    task_input.fill("Task C")
    task_input.press("Enter")

    # Should show 3 tasks, 0 done
    expect(task_count).to_have_text("3 tasks, 0 done")

    # Complete two tasks
    task_list = page.locator("#task-list")
    task_list.locator(".task-item").nth(0).locator("input[type='checkbox']").check()
    expect(task_count).to_have_text("3 tasks, 1 done")

    task_list.locator(".task-item").nth(1).locator("input[type='checkbox']").check()
    expect(task_count).to_have_text("3 tasks, 2 done")

    # Delete one task
    task_list.locator(".task-item").first.locator("button").click()
    expect(task_count).to_have_text("2 tasks, 1 done")

    # Delete all remaining tasks
    task_list.locator(".task-item").first.locator("button").click()
    expect(task_count).to_have_text("1 task, 0 done")

    task_list.locator(".task-item").first.locator("button").click()
    expect(task_count).to_have_text("0 tasks, 0 done")


def test_task_widget_empty_task_ignored(page: Page):
    """Verify that empty tasks are not added"""
    page.goto("http://localhost:8000/index.html")

    task_input = page.locator("#task-input")
    task_list = page.locator("#task-list")

    # Try to add empty task
    task_input.fill("")
    task_input.press("Enter")
    expect(task_list.locator(".task-item")).to_have_count(0)

    # Try to add whitespace-only task
    task_input.fill("   ")
    task_input.press("Enter")
    expect(task_list.locator(".task-item")).to_have_count(0)

    # Verify count stays at 0
    task_count = page.locator("#task-count")
    expect(task_count).to_have_text("0 tasks, 0 done")


def test_task_widget_localStorage_structure(page: Page):
    """Verify that localStorage contains the task data as a JSON array"""
    page.goto("http://localhost:8000/index.html")

    # Add tasks with different states
    task_input = page.locator("#task-input")
    task_input.fill("Buy groceries")
    task_input.press("Enter")
    task_input.fill("Fix bug")
    task_input.press("Enter")

    # Complete first task
    task_list = page.locator("#task-list")
    task_list.locator(".task-item").first.locator("input[type='checkbox']").check()

    # Check localStorage
    local_storage_data = page.evaluate("""
        () => {
            const data = localStorage.getItem('focusDashboardTasks');
            return data ? JSON.parse(data) : null;
        }
    """)

    # Verify structure
    assert local_storage_data is not None
    assert isinstance(local_storage_data, list)
    assert len(local_storage_data) == 2

    # Verify first task (completed)
    assert local_storage_data[0]["text"] == "Buy groceries"
    assert local_storage_data[0]["completed"] is True

    # Verify second task (not completed)
    assert local_storage_data[1]["text"] == "Fix bug"
    assert local_storage_data[1]["completed"] is False
