/**
 * app.js — Recipe Manager SPA Core
 *
 * Responsibilities:
 *  - Hash-based router: #recipes | #planner | #shopping
 *  - Active tab state management
 *  - Shared API fetch wrapper (JSON request/response, error display)
 *  - DOM helper utilities
 *  - Toast notification system
 *  - Modal management
 */

'use strict';

/* ============================================================
   Constants
   ============================================================ */
const API_BASE = '';          // same-origin; prefix for all API calls
const DEFAULT_ROUTE = 'recipes';

const ROUTES = {
  recipes:  { tabId: 'tab-recipes',  render: () => typeof renderRecipes  === 'function' && renderRecipes() },
  planner:  { tabId: 'tab-planner',  render: () => typeof renderPlanner  === 'function' && renderPlanner() },
  shopping: { tabId: 'tab-shopping', render: () => typeof renderShopping === 'function' && renderShopping() },
};

/* ============================================================
   Router
   ============================================================ */

/**
 * Extract the current route from window.location.hash.
 * Falls back to DEFAULT_ROUTE when hash is empty or unknown.
 * @returns {string} e.g. 'recipes' | 'planner' | 'shopping'
 */
function getCurrentRoute() {
  const hash = window.location.hash.replace('#', '').trim();
  return ROUTES[hash] ? hash : DEFAULT_ROUTE;
}

/**
 * Update the active nav tab visual indicator.
 * @param {string} route
 */
function setActiveTab(route) {
  Object.values(ROUTES).forEach(({ tabId }) => {
    const el = document.getElementById(tabId);
    if (!el) return;
    el.classList.remove('active');
    el.setAttribute('aria-current', 'false');
  });

  const { tabId } = ROUTES[route] || ROUTES[DEFAULT_ROUTE];
  const activeTab = document.getElementById(tabId);
  if (activeTab) {
    activeTab.classList.add('active');
    activeTab.setAttribute('aria-current', 'true');
  }
}

/**
 * Navigate to a route, updating the hash and rendering the view.
 * @param {string} route
 */
function navigate(route) {
  if (!ROUTES[route]) route = DEFAULT_ROUTE;

  // Update URL hash without triggering hashchange (avoid double render)
  if (window.location.hash !== `#${route}`) {
    window.history.pushState(null, '', `#${route}`);
  }

  setActiveTab(route);
  renderRoute(route);
}

/**
 * Render the view for the given route.
 * @param {string} route
 */
function renderRoute(route) {
  const def = ROUTES[route] || ROUTES[DEFAULT_ROUTE];
  def.render();
}

/* ============================================================
   API Wrapper
   ============================================================ */

/**
 * Shared fetch wrapper.
 * Sends JSON requests, parses JSON responses, surfaces errors as toasts.
 *
 * @param {string} path — Relative path, e.g. '/api/recipes'
 * @param {object} [opts] — Fetch init options (method, body, headers, …)
 * @returns {Promise<any>} — Parsed JSON body, or null for 204 responses
 * @throws {Error} — On network or HTTP errors
 */
async function apiFetch(path, opts = {}) {
  const url = `${API_BASE}${path}`;

  const defaultHeaders = {};
  if (opts.body && typeof opts.body !== 'string') {
    // Serialise body to JSON if it is a plain object
    opts = {
      ...opts,
      body: JSON.stringify(opts.body),
      headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
    };
  } else {
    opts = { ...opts, headers: { ...defaultHeaders, ...(opts.headers || {}) } };
  }

  let response;
  try {
    response = await fetch(url, opts);
  } catch (networkErr) {
    const msg = `Network error: ${networkErr.message}`;
    showToast(msg, 'error');
    throw new Error(msg);
  }

  // 204 No Content — return null
  if (response.status === 204) return null;

  let data;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    const detail = data?.detail || data?.message || response.statusText;
    const msg = `API error ${response.status}: ${detail}`;
    showToast(msg, 'error');
    throw new Error(msg);
  }

  return data;
}

