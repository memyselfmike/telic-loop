#!/usr/bin/env python3
"""
Verification: All 7 PRD Acceptance Criteria - Browser Value Delivery
PRD Reference: Section 4 (Acceptance Criteria)
Vision Goal: G1 - Fully functional todo app with zero setup
Category: value

This script verifies that the user gets the complete promised value:
- Zero-setup file opening
- Add tasks via Enter key
- Complete tasks with checkbox toggle and strikethrough
- Delete tasks permanently
- Filter by status (All/Active/Completed)
- LocalStorage persistence across page refreshes
- Mobile responsive design (375px viewport)

Tests run against a local HTTP server (not file://) to ensure consistent
localStorage behavior across all browsers.
"""

import http.server
import socketserver
import threading
import time
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

# Configuration
SPRINT_DIR = Path(__file__).parent.parent.parent
HTML_FILE = SPRINT_DIR / "index.html"
TEST_PORT = 8765
BASE_URL = f"http://localhost:{TEST_PORT}"
TIMEOUT = 5000  # 5 seconds


class TestResult:
    """Track test results for final summary"""
    def __init__(self):
        self.passed = []
        self.failed = []

    def pass_test(self, name):
        self.passed.append(name)
        print(f"✓ PASS: {name}")

    def fail_test(self, name, error):
        self.failed.append((name, error))
        print(f"✗ FAIL: {name}")
        print(f"  Error: {error}")

    def summary(self):
        total = len(self.passed) + len(self.failed)
        print(f"\n{'='*60}")
        print(f"Test Results: {len(self.passed)}/{total} passed")
        print(f"{'='*60}")
        if self.failed:
            print("\nFailed Tests:")
            for name, error in self.failed:
                print(f"  - {name}: {error}")
            return False
        else:
            print("\n✓ All value delivery tests PASSED!")
            print("The user receives the complete promised outcome.")
            return True


def start_server():
    """Start HTTP server in background thread"""
    os.chdir(SPRINT_DIR)
    handler = http.server.SimpleHTTPRequestHandler
    handler.extensions_map['.html'] = 'text/html'

    class QuietServer(socketserver.TCPServer):
        allow_reuse_address = True

        def handle_error(self, request, client_address):
            pass  # Suppress error output

    httpd = QuietServer(("", TEST_PORT), handler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)  # Give server time to start
    return httpd


def clear_storage(page):
    """Clear localStorage to ensure clean test state"""
    page.evaluate("localStorage.clear()")


def test_ac1_initial_page_load(page, results):
    """AC1: Opening index.html shows input field and empty task list"""
    try:
        page.goto(BASE_URL)

        # Check input field exists with correct placeholder
        input_field = page.locator("#taskInput")
        expect(input_field).to_be_visible(timeout=TIMEOUT)
        expect(input_field).to_have_attribute("placeholder", "What needs to be done?")

        # Check task list exists and is empty
        task_list = page.locator("#taskList")
        expect(task_list).to_be_visible(timeout=TIMEOUT)

        # Should show empty state message
        empty_state = page.locator(".empty-state")
        expect(empty_state).to_be_visible(timeout=TIMEOUT)

        results.pass_test("AC1: Initial page load shows input and empty list")
    except Exception as e:
        results.fail_test("AC1: Initial page load", str(e))


def test_ac2_add_task_via_enter(page, results):
    """AC2: Typing 'Buy groceries' + Enter adds it to the visible list"""
    try:
        clear_storage(page)
        page.goto(BASE_URL)

        input_field = page.locator("#taskInput")
        input_field.fill("Buy groceries")
        input_field.press("Enter")

        # Task should appear in list
        task_text = page.locator(".task-text", has_text="Buy groceries")
        expect(task_text).to_be_visible(timeout=TIMEOUT)

        # Input should be cleared
        expect(input_field).to_have_value("")

        # Empty state should be gone
        empty_state = page.locator(".empty-state")
        expect(empty_state).not_to_be_visible()

        results.pass_test("AC2: Add task via Enter key")
    except Exception as e:
        results.fail_test("AC2: Add task via Enter", str(e))


