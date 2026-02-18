/**
 * shopping.js — Shopping List View
 *
 * Renders items grouped by grocery_section with check-off, remove, and
 * item-count summary.  Uses window.App.el(), apiFetch(), showToast().
 */

'use strict';

/* ============================================================
   Constants
   ============================================================ */

/** Canonical display order for grocery sections. */
const SECTION_ORDER = ['produce', 'meat', 'dairy', 'pantry', 'frozen', 'other'];

/** Pretty display labels for each section key. */
const SECTION_LABELS = {
  produce: '🥦 Produce',
  meat:    '🥩 Meat & Seafood',
  dairy:   '🥛 Dairy & Eggs',
  pantry:  '🫙 Pantry',
  frozen:  '🧊 Frozen',
  other:   '📦 Other',
};

/* ============================================================
   Date Helpers (mirrors planner.js — no module bundler)
   ============================================================ */

/**
 * Return the ISO date string (YYYY-MM-DD) for the Monday of the
 * week containing today.
 * @returns {string}
 */
function getCurrentWeekMonday() {
  const d = new Date();
  // getDay(): 0=Sun, 1=Mon … 6=Sat  →  shift so Monday=0
  const dayOfWeek = (d.getDay() + 6) % 7;
  d.setDate(d.getDate() - dayOfWeek);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

/* ============================================================
   Module State
   ============================================================ */

/** @type {{ list: object|null, inflight: Set<number>, generating: boolean }} */
const shoppingState = {
  list:       null,      // ShoppingListResponse from API (or null when no list exists)
  inflight:   new Set(), // item IDs with a pending API call (prevents double-toggle)
  generating: false,     // true while POST /api/shopping/generate is in-flight
};

/* ============================================================
   Entry Point
   ============================================================ */

/**
 * Entry point called by app.js router when the user navigates to #shopping.
 */
async function renderShopping() {
  const { setAppContent, buildLoadingState } = window.App;

  // Show a loading state immediately so the user gets feedback.
  setAppContent(buildLoadingState('Loading shopping list…'));

  // Fetch the current list.  A 404 is normal (no list generated yet) — we
  // use raw fetch here so we can suppress the error toast for that case.
  try {
    const resp = await fetch('/api/shopping/current');
    if (resp.status === 404) {
      shoppingState.list = null;
    } else if (resp.ok) {
      shoppingState.list = await resp.json();
    } else {
      // Unexpected error — surface it via apiFetch for consistent toast.
      shoppingState.list = null;
      window.App.showToast(`Failed to load shopping list (${resp.status})`, 'error');
    }
  } catch (_) {
    shoppingState.list = null;
    window.App.showToast('Network error loading shopping list', 'error');
  }

  renderShoppingView();
}

/* ============================================================
   Core Render
   ============================================================ */

/**
 * (Re-)render the full shopping list view into #app.
 * Called after every data change.
 */
function renderShoppingView() {
  const { el, setAppContent, buildEmptyState } = window.App;
  const list = shoppingState.list;

  const header = buildShoppingHeader(list);

  let body;
  if (!list || list.items.length === 0) {
    body = buildEmptyState(
      '🛒',
      'No Shopping List Yet',
      'Open the Weekly Planner, assign recipes to meal slots, then click "Generate Shopping List" to build your list.',
    );
  } else {
    body = buildShoppingBody(list.items);
  }

  // Always render the add-item row so users can attempt to add items at any time.
  // If no list exists, a POST /api/shopping/items will return 404 and we show a
  // toast explaining they need to generate a list first.
  const addRow = buildAddItemRow();

  setAppContent(el('div', {}, header, body, addRow));
}

/* ============================================================
   Header
   ============================================================ */

/**
 * Build the page header, including the item-count summary when a list exists
 * and the Generate from This Week button.
 * @param {object|null} list
 * @returns {HTMLElement}
 */
function buildShoppingHeader(list) {
  const { el } = window.App;

  const generateBtn = buildGenerateButton(list);

  if (!list || list.items.length === 0) {
    return el('div', { className: 'page-header' },
      el('div', {},
        el('h1', { className: 'page-title' }, '🛒 Shopping List'),
      ),
      generateBtn,
    );
  }

  const total   = list.items.length;
  const checked = list.items.filter(i => i.checked).length;

  // Use existing .page-subtitle class for muted secondary text.
  const subtitle = el('p', { className: 'page-subtitle' },
    `Week of ${list.week_start}  ·  ${total} item${total !== 1 ? 's' : ''}, ${checked} checked`,
  );

  return el('div', { className: 'page-header' },
    el('div', {},
      el('h1', { className: 'page-title' }, '🛒 Shopping List'),
      subtitle,
    ),
    generateBtn,
  );
}

/**
 * Build the "Generate from This Week" button.
 * Shown in a loading/disabled state while generation is in-flight.
 * @param {object|null} list  — current shopping list (used to decide whether to warn about replacement)
 * @returns {HTMLElement}
 */
function buildGenerateButton(list) {
  const { el } = window.App;

  const isGenerating = shoppingState.generating;
  const hasExistingItems = list && list.items && list.items.length > 0;

  const btnLabel = isGenerating
    ? '⏳ Generating…'
    : '🗓️ Generate from This Week';

  const btnAttrs = {
    type:      'button',
    className: 'btn btn-primary',
    onClick:   () => handleGenerate(hasExistingItems),
  };
  if (isGenerating) {
    btnAttrs.disabled = 'disabled';
    btnAttrs.style = { opacity: '0.7', cursor: 'not-allowed' };
  }

  return el('div', { className: 'page-header-actions' },
    el('button', btnAttrs, btnLabel),
  );
}

/* ============================================================
   Generate Shopping List
   ============================================================ */

/**
 * Handle the "Generate from This Week" button click.
 *
 * Flow:
 *  1. If a non-empty list already exists → show window.confirm warning.
 *  2. Call POST /api/shopping/generate with the current week's Monday date.
 *  3. On success (201) → update shoppingState.list and re-render.
 *  4. Show a toast with the count of items generated.
 *
 * @param {boolean} hasExistingItems  — whether the current list has any items
 */
async function handleGenerate(hasExistingItems) {
  const { showToast } = window.App;

  // Guard: do nothing if already generating.
  if (shoppingState.generating) return;

  // If a list with items already exists, ask the user to confirm replacement.
  if (hasExistingItems) {
    const confirmed = window.confirm(
      'This will replace your current shopping list with items from this week\'s meal plan.\n\nContinue?'
    );
    if (!confirmed) return;
  }

  // Compute the Monday for the current week — same algorithm as planner.js.
  const weekStart = getCurrentWeekMonday();

  // Enter loading state and re-render the header to reflect it.
  shoppingState.generating = true;
  renderShoppingView();

  try {
    // POST /api/shopping/generate returns 201 Created with the new list.
    const resp = await fetch('/api/shopping/generate', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ week_start: weekStart }),
    });

    if (!resp.ok) {
      let detail = `HTTP ${resp.status}`;
      try {
        const errData = await resp.json();
        if (errData && errData.detail) detail = errData.detail;
      } catch (_) { /* ignore parse errors */ }
      showToast(`Failed to generate shopping list: ${detail}`, 'error');
      return;
    }

    // 201 — new list created/replaced.
    const newList = await resp.json();
    shoppingState.list = newList;

    const itemCount = newList.items ? newList.items.length : 0;
    showToast(
      itemCount > 0
        ? `✅ Shopping list generated — ${itemCount} item${itemCount !== 1 ? 's' : ''}`
        : '✅ Shopping list generated (no ingredients found in this week\'s meals)',
      'success',
    );

  } catch (networkErr) {
    showToast(`Network error: ${networkErr.message}`, 'error');
  } finally {
    // Always leave loading state and re-render.
    shoppingState.generating = false;
    renderShoppingView();
  }
}

