"""
test_card_crud.py — Verifies card creation, editing, and deletion.

PRD Reference: Section 3 (Cards)
Vision Goal: "Manage cards fluidly" — create, edit, delete without friction
"""
import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(autouse=True)
def collect_console_errors(page: Page):
    errors = []
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    yield errors
    assert errors == [], f"Console errors detected: {errors}"


# ── Helpers ──────────────────────────────────────────────────────────────────

def add_card(page: Page, column_index: int, title: str):
    """Click the + button on a column, type a title, press Enter to create a card."""
    add_btn = page.locator(".add-card-btn").nth(column_index)
    add_btn.click()
    inp = page.locator(".add-card-input").nth(column_index)
    inp.wait_for(state="visible")
    inp.fill(title)
    inp.press("Enter")
    # Wait for the card to appear
    page.wait_for_selector(f".card-title:has-text('{title}')", timeout=3000)


# ── Card Creation ─────────────────────────────────────────────────────────────

def test_create_card_via_plus_button(page: Page, base_url: str):
    """Clicking + on To Do column, typing a title, pressing Enter creates a card."""
    add_card(page, 0, "My First Task")
    card = page.locator(".card-title", has_text="My First Task")
    expect(card).to_be_visible()


def test_new_card_appears_in_correct_column(page: Page, base_url: str):
    """Card created via column + button appears in that column."""
    # Create in "In Progress" (index 1)
    add_card(page, 1, "Task in Progress")
    col = page.locator(".column").nth(1)
    card_in_col = col.locator(".card-title", has_text="Task in Progress")
    expect(card_in_col).to_be_visible()
    # Should NOT be in To Do
    todo_col = page.locator(".column").nth(0)
    assert todo_col.locator(".card-title", has_text="Task in Progress").count() == 0


def test_card_count_badge_updates_after_create(page: Page, base_url: str):
    """Column count badge increments when a card is added."""
    add_card(page, 0, "Badge Test Card")
    badge = page.locator(".column").nth(0).locator(".card-count-badge")
    expect(badge).to_have_text("(1)")


def test_new_card_has_medium_priority_border(page: Page, base_url: str):
    """New card has medium priority (yellow left border) by default."""
    add_card(page, 0, "Priority Default Card")
    card_el = page.locator(".card", has=page.locator(".card-title", has_text="Priority Default Card"))
    # Medium priority = yellow border #d29922
    border = page.evaluate("""
        () => {
            const card = document.querySelector('.card');
            return getComputedStyle(card).borderLeftColor;
        }
    """)
    # #d29922 = rgb(210, 153, 34)
    assert "210" in border or "d29922" in border.lower() or border == "rgb(210, 153, 34)", \
        f"New card border not medium priority yellow: {border}"


def test_escape_cancels_card_creation(page: Page, base_url: str):
    """Pressing Escape while typing cancels card creation with no card created."""
    add_btn = page.locator(".add-card-btn").nth(0)
    add_btn.click()
    inp = page.locator(".add-card-input").nth(0)
    inp.wait_for(state="visible")
    inp.fill("Should Not Appear")
    inp.press("Escape")
    # Form should be hidden
    page.wait_for_timeout(200)
    assert page.locator(".card-title", has_text="Should Not Appear").count() == 0


def test_empty_title_does_not_create_card(page: Page, base_url: str):
    """Pressing Enter with empty title creates no card."""
    add_btn = page.locator(".add-card-btn").nth(0)
    add_btn.click()
    inp = page.locator(".add-card-input").nth(0)
    inp.wait_for(state="visible")
    inp.fill("")
    inp.press("Enter")
    page.wait_for_timeout(200)
    # Badge should still say (0)
    badge = page.locator(".column").nth(0).locator(".card-count-badge")
    expect(badge).to_have_text("(0)")


# ── Card Editing ──────────────────────────────────────────────────────────────

def test_clicking_card_opens_modal(page: Page, base_url: str):
    """Clicking a card opens the edit modal overlay."""
    add_card(page, 0, "Modal Test Card")
    page.locator(".card", has=page.locator(".card-title", has_text="Modal Test Card")).click()
    expect(page.locator("#modal-overlay")).to_be_visible()


def test_modal_shows_card_title(page: Page, base_url: str):
    """Modal title input shows the card's current title."""
    add_card(page, 0, "Editable Title Card")
    page.locator(".card", has=page.locator(".card-title", has_text="Editable Title Card")).click()
    modal_title = page.locator("#modal-title-input")
    expect(modal_title).to_have_value("Editable Title Card")