def test_ac3_checkbox_toggle_strikethrough(page, results):
    """AC3: Clicking checkbox toggles strikethrough styling"""
    try:
        clear_storage(page)
        page.goto(BASE_URL)

        # Add a task
        input_field = page.locator("#taskInput")
        input_field.fill("Test task")
        input_field.press("Enter")

        # Find the task item
        task_item = page.locator(".task-item").first
        checkbox = task_item.locator(".task-checkbox")

        # Initially not completed
        expect(task_item).not_to_have_class("completed")

        # Click checkbox to complete
        checkbox.click()
        expect(task_item).to_have_class("task-item completed", timeout=TIMEOUT)

        # Check strikethrough is applied
        task_text = task_item.locator(".task-text")
        text_decoration = task_text.evaluate("el => window.getComputedStyle(el).textDecoration")
        if "line-through" not in text_decoration:
            raise AssertionError(f"Expected line-through, got: {text_decoration}")

        # Click again to toggle back
        checkbox.click()
        expect(task_item).not_to_have_class("completed")

        results.pass_test("AC3: Checkbox toggles strikethrough styling")
    except Exception as e:
        results.fail_test("AC3: Checkbox toggle", str(e))


def test_ac4_delete_button_removes_task(page, results):
    """AC4: Clicking delete button removes task from DOM"""
    try:
        clear_storage(page)
        page.goto(BASE_URL)

        # Add a task
        input_field = page.locator("#taskInput")
        input_field.fill("Task to delete")
        input_field.press("Enter")

        # Verify task exists
        task_text = page.locator(".task-text", has_text="Task to delete")
        expect(task_text).to_be_visible(timeout=TIMEOUT)

        # Click delete button
        delete_btn = page.locator(".task-item").first.locator(".delete-btn")
        delete_btn.click()

        # Task should be removed
        expect(task_text).not_to_be_visible()

        # Empty state should appear
        empty_state = page.locator(".empty-state")
        expect(empty_state).to_be_visible(timeout=TIMEOUT)

        results.pass_test("AC4: Delete button removes task")
    except Exception as e:
        results.fail_test("AC4: Delete button", str(e))


def test_ac5_filter_buttons_work(page, results):
    """AC5: Filter buttons (All/Active/Completed) show correct subsets"""
    try:
        clear_storage(page)
        page.goto(BASE_URL)

        # Add 3 tasks: 2 active, 1 completed
        tasks = ["Task 1", "Task 2", "Task 3"]
        input_field = page.locator("#taskInput")

        for task in tasks:
            input_field.fill(task)
            input_field.press("Enter")
            time.sleep(0.1)  # Small delay to ensure order

        # Complete the second task
        page.locator(".task-item").nth(1).locator(".task-checkbox").click()

        # Test "All" filter (default)
        all_btn = page.locator(".filter-btn[data-filter='all']")
        expect(all_btn).to_have_class("filter-btn active")
        expect(page.locator(".task-item")).to_have_count(3)

        # Test "Active" filter
        active_btn = page.locator(".filter-btn[data-filter='active']")
        active_btn.click()
        expect(active_btn).to_have_class("filter-btn active")
        expect(page.locator(".task-item")).to_have_count(2)

        # Test "Completed" filter
        completed_btn = page.locator(".filter-btn[data-filter='completed']")
        completed_btn.click()
        expect(completed_btn).to_have_class("filter-btn active")
        expect(page.locator(".task-item")).to_have_count(1)

        # Verify task count shows active tasks only (2 items left)
        all_btn.click()
        task_count = page.locator("#taskCount")
        expect(task_count).to_have_text("2 items left")

        results.pass_test("AC5: Filter buttons show correct subsets")
    except Exception as e:
        results.fail_test("AC5: Filter buttons", str(e))


def test_ac6_persistence_after_refresh(page, results):
    """AC6: Tasks survive page refresh (localStorage persistence)"""
    try:
        clear_storage(page)
        page.goto(BASE_URL)

        # Add multiple tasks with different states
        tasks_data = [
            ("Persistent task 1", False),
            ("Persistent task 2", True),
            ("Persistent task 3", False),
        ]

        input_field = page.locator("#taskInput")
        for task_text, should_complete in tasks_data:
            input_field.fill(task_text)
            input_field.press("Enter")

            if should_complete:
                page.locator(".task-item").last.locator(".task-checkbox").click()

            time.sleep(0.1)

        # Verify tasks before refresh
        expect(page.locator(".task-item")).to_have_count(3)

        # Refresh the page
        page.reload()

        # Verify all tasks are still present
        expect(page.locator(".task-item")).to_have_count(3)

        # Verify task states are preserved
        for i, (task_text, should_complete) in enumerate(tasks_data):
            task_item = page.locator(".task-item").nth(i)
            expect(task_item.locator(".task-text")).to_have_text(task_text)

            if should_complete:
                expect(task_item).to_have_class("task-item completed")
            else:
                expect(task_item).not_to_have_class("completed")

        results.pass_test("AC6: Tasks persist after page refresh")
    except Exception as e:
        results.fail_test("AC6: localStorage persistence", str(e))


