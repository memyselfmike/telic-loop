/**
 * recipes.js — Recipe Collection View
 *
 * Renders the Recipes tab: grid of recipe cards with search/filter controls.
 * Full implementation: task E1-3 (collection grid + filters) and E1-4 (detail + form modal).
 *
 * This file is loaded by index.html and its renderRecipes() function is
 * called by app.js whenever the user navigates to #recipes.
 */

'use strict';

/**
 * Entry point called by app.js router.
 * Renders the Recipes view into #app.
 */
async function renderRecipes() {
  const { setAppContent, buildLoadingState, apiFetch, buildEmptyState,
          buildCategoryBadge, buildTagChips, formatTotalTime, el, showToast,
          openModal, closeModal } = window.App;

  setAppContent(buildLoadingState());

  let recipes = [];
  try {
    recipes = await apiFetch('/api/recipes');
  } catch {
    setAppContent(buildEmptyState('⚠️', 'Could not load recipes', 'The server may be offline. Start it and refresh.'));
    return;
  }

  _renderRecipeCollection(recipes);
}

/**
 * Render the full recipe collection UI with toolbar and card grid.
 * @param {Array} allRecipes — Initial full recipe list from API
 */
function _renderRecipeCollection(allRecipes) {
  const { setAppContent, apiFetch, buildEmptyState, buildCategoryBadge,
          buildTagChips, formatTotalTime, el, showToast, openModal } = window.App;

  // ── State ──────────────────────────────────────────────────────────────
  let recipes = allRecipes.slice();
  let searchValue = '';
  let categoryValue = '';
  let tagValue = '';

  // ── Toolbar ────────────────────────────────────────────────────────────
  const searchInput = el('input', {
    type: 'text',
    className: 'form-control',
    placeholder: 'Search by title or ingredient…',
    value: searchValue,
    onInput: (e) => { searchValue = e.target.value; fetchFiltered(); },
  });

  const categories = ['', 'breakfast', 'lunch', 'dinner', 'snack', 'dessert'];
  const categorySelect = el('select', {
    className: 'form-control',
    onChange: (e) => { categoryValue = e.target.value; fetchFiltered(); },
  },
    ...categories.map(c => el('option', { value: c }, c ? c.charAt(0).toUpperCase() + c.slice(1) : 'All Categories')),
  );

  const tagInput = el('input', {
    type: 'text',
    className: 'form-control',
    placeholder: 'Filter by tag…',
    style: { maxWidth: '160px' },
    onInput: (e) => { tagValue = e.target.value.trim(); fetchFiltered(); },
  });

  const addBtn = el('button', {
    className: 'btn btn-primary',
    onClick: () => openRecipeForm(null, onRecipeSaved),
  }, '+ Add Recipe');

  const toolbar = el('div', { className: 'toolbar' },
    el('div', { className: 'toolbar-search' },
      el('span', { className: 'search-icon' }, '🔍'),
      searchInput,
    ),
    el('div', { className: 'toolbar-filters' },
      categorySelect,
      tagInput,
    ),
    el('div', { className: 'toolbar-actions' }, addBtn),
  );

  // ── Grid container ──────────────────────────────────────────────────────
  const grid = el('div', { className: 'recipe-grid', id: 'recipe-grid' });

  const header = el('div', { className: 'page-header' },
    el('div', {},
      el('h1', { className: 'page-title' }, '📖 Recipes'),
    ),
  );

  const view = el('div', {}, header, toolbar, grid);
  setAppContent(view);

  // Initial render of cards
  renderGrid(recipes);

  // ── Helpers ─────────────────────────────────────────────────────────────

  async function fetchFiltered() {
    const params = new URLSearchParams();
    if (searchValue)   params.set('search',   searchValue);
    if (categoryValue) params.set('category', categoryValue);
    if (tagValue)      params.set('tag',      tagValue);
    try {
      recipes = await apiFetch(`/api/recipes?${params}`);
      renderGrid(recipes);
    } catch { /* toast already shown by apiFetch */ }
  }

  function renderGrid(list) {
    const g = document.getElementById('recipe-grid');
    if (!g) return;
    window.App.clearElement(g);

    if (!list.length) {
      g.appendChild(buildEmptyState('🍽️', 'No recipes found',
        'Try adjusting your filters or add a new recipe.'));
      return;
    }

    list.forEach(recipe => {
      const card = buildRecipeCard(recipe, () => openRecipeDetail(recipe.id, onRecipeSaved));
      g.appendChild(card);
    });
  }

  function onRecipeSaved() {
    // Reload everything after create/edit/delete
    renderRecipes();
  }
}

