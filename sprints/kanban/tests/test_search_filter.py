"""
test_search_filter.py — Verifies search and priority/label filtering.

PRD Reference: Section 5 (Filtering and Search)
Vision Goal: "Find cards quickly" — real-time search, priority & label filters
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


def open_card_and_set_priority(page: Page, title: str, priority: str):
    """Open a card's modal and set its priority."""
    page.locator(".card", has=page.locator(".card-title", has_text=title)).click()
    page.locator("#modal-priority-select").select_option(priority)
    page.locator("#modal-close-btn, button[aria-label*='Close']").first.click()
    page.wait_for_timeout(200)


def is_card_visible(page: Page, title: str) -> bool:
    """Check if a card with the given title is visible (not hidden)."""
    cards = page.locator(".card-title", has_text=title)
    if cards.count() == 0:
        return False
    # Check if the card element has the 'hidden' class or display:none
    card_el = page.locator(".card", has=page.locator(".card-title", has_text=title)).first
    is_hidden = card_el.evaluate(
        "el => el.classList.contains('hidden') || getComputedStyle(el).display === 'none'"
    )
    return not is_hidden


# ── Search Tests ──────────────────────────────────────────────────────────────

def test_search_hides_non_matching_cards(page: Page, base_url: str):
    """Typing in search bar hides cards that don't match."""
    add_card(page, 0, "Alpha Task")
    add_card(page, 0, "Beta Task")
    add_card(page, 0, "Gamma Task")

    search = page.locator("#search-input")
    search.fill("Alpha")
    page.wait_for_timeout(300)  # Debounce 150ms + render

    assert is_card_visible(page, "Alpha Task"), "Alpha Task should be visible"
    assert not is_card_visible(page, "Beta Task"), "Beta Task should be hidden"
    assert not is_card_visible(page, "Gamma Task"), "Gamma Task should be hidden"


def test_search_shows_matching_cards(page: Page, base_url: str):
    """Matching cards remain visible after search."""
    add_card(page, 0, "Fix Bug")
    add_card(page, 1, "Fix Deploy")
    add_card(page, 2, "Write Docs")

    search = page.locator("#search-input")
    search.fill("Fix")
    page.wait_for_timeout(300)

    assert is_card_visible(page, "Fix Bug"), "Fix Bug should be visible"
    assert is_card_visible(page, "Fix Deploy"), "Fix Deploy should be visible"
    assert not is_card_visible(page, "Write Docs"), "Write Docs should be hidden"


def test_search_updates_count_badges(page: Page, base_url: str):
    """Count badges update to show filtered count when searching."""
    add_card(page, 0, "Matching Alpha")
    add_card(page, 0, "Not Matching Beta")

    search = page.locator("#search-input")
    search.fill("Alpha")
    page.wait_for_timeout(300)

    badge = page.locator(".column").nth(0).locator(".card-count-badge")
    expect(badge).to_have_text("(1)")


def test_search_case_insensitive(page: Page, base_url: str):
    """Search matching is case-insensitive."""
    add_card(page, 0, "UPPERCASE Card")
    search = page.locator("#search-input")
    search.fill("uppercase")
    page.wait_for_timeout(300)
    assert is_card_visible(page, "UPPERCASE Card"), "Case-insensitive search should match"


def test_search_preserves_column_structure(page: Page, base_url: str):
    """Column headers remain visible when search hides all cards."""
    add_card(page, 0, "Only Card")
    search = page.locator("#search-input")
    search.fill("XYZ_NO_MATCH")
    page.wait_for_timeout(300)

    # Column names should still be visible
    expect(page.locator(".column-name").nth(0)).to_be_visible()
    expect(page.locator(".column-name").nth(1)).to_be_visible()
    expect(page.locator(".column-name").nth(2)).to_be_visible()


# ── Priority Filter Tests ─────────────────────────────────────────────────────

def test_priority_filter_low(page: Page, base_url: str):
    """Priority filter 'Low' shows only low-priority cards."""
    add_card(page, 0, "Low Priority Task")
    add_card(page, 0, "Medium Priority Task")  # medium by default
    open_card_and_set_priority(page, "Low Priority Task", "low")

    page.locator(".filter-btn", has_text="Low").click()
    page.wait_for_timeout(300)

    assert is_card_visible(page, "Low Priority Task"), "Low priority card should be visible"
    assert not is_card_visible(page, "Medium Priority Task"), "Medium priority card should be hidden"


def test_priority_filter_urgent(page: Page, base_url: str):
    """Priority filter 'Urgent' shows only urgent cards."""
    add_card(page, 0, "Urgent Fix")
    add_card(page, 0, "Normal Work")
    open_card_and_set_priority(page, "Urgent Fix", "urgent")

    page.locator(".filter-btn", has_text="Urgent").click()
    page.wait_for_timeout(300)

    assert is_card_visible(page, "Urgent Fix"), "Urgent card should be visible"
    assert not is_card_visible(page, "Normal Work"), "Medium card should be hidden with urgent filter"


def test_priority_filter_all_shows_everything(page: Page, base_url: str):
    """Clicking 'All' after a filter resets to show all cards."""
    add_card(page, 0, "Card One")
    add_card(page, 0, "Card Two")
    open_card_and_set_priority(page, "Card Two", "high")

    page.locator(".filter-btn", has_text="High").click()
    page.wait_for_timeout(300)
    assert not is_card_visible(page, "Card One"), "Medium card should be hidden"

    page.locator(".filter-btn", has_text="All").click()
    page.wait_for_timeout(300)
    assert is_card_visible(page, "Card One"), "After 'All', medium card should be visible"
    assert is_card_visible(page, "Card Two"), "After 'All', high card should be visible"


def test_clear_filters_resets_search_and_priority(page: Page, base_url: str):
    """Clear filters button resets search text and priority filter."""
    add_card(page, 0, "Clearable Card")

    # Apply search and priority filter
    search = page.locator("#search-input")
    search.fill("nonexistent")
    page.wait_for_timeout(200)
    page.locator(".filter-btn", has_text="Urgent").click()
    page.wait_for_timeout(200)

    # Clear filters button should appear
    clear_btn = page.locator("#clear-filters-btn, button:has-text('Clear')")
    expect(clear_btn).to_be_visible()
    clear_btn.click()
    page.wait_for_timeout(300)

    # All cards should be visible again
    assert is_card_visible(page, "Clearable Card"), "Card should be visible after clearing filters"
    # Search input should be empty
    expect(page.locator("#search-input")).to_have_value("")


def test_search_and_priority_combine_with_and_logic(page: Page, base_url: str):
    """Search and priority filter combine with AND logic."""
    add_card(page, 0, "Urgent Alpha")
    add_card(page, 0, "Urgent Beta")
    add_card(page, 0, "Medium Alpha")
    open_card_and_set_priority(page, "Urgent Alpha", "urgent")
    open_card_and_set_priority(page, "Urgent Beta", "urgent")

    # Search "Alpha" AND filter "Urgent" => only "Urgent Alpha" should show
    page.locator("#search-input").fill("Alpha")
    page.wait_for_timeout(200)
    page.locator(".filter-btn", has_text="Urgent").click()
    page.wait_for_timeout(300)

    assert is_card_visible(page, "Urgent Alpha"), "Urgent Alpha matches both filters"
    assert not is_card_visible(page, "Urgent Beta"), "Urgent Beta doesn't match search"
    assert not is_card_visible(page, "Medium Alpha"), "Medium Alpha doesn't match priority filter"
