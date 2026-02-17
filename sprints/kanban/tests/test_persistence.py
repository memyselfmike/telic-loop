"""
test_persistence.py — Verifies localStorage persistence across page reloads.

PRD Reference: Section 6 (Persistence)
Vision Goal: "Trust that nothing is lost" — reload the page, everything is where you left it
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


def test_cards_persist_after_reload(page: Page, base_url: str):
    """Cards created before reload are still present after reload."""
    add_card(page, 0, "Persistent Card A")
    add_card(page, 1, "Persistent Card B")
    add_card(page, 2, "Persistent Card C")

    page.reload()
    page.wait_for_load_state("networkidle")

    expect(page.locator(".card-title", has_text="Persistent Card A")).to_be_visible()
    expect(page.locator(".card-title", has_text="Persistent Card B")).to_be_visible()
    expect(page.locator(".card-title", has_text="Persistent Card C")).to_be_visible()


def test_cards_in_correct_columns_after_reload(page: Page, base_url: str):
    """Cards remain in their correct columns after reload."""
    add_card(page, 0, "Todo Card")
    add_card(page, 1, "InProgress Card")
    add_card(page, 2, "Done Card")

    page.reload()
    page.wait_for_load_state("networkidle")

    todo_col = page.locator(".column").nth(0)
    ip_col = page.locator(".column").nth(1)
    done_col = page.locator(".column").nth(2)

    expect(todo_col.locator(".card-title", has_text="Todo Card")).to_be_visible()
    expect(ip_col.locator(".card-title", has_text="InProgress Card")).to_be_visible()
    expect(done_col.locator(".card-title", has_text="Done Card")).to_be_visible()

    # Cross-check: wrong columns should not have these cards
    assert ip_col.locator(".card-title", has_text="Todo Card").count() == 0
    assert todo_col.locator(".card-title", has_text="InProgress Card").count() == 0


def test_card_properties_persist_after_reload(page: Page, base_url: str):
    """Card priority, description, and labels survive reload."""
    add_card(page, 0, "Rich Card")
    # Open and edit
    page.locator(".card", has=page.locator(".card-title", has_text="Rich Card")).click()
    page.locator("#modal-priority-select").select_option("high")
    page.locator("#modal-desc-input").fill("Saved description")
    label_input = page.locator("#modal-label-input, input[placeholder*='label'], input[placeholder*='Label']").first
    label_input.fill("feature")
    label_input.press("Enter")
    page.wait_for_timeout(200)
    page.locator("#modal-close-btn, button[aria-label*='Close']").first.click()
    page.wait_for_timeout(200)

    page.reload()
    page.wait_for_load_state("networkidle")

    # Card should still exist
    expect(page.locator(".card-title", has_text="Rich Card")).to_be_visible()
    # Verify priority border (high = orange #d18616 = rgb(209, 134, 22))
    border = page.evaluate("""
        () => {
            const cards = document.querySelectorAll('.card');
            for (const c of cards) {
                if (c.querySelector('.card-title')?.textContent === 'Rich Card') {
                    return getComputedStyle(c).borderLeftColor;
                }
            }
            return null;
        }
    """)
    assert border is not None, "Rich Card not found after reload"
    assert "209" in border or "d18616" in border.lower() or border == "rgb(209, 134, 22)", \
        f"High priority border not orange after reload: {border}"

    # Verify label persists
    card = page.locator(".card", has=page.locator(".card-title", has_text="Rich Card"))
    expect(card.locator(".card-label, .label-chip", has_text="feature")).to_be_visible()


def test_empty_board_on_cleared_localstorage(page: Page, base_url: str):
    """If localStorage is cleared, the board loads empty without errors."""
    add_card(page, 0, "Will Be Cleared")
    page.evaluate("() => localStorage.clear()")
    page.reload()
    page.wait_for_load_state("networkidle")

    # All badges should show (0)
    badges = page.locator(".card-count-badge")
    for i in range(3):
        expect(badges.nth(i)).to_have_text("(0)")

    # No cards should exist
    assert page.locator(".card").count() == 0


def test_corrupted_localstorage_shows_empty_board(page: Page, base_url: str):
    """Corrupted JSON in localStorage results in empty board, not a crash."""
    page.evaluate("() => localStorage.setItem('kanban_board_state', '{{INVALID JSON!!!')")
    page.reload()
    page.wait_for_load_state("networkidle")

    # Should show three columns
    expect(page.locator(".column")).to_have_count(3)
    # No cards
    assert page.locator(".card").count() == 0
    # Column names still correct
    expect(page.locator(".column-name").nth(0)).to_have_text("To Do")


def test_localstorage_schema_is_correct(page: Page, base_url: str):
    """localStorage stores data in the correct schema per PRD Section 6.4."""
    add_card(page, 0, "Schema Test Card")

    stored = page.evaluate("""
        () => {
            const raw = localStorage.getItem('kanban_board_state');
            if (!raw) return null;
            return JSON.parse(raw);
        }
    """)

    assert stored is not None, "Nothing stored in localStorage"
    assert "columns" in stored, "State missing 'columns' key"
    assert "cards" in stored, "State missing 'cards' key"
    assert len(stored["columns"]) == 3, f"Expected 3 columns, got {len(stored['columns'])}"

    # Find the card we created
    cards = stored["cards"]
    found = any(c["title"] == "Schema Test Card" for c in cards.values())
    assert found, "Created card not found in localStorage"

    # Verify column has cardIds
    todo_col = next((c for c in stored["columns"] if c["id"] == "todo"), None)
    assert todo_col is not None, "Todo column not found in state"
    assert "cardIds" in todo_col, "Column missing 'cardIds'"
