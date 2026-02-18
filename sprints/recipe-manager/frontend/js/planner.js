/**
 * planner.js — Weekly Meal Planner View
 *
 * Renders a 7-column (Mon–Sun) × 4-row (Breakfast, Lunch, Dinner, Snack)
 * meal planning grid backed by GET/PUT/DELETE /api/meals.
 */

'use strict';

/* ============================================================
   Constants
   ============================================================ */

const MEAL_SLOTS = ['breakfast', 'lunch', 'dinner', 'snack'];
const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

/* ============================================================
   Date Helpers
   ============================================================ */

/**
 * Return the ISO date string (YYYY-MM-DD) for the Monday of the
 * week containing the given date (or today if no date is provided).
 * @param {Date} [from]
 * @returns {string}
 */
function getWeekStart(from = new Date()) {
  const d = new Date(from);
  // getDay(): 0=Sun, 1=Mon … 6=Sat  →  shift so Monday=0
  const dayOfWeek = (d.getDay() + 6) % 7;
  d.setDate(d.getDate() - dayOfWeek);
  return toISODate(d);
}

/**
 * Convert a Date to a YYYY-MM-DD string in local time.
 * @param {Date} d
 * @returns {string}
 */
function toISODate(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

/**
 * Advance a week-start ISO date by `delta` weeks.
 * @param {string} weekStart — YYYY-MM-DD
 * @param {number} delta — positive or negative integer
 * @returns {string}
 */
function offsetWeek(weekStart, delta) {
  const d = new Date(weekStart + 'T00:00:00');
  d.setDate(d.getDate() + delta * 7);
  return toISODate(d);
}

/**
 * Format a week-start date as a human-readable range label.
 * e.g. "Feb 16 – Feb 22, 2026"
 * @param {string} weekStart
 * @returns {string}
 */
function formatWeekLabel(weekStart) {
  const start = new Date(weekStart + 'T00:00:00');
  const end = new Date(start);
  end.setDate(end.getDate() + 6);

  const opts = { month: 'short', day: 'numeric' };
  const startStr = start.toLocaleDateString(undefined, opts);
  const endStr = end.toLocaleDateString(undefined, { ...opts, year: 'numeric' });
  return `${startStr} – ${endStr}`;
}

/* ============================================================
   Entry Point
   ============================================================ */

/**
 * Called by app.js router when the user navigates to #planner.
 * Renders the full weekly meal planner interface.
 */
async function renderPlanner() {
  const { setAppContent, buildLoadingState, el } = window.App;

  // Show loading state immediately
  setAppContent(buildLoadingState());

  // Module-level state (re-created on each navigation to #planner)
  const state = {
    weekStart: getWeekStart(),
    meals: [],      // MealPlanResponse[]
    recipes: [],    // RecipeSummary[] — loaded lazily for the picker
  };

  /**
   * Main render function — rebuilds the entire view from state.
   */
  async function render() {
    const { apiFetch, showToast } = window.App;

    try {
      state.meals = await apiFetch(`/api/meals?week=${encodeURIComponent(state.weekStart)}`);
    } catch {
      // apiFetch already showed a toast; render an empty grid so the user
      // can still see the structure.
      state.meals = [];
    }

    setAppContent(buildView());
  }

  /* ----------------------------------------------------------
     View Construction
     ---------------------------------------------------------- */

  /**
   * Build the complete planner view: header + week-nav + grid.
   * @returns {HTMLElement}
   */
  function buildView() {
    const { el } = window.App;
    return el('div', {},
      buildPageHeader(),
      buildWeekNav(),
      buildMealGrid(),
    );
  }

  /** Page title row */
  function buildPageHeader() {
    const { el } = window.App;
    return el('div', { className: 'page-header' },
      el('h1', { className: 'page-title' }, '📅 Meal Planner'),
    );
  }

  /** Previous / week-label / next navigation bar */
  function buildWeekNav() {
    const { el } = window.App;

    const prevBtn = el('button', {
      className: 'btn btn-secondary',
      'aria-label': 'Previous week',
      onClick: () => navigateWeek(-1),
    }, '← Prev');

    const nextBtn = el('button', {
      className: 'btn btn-secondary',
      'aria-label': 'Next week',
      onClick: () => navigateWeek(1),
    }, 'Next →');

    const todayBtn = el('button', {
      className: 'btn btn-ghost',
      onClick: () => navigateWeekAbsolute(getWeekStart()),
    }, 'Today');

    const label = el('span', { className: 'week-label' }, formatWeekLabel(state.weekStart));

    return el('div', { className: 'planner-week-nav' },
      prevBtn,
      todayBtn,
      label,
      nextBtn,
    );
  }

  /** The scrollable meal grid container */
  function buildMealGrid() {
    const { el } = window.App;
    return el('div', { className: 'meal-grid' },
      buildMealTable(),
    );
  }

  /**
   * Build the full <table>:
   *   thead: blank cell + Mon … Sun
   *   tbody: one <tr> per meal slot + day-total summary row
   */
  function buildMealTable() {
    const { el } = window.App;

    // Index meals by "dayIndex-slot" for O(1) lookup
    const mealIndex = indexMeals(state.meals);

    const thead = el('thead', {},
      buildHeaderRow(),
    );

    const tbody = el('tbody', {},
      ...MEAL_SLOTS.map(slot => buildSlotRow(slot, mealIndex)),
      buildTotalRow(mealIndex),
    );

    return el('table', { className: 'meal-table', role: 'grid' },
      thead,
      tbody,
    );
  }

  /** thead row: empty corner cell + Mon–Sun th cells */
  function buildHeaderRow() {
    const { el } = window.App;
    const cornerTh = el('th', { scope: 'col', 'aria-label': 'Meal type' }, '');
    const dayThs = DAY_LABELS.map(label =>
      el('th', { scope: 'col' }, label),
    );
    return el('tr', {}, cornerTh, ...dayThs);
  }

  /**
   * One tbody row for a given meal slot (breakfast / lunch / dinner / snack).
   * @param {string} slot
   * @param {Map} mealIndex
   */
  function buildSlotRow(slot, mealIndex) {
    const { el } = window.App;
    const labelTd = el('td', { className: 'meal-row-label', scope: 'row' },
      slot.charAt(0).toUpperCase() + slot.slice(1),
    );
    const cells = Array.from({ length: 7 }, (_, dayIndex) =>
      buildMealCell(dayIndex, slot, mealIndex),
    );
    return el('tr', {}, labelTd, ...cells);
  }

  /**
   * Build a single td meal cell.
   * Empty → shows "+" add button.
   * Filled → shows recipe title, time, and a remove button.
   * @param {number} dayIndex — 0=Mon … 6=Sun
   * @param {string} slot
   * @param {Map} mealIndex
   */
  function buildMealCell(dayIndex, slot, mealIndex) {
    const { el, formatTime } = window.App;
    const key = `${dayIndex}-${slot}`;
    const meal = mealIndex.get(key) || null;

    const td = el('td', {
      className: `meal-cell${meal ? ' has-recipe' : ''}`,
      role: 'gridcell',
      tabindex: '0',
      'aria-label': meal
        ? `${DAY_LABELS[dayIndex]} ${slot}: ${meal.recipe_title}`
        : `${DAY_LABELS[dayIndex]} ${slot}: empty`,
    });

    if (meal) {
      // Filled cell: recipe card
      const removeBtn = el('button', {
        className: 'meal-cell-remove',
        'aria-label': `Remove ${meal.recipe_title} from ${DAY_LABELS[dayIndex]} ${slot}`,
        onClick: async (e) => {
          e.stopPropagation();
          await removeMeal(meal.id);
        },
      }, '×');

      const recipe = el('div', { className: 'meal-cell-recipe' },
        el('div', { className: 'meal-cell-title' }, meal.recipe_title),
        meal.total_time
          ? el('div', { className: 'meal-cell-time' }, `⏱ ${formatTime(meal.total_time)}`)
          : null,
      );

      td.appendChild(recipe);
      td.appendChild(removeBtn);

      // Click filled cell → show action popup (View / Swap / Clear)
      td.addEventListener('click', (e) => {
        // Don't re-open popup if the remove button was clicked
        if (e.target.closest('.meal-cell-remove')) return;
        openSlotActionPopup(td, meal, dayIndex, slot);
      });
      td.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          openSlotActionPopup(td, meal, dayIndex, slot);
        }
      });
    } else {
      // Empty cell: + add button
      const addBtn = el('div', { className: 'meal-cell-add', 'aria-hidden': 'true' }, '+');
      td.appendChild(addBtn);

      td.addEventListener('click', () => openRecipePicker(dayIndex, slot));
      td.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          openRecipePicker(dayIndex, slot);
        }
      });
    }

    return td;
  }

  /**
   * Build the day-total summary row at the bottom.
   * Sums total_time across all meal slots for each day.
   * @param {Map} mealIndex
   */
  function buildTotalRow(mealIndex) {
    const { el, formatTime } = window.App;

    const labelTd = el('td', { className: 'meal-row-label' }, 'Total');
    const totalTds = Array.from({ length: 7 }, (_, dayIndex) => {
      const dayTotal = MEAL_SLOTS.reduce((sum, slot) => {
        const meal = mealIndex.get(`${dayIndex}-${slot}`);
        return sum + (meal ? (meal.total_time || 0) : 0);
      }, 0);
      return el('td', {}, dayTotal > 0 ? formatTime(dayTotal) : '0m');
    });

    return el('tr', { className: 'day-total-row' }, labelTd, ...totalTds);
  }

  /* ----------------------------------------------------------
     Data Helpers
     ---------------------------------------------------------- */

  /**
   * Index an array of MealPlanResponse objects by "dayIndex-slot".
   * The API returns day_of_week as 0–6 (Mon–Sun).
   * @param {object[]} meals
   * @returns {Map<string, object>}
   */
  function indexMeals(meals) {
    const map = new Map();
    for (const meal of meals) {
      map.set(`${meal.day_of_week}-${meal.meal_slot}`, meal);
    }
    return map;
  }

  /* ----------------------------------------------------------
     Navigation
     ---------------------------------------------------------- */

  async function navigateWeek(delta) {
    state.weekStart = offsetWeek(state.weekStart, delta);
    await render();
  }

  async function navigateWeekAbsolute(weekStart) {
    state.weekStart = weekStart;
    await render();
  }

  /* ----------------------------------------------------------
     Meal CRUD
     ---------------------------------------------------------- */

  /**
   * Delete a meal plan entry and re-render.
   * @param {number} mealId
   */
  async function removeMeal(mealId) {
    const { apiFetch, showToast } = window.App;
    try {
      await apiFetch(`/api/meals/${mealId}`, { method: 'DELETE' });
      showToast('Meal removed', 'success');
      await render();
    } catch {
      // apiFetch already displayed an error toast
    }
  }

  /**
   * Assign a recipe to a meal slot and re-render.
   * @param {number} recipeId
   * @param {number} dayIndex — 0=Mon … 6=Sun
   * @param {string} slot
   */
  async function assignMeal(recipeId, dayIndex, slot) {
    const { apiFetch, showToast } = window.App;
    try {
      await apiFetch('/api/meals', {
        method: 'PUT',
        body: {
          week_start: state.weekStart,
          day_of_week: dayIndex,
          meal_slot: slot,
          recipe_id: recipeId,
        },
      });
      showToast('Recipe added to plan', 'success');
      await render();
    } catch {
      // apiFetch already displayed an error toast
    }
  }

  /* ----------------------------------------------------------
     Slot Action Popup (View Recipe / Swap / Clear)
     ---------------------------------------------------------- */

  /**
   * Open a small action popup anchored to the given cell td.
   * Shows three choices: View Recipe, Swap (opens picker), Clear (removes meal).
   *
   * Only one popup is shown at a time — clicking elsewhere dismisses it.
   *
   * @param {HTMLElement} cellTd — The clicked <td> element
   * @param {object} meal — The MealPlanResponse for this slot
   * @param {number} dayIndex — 0=Mon … 6=Sun
   * @param {string} slot — 'breakfast' | 'lunch' | 'dinner' | 'snack'
   */
  function openSlotActionPopup(cellTd, meal, dayIndex, slot) {
    const { el, navigate } = window.App;

    // Dismiss any already-open popup
    closeSlotActionPopup();

    const popup = el('div', {
      className: 'meal-cell-popup',
      role: 'menu',
      'aria-label': `Actions for ${meal.recipe_title}`,
    });

    // ── View Recipe ─────────────────────────────────────────────
    const viewBtn = el('button', {
      className: 'meal-cell-popup-btn',
      role: 'menuitem',
      'aria-label': `View ${meal.recipe_title}`,
    },
      el('span', { className: 'popup-icon' }, '👁'),
      'View Recipe',
    );
    viewBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      closeSlotActionPopup();
      // Navigate to #recipes view; the recipes list will display the full collection.
      navigate('recipes');
    });

    // ── Swap ────────────────────────────────────────────────────
    const swapBtn = el('button', {
      className: 'meal-cell-popup-btn',
      role: 'menuitem',
      'aria-label': `Swap ${meal.recipe_title}`,
    },
      el('span', { className: 'popup-icon' }, '🔄'),
      'Swap',
    );
    swapBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      closeSlotActionPopup();
      openRecipePicker(dayIndex, slot);
    });

    // ── Copy to slots ────────────────────────────────────────────
    const copyBtn = el('button', {
      className: 'meal-cell-popup-btn',
      role: 'menuitem',
      'aria-label': `Copy ${meal.recipe_title} to multiple slots`,
    },
      el('span', { className: 'popup-icon' }, '📋'),
      'Copy to slots…',
    );
    copyBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      closeSlotActionPopup();
      openCopyToSlotsModal(meal, dayIndex, slot);
    });

    // ── Clear ───────────────────────────────────────────────────
    const clearBtn = el('button', {
      className: 'meal-cell-popup-btn danger',
      role: 'menuitem',
      'aria-label': `Clear ${meal.recipe_title}`,
    },
      el('span', { className: 'popup-icon' }, '🗑'),
      'Clear',
    );
    clearBtn.addEventListener('click', async (e) => {
      e.stopPropagation();
      closeSlotActionPopup();
      await removeMeal(meal.id);
    });

    popup.appendChild(viewBtn);
    popup.appendChild(swapBtn);
    popup.appendChild(copyBtn);
    popup.appendChild(clearBtn);

    // Attach to the cell (position: relative already set by .meal-cell)
    cellTd.appendChild(popup);

    // Store reference for cleanup
    cellTd._actionPopup = popup;

    // Dismiss on outside click (capture phase so it fires before cell click)
    function onOutsideClick(e) {
      if (!popup.contains(e.target) && e.target !== cellTd && !cellTd.contains(e.target)) {
        closeSlotActionPopup();
        document.removeEventListener('click', onOutsideClick, true);
      }
    }
    // Small delay so the current click event doesn't immediately dismiss the popup
    setTimeout(() => {
      document.addEventListener('click', onOutsideClick, true);
    }, 0);

    // Dismiss on Escape key
    function onEscape(e) {
      if (e.key === 'Escape') {
        closeSlotActionPopup();
        document.removeEventListener('keydown', onEscape);
        cellTd.focus();
      }
    }
    document.addEventListener('keydown', onEscape);

    // Focus the first button for keyboard accessibility
    requestAnimationFrame(() => viewBtn.focus());
  }

  /**
   * Remove the currently open slot action popup from the DOM, if any.
   */
  function closeSlotActionPopup() {
    const existing = document.querySelector('.meal-cell-popup');
    if (existing) {
      existing.remove();
      // Clean up the reference on the parent td
      const parentTd = existing.closest('td');
      if (parentTd) delete parentTd._actionPopup;
    }
  }

  /* ----------------------------------------------------------
     Recipe Picker Modal
     ---------------------------------------------------------- */

  /**
   * Open a modal with a searchable list of recipes.
   * On selection, assigns the recipe to the given slot.
   * @param {number} dayIndex
   * @param {string} slot
   */
  async function openRecipePicker(dayIndex, slot) {
    const { apiFetch, openModal, closeModal, el, showToast } = window.App;

    const dayLabel = DAY_LABELS[dayIndex];
    const slotLabel = slot.charAt(0).toUpperCase() + slot.slice(1);

    // Fetch recipes if not yet cached
    if (state.recipes.length === 0) {
      try {
        state.recipes = await apiFetch('/api/recipes');
      } catch {
        return; // toast already shown
      }
    }

    let filteredRecipes = [...state.recipes];

    // Search input
    const searchInput = el('input', {
      type: 'search',
      className: 'picker-search',
      placeholder: 'Search recipes…',
      'aria-label': 'Search recipes',
    });

    // Recipe list container
    const listEl = el('ul', { className: 'picker-list', role: 'listbox' });

    /** Render the filtered recipe list */
    function renderPickerList(recipes) {
      while (listEl.firstChild) listEl.removeChild(listEl.firstChild);

      if (recipes.length === 0) {
        listEl.appendChild(el('li', { className: 'picker-empty' }, 'No recipes found.'));
        return;
      }

      for (const recipe of recipes) {
        const totalTime = (recipe.prep_time_minutes || 0) + (recipe.cook_time_minutes || 0);
        const timeStr = totalTime ? ` · ⏱ ${window.App.formatTime(totalTime)}` : '';

        const item = el('li', {
          className: 'picker-item',
          role: 'option',
          tabindex: '0',
          'aria-label': recipe.title,
        },
          el('span', { className: 'picker-item-title' }, recipe.title),
          el('span', { className: 'picker-item-meta' }, `${recipe.category || ''}${timeStr}`),
        );

        const selectRecipe = async () => {
          closeModal();
          await assignMeal(recipe.id, dayIndex, slot);
        };

        item.addEventListener('click', selectRecipe);
        item.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            selectRecipe();
          }
        });

        listEl.appendChild(item);
      }
    }

    // Initial render
    renderPickerList(filteredRecipes);

    // Live search filtering (debounced)
    let debounceTimer = null;
    searchInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        const query = searchInput.value.trim().toLowerCase();
        filteredRecipes = query
          ? state.recipes.filter(r =>
              r.title.toLowerCase().includes(query) ||
              (r.category || '').toLowerCase().includes(query) ||
              (r.tags || '').toLowerCase().includes(query),
            )
          : [...state.recipes];
        renderPickerList(filteredRecipes);
      }, 200);
    });

    const body = el('div', {},
      searchInput,
      listEl,
    );

    openModal(`Add to ${dayLabel} ${slotLabel}`, body);
  }

  /* ----------------------------------------------------------
     Copy to Slots Modal (Meal Prep)
     ---------------------------------------------------------- */

  /**
   * Open a modal showing a 7×4 checkbox grid of all slots for the current week.
   * The user selects target slots and clicks "Copy" to assign the same recipe
   * to all selected slots in one action.
   *
   * @param {object} meal      — MealPlanResponse for the source slot
   * @param {number} srcDay    — 0=Mon … 6=Sun (the slot we're copying FROM)
   * @param {string} srcSlot   — 'breakfast' | 'lunch' | 'dinner' | 'snack'
   */
  function openCopyToSlotsModal(meal, srcDay, srcSlot) {
    const { el, openModal, closeModal, apiFetch, showToast } = window.App;

    // Build the checkbox grid — rows = meal slots, cols = days
    // Each checkbox represents one (dayIndex, slot) combination.
    // We store them in a Map keyed by `dayIndex-slot` for easy lookup.
    const checkboxMap = new Map(); // key → { checkbox, dayIndex, slot }

    // Header row: blank corner + day labels
    const headerCells = [
      el('div', { className: 'copy-grid-corner' }, ''),
      ...DAY_LABELS.map(d => el('div', { className: 'copy-grid-day-header' }, d)),
    ];

    // Body rows: one row per meal slot
    const rows = MEAL_SLOTS.map(slot => {
      const slotLabel = el('div', { className: 'copy-grid-row-label' },
        slot.charAt(0).toUpperCase() + slot.slice(1),
      );

      const cells = DAY_LABELS.map((_, dayIndex) => {
        const key = `${dayIndex}-${slot}`;
        const isSource = dayIndex === srcDay && slot === srcSlot;

        const checkbox = el('input', {
          type: 'checkbox',
          className: 'copy-slot-checkbox',
          id: `copy-slot-${key}`,
          'aria-label': `${DAY_LABELS[dayIndex]} ${slot}`,
        });

        // Pre-check the source slot
        if (isSource) {
          checkbox.checked = true;
        }

        checkboxMap.set(key, { checkbox, dayIndex, slot });

        const label = el('label', {
          className: `copy-slot-label${isSource ? ' is-source' : ''}`,
          'for': `copy-slot-${key}`,
          title: `${DAY_LABELS[dayIndex]} ${slot.charAt(0).toUpperCase() + slot.slice(1)}`,
        }, checkbox);

        return label;
      });

      return el('div', { className: 'copy-grid-row' }, slotLabel, ...cells);
    });

    // Select All / Clear All helpers
    const selectAllBtn = el('button', {
      className: 'btn btn-ghost copy-grid-action-btn',
      type: 'button',
    }, 'Select all');
    selectAllBtn.addEventListener('click', () => {
      checkboxMap.forEach(({ checkbox }) => { checkbox.checked = true; });
    });

    const clearAllBtn = el('button', {
      className: 'btn btn-ghost copy-grid-action-btn',
      type: 'button',
    }, 'Clear all');
    clearAllBtn.addEventListener('click', () => {
      checkboxMap.forEach(({ checkbox }) => { checkbox.checked = false; });
    });

    // Copy button
    const copyActionBtn = el('button', {
      className: 'btn btn-primary',
      type: 'button',
    }, 'Copy');

    copyActionBtn.addEventListener('click', async () => {
      const targets = [];
      checkboxMap.forEach(({ checkbox, dayIndex, slot }) => {
        if (checkbox.checked) {
          targets.push({ dayIndex, slot });
        }
      });

      if (targets.length === 0) {
        showToast('Select at least one slot to copy to.', 'warning');
        return;
      }

      // Disable the button to prevent double-clicks
      copyActionBtn.disabled = true;
      copyActionBtn.textContent = 'Copying…';

      closeModal();

      // Fire one PUT per target slot (sequentially to avoid race conditions)
      let succeeded = 0;
      const failed = [];

      for (const { dayIndex, slot } of targets) {
        try {
          await apiFetch('/api/meals', {
            method: 'PUT',
            body: {
              week_start: state.weekStart,
              day_of_week: dayIndex,
              meal_slot: slot,
              recipe_id: meal.recipe_id,
            },
          });
          succeeded++;
        } catch {
          // apiFetch already shows an error toast per failure
          failed.push(`${DAY_LABELS[dayIndex]} ${slot}`);
        }
      }

      // Summary toast
      if (failed.length === 0) {
        showToast(`Copied to ${succeeded} slot${succeeded !== 1 ? 's' : ''}.`, 'success');
      } else if (succeeded > 0) {
        showToast(
          `Copied to ${succeeded} slot${succeeded !== 1 ? 's' : ''}. Failed: ${failed.join(', ')}.`,
          'warning',
        );
      }
      // If all failed, error toasts from apiFetch already shown; no extra needed.

      // Refresh the grid so day totals and cell content update
      await render();
    });

    // Cancel button
    const cancelBtn = el('button', {
      className: 'btn btn-secondary',
      type: 'button',
    }, 'Cancel');
    cancelBtn.addEventListener('click', () => closeModal());

    // Assemble modal body
    const recipeLabel = el('p', { className: 'copy-recipe-label' },
      el('strong', {}, meal.recipe_title),
      ' → select destination slots:',
    );

    const gridActions = el('div', { className: 'copy-grid-actions' },
      selectAllBtn,
      clearAllBtn,
    );

    const grid = el('div', { className: 'copy-slots-grid' },
      el('div', { className: 'copy-grid-header' }, ...headerCells),
      ...rows,
    );

    const footer = el('div', { className: 'copy-modal-footer' },
      cancelBtn,
      copyActionBtn,
    );

    const body = el('div', { className: 'copy-slots-body' },
      recipeLabel,
      gridActions,
      grid,
      footer,
    );

    openModal(`Copy "${meal.recipe_title}" to Slots`, body, { wide: false });
  }

  /* ----------------------------------------------------------
     Boot
     ---------------------------------------------------------- */

  await render();
}
