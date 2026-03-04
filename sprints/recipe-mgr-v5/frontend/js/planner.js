/**
 * Weekly Meal Planner View
 * 7-column weekly grid for assigning recipes to meal slots
 */

import { apiCall, appState, formatTime, formatDate, getMondayOfWeek } from './app.js';
import { showModal, showToast, createEmptyState } from './ui.js';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const MEAL_SLOTS = ['breakfast', 'lunch', 'dinner', 'snack'];

let currentWeekStart = appState.currentWeek;
let weekMeals = [];

// ===== Main Render Function =====
export async function render(container) {
  container.innerHTML = '';

  // Update currentWeekStart from appState
  currentWeekStart = appState.currentWeek;

  // Header with week navigation
  const header = createHeader();
  container.appendChild(header);

  // Meal planner grid
  const grid = document.createElement('div');
  grid.id = 'planner-grid';
  grid.className = 'planner-grid';
  container.appendChild(grid);

  // Day summary row
  const summary = document.createElement('div');
  summary.id = 'day-summary';
  summary.className = 'day-summary';
  container.appendChild(summary);

  // Load week meals
  await loadWeekMeals();
}

// ===== Header with Week Navigation =====
function createHeader() {
  const header = document.createElement('div');
  header.className = 'view-header';

  const weekDisplay = getWeekDisplayString(currentWeekStart);

  header.innerHTML = `
    <div class="flex justify-between items-center mb-lg">
      <h2>Weekly Meal Planner</h2>
      <div class="flex gap-md items-center">
        <button class="btn btn-secondary" id="prev-week-btn">← Previous</button>
        <button class="btn btn-ghost" id="this-week-btn">This Week</button>
        <button class="btn btn-secondary" id="next-week-btn">Next →</button>
      </div>
    </div>
    <div class="flex justify-between items-center">
      <p style="color: var(--text-secondary);">${weekDisplay}</p>
    </div>
  `;

  setTimeout(() => {
    document.getElementById('prev-week-btn').addEventListener('click', () => {
      navigateWeek(-1);
    });

    document.getElementById('this-week-btn').addEventListener('click', () => {
      navigateWeek(0, true);
    });

    document.getElementById('next-week-btn').addEventListener('click', () => {
      navigateWeek(1);
    });
  }, 0);

  return header;
}

function getWeekDisplayString(weekStart) {
  const start = new Date(weekStart + 'T00:00:00');
  const end = new Date(start);
  end.setDate(start.getDate() + 6);

  const startStr = formatDate(weekStart);
  const endDate = end.toISOString().split('T')[0];
  const endStr = formatDate(endDate);

  return `Week of ${startStr} – ${endStr}`;
}

function navigateWeek(offset, reset = false) {
  if (reset) {
    currentWeekStart = appState.currentWeek;
  } else {
    const currentDate = new Date(currentWeekStart + 'T00:00:00');
    currentDate.setDate(currentDate.getDate() + (offset * 7));
    currentWeekStart = currentDate.toISOString().split('T')[0];
  }

  // Re-render just the header and reload
  const headerEl = document.querySelector('.view-header');
  const newHeader = createHeader();
  headerEl.replaceWith(newHeader);

  loadWeekMeals();
}

// ===== Load Week Meals =====
async function loadWeekMeals() {
  try {
    weekMeals = await apiCall(`/meals/?week=${currentWeekStart}`);
    renderPlannerGrid();
    renderDaySummary();
  } catch (error) {
    console.error('Failed to load week meals:', error);
  }
}

// ===== Render Planner Grid =====
function renderPlannerGrid() {
  const grid = document.getElementById('planner-grid');
  grid.innerHTML = '';

  // Header row with day names
  const headerRow = document.createElement('div');
  headerRow.className = 'planner-row planner-header-row';
  headerRow.innerHTML = '<div class="planner-cell planner-corner-cell"></div>';

  DAYS.forEach((day, index) => {
    const dayDate = new Date(currentWeekStart + 'T00:00:00');
    dayDate.setDate(dayDate.getDate() + index);
    const dateStr = dayDate.toISOString().split('T')[0];

    const cell = document.createElement('div');
    cell.className = 'planner-cell planner-day-header';
    cell.innerHTML = `
      <div class="day-name">${day}</div>
      <div class="day-date">${formatDate(dateStr).split(', ')[1]}</div>
    `;
    headerRow.appendChild(cell);
  });

  grid.appendChild(headerRow);

  // Meal slot rows
  MEAL_SLOTS.forEach(slot => {
    const row = document.createElement('div');
    row.className = 'planner-row';

    // Slot label
    const label = document.createElement('div');
    label.className = 'planner-cell planner-slot-label';
    label.textContent = slot.charAt(0).toUpperCase() + slot.slice(1);
    row.appendChild(label);

    // Day cells for this slot
    DAYS.forEach((day, dayIndex) => {
      const cell = createMealCell(dayIndex, slot);
      row.appendChild(cell);
    });

    grid.appendChild(row);
  });
}

