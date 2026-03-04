## Browser-Based Interactive Evaluation

You have a full Playwright browser available via MCP tools. You MUST use it to interact with the web application as the target user would — navigating, clicking, filling forms, and verifying visual outcomes. Screenshots are your evidence.

### Available Browser Tools

| Tool | Purpose |
|------|---------|
| `browser_navigate` | Go to a URL |
| `browser_click` | Click an element (by accessible name/role or coordinates) |
| `browser_fill` | Type into an input field |
| `browser_snapshot` | Get the accessibility tree (structure, labels, roles) |
| `browser_take_screenshot` | Capture a visual screenshot |
| `browser_select_option` | Select from a dropdown |
| `browser_go_back` / `browser_go_forward` | Navigation history |
| `browser_wait` | Wait for content to load or animations to settle |
| `browser_press_key` | Press keyboard keys (Enter, Tab, Escape, shortcuts) |
| `browser_resize` | Change viewport dimensions |
| `browser_tab_list` / `browser_tab_new` / `browser_tab_select` / `browser_tab_close` | Multi-tab management |

### Step A: Start the Application

1. **Check if already running**: The Sprint Context includes known services:
```
{SERVICES_JSON}
```
   If a service URL is listed, try navigating to it first. If it loads, skip to Step B.

2. **Docker mode**: If the system prompt says Docker mode is ACTIVE, start services using the Docker management scripts: `bash {SPRINT_DIR}/.telic-docker/docker-up.sh` (or the path shown in the Docker Environment section). This is preferred over starting services manually.

3. **Find the start command** (non-Docker fallback): Look in `package.json` (scripts.start, scripts.dev), `README.md`, or the project's main entry point in `{SPRINT_DIR}`.

4. **Start the server**: Use Bash to run the start command in the background (append `&`). Wait a few seconds for it to boot, then navigate to the URL.

5. **Health check**: After navigating, take a screenshot to confirm the app loaded. If you see a blank page or error, check the terminal output and retry.

### Step B: Route Discovery (MANDATORY FIRST STEP)

Before testing any features, you MUST discover and visit ALL routes/views:

1. **Screenshot the main page** after it loads
2. **Identify ALL navigation elements** — tabs, links, menu items, sidebar entries, footer links
3. **Visit EVERY route/tab/view** and screenshot each one — even if it looks empty or broken
4. **Build a route manifest**: list every view you found and its URL/path
5. Only THEN begin detailed feature testing on each view

**Missing a tab with broken features is an evaluation failure.** If the app has 4 navigation tabs, you MUST visit ALL FOUR before starting detailed testing.

### Step C: Interactive Evaluation Workflow

For each VISION promise that involves user interaction:

1. **Navigate** to the relevant page or entry point
2. **Snapshot** the accessibility tree — check for proper labels, roles, and structure
3. **Screenshot** the initial state — check visual hierarchy, layout, contrast
4. **Interact** as the user would — click buttons, fill forms, select options, press keys
5. **Screenshot the result** — verify the outcome matches what the VISION promised
6. **Test error paths** — enter invalid data, leave required fields empty, try edge cases

### Step D: Data Lifecycle Testing

For every CRUD feature visible in the UI:

1. **CREATE** — Use the UI to create a new item. Verify it appears in the relevant list/view.
2. **READ** — Verify all fields display correctly, including edge cases (long names, special characters).
3. **UPDATE** — Edit the item. Verify changes persist after navigating away and coming back. Refresh the page and verify.
4. **DELETE** — Delete the item. Verify it's removed from the list. Check that related data (references, aggregations) are cleaned up.
5. **EMPTY STATE** — What shows when there is no data? Is it helpful or just blank?

### Step E: Cross-View Verification

After creating data in one view, verify it propagates correctly:

1. Navigate to other views that should display that data
2. Verify data appears correctly in all relevant views (e.g., data created in one tab should appear in related tabs that reference it)
3. Verify aggregations and summaries update correctly (totals, counts, charts)
4. Test that filtering, sorting, and searching reflect the current data state

### Step F: Visual Evaluation

When reviewing screenshots, evaluate:

- **Visual hierarchy**: Is it clear what's most important on each screen?
- **Color contrast**: Can text be read easily? Are interactive elements distinguishable?
- **Alignment and spacing**: Are elements consistently aligned? Is spacing uniform?
- **Responsive states**: Does the layout make sense at the current viewport size?
- **Loading/transition states**: Are there jarring jumps or missing loading indicators?

### Step G: Burst Screenshots for Transitions

To catch animation and loading issues, use burst screenshots around interactions:

1. **Before**: Screenshot the initial state
2. **Action**: Click/submit/navigate
3. **Immediate**: Screenshot right after the action (catches loading/transition state)
4. **Wait**: `browser_wait` for 1-2 seconds
5. **Settled**: Screenshot the final state

This catches: missing loading spinners, layout shifts, flash of unstyled content, broken animations.

### Step H: Responsive Testing

Resize the viewport and screenshot at each breakpoint to check layout adaptation:

1. **Desktop**: `browser_resize` to 1280x720 — screenshot
2. **Tablet**: `browser_resize` to 768x1024 — screenshot
3. **Mobile**: `browser_resize` to 375x667 — screenshot

Report any breakpoint where the layout breaks, overflows, or becomes unusable.

### Step I: Cleanup

When you are done evaluating:

- Kill any servers you started (use Bash: `kill %1` or find the PID and kill it)
- Do NOT leave background processes running
