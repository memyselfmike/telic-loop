"""
Edge-case and UX evaluation for Developer Focus Dashboard.
Starts HTTP server on port 8789, runs Playwright tests, saves screenshots.
"""
import http.server
import threading
import os
import json
import time

SPRINT_DIR = "E:/Projects/telic-loop/sprints/smart-dash"
SCREENSHOT_DIR = os.path.join(SPRINT_DIR, "eval_screenshots")
PORT = 8789
URL = f"http://localhost:{PORT}/index.html"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

def start_server():
    os.chdir(SPRINT_DIR)
    srv = http.server.HTTPServer(("", PORT), QuietHandler)
    srv.serve_forever()

threading.Thread(target=start_server, daemon=True).start()
time.sleep(0.5)
print("Server started on port", PORT)

from playwright.sync_api import sync_playwright

results = {}

def ss(page, name):
    p = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    page.screenshot(path=p)
    return p

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    # TEST 1: Empty task submission
    print("=" * 60)
    print("TEST 1: Empty task submission")
    page = browser.new_page(viewport={"width": 1024, "height": 768})
    page.goto(URL)
    page.evaluate("localStorage.clear()")
    page.reload()
    page.wait_for_selector("#task-input")
    count_before = page.inner_text("#task-count")
    page.click("#task-input")
    page.keyboard.press("Enter")
    page.wait_for_timeout(300)
    count_after = page.inner_text("#task-count")
    task_items_after = page.query_selector_all(".task-item")
    empty_blocked = (len(task_items_after) == 0)
    results["test1_empty_submit"] = {
        "blocked": empty_blocked,
        "count_before": count_before,
        "count_after": count_after,
        "task_count": len(task_items_after),
    }
    print(f"  Empty submit blocked: {empty_blocked}")
    print(f"  Count before: {count_before}, after: {count_after}, items: {len(task_items_after)}")
    ss(page, "01_empty_submit")
    page.close()

    # TEST 2: Whitespace-only task submission
    print("=" * 60)
    print("TEST 2: Whitespace-only task submission")
    page = browser.new_page(viewport={"width": 1024, "height": 768})
    page.goto(URL)
    page.evaluate("localStorage.clear()")
    page.reload()
    page.wait_for_selector("#task-input")
    page.fill("#task-input", "     ")
    page.keyboard.press("Enter")
    page.wait_for_timeout(300)
    task_items = page.query_selector_all(".task-item")
    ws_blocked = (len(task_items) == 0)
    results["test2_whitespace_submit"] = {
        "blocked": ws_blocked,
        "task_count": len(task_items),
    }
    print(f"  Whitespace-only blocked: {ws_blocked}")
    print(f"  Task items rendered: {len(task_items)}")
    ss(page, "02_whitespace_submit")
    page.close()

    # TEST 3: Delete button click-target size
    print("=" * 60)
    print("TEST 3: Delete button click-target size")
    page = browser.new_page(viewport={"width": 1024, "height": 768})
    page.goto(URL)
    page.evaluate("localStorage.clear()")
    page.reload()
    page.wait_for_selector("#task-input")
    page.fill("#task-input", "Test task for delete button")
    page.keyboard.press("Enter")
    page.wait_for_timeout(300)
    del_btn = page.query_selector(".task-item button")
    box = del_btn.bounding_box()
    computed = page.evaluate("""() => {
        const btn = document.querySelector('.task-item button');
        const s = getComputedStyle(btn);
        return {
            width: btn.offsetWidth,
            height: btn.offsetHeight,
            padding: s.padding,
            fontSize: s.fontSize,
        };
    }""")
    w, h = box["width"], box["height"]
    touch_friendly = (w >= 44 and h >= 44)
    results["test3_delete_button_size"] = {
        "bounding_box_w": w,
        "bounding_box_h": h,
        "computed": computed,
        "touch_friendly_44px": touch_friendly,
    }
    print(f"  Bounding box: {w:.1f} x {h:.1f} px")
    print(f"  Computed: {computed}")
    print(f"  Touch-friendly (>=44x44): {touch_friendly}")
    ss(page, "03_delete_button")
    page.close()

    # TEST 4: Pause button while timer not running
    print("=" * 60)
    print("TEST 4: Pause button while timer is NOT running")
    page = browser.new_page(viewport={"width": 1024, "height": 768})
    page.goto(URL)
    page.wait_for_selector("#timer-pause")
    pause_disabled = page.get_attribute("#timer-pause", "disabled")
    start_disabled = page.get_attribute("#timer-start", "disabled")
    display_before = page.inner_text("#timer-display")
    page.click("#timer-pause", force=True)
    page.wait_for_timeout(300)
    display_after = page.inner_text("#timer-display")
    results["test4_pause_while_stopped"] = {
        "pause_disabled_attr": pause_disabled,
        "start_disabled_attr": start_disabled,
        "display_before": display_before,
        "display_after": display_after,
        "pause_is_disabled": pause_disabled is not None,
    }
    print(f"  Pause disabled attr: {pause_disabled}")
    print(f"  Start disabled attr: {start_disabled}")
    print(f"  Pause is properly disabled: {pause_disabled is not None}")
    print(f"  Display before/after click: {display_before} / {display_after}")
    ss(page, "04_pause_while_stopped")
    page.close()

    # TEST 5: Weather help text line reference accuracy
    print("=" * 60)
    print("TEST 5: Weather help text line reference")
    page = browser.new_page(viewport={"width": 1024, "height": 768})
    page.goto(URL)
    page.wait_for_timeout(500)
    help_text = page.inner_text("#weather-help")
    help_visible = page.is_visible("#weather-help")
    with open(os.path.join(SPRINT_DIR, "index.html"), "r") as fh:
        lines = fh.readlines()
    line_83_content = lines[82].strip() if len(lines) >= 83 else "FILE TOO SHORT"
    api_key_line = None
    for i, line in enumerate(lines, 1):
        if "WEATHER_API_KEY" in line and "=" in line:
            if "WEATHER_API_KEY=" in line:
                api_key_line = i
                break
    help_says_83 = "line 83" in help_text
    reference_accurate = (api_key_line == 83)
    results["test5_line_reference"] = {
        "help_text": help_text,
        "help_visible": help_visible,
        "help_says_line_83": help_says_83,
        "actual_line_83": line_83_content,
        "actual_api_key_line": api_key_line,
        "reference_accurate": reference_accurate,
    }
    print(f"  Help visible: {help_visible}")
    print(f"  Help says line 83: {help_says_83}")
    print(f"  Actual line 83 content: {line_83_content!r}")
    print(f"  WEATHER_API_KEY actually defined on line: {api_key_line}")
    print(f"  Reference accurate: {reference_accurate}")
    ss(page, "05_weather_help")
    page.close()

    # TEST 6: Long task text at 400px viewport
    print("=" * 60)
    print("TEST 6: Long task text at 400px viewport")
    page = browser.new_page(viewport={"width": 400, "height": 768})
    page.goto(URL)
    page.evaluate("localStorage.clear()")
    page.reload()
    page.wait_for_selector("#task-input")
    long_text = "This is an extremely long task title that should test text overflow behavior when the viewport is narrow at 400px wide -- does it wrap or clip or overflow the container?"
    page.fill("#task-input", long_text)
    page.keyboard.press("Enter")
    page.wait_for_timeout(300)
    overflow_info = page.evaluate("""() => {
        const item = document.querySelector('.task-item');
        const span = document.querySelector('.task-item span');
        const widget = document.getElementById('task-widget');
        if (!item || !span) return null;
        const sStyle = getComputedStyle(span);
        return {
            item_scrollWidth: item.scrollWidth,
            item_clientWidth: item.clientWidth,
            item_overflowX: item.scrollWidth > item.clientWidth,
            span_scrollWidth: span.scrollWidth,
            span_clientWidth: span.clientWidth,
            span_overflow: sStyle.overflow,
            span_textOverflow: sStyle.textOverflow,
            span_wordBreak: sStyle.wordBreak,
            span_overflowWrap: sStyle.overflowWrap,
            widget_scrollWidth: widget.scrollWidth,
            widget_clientWidth: widget.clientWidth,
            widget_overflows: widget.scrollWidth > widget.clientWidth,
            bodyOverflow: document.body.scrollWidth > document.body.clientWidth,
        };
    }""")
    results["test6_long_task"] = {
        "text_length": len(long_text),
        "overflow_info": overflow_info,
    }
    print(f"  Task text length: {len(long_text)}")
    if overflow_info:
        print(f"  Item scrollW vs clientW: {overflow_info['item_scrollWidth']} vs {overflow_info['item_clientWidth']}")
        print(f"  Item overflows: {overflow_info['item_overflowX']}")
        print(f"  Span overflow CSS: {overflow_info['span_overflow']}")
        print(f"  Widget overflows: {overflow_info['widget_overflows']}")
        print(f"  Body overflows (horiz scrollbar): {overflow_info['bodyOverflow']}")
    ss(page, "06_long_task_400px")
    page.close()

    # TEST 7: 20 rapid task additions
    print("=" * 60)
    print("TEST 7: 20 rapid task additions")
    page = browser.new_page(viewport={"width": 400, "height": 768})
    page.goto(URL)
    page.evaluate("localStorage.clear()")
    page.reload()
    page.wait_for_selector("#task-input")
    for i in range(1, 21):
        page.fill("#task-input", f"Task number {i} for scroll test")
        page.keyboard.press("Enter")
    page.wait_for_timeout(500)
    task_items = page.query_selector_all(".task-item")
    scroll_info = page.evaluate("""() => {
        const list = document.getElementById('task-list');
        const widget = document.getElementById('task-widget');
        const body = document.body;
        const listStyle = getComputedStyle(list);
        const widgetStyle = getComputedStyle(widget);
        return {
            task_count: document.querySelectorAll('.task-item').length,
            list_scrollHeight: list.scrollHeight,
            list_clientHeight: list.clientHeight,
            list_overflowY: listStyle.overflowY,
            list_maxHeight: listStyle.maxHeight,
            widget_scrollHeight: widget.scrollHeight,
            widget_clientHeight: widget.clientHeight,
            widget_overflowY: widgetStyle.overflowY,
            widget_maxHeight: widgetStyle.maxHeight,
            body_scrollHeight: body.scrollHeight,
            body_clientHeight: body.clientHeight,
            page_scrolls: body.scrollHeight > body.clientHeight,
        };
    }""")
    results["test7_rapid_20_tasks"] = {
        "rendered_count": len(task_items),
        "scroll_info": scroll_info,
    }
    print(f"  Tasks rendered: {len(task_items)}")
    if scroll_info:
        print(f"  List overflow-y: {scroll_info['list_overflowY']}, max-height: {scroll_info['list_maxHeight']}")
        print(f"  Widget overflow-y: {scroll_info['widget_overflowY']}, max-height: {scroll_info['widget_maxHeight']}")
        print(f"  List scrollH: {scroll_info['list_scrollHeight']} vs clientH: {scroll_info['list_clientHeight']}")
        print(f"  Body scrollH: {scroll_info['body_scrollHeight']} vs clientH: {scroll_info['body_clientHeight']}")
        print(f"  Page has vertical scroll: {scroll_info['page_scrolls']}")
    ss(page, "07_20_tasks_400px")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(300)
    ss(page, "07_20_tasks_scrolled_bottom")
    page.close()

    # TEST 8: Timer pulse animation during running
    print("=" * 60)
    print("TEST 8: Timer pulse animation while running")
    page = browser.new_page(viewport={"width": 1024, "height": 768})
    page.goto(URL)
    page.wait_for_selector("#timer-start")
    page.click("#timer-start")
    page.wait_for_timeout(500)
    has_running_class = page.evaluate("document.getElementById('timer-display').classList.contains('running')")
    opacities = []
    for _ in range(8):
        opacity = page.evaluate("getComputedStyle(document.getElementById('timer-display')).opacity")
        opacities.append(float(opacity))
        page.wait_for_timeout(300)
    min_opacity = min(opacities)
    max_opacity = max(opacities)
    has_variation = (max_opacity - min_opacity) > 0.1
    results["test8_pulse_animation"] = {
        "has_running_class": has_running_class,
        "opacities_sampled": opacities,
        "min_opacity": min_opacity,
        "max_opacity": max_opacity,
        "animation_visible": has_variation,
    }
    print(f"  Has running class: {has_running_class}")
    print(f"  Opacities sampled: {opacities}")
    print(f"  Min: {min_opacity}, Max: {max_opacity}")
    print(f"  Animation variation visible: {has_variation}")
    ss(page, "08_timer_pulse_running")
    page.click("#timer-pause")
    page.click("#timer-reset")
    page.close()

    # TEST 9: Reset while timer is running
    print("=" * 60)
    print("TEST 9: Reset while timer is running")
    page = browser.new_page(viewport={"width": 1024, "height": 768})
    page.goto(URL)
    page.wait_for_selector("#timer-start")
    page.click("#timer-start")
    page.wait_for_timeout(2500)
    display_before_reset = page.inner_text("#timer-display")
    page.click("#timer-reset")
    page.wait_for_timeout(500)
    display_after_reset = page.inner_text("#timer-display")
    page.wait_for_timeout(2000)
    display_after_wait = page.inner_text("#timer-display")
    timer_stopped = (display_after_reset == display_after_wait)
    is_running_after = page.evaluate("document.getElementById('timer-display').classList.contains('running')")
    start_dis = page.get_attribute("#timer-start", "disabled")
    pause_dis = page.get_attribute("#timer-pause", "disabled")
    results["test9_reset_while_running"] = {
        "display_before_reset": display_before_reset,
        "display_after_reset": display_after_reset,
        "display_after_2s_wait": display_after_wait,
        "timer_fully_stopped": timer_stopped,
        "running_class_after_reset": is_running_after,
        "start_disabled_after_reset": start_dis,
        "pause_disabled_after_reset": pause_dis,
    }
    print(f"  Display before reset: {display_before_reset}")
    print(f"  Display after reset: {display_after_reset}")
    print(f"  Display after 2s wait: {display_after_wait}")
    print(f"  Timer fully stopped: {timer_stopped}")
    print(f"  Still has running class: {is_running_after}")
    print(f"  Start disabled after reset: {start_dis}")
    print(f"  Pause disabled after reset: {pause_dis}")
    ss(page, "09_reset_while_running")
    page.close()

    # TEST 10: Keyboard accessibility / focus styles
    print("=" * 60)
    print("TEST 10: Keyboard accessibility and focus styles")
    page = browser.new_page(viewport={"width": 1024, "height": 768})
    page.goto(URL)
    page.wait_for_selector("#timer-start")
    focus_log = []
    page.keyboard.press("Tab")
    for i in range(15):
        focused = page.evaluate("""() => {
            const el = document.activeElement;
            if (!el) return null;
            const s = getComputedStyle(el);
            return {
                tag: el.tagName,
                id: el.id || '',
                type: el.type || '',
                text: (el.textContent || '').trim().substring(0, 30),
                outline: s.outline,
                outlineStyle: s.outlineStyle,
                outlineWidth: s.outlineWidth,
                outlineColor: s.outlineColor,
                boxShadow: s.boxShadow,
            };
        }""")
        focus_log.append(focused)
        page.keyboard.press("Tab")
    start_reachable = any(
        f and f.get("id") == "timer-start"
        for f in focus_log
    )
    button_entries = [f for f in focus_log if f and f.get("tag") == "BUTTON"]
    has_custom_focus = any(
        f.get("outlineStyle") not in ("none", "") or f.get("boxShadow") not in ("none", "")
        for f in button_entries
    )
    outlines_removed = any(
        f and f.get("outlineStyle") == "none" and f.get("boxShadow") in ("none", "")
        for f in button_entries
    )
    page.focus("#timer-start")
    page.wait_for_timeout(200)
    ss(page, "10_focus_start_button")
    focus_on_input = page.evaluate("""() => {
        const inp = document.getElementById('task-input');
        inp.focus();
        const s = getComputedStyle(inp);
        return {
            outline: s.outline,
            outlineStyle: s.outlineStyle,
            borderColor: s.borderColor,
        };
    }""")
    ss(page, "10_focus_task_input")
    focus_order = []
    for f in focus_log:
        if f:
            focus_order.append(f["tag"] + "#" + f["id"])
        else:
            focus_order.append("None")
    results["test10_keyboard_accessibility"] = {
        "start_button_reachable_by_tab": start_reachable,
        "button_focus_count": len(button_entries),
        "has_custom_focus_style": has_custom_focus,
        "browser_default_outlines_removed": outlines_removed,
        "task_input_focus_styles": focus_on_input,
        "focus_order": focus_order,
    }
    print(f"  Start button reachable by Tab: {start_reachable}")
    print(f"  Focus order: {focus_order}")
    for f in focus_log:
        if f:
            ident = f["tag"] + "#" + f["id"]
            print(f"    {ident}: outline={f['outline']}, boxShadow={f['boxShadow']}")
    print(f"  Button focus entries: {len(button_entries)}")
    print(f"  Has custom focus style on buttons: {has_custom_focus}")
    print(f"  Browser outlines removed (bad for a11y): {outlines_removed}")
    print(f"  Task input focus: {focus_on_input}")
    page.close()

    # SUMMARY
    print()
    print("=" * 60)
    print("SUMMARY OF ALL TESTS")
    print("=" * 60)
    browser.close()

# Save full results
results_path = os.path.join(SCREENSHOT_DIR, "eval_results.json")
with open(results_path, "w") as f:
    json.dump(results, f, indent=2, default=str)
print(f"Full results saved to: {results_path}")
print(f"Screenshots saved to: {SCREENSHOT_DIR}")
