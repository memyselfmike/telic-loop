/**
 * Weekly Meal Planner View
 * Assign recipes to day/slot combinations, navigate weeks
 */

router.register('planner', mountPlannerView);

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const MEAL_SLOTS = ['breakfast', 'lunch', 'dinner', 'snack'];

let currentMealPlan = [];

async function mountPlannerView(container) {
    container.innerHTML = `
        <div class="flex-between mb-2">
            <h2>Weekly Meal Planner</h2>
            <div class="flex gap-1">
                <button class="btn btn-secondary" onclick="navigateWeek(-1)">← Previous Week</button>
                <button class="btn btn-secondary" onclick="navigateWeek(0)">This Week</button>
                <button class="btn btn-secondary" onclick="navigateWeek(1)">Next Week →</button>
            </div>
        </div>

        <div class="mb-2 text-center">
            <strong id="week-display"></strong>
        </div>

        <div id="meal-grid-container"></div>
    `;

    await loadMealPlan();
}

async function navigateWeek(weekOffset) {
    if (weekOffset === 0) {
        appState.currentWeek = getMondayOfCurrentWeek();
    } else {
        appState.currentWeek = addWeeks(appState.currentWeek, weekOffset);
    }
    await loadMealPlan();
}

async function loadMealPlan() {
    const weekDisplay = document.getElementById('week-display');
    const gridContainer = document.getElementById('meal-grid-container');

    if (!weekDisplay || !gridContainer) return;

    const endDate = addWeeks(appState.currentWeek, 1);
    weekDisplay.textContent = `Week of ${formatDate(appState.currentWeek)} - ${formatDate(addWeeks(appState.currentWeek, 0.857))}`;

    try {
        currentMealPlan = await fetchJSON(`/api/meals?week=${appState.currentWeek}`);
        renderMealGrid(gridContainer);
    } catch (error) {
        gridContainer.innerHTML = `<div class="text-center text-muted">Error loading meal plan: ${error.message}</div>`;
        showError(`Failed to load meal plan: ${error.message}`);
    }
}

function renderMealGrid(container) {
    const grid = document.createElement('div');
    grid.className = 'meal-grid';

    grid.appendChild(createMealHeader('', true));
    DAYS.forEach((day, index) => {
        grid.appendChild(createMealHeader(day));
    });

    MEAL_SLOTS.forEach((slot, slotIndex) => {
        grid.appendChild(createMealHeader(slot.charAt(0).toUpperCase() + slot.slice(1), true));

        for (let dayIndex = 0; dayIndex < 7; dayIndex++) {
            const mealEntry = currentMealPlan.find(m =>
                m.day_of_week === dayIndex && m.meal_slot === slot
            );

            grid.appendChild(createMealCell(dayIndex, slot, mealEntry));
        }
    });

    grid.appendChild(createMealHeader('Total Time', true));
    for (let dayIndex = 0; dayIndex < 7; dayIndex++) {
        const dayTotal = calculateDayTotal(dayIndex);
        grid.appendChild(createDaySummaryCell(dayTotal));
    }

    container.innerHTML = '';
    container.appendChild(grid);
}

function createMealHeader(text, isRowLabel = false) {
    const cell = document.createElement('div');
    cell.className = 'meal-cell meal-header';
    if (isRowLabel) {
        cell.style.fontWeight = '700';
    }
    cell.textContent = text;
    return cell;
}

function createMealCell(dayIndex, slot, mealEntry) {
    const cell = document.createElement('div');
    cell.className = 'meal-cell';

    if (mealEntry) {
        cell.innerHTML = `
            <div style="cursor: pointer; width: 100%;" onclick="showMealOptions(${mealEntry.id}, ${dayIndex}, '${slot}', ${mealEntry.recipe_id})">
                <strong>${escapeHtml(mealEntry.recipe_title)}</strong>
                <div style="font-size: 0.8em; color: var(--text-muted);">
                    ${mealEntry.prep_time_minutes + mealEntry.cook_time_minutes} min
                </div>
            </div>
        `;
    } else {
        cell.innerHTML = `
            <button class="btn btn-secondary btn-small" onclick="showRecipePicker(${dayIndex}, '${slot}')">+</button>
        `;
    }

    return cell;
}

function createDaySummaryCell(totalMinutes) {
    const cell = document.createElement('div');
    cell.className = 'meal-cell';
    cell.style.fontWeight = '600';
    cell.style.color = 'var(--accent-primary)';
    cell.textContent = `${totalMinutes} min`;
    return cell;
}

function calculateDayTotal(dayIndex) {
    return currentMealPlan
        .filter(m => m.day_of_week === dayIndex)
        .reduce((sum, m) => sum + m.prep_time_minutes + m.cook_time_minutes, 0);
}

async function showRecipePicker(dayIndex, slot) {
    try {
        const recipes = await fetchJSON('/api/recipes');

        if (recipes.length === 0) {
            showError('No recipes available. Create a recipe first.');
            return;
        }

        const content = `
            <h2 class="modal-title">Pick a Recipe</h2>

            <div class="form-group">
                <input type="text" id="picker-search" class="form-input" placeholder="Search recipes...">
            </div>

            <div id="picker-list" style="max-height: 400px; overflow-y: auto;">
                ${recipes.map(r => `
                    <div class="card mb-1" onclick="assignMeal(${dayIndex}, '${slot}', ${r.id})" style="cursor: pointer;">
                        <div class="flex-between">
                            <strong>${escapeHtml(r.title)}</strong>
                            <span class="badge badge-${r.category}">${r.category}</span>
                        </div>
                        <div class="text-muted" style="font-size: 0.9em;">
                            ${r.prep_time_minutes + r.cook_time_minutes} min total
                        </div>
                    </div>
                `).join('')}
            </div>

            <button class="btn btn-secondary mt-2" onclick="modal.hide()">Cancel</button>
        `;

        modal.show(content);

        const searchInput = document.getElementById('picker-search');
        searchInput.addEventListener('input', () => filterRecipePicker(recipes, dayIndex, slot));
    } catch (error) {
        showError(`Failed to load recipes: ${error.message}`);
    }
}