/* ============================================================
   DOM Helpers
   ============================================================ */

/**
 * Create an element with optional attributes and children.
 *
 * @param {string} tag — HTML tag name
 * @param {object} [attrs] — Attribute map; class → className, event handlers (onClick → addEventListener)
 * @param {...(Node|string)} children — Child nodes or text content
 * @returns {HTMLElement}
 */
function createElement(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);

  for (const [key, value] of Object.entries(attrs)) {
    if (key === 'className') {
      el.className = value;
    } else if (key === 'dataset') {
      Object.assign(el.dataset, value);
    } else if (key === 'style' && typeof value === 'object') {
      Object.assign(el.style, value);
    } else if (key.startsWith('on') && typeof value === 'function') {
      // e.g. onClick → 'click'
      el.addEventListener(key.slice(2).toLowerCase(), value);
    } else if (value !== null && value !== undefined && value !== false) {
      el.setAttribute(key, value);
    }
  }

  for (const child of children.flat(Infinity)) {
    if (child == null) continue;
    if (child instanceof Node) {
      el.appendChild(child);
    } else {
      el.appendChild(document.createTextNode(String(child)));
    }
  }

  return el;
}

/** Shorthand alias */
const el = createElement;

/**
 * Clear all children of a DOM element.
 * @param {HTMLElement} container
 */
function clearElement(container) {
  while (container.firstChild) {
    container.removeChild(container.firstChild);
  }
}

/**
 * Set the content of the #app element.
 * @param {...(Node|string)} nodes
 */
function setAppContent(...nodes) {
  const app = document.getElementById('app');
  clearElement(app);
  nodes.forEach(node => {
    if (node instanceof Node) app.appendChild(node);
    else if (node != null) app.insertAdjacentHTML('beforeend', node);
  });
}

/**
 * Build a loading spinner placeholder.
 * @returns {HTMLElement}
 */
function buildLoadingState() {
  return el('div', { className: 'loading-state' },
    el('div', { className: 'spinner' }),
    el('p', {}, 'Loading…'),
  );
}

/**
 * Build an empty-state message.
 * @param {string} icon — Emoji or text icon
 * @param {string} title
 * @param {string} [text]
 * @param {HTMLElement} [action] — Optional CTA button
 * @returns {HTMLElement}
 */
function buildEmptyState(icon, title, text = '', action = null) {
  return el('div', { className: 'empty-state' },
    el('div', { className: 'empty-state-icon' }, icon),
    el('p', { className: 'empty-state-title' }, title),
    text ? el('p', { className: 'empty-state-text text-muted' }, text) : null,
    action,
  );
}

/**
 * Build a category badge element.
 * @param {string} category
 * @returns {HTMLElement}
 */
function buildCategoryBadge(category) {
  const cls = `badge badge-${category || 'default'}`;
  return el('span', { className: cls }, category || '—');
}

/**
 * Build tag chip elements from a comma-separated string.
 * @param {string} tagsStr — e.g. "quick,vegetarian"
 * @returns {HTMLElement[]}
 */
function buildTagChips(tagsStr) {
  if (!tagsStr) return [];
  return tagsStr.split(',').map(t => t.trim()).filter(Boolean).map(tag =>
    el('span', { className: 'tag-chip' }, tag),
  );
}

/**
 * Format minutes as "Xh Ym" or "Ym".
 * @param {number} minutes
 * @returns {string}
 */
