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
   Module State
   ============================================================ */

/** @type {{ list: object|null }} */
const shoppingState = {
  list: null,   // ShoppingListResponse from API (or null when no list exists)
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

  setAppContent(el('div', {}, header, body));
}

/* ============================================================
   Header
   ============================================================ */

/**
 * Build the page header, including the item-count summary when a list exists.
 * @param {object|null} list
 * @returns {HTMLElement}
 */
function buildShoppingHeader(list) {
  const { el } = window.App;

  if (!list || list.items.length === 0) {
    return el('div', { className: 'page-header' },
      el('h1', { className: 'page-title' }, '🛒 Shopping List'),
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
  );
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

  const qty = formatQty(item.quantity, item.unit);

  const checkbox = el('input', {
    type:      'checkbox',
    className: 'shopping-checkbox',
    onClick:   (e) => handleToggle(item.id, e.target.checked),
  });
  // Set .checked as a DOM property (not HTML attribute) so it reflects current state.
  checkbox.checked = item.checked;

  const qtySpan  = el('span', { className: 'shopping-item-qty' }, qty);
  const nameSpan = el('span', { className: 'shopping-item-text' }, item.item);

  const removeBtn = el('button', {
    className: 'btn btn-icon shopping-item-remove',
    title:     'Remove item',
    onClick:   () => handleRemove(item.id),
  }, '✕');

  const rowClass = 'shopping-item' + (item.checked ? ' checked' : '');

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
 * @param {number}  itemId
 * @param {boolean} isChecked   — The NEW intended state (from checkbox event)
 */
async function handleToggle(itemId, isChecked) {
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
      renderShoppingView();
    }
  } catch (_) {
    // apiFetch already showed a toast; re-render to restore checkbox state.
    renderShoppingView();
  }
}

/**
 * Remove an item via DELETE, then re-render.
 * @param {number} itemId
 */
async function handleRemove(itemId) {
  try {
    await window.App.apiFetch(`/api/shopping/items/${itemId}`, {
      method: 'DELETE',
    });
    if (shoppingState.list) {
      shoppingState.list.items = shoppingState.list.items.filter(i => i.id !== itemId);
      renderShoppingView();
      window.App.showToast('Item removed', 'success');
    }
  } catch (_) {
    // apiFetch showed an error toast already.
  }
}
