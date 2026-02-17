"""Quick integration verification test for the dashboard"""
import pytest
from playwright.sync_api import Page, expect

def test_all_widgets_present(page: Page):
    """Verify all four widgets are present and rendering"""
    page.goto("http://localhost:8000/index.html")
    
    # Check all four widgets exist
    expect(page.locator("#clock-widget")).to_be_visible()
    expect(page.locator("#weather-widget")).to_be_visible()
    expect(page.locator("#task-widget")).to_be_visible()
    expect(page.locator("#timer-widget")).to_be_visible()
    
    # Check clock is displaying time (not placeholder)
    clock_time = page.locator("#clock-time").text_content()
    assert clock_time != "--:--:--", "Clock should display actual time"
    assert ":" in clock_time, "Clock should display time with colons"
    
    # Check weather shows fallback (no API key configured)
    weather_info = page.locator("#weather-info").text_content()
    assert weather_info == "Weather unavailable", "Weather should show fallback without API key"
    
    # Check task widget shows initial state
    task_count = page.locator("#task-count").text_content()
    assert "0 tasks" in task_count, "Task count should show 0 tasks initially"
    
    # Check timer shows default time
    timer_display = page.locator("#timer-display").text_content()
    assert timer_display == "25:00", "Timer should show 25:00 initially"
    
    # Check timer mode
    timer_mode = page.locator("#timer-mode").text_content()
    assert timer_mode == "WORK", "Timer should start in WORK mode"

def test_no_console_errors(page: Page):
    """Verify no console errors on page load"""
    errors = []
    page.on("pageerror", lambda err: errors.append(str(err)))
    
    page.goto("http://localhost:8000/index.html")
    page.wait_for_timeout(1000)
    
    assert len(errors) == 0, f"Console errors detected: {errors}"

def test_widgets_dont_interfere(page: Page):
    """Verify multiple setInterval calls work simultaneously"""
    page.goto("http://localhost:8000/index.html")
    
    # Get initial clock time
    initial_time = page.locator("#clock-time").text_content()
    
    # Wait 2 seconds
    page.wait_for_timeout(2000)
    
    # Clock should have updated
    updated_time = page.locator("#clock-time").text_content()
    assert updated_time != initial_time, "Clock should update while other widgets are active"
    
    # All widgets should still be visible and functional
    expect(page.locator("#clock-widget")).to_be_visible()
    expect(page.locator("#weather-widget")).to_be_visible()
    expect(page.locator("#task-widget")).to_be_visible()
    expect(page.locator("#timer-widget")).to_be_visible()