/**
 * Build a single recipe card element.
 * @param {object} recipe
 * @param {Function} onClick
 * @returns {HTMLElement}
 */
function buildRecipeCard(recipe, onClick) {
  const { buildCategoryBadge, buildTagChips, formatTotalTime, el } = window.App;

  const card = el('div', {
    className: 'card card-clickable recipe-card',
    onClick,
    tabIndex: '0',
    role: 'button',
    'aria-label': `View recipe: ${recipe.title}`,
    onKeydown: (e) => { if (e.key === 'Enter' || e.key === ' ') onClick(); },
  },
    el('div', { className: 'card-header' },
      el('h3', { className: 'card-title' }, recipe.title),
      buildCategoryBadge(recipe.category),
    ),
    el('p', { className: 'card-body' }, recipe.description || ''),
    el('div', { className: 'card-footer' },
      el('div', { className: 'recipe-meta' },
        el('span', { className: 'recipe-time' }, formatTotalTime(recipe)),
        recipe.servings ? el('span', {}, `👤 ${recipe.servings}`) : null,
      ),
      ...buildTagChips(recipe.tags),
    ),
  );

  return card;
}

/**
 * Open recipe detail view in the modal.
 * @param {number} recipeId
 * @param {Function} onMutated — called after edit/delete
 */
async function openRecipeDetail(recipeId, onMutated) {
  const { apiFetch, openModal, closeModal, buildCategoryBadge, buildTagChips,
          formatTime, el, showToast } = window.App;

  openModal('Loading…', window.App.buildLoadingState());

  let recipe;
  try {
    recipe = await apiFetch(`/api/recipes/${recipeId}`);
  } catch {
    closeModal();
    return;
  }

  const totalMins = (recipe.prep_time_minutes || 0) + (recipe.cook_time_minutes || 0);

  // ── Detail content ──────────────────────────────────────────────────────
  const ingredientEls = (recipe.ingredients || []).map(ing =>
    el('div', { className: 'ingredient-item' },
      el('span', { className: 'ingredient-qty' },
        [ing.quantity, ing.unit].filter(Boolean).join(' '),
      ),
      el('span', {}, ing.item),
    ),
  );

  const stepEls = (recipe.instructions || '')
    .split('\n').filter(s => s.trim())
    .map((step, i) =>
      el('div', { className: 'instruction-step' },
        el('span', { className: 'step-number' }, String(i + 1)),
        el('p', { className: 'step-text' }, step.trim()),
      ),
    );

  const body = el('div', {},
    // Stats bar
    el('div', { className: 'recipe-stats' },
      el('div', { className: 'stat-item' },
        el('span', { className: 'stat-label' }, 'Prep'),
        el('span', { className: 'stat-value' }, formatTime(recipe.prep_time_minutes)),
      ),
      el('div', { className: 'stat-item' },
        el('span', { className: 'stat-label' }, 'Cook'),
        el('span', { className: 'stat-value' }, formatTime(recipe.cook_time_minutes)),
      ),
      el('div', { className: 'stat-item' },
        el('span', { className: 'stat-label' }, 'Total'),
        el('span', { className: 'stat-value' }, formatTime(totalMins)),
      ),
      el('div', { className: 'stat-item' },
        el('span', { className: 'stat-label' }, 'Servings'),
        el('span', { className: 'stat-value' }, recipe.servings || '—'),
      ),
    ),
    // Tags
    recipe.tags ? el('div', { className: 'card-footer', style: { marginBottom: '1rem' } },
      ...buildTagChips(recipe.tags),
    ) : null,
    // Description
    recipe.description ? el('p', { className: 'text-muted', style: { marginBottom: '1.5rem' } }, recipe.description) : null,
    // Ingredients
    el('h3', { className: 'recipe-section-title' }, 'Ingredients'),
    el('div', { className: 'ingredient-list' }, ...ingredientEls),
    // Instructions
    el('h3', { className: 'recipe-section-title' }, 'Instructions'),
    el('div', { className: 'instructions-list' }, ...stepEls),
    // Actions
    el('div', { className: 'd-flex gap-sm', style: { marginTop: '1.5rem' } },
      el('button', {
        className: 'btn btn-secondary',
        onClick: () => openRecipeForm(recipe, () => { closeModal(); onMutated(); }),
      }, '✏️ Edit'),
      el('button', {
        className: 'btn btn-danger',
        onClick: async () => {
          if (!confirm(`Delete "${recipe.title}"? This cannot be undone.`)) return;
          try {
            await apiFetch(`/api/recipes/${recipe.id}`, { method: 'DELETE' });
            showToast(`"${recipe.title}" deleted`, 'success');
            closeModal();
            onMutated();
          } catch { /* toast shown by apiFetch */ }
        },
      }, '🗑️ Delete'),
    ),
  );

  openModal(recipe.title, body, { wide: true });
}

