/**
 * shopping.js — Shopping List View
 *
 * Full implementation: task E1-7 or later epic.
 * This stub renders a skeleton placeholder so navigation works without errors.
 */

'use strict';

/**
 * Entry point called by app.js router when the user navigates to #shopping.
 */
async function renderShopping() {
  const { setAppContent, buildEmptyState, el } = window.App;

  const header = el('div', { className: 'page-header' },
    el('h1', { className: 'page-title' }, '🛒 Shopping List'),
  );

  const placeholder = buildEmptyState(
    '🛒',
    'Shopping List Coming Soon',
    'Generate a grouped shopping list from the week\'s meal plan.',
  );

  setAppContent(el('div', {}, header, placeholder));
}