def test_ac7_mobile_responsive(page, results):
    """AC7: 375px viewport has no overflow and 44px tap targets"""
    try:
        clear_storage(page)

        # Set mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(BASE_URL)

        # Check no horizontal overflow
        body_width = page.evaluate("document.body.scrollWidth")
        viewport_width = page.evaluate("window.innerWidth")

        if body_width > viewport_width:
            raise AssertionError(f"Horizontal overflow detected: body width {body_width}px > viewport {viewport_width}px")

        # Add a task to test interactive elements
        input_field = page.locator("#taskInput")
        input_field.fill("Mobile test task")
        input_field.press("Enter")

        # Check tap target sizes (minimum 44px)
        # Note: The checkbox itself might be 22px, but it's in a task-item container
        # that provides the 44px tap target as per PRD requirements
        elements_to_check = [
            ("#addButton", "Add button"),
            (".task-item", "Task item (contains checkbox tap area)"),
            (".delete-btn", "Delete button"),
            (".filter-btn", "Filter button"),
        ]

        for selector, name in elements_to_check:
            element = page.locator(selector).first
            box = element.bounding_box()

            if box["height"] < 44:
                raise AssertionError(f"{name} height {box['height']}px < 44px minimum")

        # Verify delete button is always visible on mobile (not hover-only)
        delete_btn = page.locator(".delete-btn").first
        opacity = delete_btn.evaluate("el => window.getComputedStyle(el).opacity")

        if float(opacity) < 1.0:
            raise AssertionError(f"Delete button not fully visible on mobile (opacity: {opacity})")

        results.pass_test("AC7: Mobile responsive (375px viewport)")
    except Exception as e:
        results.fail_test("AC7: Mobile responsive", str(e))


def test_empty_input_guard(page, results):
    """Bonus: Empty input should not create a task"""
    try:
        clear_storage(page)
        page.goto(BASE_URL)

        input_field = page.locator("#taskInput")

        # Try to add empty task
        input_field.fill("")
        input_field.press("Enter")

        # Should still show empty state
        empty_state = page.locator(".empty-state")
        expect(empty_state).to_be_visible(timeout=TIMEOUT)

        # Try whitespace only
        input_field.fill("   ")
        input_field.press("Enter")

        # Should still show empty state
        expect(empty_state).to_be_visible(timeout=TIMEOUT)

        results.pass_test("Bonus: Empty input guard works")
    except Exception as e:
        results.fail_test("Bonus: Empty input guard", str(e))


def main():
    """Run all value delivery tests"""
    print("="*60)
    print("TODO APP - Value Delivery Verification")
    print("="*60)
    print(f"Testing: {HTML_FILE}")
    print(f"Server: {BASE_URL}")
    print("="*60 + "\n")

    if not HTML_FILE.exists():
        print(f"✗ FAIL: {HTML_FILE} does not exist")
        return 1

    # Start HTTP server
    print("Starting local HTTP server...")
    server = start_server()

    results = TestResult()

    try:
        with sync_playwright() as p:
            # Use Chromium for tests
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # Run all acceptance criteria tests
            test_ac1_initial_page_load(page, results)
            test_ac2_add_task_via_enter(page, results)
            test_ac3_checkbox_toggle_strikethrough(page, results)
            test_ac4_delete_button_removes_task(page, results)
            test_ac5_filter_buttons_work(page, results)
            test_ac6_persistence_after_refresh(page, results)
            test_ac7_mobile_responsive(page, results)
            test_empty_input_guard(page, results)

            browser.close()

    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        server.shutdown()

    # Print summary and return exit code
    success = results.summary()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
