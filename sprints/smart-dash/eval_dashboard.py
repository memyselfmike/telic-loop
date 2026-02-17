import subprocess, sys, time, re
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path("E:/Projects/telic-loop/sprints/smart-dash")
SCREENSHOTS_DIR = BASE_DIR / "eval_screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)
PORT = 8787
URL = "http://localhost:" + str(PORT) + "/index.html"
observations = []

def observe(label, detail):
    entry = "[" + label + "] " + detail
    observations.append(entry)
    print(entry)

def take_ss(page, name, full_page=True):
    path = SCREENSHOTS_DIR / (name + ".png")
    page.screenshot(path=str(path), full_page=full_page)
    observe("SCREENSHOT", "Saved: " + path.name)

def parse_rgb(s):
    nums = re.findall(r"\d+", s)
    return tuple(int(n) for n in nums[:3])

def luminance(r, g, b):
    def c(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * c(r) + 0.7152 * c(g) + 0.0722 * c(b)

def main():
    observe("SETUP", "Starting HTTP server on port " + str(PORT))
    srv = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--directory", str(BASE_DIR)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    time.sleep(1.5)
    try:
        run_eval()
    finally:
        observe("SETUP", "Stopping HTTP server")
        srv.terminate()
        try:
            srv.wait(timeout=5)
        except Exception:
            srv.kill()
    print()
    print("=" * 72)
    print("FULL EVALUATION REPORT")
    print("=" * 72)
    for obs in observations:
        print(obs)
    print("=" * 72)
    print("Total observations: " + str(len(observations)))
    print("Screenshots saved to: " + str(SCREENSHOTS_DIR))
    for s in sorted(SCREENSHOTS_DIR.glob("*.png")):
        kb = s.stat().st_size / 1024
        print(f"  - {s.name} ({kb:.1f} KB)")

def run_eval():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        con400 = []
        con_main = []

        # === 400px ===
        observe("EVAL", "--- 400px width evaluation ---")
        ctx400 = browser.new_context(viewport={"width": 400, "height": 900}, device_scale_factor=2)
        pg = ctx400.new_page()
        pg.on("console", lambda msg: con400.append({"type": msg.type, "text": msg.text}))
        pg.goto(URL, wait_until="networkidle")
        time.sleep(1)
        take_ss(pg, "01_initial_400px")

        has_hs = pg.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
        sw = pg.evaluate("document.documentElement.scrollWidth")
        cw = pg.evaluate("document.documentElement.clientWidth")
        observe("400px-LAYOUT", "Horizontal scrollbar present: " + str(has_hs))
        observe("400px-LAYOUT", "scrollWidth=" + str(sw) + ", clientWidth=" + str(cw))

        widgets = pg.query_selector_all(".widget")
        observe("400px-LAYOUT", "Number of widgets: " + str(len(widgets)))
        for w in widgets:
            bb = w.bounding_box()
            if bb:
                fits = bb["x"] >= 0 and (bb["x"] + bb["width"]) <= 400
                x_val = bb["x"]
                w_val = bb["width"]
                observe("400px-LAYOUT", f"Widget x={x_val:.0f} w={w_val:.0f} fits={fits}")

        pg.close()
        ctx400.close()

        # === 1920px ===
        observe("EVAL", "--- 1920px width evaluation ---")
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        page = ctx.new_page()
        page.on("console", lambda msg: con_main.append({"type": msg.type, "text": msg.text}))
        page.goto(URL, wait_until="networkidle")
        time.sleep(1)
        take_ss(page, "02_initial_1920px")

        # Weather
        wt = page.inner_text("#weather-info")
        observe("WEATHER", "Text on first load: " + repr(wt))
        hv_js = "window.getComputedStyle(document.getElementById(" + chr(39) + "weather-help" + chr(39) + ")).display !== " + chr(39) + "none" + chr(39)
        hv = page.evaluate(hv_js)
        observe("WEATHER", "Help element visible: " + str(hv))
        if hv:
            observe("WEATHER", "Help text: " + repr(page.inner_text("#weather-help")))
            observe("WEATHER", "Help HTML: " + repr(page.inner_html("#weather-help")))

        # Clock
        ct = page.inner_text("#clock-time")
        cd = page.inner_text("#clock-date")
        observe("CLOCK", "Time: " + repr(ct))
        observe("CLOCK", "Date: " + repr(cd))
        time_ok = bool(re.match(r"^\d{2}:\d{2}:\d{2}$", ct))
        observe("CLOCK", "Time HH:MM:SS valid: " + str(time_ok))
        date_pat = r"^(Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day, (January|February|March|April|May|June|July|August|September|October|November|December) \d+$"
        date_ok = bool(re.match(date_pat, cd))
        observe("CLOCK", "Date Weekday-Month-Day valid: " + str(date_ok))

        # Timer initial
        observe("TIMER", "Initial mode: " + repr(page.inner_text("#timer-mode")))
        observe("TIMER", "Initial display: " + repr(page.inner_text("#timer-display")))
        observe("TIMER", "Initial stats: " + repr(page.inner_text("#timer-stats")))
        observe("TIMER", "Start disabled: " + str(page.get_attribute("#timer-start", "disabled") is not None))
        observe("TIMER", "Pause disabled: " + str(page.get_attribute("#timer-pause", "disabled") is not None))
        observe("TIMER", "Reset disabled: " + str(page.get_attribute("#timer-reset", "disabled") is not None))

        # Contrast
        fg_js = "window.getComputedStyle(document.getElementById(" + chr(39) + "timer-mode" + chr(39) + ")).color"
        bg_js = "window.getComputedStyle(document.getElementById(" + chr(39) + "timer-widget" + chr(39) + ")).backgroundColor"
        fg_s = page.evaluate(fg_js)
        bg_s = page.evaluate(bg_js)
        observe("CONTRAST", "Timer mode color: " + fg_s)
        observe("CONTRAST", "Timer widget bg: " + bg_s)
        fg = parse_rgb(fg_s)
        bg = parse_rgb(bg_s)
        l1 = luminance(*fg)
        l2 = luminance(*bg)
        ratio = (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)
        observe("CONTRAST", f"Contrast ratio: {ratio:.2f}:1 (WCAG AA large=3:1, normal=4.5:1)")
        observe("CONTRAST", "Large bold text (1.2rem 600wt): " + ("PASS" if ratio >= 3.0 else "FAIL"))

        # Add 3 tasks
        observe("EVAL", "--- Adding 3 tasks ---")
        ti = page.locator("#task-input")
        for name in ["Fix login bug", "Write tests", "Deploy v2"]:
            ti.fill(name)
            ti.press("Enter")
            time.sleep(0.3)
        observe("TASKS", "Count after adding 3: " + repr(page.inner_text("#task-count")))
        take_ss(page, "03_three_tasks_added")
        for i, sp in enumerate(page.query_selector_all(".task-item span")):
            observe("TASKS", "  Task " + str(i) + ": " + repr(sp.inner_text()))

        # Complete Write tests (2nd task = index 1)
        observe("EVAL", "--- Completing Write tests ---")
        cbs = page.query_selector_all(".task-item input[type=" + chr(39) + "checkbox" + chr(39) + "]")
        cbs[1].click()
        time.sleep(0.3)
        observe("TASKS", "Count after completing: " + repr(page.inner_text("#task-count")))
        for i, it in enumerate(page.query_selector_all(".task-item")):
            cls = it.get_attribute("class")
            txt = it.query_selector("span").inner_text()
            observe("TASKS", "  Task " + str(i) + ": " + repr(txt) + " classes=" + repr(cls))
        take_ss(page, "04_write_tests_completed")

        # Delete Deploy v2
        observe("EVAL", "--- Deleting Deploy v2 ---")
        del_js = "el => el.querySelector(" + chr(39) + "span" + chr(39) + ").textContent"
        for btn in page.query_selector_all(".task-item button"):
            parent = btn.evaluate_handle("el => el.parentElement")
            st = parent.evaluate(del_js)
            if st == "Deploy v2":
                btn.click()
                break
        time.sleep(0.3)
        observe("TASKS", "Count after deleting: " + repr(page.inner_text("#task-count")))
        for i, sp in enumerate(page.query_selector_all(".task-item span")):
            observe("TASKS", "  Remaining " + str(i) + ": " + repr(sp.inner_text()))
        take_ss(page, "05_deploy_v2_deleted")

        # Timer Start
        observe("EVAL", "--- Starting timer ---")
        page.click("#timer-start")
        time.sleep(2)
        observe("TIMER", "Display after 2s: " + repr(page.inner_text("#timer-display")))
        hr_js = "document.getElementById(" + chr(39) + "timer-display" + chr(39) + ").classList.contains(" + chr(39) + "running" + chr(39) + ")"
        ha_js = "document.getElementById(" + chr(39) + "timer-start" + chr(39) + ").classList.contains(" + chr(39) + "active" + chr(39) + ")"
        hr = page.evaluate(hr_js)
        ha = page.evaluate(ha_js)
        observe("TIMER", "Has running class (pulse anim): " + str(hr))
        observe("TIMER", "Start has active class (green glow): " + str(ha))
        observe("TIMER", "Start disabled while running: " + str(page.get_attribute("#timer-start", "disabled") is not None))
        observe("TIMER", "Pause enabled while running: " + str(page.get_attribute("#timer-pause", "disabled") is None))
        take_ss(page, "06_timer_running_2s")

        # Timer Pause
        observe("EVAL", "--- Pausing timer ---")
        page.click("#timer-pause")
        time.sleep(0.5)
        observe("TIMER", "Display after pause: " + repr(page.inner_text("#timer-display")))
        rr = page.evaluate(hr_js)
        observe("TIMER", "Running class removed: " + str(not rr))
        observe("TIMER", "Start re-enabled: " + str(page.get_attribute("#timer-start", "disabled") is None))
        observe("TIMER", "Pause disabled: " + str(page.get_attribute("#timer-pause", "disabled") is not None))
        take_ss(page, "07_timer_paused")

        # Timer Reset
        observe("EVAL", "--- Resetting timer ---")
        page.click("#timer-reset")
        time.sleep(0.3)
        observe("TIMER", "Display after reset: " + repr(page.inner_text("#timer-display")))
        observe("TIMER", "Mode after reset: " + repr(page.inner_text("#timer-mode")))
        take_ss(page, "08_timer_reset")

        # Accessibility
        observe("EVAL", "--- Accessibility checks ---")
        for btn in page.query_selector_all("button"):
            text = btn.inner_text().strip()
            aria = btn.get_attribute("aria-label") or ""
            ok = bool(text) or bool(aria)
            observe("A11Y", "Button text=" + repr(text) + " aria=" + repr(aria) + " accessible=" + str(ok))
        cb_sel = "input[type=" + chr(39) + "text" + chr(39) + "]"
        for inp in page.query_selector_all(cb_sel):
            ph = inp.get_attribute("placeholder") or ""
            observe("A11Y", "Text input placeholder=" + repr(ph) + " has_placeholder=" + str(bool(ph)))
        lang_attr = page.evaluate("document.documentElement.lang")
        observe("A11Y", "HTML lang attribute: " + repr(lang_attr))

        # Console
        observe("EVAL", "--- Console messages (1920px) ---")
        errs = False
        for m in con_main:
            observe("CONSOLE", "[" + m["type"] + "] " + m["text"])
            if m["type"] in ("error", "warning"):
                errs = True
        if not con_main:
            observe("CONSOLE", "No console messages captured")
        observe("CONSOLE", "Errors/warnings found: " + str(errs))
        observe("EVAL", "--- Console messages (400px) ---")
        for m in con400:
            observe("CONSOLE-400", "[" + m["type"] + "] " + m["text"])

        page.close()
        ctx.close()
        browser.close()

if __name__ == "__main__":
    main()