/* ============================================================
   Body — Grouped Sections
   ============================================================ */

/**
 * Build the scrollable list body, grouping items by grocery_section.
 * @param {Array<object>} items  — ShoppingItemResponse[]
 * @returns {HTMLElement}
 */
function buildShoppingBody(items) {
  const { el } = window.App;

  // Group items by section.
  /** @type {Map<string, object[]>} */
  const bySection = new Map();
  for (const item of items) {
    const key = (item.grocery_section || 'other').toLowerCase();
    if (!bySection.has(key)) bySection.set(key, []);
    bySection.get(key).push(item);
  }

  // Determine section render order: canonical order first, then any extras alphabetically.
  const extra = [...bySection.keys()].filter(k => !SECTION_ORDER.includes(k)).sort();
  const order = [...SECTION_ORDER.filter(k => bySection.has(k)), ...extra];

  const sections = order.map(sectionKey =>
    buildSection(sectionKey, bySection.get(sectionKey)),
  );

  return el('div', {}, ...sections);
}

/**
 * Build a single grocery-section block.
 * @param {string}        sectionKey
 * @param {Array<object>} items
 * @returns {HTMLElement}
 */
function buildSection(sectionKey, items) {
  const { el } = window.App;

  const label = SECTION_LABELS[sectionKey]
    || (sectionKey.charAt(0).toUpperCase() + sectionKey.slice(1));

  // Sort: unchecked (alphabetical) → checked (alphabetical).
  const sorted = [...items].sort((a, b) => {
    if (a.checked !== b.checked) return a.checked ? 1 : -1;
    return a.item.localeCompare(b.item);
  });

  const itemEls = sorted.map(item => buildItem(item));

  return el('div', { className: 'shopping-section' },
    el('div', { className: 'shopping-section-title' }, label),
    ...itemEls,
  );
}