function createMealCell(dayOfWeek, mealSlot) {
  const cell = document.createElement('div');
  cell.className = 'planner-cell planner-meal-cell';

  // Find meal for this slot
  const meal = weekMeals.find(m => m.day_of_week === dayOfWeek && m.meal_slot === mealSlot);

  if (meal) {
    cell.innerHTML = `
      <div class="meal-assignment">
        <div class="meal-title">${escapeHtml(meal.recipe_title)}</div>
        <div class="meal-time">⏱️ ${formatTime(meal.prep_time_minutes + meal.cook_time_minutes)}</div>
      </div>
    `;

    cell.addEventListener('click', () => showMealMenu(meal, dayOfWeek, mealSlot));
  } else {
    cell.innerHTML = '<button class="add-meal-btn">+</button>';
    cell.querySelector('.add-meal-btn').addEventListener('click', () => showRecipePicker(dayOfWeek, mealSlot));
  }

  return cell;
}

// ===== Show Recipe Picker Modal =====
async function showRecipePicker(dayOfWeek, mealSlot) {
  try {
    const recipes = await apiCall('/recipes/');

    const content = document.createElement('div');

    // Search box
    const searchBox = document.createElement('input');
    searchBox.type = 'search';
    searchBox.className = 'form-input';
    searchBox.placeholder = '🔍 Search recipes...';
    searchBox.style.marginBottom = 'var(--space-md)';

    content.appendChild(searchBox);

    // Recipe list
    const recipeList = document.createElement('div');
    recipeList.className = 'recipe-picker-list';
    content.appendChild(recipeList);

    function renderRecipeList(filteredRecipes) {
      recipeList.innerHTML = '';

      if (filteredRecipes.length === 0) {
        const empty = createEmptyState('🔍', 'No recipes found', 'Try a different search term');
        recipeList.appendChild(empty);
        return;
      }

      filteredRecipes.forEach(recipe => {
        const item = document.createElement('div');
        item.className = 'recipe-picker-item';

        const totalTime = recipe.prep_time_minutes + recipe.cook_time_minutes;

        item.innerHTML = `
          <div class="flex justify-between items-center">
            <div>
              <div class="recipe-picker-title">${escapeHtml(recipe.title)}</div>
              <div class="recipe-picker-meta">
                <span class="badge badge-${recipe.category}">${recipe.category}</span>
                <span style="margin-left: var(--space-sm); color: var(--text-muted);">⏱️ ${formatTime(totalTime)}</span>
              </div>
            </div>
            <button class="btn btn-primary btn-sm assign-btn" data-recipe-id="${recipe.id}">
              Assign
            </button>
          </div>
        `;

        item.querySelector('.assign-btn').addEventListener('click', async () => {
          await assignRecipeToSlot(recipe.id, dayOfWeek, mealSlot);
          modal.close();
        });

        recipeList.appendChild(item);
      });
    }

    renderRecipeList(recipes);

    // Search functionality
    searchBox.addEventListener('input', (e) => {
      const term = e.target.value.toLowerCase();
      const filtered = recipes.filter(r =>
        r.title.toLowerCase().includes(term) ||
        r.description.toLowerCase().includes(term) ||
        r.category.toLowerCase().includes(term)
      );
      renderRecipeList(filtered);
    });

    const slotName = `${DAYS[dayOfWeek]} ${mealSlot.charAt(0).toUpperCase() + mealSlot.slice(1)}`;
    const modal = showModal(`Assign Recipe to ${slotName}`, content);
  } catch (error) {
    console.error('Failed to load recipes:', error);
  }
}

async function assignRecipeToSlot(recipeId, dayOfWeek, mealSlot) {
  try {
    await apiCall('/meals/', {
      method: 'PUT',
      body: JSON.stringify({
        week_start: currentWeekStart,
        day_of_week: dayOfWeek,
        meal_slot: mealSlot,
        recipe_id: recipeId
      })
    });

    showToast('Recipe assigned to meal plan', 'success');
    await loadWeekMeals();
  } catch (error) {
    // Error already shown by apiCall
  }
}

