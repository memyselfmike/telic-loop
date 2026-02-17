#!/usr/bin/env python3
"""
value_user_journey.py — Full user journey verification: open, create, organize, search, persist.

PRD Reference: All sections (end-to-end value chain)
Vision Goal: All 8 vision deliverables verified in a single realistic user workflow
Category: value

This script simulates a real user working with the Kanban board through a realistic
sequence: open the file, create tasks, organize by priority, move cards between columns,
search for a specific card, and verify persistence across reload.
"""
import os
import sys
import socket
import threading
import time
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# ─── Try to import playwright ───────────────────────────────────────────────
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("FAIL: playwright not installed. Run: pip install playwright && playwright install")
    sys.exit(1)

KANBAN_DIR = Path(__file__).parent.parent.parent.resolve()


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start_server(port, directory):
    original = os.getcwd()
    os.chdir(str(directory))
    server = HTTPServer(("127.0.0.1", port), QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, original


def wait_ready(url, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except (urllib.error.URLError, ConnectionRefusedError):
            time.sleep(0.1)
    return False


PASS_COUNT = 0
FAIL_COUNT = 0
FAILURES = []


def check(condition, description):
    global PASS_COUNT, FAIL_COUNT
    if condition:
        print(f"  ✓ {description}")
        PASS_COUNT += 1
    else:
        print(f"  ✗ FAIL: {description}")
        FAIL_COUNT += 1
        FAILURES.append(description)


def main():
    print("=== Value Delivery: Full User Journey ===")
    print()

    port = get_free_port()
    server, original_dir = start_server(port, KANBAN_DIR)
    base_url = f"http://127.0.0.1:{port}"

    if not wait_ready(f"{base_url}/index.html"):
        print("FAIL: HTTP server did not start in 5 seconds")
        sys.exit(1)

    print(f"HTTP server started on port {port}")
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()

        # Collect console errors throughout the journey
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        try:
            # ─── Step 1: Open the board ───────────────────────────────────
            print("Step 1: User opens the Kanban board")
            page.goto(f"{base_url}/index.html")
            page.evaluate("() => localStorage.clear()")
            page.reload()

            columns = page.locator(".column")
            check(columns.count() == 3, "Board shows three columns")
            check(page.locator(".column-name", has_text="To Do").is_visible(), "To Do column visible")
            check(page.locator(".column-name", has_text="In Progress").is_visible(), "In Progress column visible")
            check(page.locator(".column-name", has_text="Done").is_visible(), "Done column visible")
            print()

            # ─── Step 2: Create tasks ──────────────────────────────────────
            print("Step 2: User creates cards in different columns")

            def add_card(col_index, title):
                page.locator(".add-card-btn").nth(col_index).click()
                inp = page.locator(".add-card-input").nth(col_index)
                inp.wait_for(state="visible")
                inp.fill(title)
                inp.press("Enter")
                page.wait_for_selector(f".card-title:has-text('{title}')", timeout=3000)

            add_card(0, "Fix authentication bug")
            add_card(0, "Update documentation")
            add_card(0, "Add unit tests")
            add_card(1, "Review pull request")
            add_card(2, "Deploy v1.0")

            check(page.locator(".card-title", has_text="Fix authentication bug").is_visible(),
                  "Card 'Fix authentication bug' created in To Do")
            check(page.locator(".card-title", has_text="Review pull request").is_visible(),
                  "Card 'Review pull request' created in In Progress")
            check(page.locator(".card-title", has_text="Deploy v1.0").is_visible(),
                  "Card 'Deploy v1.0' created in Done")

            todo_badge = page.locator(".column").nth(0).locator(".card-count-badge")
            check(todo_badge.text_content() == "(3)", "To Do badge shows (3)")
            print()

            # ─── Step 3: Edit a card ───────────────────────────────────────
            print("Step 3: User enriches a card with priority and labels")
            page.locator(".card", has=page.locator(".card-title", has_text="Fix authentication bug")).click()
            page.locator("#modal-priority-select").select_option("urgent")
            label_input = page.locator("#modal-label-input, input[placeholder*='label'], input[placeholder*='Label']").first
            label_input.fill("security")
            label_input.press("Enter")
            page.wait_for_timeout(200)
            page.locator("#modal-close-btn, button[aria-label*='Close']").first.click()
            page.wait_for_timeout(200)

            bug_card = page.locator(".card", has=page.locator(".card-title", has_text="Fix authentication bug"))
            border_color = page.evaluate("""
                () => {
                    const cards = document.querySelectorAll('.card');
                    for (const c of cards) {
                        if (c.querySelector('.card-title')?.textContent === 'Fix authentication bug') {
                            return getComputedStyle(c).borderLeftColor;
                        }
                    }
                    return null;
                }
            """)
            # Urgent = red #f85149 = rgb(248, 81, 73)
            check(border_color is not None and ("248" in border_color or "f85149" in border_color.lower()),
                  "Urgent card has red left border")
            check(bug_card.locator(".card-label, .label-chip", has_text="security").is_visible(),
                  "Security label appears on card")
            print()

            # ─── Step 4: Search ───────────────────────────────────────────
            print("Step 4: User searches for a specific card")
            search = page.locator("#search-input")
            search.fill("auth")
            page.wait_for_timeout(300)

            def is_card_visible(title):
                card_el = page.locator(".card", has=page.locator(".card-title", has_text=title)).first
                if card_el.count() == 0:
                    return False
                return not card_el.evaluate(
                    "el => el.classList.contains('hidden') || getComputedStyle(el).display === 'none'"
                )

            check(is_card_visible("Fix authentication bug"), "Matching card 'Fix authentication bug' visible")
            check(not is_card_visible("Update documentation"), "Non-matching card hidden during search")
            check(not is_card_visible("Add unit tests"), "Non-matching card hidden during search")

            # Clear search
            search.fill("")
            page.wait_for_timeout(300)
            check(is_card_visible("Update documentation"), "All cards visible after clearing search")
            print()

            # ─── Step 5: Priority filter ──────────────────────────────────
            print("Step 5: User filters by Urgent priority")
            page.locator(".filter-btn", has_text="Urgent").click()
            page.wait_for_timeout(300)

            check(is_card_visible("Fix authentication bug"), "Urgent card visible with Urgent filter")
            check(not is_card_visible("Update documentation"), "Medium card hidden with Urgent filter")

            page.locator(".filter-btn", has_text="All").click()
            page.wait_for_timeout(300)
            print()

            # ─── Step 6: Drag-and-drop ────────────────────────────────────
            print("Step 6: User drags a card between columns")
            card = page.locator(".card", has=page.locator(".card-title", has_text="Update documentation"))
            src_box = card.bounding_box()
            target = page.locator(".column").nth(1).locator(".card-list")
            tgt_box = target.bounding_box()

            if src_box and tgt_box:
                page.mouse.move(src_box["x"] + src_box["width"]/2, src_box["y"] + src_box["height"]/2)
                page.mouse.down()
                page.mouse.move(tgt_box["x"] + tgt_box["width"]/2, tgt_box["y"] + tgt_box["height"]/2, steps=15)
                page.wait_for_timeout(100)
                page.mouse.up()
                page.wait_for_timeout(300)

                in_progress_col = page.locator(".column").nth(1)
                check(in_progress_col.locator(".card-title", has_text="Update documentation").is_visible(),
                      "Card dragged from To Do to In Progress")
            else:
                check(False, "Could not get bounding boxes for drag test")
            print()

            # ─── Step 7: Undo ─────────────────────────────────────────────
            print("Step 7: User presses Ctrl+Z to undo last action")
            # Create a card to undo
            add_card(0, "Card To Undo")
            check(page.locator(".card-title", has_text="Card To Undo").is_visible(),
                  "Card 'Card To Undo' created")
            page.keyboard.press("Control+z")
            page.wait_for_timeout(500)
            check(page.locator(".card-title", has_text="Card To Undo").count() == 0,
                  "Card removed after Ctrl+Z undo")
            print()

            # ─── Step 8: Persistence ─────────────────────────────────────
            print("Step 8: User reloads the page — all cards are still there")
            page.reload()
            page.wait_for_load_state("networkidle")

            check(page.locator(".card-title", has_text="Fix authentication bug").is_visible(),
                  "Card 'Fix authentication bug' persists after reload")
            check(page.locator(".card-title", has_text="Deploy v1.0").is_visible(),
                  "Card 'Deploy v1.0' persists after reload")
            print()

            # ─── Step 9: Keyboard shortcuts ───────────────────────────────
            print("Step 9: User uses keyboard shortcuts")
            page.locator("body").click()
            page.wait_for_timeout(100)
            page.keyboard.press("n")
            page.wait_for_timeout(200)
            todo_col = page.locator(".column").nth(0)
            form_visible = todo_col.locator(".add-card-form").evaluate(
                "el => el.classList.contains('visible') || getComputedStyle(el).display !== 'none'"
            )
            check(form_visible, "N key opens card creation form in To Do")

            page.keyboard.press("Escape")
            page.wait_for_timeout(100)
            page.keyboard.press("/")
            page.wait_for_timeout(200)
            search_focused = page.evaluate(
                "() => document.activeElement === document.getElementById('search-input')"
            )
            check(search_focused, "/ key focuses search input")
            print()

            # ─── Final: No console errors ─────────────────────────────────
            check(len(console_errors) == 0,
                  f"No console errors during entire journey (found: {len(console_errors)})")
            if console_errors:
                print(f"    Console errors: {console_errors[:5]}")

        finally:
            browser.close()
            server.shutdown()
            os.chdir(original_dir)

    # ─── Summary ─────────────────────────────────────────────────────────────
    print()
    print("=" * 50)
    total = PASS_COUNT + FAIL_COUNT
    print(f"Results: {PASS_COUNT}/{total} checks passed")

    if FAIL_COUNT > 0:
        print(f"\nFailed checks:")
        for f in FAILURES:
            print(f"  - {f}")
        print("\nFAIL: User journey did not complete successfully")
        sys.exit(1)
    else:
        print("\nPASS: Complete user journey delivered all promised value")
        sys.exit(0)


if __name__ == "__main__":
    main()
