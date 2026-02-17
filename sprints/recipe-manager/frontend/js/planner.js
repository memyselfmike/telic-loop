/**
 * planner.js — Weekly Meal Planner View
 *
 * Full implementation: task E1-6 or later epic.
 * This stub renders a skeleton placeholder so navigation works without errors.
 */

'use strict';

/**
 * Entry point called by app.js router when the user navigates to #planner.
 */
async function renderPlanner() {
  const { setAppContent, buildEmptyState, el } = window.App;

  const header = el('div', { className: 'page-header' },
    el('h1', { className: 'page-title' }, '📅 Meal Plan'),
  );

  const placeholder = buildEmptyState(
    '📅',
    'Meal Planner Coming Soon',
    'Assign recipes to breakfast, lunch, dinner, and snack slots across the week.',
  );

  setAppContent(el('div', {}, header, placeholder));
}