/* ============================================================
   Item Row
   ============================================================ */

/**
 * Build a single item row with checkbox, qty, name, and remove button.
 * @param {object} item — ShoppingItemResponse
 * @returns {HTMLElement}
 */
function buildItem(item) {
  const { el } = window.App;

  const qty       = formatQty(item.quantity, item.unit);
  const isPending = shoppingState.inflight.has(item.id);

  const checkboxAttrs = {
    type:      'checkbox',
    className: 'shopping-checkbox',
    onClick:   (e) => handleToggle(item.id, e.target.checked),
  };
  // Disable interaction while an API call is in-flight for this item.
  if (isPending) checkboxAttrs.disabled = 'disabled';

  const checkbox = el('input', checkboxAttrs);
  // Set .checked as a DOM property (not HTML attribute) so it reflects current state.
  checkbox.checked = item.checked;

  const qtySpan  = el('span', { className: 'shopping-item-qty' }, qty);
  const nameSpan = el('span', { className: 'shopping-item-text' }, item.item);

  const removeBtnAttrs = {
    className: 'btn btn-icon shopping-item-remove',
    title:     'Remove item',
    onClick:   () => handleRemove(item.id),
  };
  if (isPending) removeBtnAttrs.disabled = 'disabled';

  const removeBtn = el('button', removeBtnAttrs, '✕');

  const rowClass = 'shopping-item' + (item.checked ? ' checked' : '') + (isPending ? ' pending' : '');

  return el('div', {
    className:        rowClass,
    dataset:          { itemId: String(item.id) },
  }, checkbox, qtySpan, nameSpan, removeBtn);
}

/* ============================================================
   Quantity Formatting
   ============================================================ */

/**
 * Format a numeric quantity + unit into a human-readable string.
 * Whole numbers show without decimal; fractions keep up to 1 decimal place.
 * @param {number} qty
 * @param {string} unit
 * @returns {string}
 */
function formatQty(qty, unit) {
  const num = qty === Math.floor(qty) ? String(qty) : qty.toFixed(1);
  return unit && unit !== 'whole' ? `${num} ${unit}` : num;
}

/* ============================================================
   Event Handlers
   ============================================================ */

/**
 * Toggle an item's checked state via PATCH, then re-render.
 * Guards against double-toggle by tracking in-flight item IDs.
 * @param {number}  itemId
 * @param {boolean} isChecked   — The NEW intended state (from checkbox event)
 */
