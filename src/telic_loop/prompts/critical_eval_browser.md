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

2. **Find the start command**: Look in `package.json` (scripts.start, scripts.dev), `README.md`, or the project's main entry point in `{SPRINT_DIR}`.

3. **Start the server**: Use Bash to run the start command in the background (append `&`). Wait a few seconds for it to boot, then navigate to the URL.

4. **Health check**: After navigating, take a screenshot to confirm the app loaded. If you see a blank page or error, check the terminal output and retry.

### Step B: Interactive Evaluation Workflow

For each VISION promise that involves user interaction:

1. **Navigate** to the relevant page or entry point
2. **Snapshot** the accessibility tree — check for proper labels, roles, and structure
3. **Screenshot** the initial state — check visual hierarchy, layout, contrast
4. **Interact** as the user would — click buttons, fill forms, select options, press keys
5. **Screenshot the result** — verify the outcome matches what the VISION promised
6. **Test error paths** — enter invalid data, leave required fields empty, try edge cases

### Step C: Visual Evaluation

When reviewing screenshots, evaluate:

- **Visual hierarchy**: Is it clear what's most important on each screen?
- **Color contrast**: Can text be read easily? Are interactive elements distinguishable?
- **Alignment and spacing**: Are elements consistently aligned? Is spacing uniform?
- **Responsive states**: Does the layout make sense at the current viewport size?
- **Loading/transition states**: Are there jarring jumps or missing loading indicators?

### Step D: Burst Screenshots for Transitions

To catch animation and loading issues, use burst screenshots around interactions:

1. **Before**: Screenshot the initial state
2. **Action**: Click/submit/navigate
3. **Immediate**: Screenshot right after the action (catches loading/transition state)
4. **Wait**: `browser_wait` for 1-2 seconds
5. **Settled**: Screenshot the final state

This catches: missing loading spinners, layout shifts, flash of unstyled content, broken animations.

### Step E: Responsive Testing

Resize the viewport and screenshot at each breakpoint to check layout adaptation:

1. **Desktop**: `browser_resize` to 1280x720 — screenshot
2. **Tablet**: `browser_resize` to 768x1024 — screenshot
3. **Mobile**: `browser_resize` to 375x667 — screenshot

Report any breakpoint where the layout breaks, overflows, or becomes unusable.

### Step F: Cleanup

When you are done evaluating:

- Kill any servers you started (use Bash: `kill %1` or find the PID and kill it)
- Do NOT leave background processes running