def test_edit_title_saves_on_close(page: Page, base_url: str):
    """Editing title in modal and closing persists the new title."""
    add_card(page, 0, "Original Title")
    page.locator(".card", has=page.locator(".card-title", has_text="Original Title")).click()
    modal_title = page.locator("#modal-title-input")
    modal_title.fill("Updated Title")
    modal_title.press("Tab")  # blur to save
    # Close modal
    page.locator("#modal-close-btn, button[aria-label*='Close']").first.click()
    expect(page.locator(".card-title", has_text="Updated Title")).to_be_visible()


def test_edit_description_saves(page: Page, base_url: str):
    """Editing description in modal persists after close."""
    add_card(page, 0, "Desc Card")
    page.locator(".card", has=page.locator(".card-title", has_text="Desc Card")).click()
    desc = page.locator("#modal-desc-input")
    desc.fill("This is a description")
    desc.press("Tab")
    page.locator("#modal-close-btn, button[aria-label*='Close']").first.click()
    # Reopen the card modal to verify
    page.locator(".card", has=page.locator(".card-title", has_text="Desc Card")).click()
    expect(page.locator("#modal-desc-input")).to_have_value("This is a description")


def test_change_priority_updates_border(page: Page, base_url: str):
    """Changing priority in modal updates the card's left border color."""
    add_card(page, 0, "Priority Change Card")
    page.locator(".card", has=page.locator(".card-title", has_text="Priority Change Card")).click()
    priority_sel = page.locator("#modal-priority-select")
    priority_sel.select_option("urgent")
    page.locator("#modal-close-btn, button[aria-label*='Close']").first.click()
    # Urgent = red border #f85149 = rgb(248, 81, 73)
    border = page.evaluate("""
        () => {
            const cards = document.querySelectorAll('.card');
            for (const c of cards) {
                if (c.querySelector('.card-title')?.textContent === 'Priority Change Card') {
                    return getComputedStyle(c).borderLeftColor;
                }
            }
            return null;
        }
    """)
    assert border is not None, "Card not found after priority change"
    assert "248" in border or "f85149" in border.lower() or border == "rgb(248, 81, 73)", \
        f"Urgent priority border not red: {border}"


def test_add_label_appears_on_card(page: Page, base_url: str):
    """Adding a label in the modal shows it as a chip on the card."""
    add_card(page, 0, "Label Card")
    page.locator(".card", has=page.locator(".card-title", has_text="Label Card")).click()
    # Find label input
    label_input = page.locator("#modal-label-input, input[placeholder*='label'], input[placeholder*='Label']").first
    label_input.fill("bug")
    label_input.press("Enter")
    page.wait_for_timeout(200)
    page.locator("#modal-close-btn, button[aria-label*='Close']").first.click()
    # Label chip should appear on the card
    card = page.locator(".card", has=page.locator(".card-title", has_text="Label Card"))
    expect(card.locator(".card-label, .label-chip", has_text="bug")).to_be_visible()


def test_close_modal_by_clicking_outside(page: Page, base_url: str):
    """Clicking outside the modal closes it."""
    add_card(page, 0, "Outside Click Card")
    page.locator(".card", has=page.locator(".card-title", has_text="Outside Click Card")).click()
    expect(page.locator("#modal-overlay")).to_be_visible()
    # Click the overlay background (not the modal itself)
    page.locator("#modal-overlay").click(position={"x": 10, "y": 10})
    page.wait_for_timeout(300)
    expect(page.locator("#modal-overlay")).not_to_be_visible()


def test_escape_closes_modal(page: Page, base_url: str):
    """Pressing Escape closes the edit modal."""
    add_card(page, 0, "Escape Modal Card")
    page.locator(".card", has=page.locator(".card-title", has_text="Escape Modal Card")).click()
    expect(page.locator("#modal-overlay")).to_be_visible()
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    expect(page.locator("#modal-overlay")).not_to_be_visible()


# ── Card Deletion ─────────────────────────────────────────────────────────────

def test_delete_card_with_confirmation(page: Page, base_url: str):
    """Delete button shows confirmation dialog, then removes the card."""
    add_card(page, 0, "Card To Delete")
    page.locator(".card", has=page.locator(".card-title", has_text="Card To Delete")).click()
    # Click the delete button in the modal (opens confirm dialog)
    page.locator("#btn-delete-card").click()
    # Confirmation dialog should appear
    page.wait_for_selector("#confirm-overlay.visible", timeout=2000)
    # Click the confirm-delete button inside the dialog
    page.locator("#btn-confirm-delete").click()
    page.wait_for_timeout(300)
    assert page.locator(".card-title", has_text="Card To Delete").count() == 0, \
        "Card was not deleted after confirmation"
