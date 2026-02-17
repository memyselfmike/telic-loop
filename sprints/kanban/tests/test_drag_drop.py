"""
test_drag_drop.py — Verifies drag-and-drop between columns.

PRD Reference: Section 4 (Drag and Drop)
Vision Goal: "Drag cards between columns" — smooth, reliable card movement

IMPORTANT: Uses low-level mouse API (mouse.move/down/up with steps) to simulate
the custom mousedown/mousemove/mouseup drag handlers. The HTML5 drag_and_drop API
is NOT used here because the implementation uses custom event handlers.
"""
import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(autouse=True)
def collect_console_errors(page: Page):
    errors = []
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    yield errors
    assert errors == [], f"Console errors detected: {errors}"


def add_card(page: Page, column_index: int, title: str):
    """Helper: create a card in the specified column."""
    add_btn = page.locator(".add-card-btn").nth(column_index)
    add_btn.click()
    inp = page.locator(".add-card-input").nth(column_index)
    inp.wait_for(state="visible")
    inp.fill(title)
    inp.press("Enter")
    page.wait_for_selector(f".card-title:has-text('{title}')", timeout=3000)


def drag_card_to_column(page: Page, card_title: str, target_column_index: int):
    """
    Drag a card to a target column using low-level mouse events.

    The custom drag handler activates on mousemove with button pressed,
    so we need intermediate steps between mousedown and the target position.
    """
    # Find the source card
    card = page.locator(".card", has=page.locator(".card-title", has_text=card_title))
    card.wait_for(state="visible")
    src_box = card.bounding_box()
    assert src_box is not None, f"Card '{card_title}' not found"

    src_x = src_box["x"] + src_box["width"] / 2
    src_y = src_box["y"] + src_box["height"] / 2

    # Find the target column's card list
    target_col = page.locator(".column").nth(target_column_index)
    target_list = target_col.locator(".card-list")
    target_box = target_list.bounding_box()
    assert target_box is not None, f"Target column {target_column_index} card-list not found"

    tgt_x = target_box["x"] + target_box["width"] / 2
    tgt_y = target_box["y"] + target_box["height"] / 2

    # Perform the drag: move to source → press → move to target with steps → release
    page.mouse.move(src_x, src_y)
    page.mouse.down()
    # Move with steps to trigger intermediate mousemove events that activate drag mode
    page.mouse.move(tgt_x, tgt_y, steps=15)
    page.wait_for_timeout(100)
    page.mouse.up()
    page.wait_for_timeout(300)  # Allow re-render


def test_drag_card_from_todo_to_in_progress(page: Page, base_url: str):
    """
    User drags a card from To Do to In Progress — card appears in In Progress.
    PRD Section 4.3: drop moves card to new position.
    """
    add_card(page, 0, "Drag Me Task")

    # Verify starting position
    todo_col = page.locator(".column").nth(0)
    expect(todo_col.locator(".card-title", has_text="Drag Me Task")).to_be_visible()

    drag_card_to_column(page, "Drag Me Task", 1)

    # Card should now be in In Progress (column 1)
    in_progress_col = page.locator(".column").nth(1)
    expect(in_progress_col.locator(".card-title", has_text="Drag Me Task")).to_be_visible()

    # Card should NOT still be in To Do
    assert todo_col.locator(".card-title", has_text="Drag Me Task").count() == 0, \
        "Card is still in To Do after drag to In Progress"


def test_drag_card_from_todo_to_done(page: Page, base_url: str):
    """User drags a card all the way from To Do to Done."""
    add_card(page, 0, "Complete Me")

    drag_card_to_column(page, "Complete Me", 2)

    done_col = page.locator(".column").nth(2)
    expect(done_col.locator(".card-title", has_text="Complete Me")).to_be_visible()


def test_drag_card_back_to_original_column(page: Page, base_url: str):
    """User can drag a card from In Progress back to To Do."""
    add_card(page, 1, "Regressed Task")

    drag_card_to_column(page, "Regressed Task", 0)

    todo_col = page.locator(".column").nth(0)
    expect(todo_col.locator(".card-title", has_text="Regressed Task")).to_be_visible()

    in_progress_col = page.locator(".column").nth(1)
    assert in_progress_col.locator(".card-title", has_text="Regressed Task").count() == 0


def test_drag_card_persists_after_reload(page: Page, base_url: str):
    """After dragging a card to a new column, the position persists after reload."""
    add_card(page, 0, "Persistent Drag Card")

    drag_card_to_column(page, "Persistent Drag Card", 2)

    # Reload page — card should still be in Done
    page.reload()
    page.wait_for_load_state("networkidle")

    done_col = page.locator(".column").nth(2)
    expect(done_col.locator(".card-title", has_text="Persistent Drag Card")).to_be_visible()

    todo_col = page.locator(".column").nth(0)
    assert todo_col.locator(".card-title", has_text="Persistent Drag Card").count() == 0


def test_drag_updates_column_count_badge(page: Page, base_url: str):
    """Card count badges update after drag (source column decrements, target increments)."""
    add_card(page, 0, "Badge Drag Card")

    todo_badge = page.locator(".column").nth(0).locator(".card-count-badge")
    ip_badge = page.locator(".column").nth(1).locator(".card-count-badge")

    expect(todo_badge).to_have_text("(1)")
    expect(ip_badge).to_have_text("(0)")

    drag_card_to_column(page, "Badge Drag Card", 1)

    expect(todo_badge).to_have_text("(0)")
    expect(ip_badge).to_have_text("(1)")