/**
 * Open create/edit recipe form in the modal.
 * @param {object|null} recipe — Existing recipe for edit, or null for create
 * @param {Function} onSaved — Called after successful save
 */
function openRecipeForm(recipe, onSaved) {
  const { openModal, closeModal, apiFetch, showToast, el, clearElement } = window.App;

  const isEdit = !!recipe;
  const title = isEdit ? `Edit: ${recipe.title}` : 'Add New Recipe';

  // ── Ingredient rows state ───────────────────────────────────────────────
  const initialIngredients = (recipe?.ingredients || [{ quantity: '', unit: '', item: '', grocery_section: '' }]);
  let ingredientCount = 0;

  const ingRowsContainer = el('div', { className: 'ingredient-rows', id: 'ingredient-rows' });

  function addIngredientRow(data = {}) {
    const idx = ++ingredientCount;
    const row = el('div', { className: 'ingredient-row', dataset: { idx: String(idx) } },
      el('div', { className: 'form-group' },
        idx === 1 ? el('label', { className: 'form-label' }, 'Qty') : null,
        el('input', { type: 'text', className: 'form-control', name: 'ing-qty', placeholder: '1', value: data.quantity || '' }),
      ),
      el('div', { className: 'form-group' },
        idx === 1 ? el('label', { className: 'form-label' }, 'Unit') : null,
        el('input', { type: 'text', className: 'form-control', name: 'ing-unit', placeholder: 'cup', value: data.unit || '' }),
      ),
      el('div', { className: 'form-group' },
        idx === 1 ? el('label', { className: 'form-label required' }, 'Ingredient') : null,
        el('input', { type: 'text', className: 'form-control', name: 'ing-item', placeholder: 'e.g. flour', value: data.item || '' }),
      ),
      el('div', { className: 'form-group' },
        idx === 1 ? el('label', { className: 'form-label' }, 'Section') : null,
        el('input', { type: 'text', className: 'form-control', name: 'ing-section', placeholder: 'produce', value: data.grocery_section || '' }),
      ),
      el('button', {
        type: 'button',
        className: 'btn btn-ghost btn-icon',
        title: 'Remove ingredient',
        style: { marginTop: idx === 1 ? '22px' : '0' },
        onClick: () => row.remove(),
      }, '✕'),
    );
    ingRowsContainer.appendChild(row);
  }

  initialIngredients.forEach(i => addIngredientRow(i));

  // ── Form ────────────────────────────────────────────────────────────────
  const form = el('form', { id: 'recipe-form' },
    el('div', { className: 'form-group' },
      el('label', { className: 'form-label required', for: 'f-title' }, 'Title'),
      el('input', { type: 'text', id: 'f-title', className: 'form-control', required: 'true',
        placeholder: 'e.g. Classic Oatmeal', value: recipe?.title || '' }),
    ),
    el('div', { className: 'form-row' },
      el('div', { className: 'form-group' },
        el('label', { className: 'form-label required', for: 'f-category' }, 'Category'),
        el('select', { id: 'f-category', className: 'form-control', required: 'true' },
          ...['breakfast','lunch','dinner','snack','dessert'].map(c =>
            el('option', { value: c, ...(recipe?.category === c ? { selected: 'true' } : {}) },
              c.charAt(0).toUpperCase() + c.slice(1)),
          ),
        ),
      ),
      el('div', { className: 'form-group' },
        el('label', { className: 'form-label', for: 'f-prep' }, 'Prep (min)'),
        el('input', { type: 'number', id: 'f-prep', className: 'form-control', min: '0', value: recipe?.prep_time_minutes || '' }),
      ),
      el('div', { className: 'form-group' },
        el('label', { className: 'form-label', for: 'f-cook' }, 'Cook (min)'),
        el('input', { type: 'number', id: 'f-cook', className: 'form-control', min: '0', value: recipe?.cook_time_minutes || '' }),
      ),
      el('div', { className: 'form-group' },
        el('label', { className: 'form-label', for: 'f-servings' }, 'Servings'),
        el('input', { type: 'number', id: 'f-servings', className: 'form-control', min: '1', value: recipe?.servings || '' }),
      ),
    ),
    el('div', { className: 'form-group' },
      el('label', { className: 'form-label', for: 'f-desc' }, 'Description'),
      el('textarea', { id: 'f-desc', className: 'form-control', placeholder: 'Short description…' }, recipe?.description || ''),
    ),
    el('div', { className: 'form-group' },
      el('label', { className: 'form-label', for: 'f-tags' }, 'Tags'),
      el('input', { type: 'text', id: 'f-tags', className: 'form-control',
        placeholder: 'quick,vegetarian,gluten-free', value: recipe?.tags || '' }),
      el('span', { className: 'form-hint' }, 'Comma-separated'),
    ),
    el('div', { className: 'form-group' },
      el('label', { className: 'form-label' }, 'Ingredients'),
      ingRowsContainer,
      el('button', { type: 'button', className: 'btn btn-ghost btn-sm', style: { marginTop: '0.5rem' },
        onClick: () => addIngredientRow() }, '+ Add Ingredient'),
    ),
    el('div', { className: 'form-group' },
      el('label', { className: 'form-label required', for: 'f-instructions' }, 'Instructions'),
      el('textarea', { id: 'f-instructions', className: 'form-control', style: { minHeight: '140px' },
        required: 'true', placeholder: 'One step per line…' },
        recipe?.instructions || '',
      ),
    ),
    el('div', { className: 'modal-footer' },
      el('button', { type: 'button', className: 'btn btn-ghost', onClick: closeModal }, 'Cancel'),
      el('button', { type: 'submit', className: 'btn btn-primary' }, isEdit ? 'Save Changes' : 'Add Recipe'),
    ),
  );

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Collect ingredient rows
    const rows = ingRowsContainer.querySelectorAll('.ingredient-row');
    const ingredients = [];
    rows.forEach(row => {
      const qty     = row.querySelector('[name="ing-qty"]').value.trim();
      const unit    = row.querySelector('[name="ing-unit"]').value.trim();
      const item    = row.querySelector('[name="ing-item"]').value.trim();
      const section = row.querySelector('[name="ing-section"]').value.trim();
      if (item) ingredients.push({ quantity: qty, unit, item, grocery_section: section });
    });

    const payload = {
      title:              form.querySelector('#f-title').value.trim(),
      category:           form.querySelector('#f-category').value,
      description:        form.querySelector('#f-desc').value.trim(),
      prep_time_minutes:  parseInt(form.querySelector('#f-prep').value) || null,
      cook_time_minutes:  parseInt(form.querySelector('#f-cook').value) || null,
      servings:           parseInt(form.querySelector('#f-servings').value) || null,
      tags:               form.querySelector('#f-tags').value.trim(),
      instructions:       form.querySelector('#f-instructions').value.trim(),
      ingredients,
    };

    const submitBtn = form.querySelector('[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Saving…';

    try {
      if (isEdit) {
        await apiFetch(`/api/recipes/${recipe.id}`, { method: 'PUT', body: payload });
        showToast(`"${payload.title}" updated`, 'success');
      } else {
        await apiFetch('/api/recipes', { method: 'POST', body: payload });
        showToast(`"${payload.title}" added`, 'success');
      }
      closeModal();
      onSaved();
    } catch {
      submitBtn.disabled = false;
      submitBtn.textContent = isEdit ? 'Save Changes' : 'Add Recipe';
    }
  });

  openModal(title, form, { wide: true });
}
