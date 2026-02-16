"""Playwright tests for todo app - verifying all PRD acceptance criteria."""
import pytest
from playwright.sync_api import Page, expect


def test_ac1_initial_page_load(page: Page):
    """AC1: Opening index.html shows an input field and empty task list area."""
    # Verify input field is present
    input_field = page.locator("#taskInput")
    expect(input_field).to_be_visible()
    expect(input_field).to_have_attribute("placeholder", "What needs to be done?")

    # Verify task list container exists
    task_list = page.locator("#taskList")
    expect(task_list).to_be_visible()

    # Verify it's empty (shows empty state message)
    empty_state = page.locator(".empty-state")
    expect(empty_state).to_be_visible()
    expect(empty_state).to_contain_text("No tasks yet")


def test_ac2_add_task_via_enter_key(page: Page):
    """AC2: Typing 'Buy groceries' + Enter adds 'Buy groceries' to the visible list."""
    input_field = page.locator("#taskInput")

    # Type task and press Enter
    input_field.fill("Buy groceries")
    input_field.press("Enter")

    # Verify task appears in the list
    task_text = page.locator(".task-text", has_text="Buy groceries")
    expect(task_text).to_be_visible()

    # Verify input field is cleared
    expect(input_field).to_have_value("")

    # Verify task count updated
    task_count = page.locator("#taskCount")
    expect(task_count).to_contain_text("1 item left")


def test_ac3_checkbox_toggles_strikethrough(page: Page):
    """AC3: Clicking the task's checkbox applies strikethrough styling and marks it completed."""
    # Add a task
    input_field = page.locator("#taskInput")
    input_field.fill("Test task")
    input_field.press("Enter")

    # Get the task item and checkbox
    task_item = page.locator(".task-item").first
    checkbox = task_item.locator(".task-checkbox")
    task_text = task_item.locator(".task-text")

    # Verify initially not completed
    expect(task_item).not_to_have_class("completed")
    expect(checkbox).not_to_be_checked()

    # Click checkbox to complete
    checkbox.click()

    # Verify task is now completed with strikethrough
    expect(task_item).to_have_class("task-item completed")
    expect(checkbox).to_be_checked()
    # Check that text-decoration contains "line-through"
    text_decoration = task_text.evaluate("el => getComputedStyle(el).textDecoration")
    assert "line-through" in text_decoration

    # Click again to uncomplete
    checkbox.click()

    # Verify task is back to active state
    expect(task_item).to_have_class("task-item")
    expect(task_item).not_to_have_class("completed")
    expect(checkbox).not_to_be_checked()


def test_ac4_delete_button_removes_task(page: Page):
    """AC4: Clicking the delete button removes the task from the DOM."""
    # Add a task
    input_field = page.locator("#taskInput")
    input_field.fill("Task to delete")
    input_field.press("Enter")

    # Verify task exists
    task_text = page.locator(".task-text", has_text="Task to delete")
    expect(task_text).to_be_visible()

    # Click delete button
    delete_btn = page.locator(".delete-btn").first
    delete_btn.click()

    # Verify task is removed
    expect(task_text).not_to_be_visible()

    # Verify empty state is shown
    empty_state = page.locator(".empty-state")
    expect(empty_state).to_be_visible()


def test_ac5_filter_buttons_show_correct_subsets(page: Page):
    """AC5: With 3 tasks (2 active, 1 completed): filters show correct subsets."""
    input_field = page.locator("#taskInput")

    # Add 3 tasks
    tasks = ["Task 1", "Task 2", "Task 3"]
    for task_name in tasks:
        input_field.fill(task_name)
        input_field.press("Enter")

    # Complete the second task
    task_items = page.locator(".task-item")
    task_items.nth(1).locator(".task-checkbox").click()

    # Verify "All" filter shows all 3 tasks
    all_filter = page.locator('.filter-btn[data-filter="all"]')
    all_filter.click()
    expect(task_items).to_have_count(3)

    # Verify "Active" filter shows 2 tasks
    active_filter = page.locator('.filter-btn[data-filter="active"]')
    active_filter.click()
    expect(page.locator(".task-item")).to_have_count(2)
    expect(page.locator(".task-text", has_text="Task 1")).to_be_visible()
    expect(page.locator(".task-text", has_text="Task 3")).to_be_visible()
    expect(page.locator(".task-text", has_text="Task 2")).not_to_be_visible()

    # Verify "Completed" filter shows 1 task
    completed_filter = page.locator('.filter-btn[data-filter="completed"]')
    completed_filter.click()
    expect(page.locator(".task-item")).to_have_count(1)
    expect(page.locator(".task-text", has_text="Task 2")).to_be_visible()

    # Verify task count shows "2 items left" (active tasks only)
    task_count = page.locator("#taskCount")
    expect(task_count).to_contain_text("2 items left")