function formatTime(minutes) {
  if (!minutes && minutes !== 0) return '—';
  if (minutes < 60) return `${minutes}m`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

/**
 * Format total recipe time (prep + cook).
 * @param {object} recipe
 * @returns {string}
 */
function formatTotalTime(recipe) {
  const total = (recipe.prep_time_minutes || 0) + (recipe.cook_time_minutes || 0);
  return total ? `⏱ ${formatTime(total)}` : '';
}

/* ============================================================
   Modal Management
   ============================================================ */

let _onModalClose = null;

/**
 * Open the global modal.
 * @param {string} title
 * @param {Node|string} bodyContent
 * @param {object} [opts]
 * @param {boolean} [opts.wide] — Use wider modal container
 * @param {Function} [opts.onClose] — Callback when modal closes
 */
function openModal(title, bodyContent, opts = {}) {
  const overlay = document.getElementById('modal-overlay');
  const titleEl = document.getElementById('modal-title');
  const bodyEl  = document.getElementById('modal-body');
  const container = overlay.querySelector('.modal-container');

  titleEl.textContent = title;
  clearElement(bodyEl);

  if (bodyContent instanceof Node) {
    bodyEl.appendChild(bodyContent);
  } else {
    bodyEl.innerHTML = bodyContent;
  }

  container.classList.toggle('modal-wide', !!opts.wide);
  _onModalClose = opts.onClose || null;

  overlay.hidden = false;
  overlay.setAttribute('aria-hidden', 'false');

  // Focus first focusable element
  requestAnimationFrame(() => {
    const focusable = overlay.querySelector('input, button, select, textarea, [tabindex]:not([tabindex="-1"])');
    if (focusable) focusable.focus();
  });
}

/**
 * Close the global modal.
 */
function closeModal() {
  const overlay = document.getElementById('modal-overlay');
  overlay.hidden = true;
  overlay.setAttribute('aria-hidden', 'true');

  if (typeof _onModalClose === 'function') {
    _onModalClose();
    _onModalClose = null;
  }

  // Clear body to release memory
  const bodyEl = document.getElementById('modal-body');
  clearElement(bodyEl);
}

/* ============================================================
   Toast Notifications
   ============================================================ */

/**
 * Display a toast notification.
 * @param {string} message
 * @param {'success'|'error'|'info'|'warning'} [type]
 * @param {number} [duration] — ms before auto-dismiss (0 = permanent)
 */
function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = el('div', { className: `toast toast-${type}` }, message);
  container.appendChild(toast);

  if (duration > 0) {
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 300ms';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }
}

/* ============================================================
   Keyboard & Accessibility
   ============================================================ */

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    const overlay = document.getElementById('modal-overlay');
    if (overlay && !overlay.hidden) closeModal();
  }
});

/* ============================================================
   Initialisation
   ============================================================ */

/**
 * Wire up modal close button and overlay click-to-dismiss.
 */
function initModal() {
  const overlay   = document.getElementById('modal-overlay');
  const closeBtn  = document.getElementById('modal-close');

  closeBtn.addEventListener('click', closeModal);

  // Click outside the container to close
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeModal();
  });
}

/**
 * Handle hashchange events from the browser.
 */
function onHashChange() {
  const route = getCurrentRoute();
  setActiveTab(route);
  renderRoute(route);
}

/**
 * App entry point — called when the DOM is ready.
 */
function initApp() {
  initModal();

  // Listen for hash changes (back/forward navigation)
  window.addEventListener('hashchange', onHashChange);

  // Nav tab clicks
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', (e) => {
      // Allow default href behaviour to update the hash;
      // hashchange will trigger onHashChange
    });
  });

  // Initial render: default to #recipes if no hash
  if (!window.location.hash || !ROUTES[window.location.hash.replace('#', '')]) {
    window.location.replace(`#${DEFAULT_ROUTE}`);
  } else {
    onHashChange();
  }
}

// Boot when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}

/* ============================================================
   Exports (global — no bundler used)
   Expose shared utilities for other view scripts
   ============================================================ */
window.App = {
  navigate,
  apiFetch,
  openModal,
  closeModal,
  showToast,
  setAppContent,
  buildLoadingState,
  buildEmptyState,
  buildCategoryBadge,
  buildTagChips,
  formatTime,
  formatTotalTime,
  el,
  createElement,
  clearElement,
};
