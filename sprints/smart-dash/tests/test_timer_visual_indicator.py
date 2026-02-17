"""
Test for the pomodoro timer visual running indicator.

Verifies CE-7-10: Timer must show clear visual indication of whether it's running or paused.
"""
import pytest
from playwright.sync_api import Page, expect


def test_timer_running_indicator(page: Page, http_server: str):
    """
    CE-7-10: Timer displays visual running indicator.

    Verifies that when the timer is running vs paused, there are clear visual differences:
    - Start button gets 'active' class (green highlight) when timer is running
    - Timer display gets 'running' class (pulsing animation) when timer is running
    - Start button is disabled when timer is running
    - Pause button is disabled when timer is not running
    """
    page.goto(f"{http_server}/index.html")

    timer_display = page.locator("#timer-display")
    start_button = page.locator("#timer-start")
    pause_button = page.locator("#timer-pause")

    # Initial state: timer is paused
    # Start button should NOT have 'active' class
    assert "active" not in (start_button.get_attribute("class") or ""), \
        "Start button should not have 'active' class when paused"

    # Timer display should NOT have 'running' class
    assert "running" not in (timer_display.get_attribute("class") or ""), \
        "Timer display should not have 'running' class when paused"

    # Start button should be enabled, Pause button should be disabled
    expect(start_button).to_be_enabled()
    expect(pause_button).to_be_disabled()

    # Click Start
    start_button.click()

    # Wait a moment for state to update
    page.wait_for_timeout(200)

    # RUNNING state: Start button should have 'active' class
    start_class = start_button.get_attribute("class") or ""
    assert "active" in start_class, \
        f"Start button should have 'active' class when running, got: {start_class}"

    # Timer display should have 'running' class (for pulsing animation)
    display_class = timer_display.get_attribute("class") or ""
    assert "running" in display_class, \
        f"Timer display should have 'running' class when running, got: {display_class}"

    # Start button should be disabled, Pause button should be enabled
    expect(start_button).to_be_disabled()
    expect(pause_button).to_be_enabled()

    # Verify the Start button has the green active styling (computed style)
    start_bg = page.evaluate("""
        () => {
            const btn = document.getElementById('timer-start');
            return window.getComputedStyle(btn).backgroundColor;
        }
    """)
    # The green color should be rgb(34, 197, 94) base or rgb(22, 163, 74) hover
    # Both are green colors from Tailwind's green palette
    assert ("rgb(34, 197, 94)" in start_bg or "rgb(22, 163, 74)" in start_bg), \
        f"Start button should have green background when active, got: {start_bg}"

    # Click Pause
    pause_button.click()

    # Wait a moment for state to update
    page.wait_for_timeout(200)

    # PAUSED state: Start button should NOT have 'active' class
    start_class_after_pause = start_button.get_attribute("class") or ""
    assert "active" not in start_class_after_pause, \
        f"Start button should not have 'active' class when paused, got: {start_class_after_pause}"

    # Timer display should NOT have 'running' class
    display_class_after_pause = timer_display.get_attribute("class") or ""
    assert "running" not in display_class_after_pause, \
        f"Timer display should not have 'running' class when paused, got: {display_class_after_pause}"

    # Start button should be enabled, Pause button should be disabled
    expect(start_button).to_be_enabled()
    expect(pause_button).to_be_disabled()


def test_timer_at_a_glance(page: Page, http_server: str):
    """
    CE-7-10: Verify developer can see timer state at a glance.

    The value proposition is that a developer can look at the dashboard
    and immediately know if the timer is running or paused without having
    to watch the countdown numbers change.
    """
    page.goto(f"{http_server}/index.html")

    timer_display = page.locator("#timer-display")
    start_button = page.locator("#timer-start")
    pause_button = page.locator("#timer-pause")

    # Start the timer
    start_button.click()
    page.wait_for_timeout(500)

    # After 2 seconds, take a snapshot of the visual state
    page.wait_for_timeout(2000)

    # Visual indicators should be present
    # 1. Pulsing animation on timer display (running class)
    assert "running" in (timer_display.get_attribute("class") or ""), \
        "Timer display should have pulsing animation when running"

    # 2. Green active button (active class)
    assert "active" in (start_button.get_attribute("class") or ""), \
        "Start button should have green highlight when running"

    # 3. Disabled start button, enabled pause button
    expect(start_button).to_be_disabled()
    expect(pause_button).to_be_enabled()

    # Pause the timer
    pause_button.click()
    page.wait_for_timeout(500)

    # Visual indicators should be absent
    # 1. No pulsing animation
    assert "running" not in (timer_display.get_attribute("class") or ""), \
        "Timer display should not pulse when paused"

    # 2. No green highlight
    assert "active" not in (start_button.get_attribute("class") or ""), \
        "Start button should not be highlighted when paused"

    # 3. Enabled start button, disabled pause button
    expect(start_button).to_be_enabled()
    expect(pause_button).to_be_disabled()


def test_timer_animation_present(page: Page, http_server: str):
    """
    CE-7-10: Verify the pulse animation is actually defined in CSS.

    Checks that the @keyframes pulse animation exists and is applied
    to the .running class.
    """
    page.goto(f"{http_server}/index.html")

    # Check that the CSS animation is defined
    has_animation = page.evaluate("""
        () => {
            // Start the timer to add the 'running' class
            document.getElementById('timer-start').click();

            // Wait a tick
            return new Promise((resolve) => {
                setTimeout(() => {
                    const display = document.getElementById('timer-display');
                    const computedStyle = window.getComputedStyle(display);

                    // Check if animation is applied
                    const animation = computedStyle.animation || computedStyle.webkitAnimation;

                    resolve({
                        hasAnimation: animation && animation !== 'none',
                        animationName: computedStyle.animationName,
                        className: display.className
                    });
                }, 100);
            });
        }
    """)

    # Verify animation is applied
    assert has_animation["hasAnimation"], \
        f"Pulse animation should be applied when timer is running. Got: {has_animation}"
    assert "pulse" in has_animation["animationName"], \
        f"Animation name should be 'pulse', got: {has_animation['animationName']}"
    assert "running" in has_animation["className"], \
        f"Timer display should have 'running' class, got: {has_animation['className']}"