def test_ac6_persistence_after_refresh(page: Page, http_server: str):
    """AC6: After adding 3 tasks and refreshing the page, all 3 tasks are still present."""
    input_field = page.locator("#taskInput")

    # Add 3 tasks
    tasks = ["Persistent task 1", "Persistent task 2", "Persistent task 3"]
    for task_name in tasks:
        input_field.fill(task_name)
        input_field.press("Enter")

    # Complete one task to verify completion state persists too
    page.locator(".task-item").first.locator(".task-checkbox").click()

    # Verify all tasks are visible before refresh
    expect(page.locator(".task-item")).to_have_count(3)

    # Refresh the page
    page.reload()

    # Verify all 3 tasks are still present
    expect(page.locator(".task-item")).to_have_count(3)

    # Verify task texts are preserved
    for task_name in tasks:
        expect(page.locator(".task-text", has_text=task_name)).to_be_visible()

    # Verify completion state is preserved
    first_task = page.locator(".task-item").first
    expect(first_task).to_have_class("task-item completed")
    expect(first_task.locator(".task-checkbox")).to_be_checked()


def test_ac7_mobile_viewport_responsiveness(page: Page):
    """AC7: On a 375px viewport, the UI has no horizontal overflow and tap targets are at least 44px."""
    # Set viewport to 375px width (iPhone SE size)
    page.set_viewport_size({"width": 375, "height": 667})

    # Add some tasks to have interactive elements
    input_field = page.locator("#taskInput")
    input_field.fill("Mobile test task")
    input_field.press("Enter")

    # Check no horizontal overflow on body
    body = page.locator("body")
    body_box = body.bounding_box()

    # Verify body width doesn't exceed viewport
    assert body_box["width"] <= 375, "Body width exceeds viewport width"

    # Check container doesn't cause overflow
    container = page.locator(".container")
    container_box = container.bounding_box()
    assert container_box["x"] >= 0, "Container extends beyond left edge"
    assert container_box["x"] + container_box["width"] <= 375, "Container extends beyond right edge"

    # Verify tap target sizes (minimum 44px as per Apple HIG)
    # Check Add button
    add_button = page.locator("#addButton")
    add_button_box = add_button.bounding_box()
    assert add_button_box["height"] >= 44, f"Add button height {add_button_box['height']}px is less than 44px"

    # Check filter buttons
    filter_buttons = page.locator(".filter-btn")
    for i in range(filter_buttons.count()):
        btn_box = filter_buttons.nth(i).bounding_box()
        assert btn_box["height"] >= 44, f"Filter button {i} height {btn_box['height']}px is less than 44px"

    # Check delete button
    delete_btn = page.locator(".delete-btn")
    delete_btn_box = delete_btn.bounding_box()
    assert delete_btn_box["height"] >= 44, f"Delete button height {delete_btn_box['height']}px is less than 44px"

    # Check task item (entire row should be tappable)
    task_item = page.locator(".task-item").first
    task_item_box = task_item.bounding_box()
    assert task_item_box["height"] >= 44, f"Task item height {task_item_box['height']}px is less than 44px"


def test_empty_input_ignored(page: Page):
    """Supplemental test: Empty input should not create a task."""
    input_field = page.locator("#taskInput")

    # Try to add empty task by pressing Enter with no text
    input_field.click()
    input_field.press("Enter")

    # Verify no task was created
    expect(page.locator(".empty-state")).to_be_visible()
    expect(page.locator(".task-item")).to_have_count(0)

    # Try with whitespace only
    input_field.fill("   ")
    input_field.press("Enter")

    # Verify still no task created
    expect(page.locator(".empty-state")).to_be_visible()
    expect(page.locator(".task-item")).to_have_count(0)


def test_task_count_singular_plural(page: Page):
    """Supplemental test: Task count shows correct singular/plural forms."""
    input_field = page.locator("#taskInput")
    task_count = page.locator("#taskCount")

    # Zero items
    expect(task_count).to_contain_text("0 items left")

    # One item (singular)
    input_field.fill("Single task")
    input_field.press("Enter")
    expect(task_count).to_contain_text("1 item left")

    # Two items (plural)
    input_field.fill("Second task")
    input_field.press("Enter")
    expect(task_count).to_contain_text("2 items left")

    # Complete one - back to singular
    page.locator(".task-checkbox").first.click()
    expect(task_count).to_contain_text("1 item left")
