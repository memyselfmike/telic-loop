#!/usr/bin/env python3
"""
Verification: Edge cases and error handling
PRD Reference: Section 2.1, 2.3 (Input validation, deletion)
Vision Goal: G1 - Robust user experience
Category: unit

Tests edge cases that could break user experience:
- Empty input rejection
- Whitespace-only input
- Very long task text
- Rapid clicking (race conditions)
- Special characters in task text
"""

import http.server
import socketserver
import threading
import time
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

SPRINT_DIR = Path(__file__).parent.parent.parent
HTML_FILE = SPRINT_DIR / "index.html"
TEST_PORT = 8767
BASE_URL = f"http://localhost:{TEST_PORT}"


def start_server():
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
    print("Unit Test: Edge Cases & Error Handling")
    print("="*60)

    if not HTML_FILE.exists():
        print(f"✗ FAIL: {HTML_FILE} does not exist")
        return 1

    server = start_server()
    failures = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # Test 1: Empty input
            try:
                page.goto(BASE_URL)
                page.evaluate("localStorage.clear()")
                page.reload()

                input_field = page.locator("#taskInput")
                input_field.fill("")
                input_field.press("Enter")

                # Should still have empty state
                expect(page.locator(".empty-state")).to_be_visible()
                print("✓ Empty input rejected correctly")
            except Exception as e:
                failures.append(f"Empty input test: {e}")
                print(f"✗ Empty input test failed: {e}")

            # Test 2: Whitespace-only input
            try:
                input_field.fill("   \t\n  ")
                input_field.press("Enter")

                expect(page.locator(".empty-state")).to_be_visible()
                print("✓ Whitespace-only input rejected correctly")
            except Exception as e:
                failures.append(f"Whitespace input test: {e}")
                print(f"✗ Whitespace input test failed: {e}")

            # Test 3: Very long task text
            try:
                long_text = "A" * 500  # 500 characters
                input_field.fill(long_text)
                input_field.press("Enter")

                task_text = page.locator(".task-text").first
                expect(task_text).to_be_visible()
                actual_text = task_text.text_content()

                if actual_text == long_text:
                    print("✓ Very long task text handled correctly")
                else:
                    raise AssertionError("Task text was truncated or modified")
            except Exception as e:
                failures.append(f"Long text test: {e}")
                print(f"✗ Long text test failed: {e}")

            # Test 4: Special characters in task text
            try:
                special_chars = '<script>alert("xss")</script> & "quotes" \'apostrophes\''
                input_field.fill(special_chars)
                input_field.press("Enter")

                task_text = page.locator(".task-text").last
                actual_text = task_text.text_content()

                # Text should be properly escaped (not executed)
                if actual_text == special_chars:
                    print("✓ Special characters handled correctly (XSS-safe)")
                else:
                    raise AssertionError(f"Special chars modified: got '{actual_text}'")
            except Exception as e:
                failures.append(f"Special characters test: {e}")
                print(f"✗ Special characters test failed: {e}")

            # Test 5: Rapid task addition (no race conditions)
            try:
                page.evaluate("localStorage.clear()")
                page.reload()

                rapid_tasks = ["Task 1", "Task 2", "Task 3", "Task 4", "Task 5"]
                for task in rapid_tasks:
                    input_field.fill(task)
                    input_field.press("Enter")
                    # No delay - rapid fire!

                # All tasks should be present
                time.sleep(0.3)  # Brief wait for rendering
                task_count = page.locator(".task-item").count()

                if task_count == len(rapid_tasks):
                    print(f"✓ Rapid task addition works ({task_count} tasks)")
                else:
                    raise AssertionError(f"Expected {len(rapid_tasks)}, got {task_count}")
            except Exception as e:
                failures.append(f"Rapid addition test: {e}")
                print(f"✗ Rapid addition test failed: {e}")

            # Test 6: Delete all tasks leaves clean state
            try:
                # Delete all tasks
                while page.locator(".task-item").count() > 0:
                    page.locator(".delete-btn").first.click()
                    time.sleep(0.05)

                # Should show empty state again
                expect(page.locator(".empty-state")).to_be_visible()

                # localStorage should be empty array
                storage = page.evaluate("localStorage.getItem('todo-app-tasks')")
                import json
                tasks = json.loads(storage)

                if len(tasks) == 0:
                    print("✓ Deleting all tasks returns to clean state")
                else:
                    raise AssertionError(f"Storage not empty: {len(tasks)} tasks remain")
            except Exception as e:
                failures.append(f"Delete all test: {e}")
                print(f"✗ Delete all test failed: {e}")

            # Test 7: Filter persistence during operations
            try:
                # Add tasks with mixed completion states
                for i in range(3):
                    input_field.fill(f"Filter test {i+1}")
                    input_field.press("Enter")
                    time.sleep(0.05)

                # Complete first task
                page.locator(".task-checkbox").first.click()

                # Switch to "Active" filter
                page.locator(".filter-btn[data-filter='active']").click()
                expect(page.locator(".task-item")).to_have_count(2)

                # Add a new task while filtered
                input_field.fill("New task while filtered")
                input_field.press("Enter")

                # Should see 3 active tasks now
                expect(page.locator(".task-item")).to_have_count(3)

                print("✓ Filter state maintained during operations")
            except Exception as e:
                failures.append(f"Filter persistence test: {e}")
                print(f"✗ Filter persistence test failed: {e}")

            # Test 8: Task count accuracy
            try:
                page.locator(".filter-btn[data-filter='all']").click()
                total_tasks = page.locator(".task-item").count()
                completed_count = page.locator(".task-item.completed").count()
                active_count = total_tasks - completed_count

                task_count_text = page.locator("#taskCount").text_content()
                expected_text = f"{active_count} item{'s' if active_count != 1 else ''} left"

                if task_count_text == expected_text:
                    print(f"✓ Task count accurate: {task_count_text}")
                else:
                    raise AssertionError(f"Expected '{expected_text}', got '{task_count_text}'")
            except Exception as e:
                failures.append(f"Task count test: {e}")
                print(f"✗ Task count test failed: {e}")

            browser.close()

    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        server.shutdown()

    print("\n" + "="*60)
    if failures:
        print(f"FAIL: {len(failures)} edge case(s) failed")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    else:
        print("PASS: All edge cases handled correctly")
        print("The app is robust against user input errors and edge cases.")
    print("="*60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