// ===== Show Meal Menu (for assigned meals) =====
function showMealMenu(meal, dayOfWeek, mealSlot) {
  const content = document.createElement('div');

  content.innerHTML = `
    <p style="color: var(--text-secondary); margin-bottom: var(--space-lg);">
      ${DAYS[dayOfWeek]} ${mealSlot.charAt(0).toUpperCase() + mealSlot.slice(1)}
    </p>

    <div style="margin-bottom: var(--space-xl);">
      <h3 style="margin-bottom: var(--space-sm);">${escapeHtml(meal.recipe_title)}</h3>
      <div style="color: var(--text-muted);">
        ⏱️ Prep: ${formatTime(meal.prep_time_minutes)} | Cook: ${formatTime(meal.cook_time_minutes)}
      </div>
    </div>

    <div class="modal-actions" style="flex-direction: column; gap: var(--space-sm);">
      <button class="btn btn-secondary w-full" id="swap-btn">🔄 Swap Recipe</button>
      <button class="btn btn-secondary w-full" id="copy-btn">📋 Copy to Other Slots</button>
      <button class="btn btn-danger w-full" id="clear-btn">✕ Clear Slot</button>
    </div>
  `;

  const modal = showModal(meal.recipe_title, content);

  content.querySelector('#swap-btn').addEventListener('click', () => {
    modal.close();
    showRecipePicker(dayOfWeek, mealSlot);
  });

  content.querySelector('#copy-btn').addEventListener('click', () => {
    modal.close();
    showCopyToSlotsModal(meal.recipe_id);
  });

  content.querySelector('#clear-btn').addEventListener('click', async () => {
    try {
      await apiCall(`/meals/${meal.id}`, { method: 'DELETE' });
      showToast('Meal assignment cleared', 'success');
      modal.close();
      await loadWeekMeals();
    } catch (error) {
      // Error already shown by apiCall
    }
  });
}

// ===== Copy to Slots Modal =====
function showCopyToSlotsModal(recipeId) {
  const content = document.createElement('div');

  content.innerHTML = `
    <p style="color: var(--text-secondary); margin-bottom: var(--space-lg);">
      Select which meal slots to copy this recipe to:
    </p>

    <div id="slot-selection-grid" class="slot-selection-grid"></div>

    <div class="modal-actions">
      <button class="btn btn-secondary" id="cancel-copy-btn">Cancel</button>
      <button class="btn btn-primary" id="confirm-copy-btn">Copy to Selected Slots</button>
    </div>
  `;

  const grid = content.querySelector('#slot-selection-grid');

  // Create checkbox grid
  DAYS.forEach((day, dayIndex) => {
    MEAL_SLOTS.forEach(slot => {
      const checkbox = document.createElement('label');
      checkbox.className = 'slot-checkbox-label';

      checkbox.innerHTML = `
        <input type="checkbox" class="form-checkbox slot-checkbox" data-day="${dayIndex}" data-slot="${slot}" />
        <span>${day.substring(0, 3)} - ${slot.charAt(0).toUpperCase() + slot.slice(1)}</span>
      `;

      grid.appendChild(checkbox);
    });
  });

  const modal = showModal('Copy Recipe to Slots', content);

  content.querySelector('#cancel-copy-btn').addEventListener('click', () => {
    modal.close();
  });

  content.querySelector('#confirm-copy-btn').addEventListener('click', async () => {
    const checkboxes = content.querySelectorAll('.slot-checkbox:checked');

    if (checkboxes.length === 0) {
      showToast('Please select at least one slot', 'warning');
      return;
    }

    const assignments = Array.from(checkboxes).map(cb => ({
      week_start: currentWeekStart,
      day_of_week: parseInt(cb.dataset.day),
      meal_slot: cb.dataset.slot,
      recipe_id: recipeId
    }));

    try {
      // Assign to all selected slots
      for (const assignment of assignments) {
        await apiCall('/meals/', {
          method: 'PUT',
          body: JSON.stringify(assignment)
        });
      }

      showToast(`Recipe copied to ${assignments.length} slot(s)`, 'success');
      modal.close();
      await loadWeekMeals();
    } catch (error) {
      // Error already shown by apiCall
    }
  });
}

// ===== Render Day Summary =====
function renderDaySummary() {
  const summary = document.getElementById('day-summary');
  summary.innerHTML = '<h3 style="margin-bottom: var(--space-md);">Daily Time Summary</h3>';

  const summaryGrid = document.createElement('div');
  summaryGrid.className = 'summary-grid';

  DAYS.forEach((day, dayIndex) => {
    const dayMeals = weekMeals.filter(m => m.day_of_week === dayIndex);
    const totalPrepTime = dayMeals.reduce((sum, m) => sum + m.prep_time_minutes, 0);
    const totalCookTime = dayMeals.reduce((sum, m) => sum + m.cook_time_minutes, 0);
    const totalTime = totalPrepTime + totalCookTime;

    const summaryItem = document.createElement('div');
    summaryItem.className = 'summary-item';

    summaryItem.innerHTML = `
      <div class="summary-day">${day.substring(0, 3)}</div>
      <div class="summary-time">⏱️ ${formatTime(totalTime)}</div>
      <div class="summary-meals">${dayMeals.length} meal${dayMeals.length !== 1 ? 's' : ''}</div>
    `;

    summaryGrid.appendChild(summaryItem);
  });

  summary.appendChild(summaryGrid);
}

// ===== Utility =====
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
