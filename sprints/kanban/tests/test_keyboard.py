"""
test_keyboard.py — Verifies keyboard shortcuts.

PRD Reference: Section 8 (Keyboard Shortcuts)
Vision Goal: "Work efficiently with keyboard" — N, /, Escape, Ctrl+Z
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


# ── N key ─────────────────────────────────────────────────────────────────────

def test_n_key_opens_new_card_form_in_todo(page: Page, base_url: str):
    """Pressing N opens the card creation form in the To Do column."""
    # Ensure no input is focused
    page.locator("body").click()
    page.wait_for_timeout(100)
    page.keyboard.press("n")
    page.wait_for_timeout(200)

    # The add-card form in To Do column should be visible
    todo_col = page.locator(".column").nth(0)
    form = todo_col.locator(".add-card-form, .add-card-input")
    expect(form.first).to_be_visible()


def test_n_key_does_not_fire_when_input_focused(page: Page, base_url: str):
    """Pressing N while a text input is focused types 'n', does not open form."""
    # Focus the search input
    page.locator("#search-input").focus()
    page.keyboard.press("n")
    page.wait_for_timeout(200)

    # Search input should contain 'n', and add form should NOT open
    search_val = page.locator("#search-input").input_value()
    assert "n" in search_val.lower(), f"Expected 'n' in search input, got: '{search_val}'"

    # The To Do add-card form should NOT be visible
    todo_col = page.locator(".column").nth(0)
    add_form = todo_col.locator(".add-card-form")
    # The form should not be visible (it only becomes visible when add-btn is clicked or N pressed without focus)
    is_visible = add_form.evaluate("el => el.classList.contains('visible') || getComputedStyle(el).display !== 'none'")
    assert not is_visible, "Add card form should not open when N pressed in an input field"


# ── / key ─────────────────────────────────────────────────────────────────────

def test_slash_key_focuses_search(page: Page, base_url: str):
    """Pressing / focuses the search input."""
    page.locator("body").click()
    page.wait_for_timeout(100)
    page.keyboard.press("/")
    page.wait_for_timeout(200)

    # Search should be focused
    search = page.locator("#search-input")
    is_focused = page.evaluate("() => document.activeElement === document.getElementById('search-input')")
    assert is_focused, "Search input should be focused after pressing /"


# ── Escape key ────────────────────────────────────────────────────────────────

def test_escape_closes_modal(page: Page, base_url: str):
    """Pressing Escape closes the edit modal."""
    add_card(page, 0, "Modal Escape Card")
    page.locator(".card", has=page.locator(".card-title", has_text="Modal Escape Card")).click()
    expect(page.locator("#modal-overlay")).to_be_visible()

    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    expect(page.locator("#modal-overlay")).not_to_be_visible()


def test_escape_cancels_card_creation_form(page: Page, base_url: str):
    """Pressing Escape in the card creation form dismisses it without creating a card."""
    page.locator(".add-card-btn").nth(0).click()
    inp = page.locator(".add-card-input").nth(0)
    inp.wait_for(state="visible")
    inp.fill("Canceled Card")
    inp.press("Escape")
    page.wait_for_timeout(200)

    assert page.locator(".card-title", has_text="Canceled Card").count() == 0


def test_escape_clears_search(page: Page, base_url: str):
    """Pressing Escape when search is focused clears the search text."""
    search = page.locator("#search-input")
    search.focus()
    search.fill("some search text")
    page.wait_for_timeout(200)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    # Search should be cleared or input cleared (behavior: Escape clears search)
    val = search.input_value()
    # Either the value is cleared or the focus moved elsewhere — either is valid per PRD
    # The PRD says "Escape clears search" so we assert it's empty
    assert val == "" or len(val) == 0, f"Search not cleared after Escape: '{val}'"


# ── Ctrl+Z (Undo) ─────────────────────────────────────────────────────────────

def test_ctrl_z_undoes_card_creation(page: Page, base_url: str):
    """Ctrl+Z after creating a card removes it (undoes creation)."""
    add_card(page, 0, "Undo Creation Card")
    expect(page.locator(".card-title", has_text="Undo Creation Card")).to_be_visible()

    page.keyboard.press("Control+z")
    page.wait_for_timeout(500)

    assert page.locator(".card-title", has_text="Undo Creation Card").count() == 0, \
        "Card should be removed after Ctrl+Z"


def test_ctrl_z_shows_undo_notification(page: Page, base_url: str):
    """Pressing Ctrl+Z displays a notification message at the bottom."""
    add_card(page, 0, "Notification Undo Card")
    page.keyboard.press("Control+z")
    page.wait_for_timeout(300)

    # Some notification element should be visible
    notification = page.locator(".undo-notification, .notification, [class*='undo'], [class*='toast']")
    expect(notification.first).to_be_visible()


def test_ctrl_z_with_nothing_to_undo_is_no_op(page: Page, base_url: str):
    """Pressing Ctrl+Z with no action to undo does nothing (no error)."""
    # Fresh board, no actions taken
    page.keyboard.press("Control+z")
    page.wait_for_timeout(300)
    # No cards should appear or disappear
    assert page.locator(".card").count() == 0
    # No error notifications
    error_notification = page.locator(".error, [class*='error']")
    assert error_notification.count() == 0 or all(
        not error_notification.nth(i).is_visible()
        for i in range(error_notification.count())
    )