async function handleToggle(itemId, isChecked) {
  // Ignore the click if another API call for this item is already in-flight.
  if (shoppingState.inflight.has(itemId)) return;

  // Mark this item as in-flight and re-render to disable its controls.
  shoppingState.inflight.add(itemId);
  renderShoppingView();

  // The backend toggles the state; it doesn't accept the new value directly.
  // We call PATCH and let the response be the source of truth.
  try {
    const updated = await window.App.apiFetch(`/api/shopping/items/${itemId}`, {
      method: 'PATCH',
    });
    if (updated && shoppingState.list) {
      // Update the item in-place so we don't need a full re-fetch.
      const idx = shoppingState.list.items.findIndex(i => i.id === itemId);
      if (idx !== -1) {
        shoppingState.list.items[idx] = updated;
      }
    }
  } catch (_) {
    // apiFetch already showed a toast; fall through so we re-render to
    // restore the checkbox to its server-side state.
  } finally {
    // Always clear the inflight lock and re-render.
    shoppingState.inflight.delete(itemId);
    renderShoppingView();
  }
}

/**
 * Remove an item via DELETE, then re-render.
 * Guards against double-click by tracking in-flight item IDs.
 * @param {number} itemId
 */
async function handleRemove(itemId) {
  // Ignore the click if another API call for this item is already in-flight.
  if (shoppingState.inflight.has(itemId)) return;

  // Mark this item as in-flight and re-render to disable its controls.
  shoppingState.inflight.add(itemId);
  renderShoppingView();

  try {
    await window.App.apiFetch(`/api/shopping/items/${itemId}`, {
      method: 'DELETE',
    });
    if (shoppingState.list) {
      // Remove the item from local state — no need to re-fetch.
      shoppingState.list.items = shoppingState.list.items.filter(i => i.id !== itemId);
      // Clear inflight BEFORE re-rendering (item is gone, no need to unlock it).
      shoppingState.inflight.delete(itemId);
      renderShoppingView();
      window.App.showToast('Item removed', 'success');
    }
  } catch (_) {
    // apiFetch showed an error toast already.  Unlock and restore.
    shoppingState.inflight.delete(itemId);
    renderShoppingView();
  }
}

/* ============================================================
   Add Manual Item
   ============================================================ */

/**
 * Build the add-item row shown below the shopping list.
 * Contains inputs for name, quantity, unit, and grocery section, plus an Add button.
 * Always rendered — if no list exists the submit handler shows a toast explaining
 * the user must generate a list first.
 * @returns {HTMLElement}
 */
function buildAddItemRow() {
  const { el } = window.App;

  // ── Inputs ──────────────────────────────────────────────────

  const nameInput = el('input', {
    type:        'text',
    className:   'form-control shopping-add-name',
    placeholder: 'Item name…',
    'aria-label': 'Item name',
    maxlength:   '200',
  });

  const qtyInput = el('input', {
    type:        'number',
    className:   'form-control shopping-add-qty',
    value:       '1',
    min:         '0.001',
    step:        'any',
    'aria-label': 'Quantity',
  });

  const unitInput = el('input', {
    type:        'text',
    className:   'form-control shopping-add-unit',
    value:       'whole',
    placeholder: 'unit',
    'aria-label': 'Unit',
    maxlength:   '50',
  });

  const sectionSelect = el('select', {
    className:   'form-control shopping-add-section',
    'aria-label': 'Grocery section',
  });

  for (const key of SECTION_ORDER) {
    const label = SECTION_LABELS[key] || key;
    const option = document.createElement('option');
    option.value = key;
    option.textContent = label;
    if (key === 'other') option.selected = true;
    sectionSelect.appendChild(option);
  }

  // Validation feedback element (hidden until needed)
  const validationMsg = el('span', {
    className: 'shopping-add-validation',
    role:      'alert',
    style:     { color: 'var(--color-danger)', fontSize: 'var(--font-size-xs)', display: 'none' },
  }, 'Item name is required');

  // ── Add Button ───────────────────────────────────────────────

  const addBtn = el('button', {
    type:      'button',
    className: 'btn btn-primary shopping-add-btn',
    onClick:   () => handleAddItem(nameInput, qtyInput, unitInput, sectionSelect, validationMsg),
  }, '+ Add');

  // Allow Enter key in the name input to submit
  nameInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddItem(nameInput, qtyInput, unitInput, sectionSelect, validationMsg);
    }
  });

  // Hide validation message as soon as the user starts typing
  nameInput.addEventListener('input', () => {
    if (nameInput.value.trim()) {
      validationMsg.style.display = 'none';
    }
  });

  // ── Assemble ────────────────────────────────────────────────

  const inputsRow = el('div', { className: 'shopping-add-row' },
    nameInput,
    qtyInput,
    unitInput,
    sectionSelect,
    addBtn,
  );

  return el('div', { className: 'shopping-add-container' },
    inputsRow,
    validationMsg,
  );
}

