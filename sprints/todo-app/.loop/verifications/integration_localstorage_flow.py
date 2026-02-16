#!/usr/bin/env python3
"""
Verification: LocalStorage data flow (add → save → load → render)
PRD Reference: Section 2.5 (Persistence)
Vision Goal: G1 - Tasks persist across browser sessions
Category: integration

This verifies the complete data flow from user action through localStorage
to page reload, ensuring data integrity is maintained throughout.
"""

import http.server
import socketserver
import threading
import time
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

# Configuration
SPRINT_DIR = Path(__file__).parent.parent.parent
HTML_FILE = SPRINT_DIR / "index.html"
TEST_PORT = 8766
BASE_URL = f"http://localhost:{TEST_PORT}"


def start_server():
    """Start HTTP server in background"""
    os.chdir(SPRINT_DIR)
    handler = http.server.SimpleHTTPRequestHandler

    class QuietServer(socketserver.TCPServer):
        allow_reuse_address = True

    httpd = QuietServer(("", TEST_PORT), handler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)
    return httpd


def main():
    print("="*60)
    print("Integration Test: LocalStorage Data Flow")
    print("="*60)

    if not HTML_FILE.exists():
        print(f"✗ FAIL: {HTML_FILE} does not exist")
        return 1

    server = start_server()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # Clear any existing storage
            page.goto(BASE_URL)
            page.evaluate("localStorage.clear()")
            print("✓ Cleared localStorage")

            # Step 1: Add tasks through UI
            page.reload()
            test_tasks = [
                ("Task Alpha", False),
                ("Task Beta", True),
                ("Task Gamma", False),
            ]

            input_field = page.locator("#taskInput")
            for task_text, should_complete in test_tasks:
                input_field.fill(task_text)
                input_field.press("Enter")
                if should_complete:
                    page.locator(".task-item").last.locator(".task-checkbox").click()
                time.sleep(0.1)

            print(f"✓ Added {len(test_tasks)} tasks via UI")

            # Step 2: Verify localStorage contains data
            storage_data = page.evaluate("localStorage.getItem('todo-app-tasks')")
            if not storage_data:
                print("✗ FAIL: No data in localStorage")
                return 1

            print("✓ LocalStorage contains data")

            # Step 3: Parse and verify storage structure
            import json
            stored_tasks = json.loads(storage_data)

            if not isinstance(stored_tasks, list):
                print("✗ FAIL: Storage data is not an array")
                return 1

            if len(stored_tasks) != len(test_tasks):
                print(f"✗ FAIL: Expected {len(test_tasks)} tasks, found {len(stored_tasks)}")
                return 1

            print(f"✓ Storage contains {len(stored_tasks)} tasks")

            # Step 4: Verify task data structure
            required_fields = ["id", "text", "completed", "createdAt"]
            for i, task in enumerate(stored_tasks):
                for field in required_fields:
                    if field not in task:
                        print(f"✗ FAIL: Task {i} missing field: {field}")
                        return 1

                # Verify task text matches
                expected_text = test_tasks[i][0]
                if task["text"] != expected_text:
                    print(f"✗ FAIL: Task {i} text mismatch: expected '{expected_text}', got '{task['text']}'")
                    return 1

                # Verify completed state matches
                expected_completed = test_tasks[i][1]
                if task["completed"] != expected_completed:
                    print(f"✗ FAIL: Task {i} completed state mismatch: expected {expected_completed}, got {task['completed']}")
                    return 1

            print("✓ All tasks have correct structure and data")

            # Step 5: Reload page and verify tasks are restored
            page.reload()
            time.sleep(0.5)

            visible_tasks = page.locator(".task-item").count()
            if visible_tasks != len(test_tasks):
                print(f"✗ FAIL: After reload, expected {len(test_tasks)} visible tasks, found {visible_tasks}")
                return 1

            print("✓ Tasks restored after page reload")

            # Step 6: Verify task states are preserved
            for i, (task_text, should_complete) in enumerate(test_tasks):
                task_item = page.locator(".task-item").nth(i)
                text_element = task_item.locator(".task-text")

                if text_element.text_content() != task_text:
                    print(f"✗ FAIL: Task {i} text not preserved after reload")
                    return 1

                has_completed_class = "completed" in task_item.get_attribute("class")
                if has_completed_class != should_complete:
                    print(f"✗ FAIL: Task {i} completed state not preserved after reload")
                    return 1

            print("✓ All task states preserved correctly")

            # Step 7: Delete a task and verify localStorage updates
            initial_count = len(stored_tasks)
            page.locator(".delete-btn").first.click()
            time.sleep(0.2)

            updated_storage = page.evaluate("localStorage.getItem('todo-app-tasks')")
            updated_tasks = json.loads(updated_storage)

            if len(updated_tasks) != initial_count - 1:
                print(f"✗ FAIL: After delete, expected {initial_count - 1} tasks, found {len(updated_tasks)}")
                return 1

            print("✓ Delete operation updates localStorage")

            # Step 8: Toggle completion and verify localStorage updates
            # Get the current completed state before toggle
            pre_toggle_storage = page.evaluate("localStorage.getItem('todo-app-tasks')")
            pre_toggle_tasks = json.loads(pre_toggle_storage)
            first_task_id = pre_toggle_tasks[0]["id"]
            first_task_was_completed = pre_toggle_tasks[0]["completed"]

            # Toggle the first checkbox
            page.locator(".task-checkbox").first.click()
            time.sleep(0.2)

            # Verify localStorage was updated
            post_toggle_storage = page.evaluate("localStorage.getItem('todo-app-tasks')")
            post_toggle_tasks = json.loads(post_toggle_storage)

            # Find the same task and verify its state changed
            toggled_task = next((t for t in post_toggle_tasks if t["id"] == first_task_id), None)
            if not toggled_task:
                print("✗ FAIL: Task disappeared after toggle")
                return 1

            if toggled_task["completed"] == first_task_was_completed:
                print(f"✗ FAIL: Toggle completion did not update localStorage (still {first_task_was_completed})")
                return 1

            print("✓ Toggle operation updates localStorage")

            browser.close()

    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        server.shutdown()

    print("\n" + "="*60)
    print("PASS: LocalStorage integration complete")
    print("="*60)
    print("Data flows correctly through the entire persistence cycle:")
    print("  UI action → localStorage save → page reload → data restore → UI render")
    return 0


if __name__ == "__main__":
    sys.exit(main())
