"""
test_board_structure.py — Verifies the board loads with the correct visual structure.

PRD Reference: Section 2 (Board Structure), Section 10 (Visual Design)
Vision Goal: "See their work at a glance" — three columns immediately visible
"""
import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(autouse=True)
def collect_console_errors(page: Page):
    errors = []
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    yield errors
    assert errors == [], f"Console errors detected: {errors}"


def test_three_columns_present(page: Page, base_url: str):
    """Board loads with exactly three columns: To Do, In Progress, Done."""
    columns = page.locator(".column")
    expect(columns).to_have_count(3)


def test_column_names(page: Page, base_url: str):
    """Each column has the correct name."""
    names = page.locator(".column-name")
    expect(names.nth(0)).to_have_text("To Do")
    expect(names.nth(1)).to_have_text("In Progress")
    expect(names.nth(2)).to_have_text("Done")


def test_column_count_badges_start_at_zero(page: Page, base_url: str):
    """Each column shows (0) card count badge on a fresh empty board."""
    badges = page.locator(".card-count-badge")
    expect(badges).to_have_count(3)
    for i in range(3):
        expect(badges.nth(i)).to_have_text("(0)")


def test_add_card_buttons_present(page: Page, base_url: str):
    """Each column has an add-card button with aria-label."""
    add_btns = page.locator(".add-card-btn")
    expect(add_btns).to_have_count(3)
    for i in range(3):
        label = add_btns.nth(i).get_attribute("aria-label")
        assert label is not None and len(label) > 0, f"Column {i} add button missing aria-label"


def test_search_bar_present(page: Page, base_url: str):
    """Search bar is present with correct placeholder."""
    search = page.locator("#search-input")
    expect(search).to_be_visible()
    placeholder = search.get_attribute("placeholder")
    assert "Search" in placeholder, f"Search bar placeholder missing 'Search': {placeholder}"


def test_priority_filter_buttons_present(page: Page, base_url: str):
    """Priority filter row contains All, Low, Medium, High, Urgent buttons."""
    expected = ["All", "Low", "Medium", "High", "Urgent"]
    for label in expected:
        btn = page.locator(f".filter-btn:has-text('{label}')")
        expect(btn).to_be_visible()


def test_dark_theme_colors(page: Page, base_url: str):
    """Board has correct dark theme background color."""
    bg_color = page.evaluate("() => getComputedStyle(document.body).backgroundColor")
    # #0d1117 = rgb(13, 17, 23)
    assert "13" in bg_color or "0d1117" in bg_color.lower() or bg_color == "rgb(13, 17, 23)", \
        f"Body background not dark theme (#0d1117): got {bg_color}"


def test_columns_side_by_side_at_desktop(page: Page, base_url: str):
    """At 1024px width, columns are displayed side-by-side (not stacked)."""
    page.set_viewport_size({"width": 1024, "height": 768})
    columns = page.locator(".column")
    expect(columns).to_have_count(3)

    boxes = [columns.nth(i).bounding_box() for i in range(3)]
    # Side-by-side means columns have different x positions
    assert boxes[0]["x"] < boxes[1]["x"], "Columns not side-by-side at 1024px"
    assert boxes[1]["x"] < boxes[2]["x"], "Columns not side-by-side at 1024px"


def test_columns_stacked_at_mobile(page: Page, base_url: str):
    """At 375px width, columns stack vertically."""
    page.set_viewport_size({"width": 375, "height": 667})
    page.reload()

    columns = page.locator(".column")
    expect(columns).to_have_count(3)

    boxes = [columns.nth(i).bounding_box() for i in range(3)]
    # Stacked means all columns start at approximately the same x
    assert abs(boxes[0]["x"] - boxes[1]["x"]) < 10, \
        f"Columns not stacked at 375px: x positions {[b['x'] for b in boxes]}"
    assert abs(boxes[1]["x"] - boxes[2]["x"]) < 10, \
        f"Columns not stacked at 375px: x positions {[b['x'] for b in boxes]}"
    # And they have different y positions (one above the other)
    assert boxes[0]["y"] < boxes[1]["y"], "Stacked columns should have increasing y positions"