/**
 * Handle the "Add" button click.
 * Validates input, calls POST /api/shopping/items, updates DOM state, and
 * shows a toast on success or for "no list" errors.
 *
 * @param {HTMLInputElement}  nameInput
 * @param {HTMLInputElement}  qtyInput
 * @param {HTMLInputElement}  unitInput
 * @param {HTMLSelectElement} sectionSelect
 * @param {HTMLElement}       validationMsg
 */
async function handleAddItem(nameInput, qtyInput, unitInput, sectionSelect, validationMsg) {
  const { showToast } = window.App;

  // ── Validate ───────────────────────────────────────────────

  const itemName = nameInput.value.trim();
  if (!itemName) {
    validationMsg.style.display = '';
    nameInput.focus();
    return;
  }
  validationMsg.style.display = 'none';

  const qty = parseFloat(qtyInput.value);
  const quantity = isNaN(qty) || qty <= 0 ? 1 : qty;
  const unit = unitInput.value.trim() || 'whole';
  const grocerySection = sectionSelect.value || 'other';

  // ── Disable controls while in-flight ──────────────────────

  nameInput.disabled = true;
  qtyInput.disabled = true;
  unitInput.disabled = true;
  sectionSelect.disabled = true;

  const addBtn = nameInput.closest('.shopping-add-container')
    ? nameInput.closest('.shopping-add-container').querySelector('.shopping-add-btn')
    : null;
  if (addBtn) {
    addBtn.disabled = true;
    addBtn.textContent = 'Adding…';
  }

  // ── API Call ───────────────────────────────────────────────

  try {
    // Use raw fetch so we can inspect the 404 case without apiFetch auto-toasting it.
    const resp = await fetch('/api/shopping/items', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        item:            itemName,
        quantity:        quantity,
        unit:            unit,
        grocery_section: grocerySection,
        source:          'manual',
      }),
    });

    if (resp.status === 404) {
      // No shopping list exists yet — tell the user what to do.
      let detail = 'No shopping list exists. Generate one from the Meal Planner first.';
      try {
        const data = await resp.json();
        if (data && data.detail) detail = data.detail + ' Open the Meal Planner to generate one.';
      } catch (_) { /* ignore */ }
      showToast(detail, 'info', 6000);
      return;
    }

    if (!resp.ok) {
      let errorDetail = resp.statusText;
      try {
        const errData = await resp.json();
        if (errData && errData.detail) errorDetail = errData.detail;
      } catch (_) { /* ignore */ }
      showToast(`Failed to add item: ${errorDetail}`, 'error');
      return;
    }

    const newItem = await resp.json();

    // ── Success: update local state ──────────────────────────

    if (shoppingState.list) {
      shoppingState.list.items.push(newItem);
    } else {
      // Edge case: list was null but POST succeeded (should not happen with backend logic,
      // but handle gracefully by re-fetching).
      try {
        const freshResp = await fetch('/api/shopping/current');
        if (freshResp.ok) shoppingState.list = await freshResp.json();
      } catch (_) { /* ignore */ }
    }

    showToast(`"${itemName}" added to ${SECTION_LABELS[grocerySection] || grocerySection}`, 'success');

    // Re-render to insert the item in the correct section and update the count summary.
    renderShoppingView();

    // Note: renderShoppingView() replaces the DOM, so the old inputs are gone.
    // The new add-row inputs will be blank (fresh render), which is the desired
    // behaviour — inputs cleared after successful add.

  } catch (networkErr) {
    showToast(`Network error: ${networkErr.message}`, 'error');
  } finally {
    // Re-enable controls. If we didn't full-re-render, restore them.
    nameInput.disabled = false;
    qtyInput.disabled = false;
    unitInput.disabled = false;
    sectionSelect.disabled = false;
    if (addBtn) {
      addBtn.disabled = false;
      addBtn.textContent = '+ Add';
    }
  }
}
