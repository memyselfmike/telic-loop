from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch()

    # Test 1: Timer running state - is there any visual indicator that timer is running vs paused?
    page = browser.new_page(viewport={'width': 400, 'height': 900})
    page.goto('http://localhost:8000/index.html')
    page.wait_for_timeout(1000)

    # Check Start button style when timer is NOT running
    start_style_idle = page.evaluate('''() => {
        const btn = document.getElementById('timer-start');
        const style = window.getComputedStyle(btn);
        return { bg: style.backgroundColor, color: style.color, opacity: style.opacity }
    }''')
    print('Start button idle:', json.dumps(start_style_idle))

    # Start timer
    page.locator('#timer-start').click()
    page.wait_for_timeout(500)

    # Check Start button style when timer IS running
    start_style_running = page.evaluate('''() => {
        const btn = document.getElementById('timer-start');
        const style = window.getComputedStyle(btn);
        return { bg: style.backgroundColor, color: style.color, opacity: style.opacity }
    }''')
    print('Start button running:', json.dumps(start_style_running))
    different = (start_style_idle != start_style_running)
    print('Buttons look different?', different)

    # Test 2: Can you tell whether the timer is paused or just hasn't started?
    page.locator('#timer-pause').click()
    page.wait_for_timeout(500)
    timer_after_pause = page.locator('#timer-display').text_content()
    mode_after_pause = page.locator('#timer-mode').text_content()
    print('After pause - timer:', timer_after_pause, 'mode:', mode_after_pause)

    # Test 3: What happens if you click Start while already running?
    page.locator('#timer-start').click()
    page.wait_for_timeout(200)
    page.locator('#timer-start').click()
    page.wait_for_timeout(2000)
    timer_after_double = page.locator('#timer-display').text_content()
    print('After double-start timer:', timer_after_double)

    # Check if multiple intervals were created (would cause timer to tick faster)
    page.locator('#timer-reset').click()
    page.locator('#timer-start').click()
    page.wait_for_timeout(100)
    page.locator('#timer-start').click()
    page.wait_for_timeout(100)
    page.locator('#timer-start').click()
    page.wait_for_timeout(3000)
    timer_val = page.locator('#timer-display').text_content()
    print('After triple-start + 3s:', timer_val, '(should be ~24:57 if no duplicate intervals)')

    # Test 4: Tab title - does it show useful info?
    title = page.title()
    print('Page title:', title)

    # Test 5: Keyboard accessibility - can I tab through controls?
    page.keyboard.press('Tab')
    focused = page.evaluate('document.activeElement.tagName + "#" + (document.activeElement.id || "")')
    print('First tab focus:', focused)

    page.keyboard.press('Tab')
    focused2 = page.evaluate('document.activeElement.tagName + "#" + (document.activeElement.id || "")')
    print('Second tab focus:', focused2)

    # Test 6: Does the task input have any visual focus indicator?
    page2 = browser.new_page(viewport={'width': 400, 'height': 900})
    page2.goto('http://localhost:8000/index.html')
    page2.wait_for_timeout(1000)

    page2.locator('#task-input').focus()
    focus_border = page2.evaluate('''() => {
        const el = document.getElementById('task-input');
        const style = window.getComputedStyle(el);
        return { borderColor: style.borderColor, outline: style.outline, boxShadow: style.boxShadow }
    }''')
    print('Task input focused style:', json.dumps(focus_border))

    # Test 7: Can you add a task by clicking (no button, only Enter)?
    has_add_button = page2.locator('#task-widget button').count()
    print('Task add buttons visible (before adding tasks):', has_add_button)

    # Test 8: Weather help link - is it clickable?
    help_link = page2.locator('#weather-help a')
    link_count = help_link.count()
    print('Weather help links count:', link_count)
    if link_count > 0:
        href = help_link.first.get_attribute('href')
        target = help_link.first.get_attribute('target')
        print('Link href:', href, 'target:', target)

    # Test 9: Check timer-mode color with the fix applied (CE-4-7)
    timer_mode_styles = page2.evaluate('''() => {
        const el = document.getElementById('timer-mode');
        const style = window.getComputedStyle(el);
        return { color: style.color, fontSize: style.fontSize, fontWeight: style.fontWeight }
    }''')
    print('Timer mode styles:', json.dumps(timer_mode_styles))

    # Test 10: What does the page look like at extreme narrow width (320px)?
    page3 = browser.new_page(viewport={'width': 320, 'height': 900})
    page3.goto('http://localhost:8000/index.html')
    page3.wait_for_timeout(1000)
    scroll_320 = page3.evaluate('document.documentElement.scrollWidth')
    print('Scroll width at 320px:', scroll_320)
    page3.screenshot(path='sprints/smart-dash/tests/screenshot_320px.png', full_page=True)

    # Test 11: Check if completed tasks have accessible strikethrough
    page4 = browser.new_page(viewport={'width': 400, 'height': 900})
    page4.goto('http://localhost:8000/index.html')
    page4.wait_for_timeout(1000)
    page4.locator('#task-input').fill('Test task')
    page4.locator('#task-input').press('Enter')
    page4.locator('.task-item input[type=checkbox]').check()

    completed_style = page4.evaluate('''() => {
        const span = document.querySelector('.task-item.completed span');
        const style = window.getComputedStyle(span);
        return { textDecoration: style.textDecorationLine, color: style.color }
    }''')
    print('Completed task style:', json.dumps(completed_style))

    # Test 12: Check delete button accessibility
    delete_btn_aria = page4.locator('.task-item button').first.get_attribute('aria-label')
    print('Delete button aria-label:', delete_btn_aria)

    browser.close()
    print()
    print('All edge case tests complete.')
