"""
test_responsive.py — Verifies responsive layout at different viewport sizes.

PRD Reference: Section 9 (Responsive Design)
Vision Goal: "Use it anywhere" — desktop monitor and tablet, columns usable with touch
"""
import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(autouse=True)
def collect_console_errors(page: Page):
    errors = []
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    yield errors
    assert errors == [], f"Console errors detected: {errors}"


def test_columns_side_by_side_at_1024px(page: Page, base_url: str):
    """
    At 1024px viewport width, three columns are displayed side-by-side.
    PRD Section 9.1: Desktop >= 1024px — three columns side-by-side.
    """
    page.set_viewport_size({"width": 1024, "height": 768})
    page.reload()

    columns = page.locator(".column")
    expect(columns).to_have_count(3)

    boxes = [columns.nth(i).bounding_box() for i in range(3)]
    for b in boxes:
        assert b is not None, "Column bounding box is None"

    # Side-by-side: each column's x position increases
    assert boxes[0]["x"] < boxes[1]["x"], \
        f"Columns 0 and 1 not side-by-side at 1024px: x={[b['x'] for b in boxes]}"
    assert boxes[1]["x"] < boxes[2]["x"], \
        f"Columns 1 and 2 not side-by-side at 1024px: x={[b['x'] for b in boxes]}"

    # Columns should be roughly the same height (same y position)
    assert abs(boxes[0]["y"] - boxes[1]["y"]) < 20, "Column tops misaligned at 1024px"
    assert abs(boxes[1]["y"] - boxes[2]["y"]) < 20, "Column tops misaligned at 1024px"


def test_columns_side_by_side_at_768px(page: Page, base_url: str):
    """
    At 768px viewport width, three columns are still side-by-side.
    PRD Section 9.2: Tablet 768px-1023px — three columns side-by-side but narrower.
    """
    page.set_viewport_size({"width": 768, "height": 1024})
    page.reload()

    columns = page.locator(".column")
    expect(columns).to_have_count(3)

    boxes = [columns.nth(i).bounding_box() for i in range(3)]
    for b in boxes:
        assert b is not None, "Column bounding box is None at 768px"

    assert boxes[0]["x"] < boxes[1]["x"], \
        f"Columns not side-by-side at 768px: x={[b['x'] for b in boxes]}"
    assert boxes[1]["x"] < boxes[2]["x"], \
        f"Columns not side-by-side at 768px: x={[b['x'] for b in boxes]}"


def test_columns_stacked_at_375px(page: Page, base_url: str):
    """
    At 375px viewport width, columns stack vertically.
    PRD Section 9.3: Mobile < 768px — columns stack vertically, each full-width.
    """
    page.set_viewport_size({"width": 375, "height": 667})
    page.reload()

    columns = page.locator(".column")
    expect(columns).to_have_count(3)

    boxes = [columns.nth(i).bounding_box() for i in range(3)]
    for b in boxes:
        assert b is not None, "Column bounding box is None at 375px"

    # Stacked: columns have approximately the same x (left-aligned)
    assert abs(boxes[0]["x"] - boxes[1]["x"]) < 20, \
        f"Columns not stacked at 375px: x={[b['x'] for b in boxes]}"
    assert abs(boxes[1]["x"] - boxes[2]["x"]) < 20, \
        f"Columns not stacked at 375px: x={[b['x'] for b in boxes]}"

    # Stacked: columns have increasing y positions
    assert boxes[0]["y"] < boxes[1]["y"], \
        f"Stacked columns should have increasing y at 375px: y={[b['y'] for b in boxes]}"
    assert boxes[1]["y"] < boxes[2]["y"], \
        f"Stacked columns should have increasing y at 375px: y={[b['y'] for b in boxes]}"


def test_columns_each_full_width_at_375px(page: Page, base_url: str):
    """
    At 375px viewport, each column is approximately full-width.
    PRD Section 9.3: each column is full-width on mobile.
    """
    page.set_viewport_size({"width": 375, "height": 667})
    page.reload()

    columns = page.locator(".column")
    for i in range(3):
        box = columns.nth(i).bounding_box()
        assert box is not None
        # Each column should take up most of the viewport width (at least 80%)
        assert box["width"] >= 280, \
            f"Column {i} too narrow at 375px: width={box['width']}px (expected >= 280px)"


def test_board_usable_at_1024px(page: Page, base_url: str):
    """
    At 1024px, all interactive elements are accessible (search, filter buttons, add card).
    PRD Section 9.1: board centered with max-width container.
    """
    page.set_viewport_size({"width": 1024, "height": 768})
    page.reload()

    expect(page.locator("#search-input")).to_be_visible()
    expect(page.locator(".filter-btn", has_text="All")).to_be_visible()
    expect(page.locator(".add-card-btn").first).to_be_visible()


def test_board_usable_at_375px(page: Page, base_url: str):
    """
    At 375px, search bar, filters, and add buttons are visible and usable.
    PRD Section 9.3: board scrolls vertically on mobile.
    """
    page.set_viewport_size({"width": 375, "height": 667})
    page.reload()

    expect(page.locator("#search-input")).to_be_visible()
    expect(page.locator(".add-card-btn").first).to_be_visible()


def test_flex_direction_column_at_375px(page: Page, base_url: str):
    """
    The board's flex-direction is column (or equivalent) at 375px to stack columns.
    """
    page.set_viewport_size({"width": 375, "height": 667})
    page.reload()

    # Either the board wrapper or a parent element should have flex-direction: column
    flex_dir = page.evaluate("""
        () => {
            const board = document.getElementById('board');
            if (!board) return null;
            return getComputedStyle(board).flexDirection;
        }
    """)
    assert flex_dir == "column", \
        f"Board flex-direction should be 'column' at 375px, got: '{flex_dir}'"