function filterRecipePicker(allRecipes, dayIndex, slot) {
    const searchTerm = document.getElementById('picker-search').value.toLowerCase();
    const filtered = allRecipes.filter(r =>
        r.title.toLowerCase().includes(searchTerm) ||
        r.tags.toLowerCase().includes(searchTerm)
    );

    const pickerList = document.getElementById('picker-list');
    pickerList.innerHTML = filtered.map(r => `
        <div class="card mb-1" onclick="assignMeal(${dayIndex}, '${slot}', ${r.id})" style="cursor: pointer;">
            <div class="flex-between">
                <strong>${escapeHtml(r.title)}</strong>
                <span class="badge badge-${r.category}">${r.category}</span>
            </div>
            <div class="text-muted" style="font-size: 0.9em;">
                ${r.prep_time_minutes + r.cook_time_minutes} min total
            </div>
        </div>
    `).join('');
}

async function assignMeal(dayIndex, slot, recipeId) {
    try {
        await fetchJSON('/api/meals', {
            method: 'PUT',
            body: JSON.stringify({
                week_start: appState.currentWeek,
                day_of_week: dayIndex,
                meal_slot: slot,
                recipe_id: recipeId
            })
        });

        modal.hide();
        await loadMealPlan();
        showSuccess('Meal assigned successfully');
    } catch (error) {
        showError(`Failed to assign meal: ${error.message}`);
    }
}

async function showMealOptions(mealId, dayIndex, slot, recipeId) {
    const content = `
        <h2 class="modal-title">Meal Options</h2>

        <div class="flex gap-1" style="flex-direction: column;">
            <button class="btn btn-secondary" onclick="viewRecipeFromPlanner(${recipeId})">View Recipe</button>
            <button class="btn btn-secondary" onclick="swapMeal(${dayIndex}, '${slot}')">Swap Recipe</button>
            <button class="btn btn-secondary" onclick="showCopyToSlots(${recipeId})">Copy to Multiple Slots</button>
            <button class="btn btn-danger" onclick="clearMealSlot(${mealId})">Clear Slot</button>
            <button class="btn btn-secondary" onclick="modal.hide()">Cancel</button>
        </div>
    `;

    modal.show(content);
}

async function viewRecipeFromPlanner(recipeId) {
    modal.hide();
    await showRecipeDetail(recipeId);
}

async function swapMeal(dayIndex, slot) {
    await showRecipePicker(dayIndex, slot);
}

async function clearMealSlot(mealId) {
    if (!confirm('Remove this meal from the plan?')) {
        return;
    }

    try {
        await fetchJSON(`/api/meals/${mealId}`, { method: 'DELETE' });
        modal.hide();
        await loadMealPlan();
        showSuccess('Meal slot cleared');
    } catch (error) {
        showError(`Failed to clear slot: ${error.message}`);
    }
}

function showCopyToSlots(recipeId) {
    const content = `
        <h2 class="modal-title">Copy to Multiple Slots</h2>
        <p class="mb-2">Select the day/slot combinations where you want to add this recipe:</p>

        <form id="copy-slots-form" onsubmit="executeCopyToSlots(event, ${recipeId})">
            <div id="slot-checkboxes" style="max-height: 400px; overflow-y: auto;">
                ${DAYS.map((day, dayIndex) => `
                    <div class="mb-2">
                        <strong>${day}</strong>
                        ${MEAL_SLOTS.map(slot => `
                            <label style="display: block; margin-left: 1rem; cursor: pointer;">
                                <input type="checkbox" name="slot" value="${dayIndex}-${slot}">
                                ${slot.charAt(0).toUpperCase() + slot.slice(1)}
                            </label>
                        `).join('')}
                    </div>
                `).join('')}
            </div>

            <div class="flex gap-1 mt-2">
                <button type="submit" class="btn btn-primary">Copy</button>
                <button type="button" class="btn btn-secondary" onclick="modal.hide()">Cancel</button>
            </div>
        </form>
    `;

    modal.show(content);
}

async function executeCopyToSlots(event, recipeId) {
    event.preventDefault();

    const form = event.target;
    const checkboxes = form.querySelectorAll('input[name="slot"]:checked');

    if (checkboxes.length === 0) {
        showError('Please select at least one slot');
        return;
    }

    try {
        const promises = Array.from(checkboxes).map(checkbox => {
            const [dayIndex, slot] = checkbox.value.split('-');
            return fetchJSON('/api/meals', {
                method: 'PUT',
                body: JSON.stringify({
                    week_start: appState.currentWeek,
                    day_of_week: parseInt(dayIndex),
                    meal_slot: slot,
                    recipe_id: recipeId
                })
            });
        });

        await Promise.all(promises);
        modal.hide();
        await loadMealPlan();
        showSuccess(`Recipe copied to ${checkboxes.length} slot(s)`);
    } catch (error) {
        showError(`Failed to copy recipe: ${error.message}`);
    }
}
