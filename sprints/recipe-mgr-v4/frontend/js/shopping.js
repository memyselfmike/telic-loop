/**
 * Shopping List View
 * Generate, view, and manage shopping lists with section grouping
 */

router.register('shopping', mountShoppingView);

const GROCERY_SECTIONS = ['produce', 'meat', 'dairy', 'pantry', 'frozen', 'other'];
const UNIT_OPTIONS = ['tsp', 'tbsp', 'cup', 'oz', 'lb', 'whole', 'piece', 'each'];

let currentShoppingList = null;

async function mountShoppingView(container) {
    container.innerHTML = `
        <div class="flex-between mb-2">
            <h2>Shopping List</h2>
            <div class="flex gap-1">
                <button class="btn btn-secondary" onclick="navigateShoppingWeek(-1)">← Previous Week</button>
                <button class="btn btn-secondary" onclick="navigateShoppingWeek(0)">This Week</button>
                <button class="btn btn-secondary" onclick="navigateShoppingWeek(1)">Next Week →</button>
            </div>
        </div>

        <div class="mb-2 text-center">
            <strong id="shopping-week-display"></strong>
        </div>

        <div class="mb-2">
            <button class="btn btn-primary" onclick="generateShoppingList()">
                Generate from This Week
            </button>
        </div>

        <div id="shopping-content"></div>
    `;

    await updateShoppingWeekDisplay();
    await loadShoppingList();
}

function updateShoppingWeekDisplay() {
    const weekDisplay = document.getElementById('shopping-week-display');
    if (weekDisplay) {
        weekDisplay.textContent = `Week of ${formatDate(appState.currentWeek)}`;
    }
}

async function navigateShoppingWeek(weekOffset) {
    if (weekOffset === 0) {
        appState.currentWeek = getMondayOfCurrentWeek();
    } else {
        appState.currentWeek = addWeeks(appState.currentWeek, weekOffset);
    }
    updateShoppingWeekDisplay();
}

async function generateShoppingList() {
    // Check if a shopping list already exists
    if (currentShoppingList && currentShoppingList.items.length > 0) {
        if (!confirm('A shopping list already exists. Replace it with a new one generated from the current week?')) {
            return;
        }
    }

    try {
        const response = await fetchJSON('/api/shopping/generate', {
            method: 'POST',
            body: JSON.stringify({
                week_start: appState.currentWeek
            })
        });

        currentShoppingList = response;
        renderShoppingList();
        showSuccess('Shopping list generated successfully');
    } catch (error) {
        showError(`Failed to generate shopping list: ${error.message}`);
    }
}

async function loadShoppingList() {
    const contentDiv = document.getElementById('shopping-content');
    if (!contentDiv) return;

    try {
        currentShoppingList = await fetchJSON('/api/shopping/current');
        renderShoppingList();
    } catch (error) {
        // No shopping list exists yet - show empty state
        if (error.message.includes('404') || error.message.includes('not found')) {
            renderEmptyState();
        } else {
            contentDiv.innerHTML = `<div class="text-center text-muted">Error loading shopping list: ${escapeHtml(error.message)}</div>`;
        }
    }
}

function renderEmptyState() {
    const contentDiv = document.getElementById('shopping-content');
    if (!contentDiv) return;

    contentDiv.innerHTML = `
        <div class="card text-center" style="padding: 3rem;">
            <h3 style="color: var(--text-muted); margin-bottom: 1rem;">No Shopping List Yet</h3>
            <p class="text-muted">Generate a shopping list from your weekly meal plan to get started.</p>
        </div>
    `;
}

function renderShoppingList() {
    const contentDiv = document.getElementById('shopping-content');
    if (!contentDiv) return;

    if (!currentShoppingList || !currentShoppingList.items || currentShoppingList.items.length === 0) {
        renderEmptyState();
        return;
    }

    // Group items by grocery section
    const itemsBySection = {};
    GROCERY_SECTIONS.forEach(section => {
        itemsBySection[section] = [];
    });

    currentShoppingList.items.forEach(item => {
        const section = item.grocery_section || 'other';
        if (!itemsBySection[section]) {
            itemsBySection[section] = [];
        }
        itemsBySection[section].push(item);
    });

    // Sort items within each section: unchecked first, then checked
    Object.keys(itemsBySection).forEach(section => {
        itemsBySection[section].sort((a, b) => {
            if (a.checked === b.checked) {
                return a.item.localeCompare(b.item);
            }
            return a.checked ? 1 : -1;
        });
    });

    // Calculate totals
    const totalItems = currentShoppingList.items.length;
    const checkedItems = currentShoppingList.items.filter(item => item.checked).length;

    // Render
    let html = `
        <div class="mb-2 flex-between">
            <div>
                <strong>Summary:</strong>
                <span>${totalItems} items, ${checkedItems} checked</span>
            </div>
            <button class="btn btn-secondary btn-small" onclick="showAddItemForm()">+ Add Item</button>
        </div>
    `;

    // Render sections
    GROCERY_SECTIONS.forEach(section => {
        const items = itemsBySection[section];
        if (items.length === 0) return;

        html += `
            <div class="shopping-section mb-2">
                <h3 class="section-header">${section.charAt(0).toUpperCase() + section.slice(1)}</h3>
                <div class="shopping-items">
                    ${items.map(item => renderShoppingItem(item)).join('')}
                </div>
            </div>
        `;
    });

    contentDiv.innerHTML = html;
}

function renderShoppingItem(item) {
    const checkedClass = item.checked ? 'checked' : '';
    const strikethroughStyle = item.checked ? 'text-decoration: line-through; color: var(--text-muted);' : '';

    return `
        <div class="shopping-item ${checkedClass}" style="display: flex; align-items: center; padding: 0.5rem; border-bottom: 1px solid var(--border-color);">
            <input
                type="checkbox"
                ${item.checked ? 'checked' : ''}
                onchange="toggleItemChecked(${item.id})"
                style="margin-right: 1rem; cursor: pointer; width: 18px; height: 18px;"
            >
            <div style="flex: 1; ${strikethroughStyle}">
                <strong>${escapeHtml(item.item)}</strong>
                <span class="text-muted" style="margin-left: 0.5rem;">
                    ${item.quantity} ${item.unit}
                </span>
            </div>
            <button
                class="btn btn-danger btn-small"
                onclick="removeItem(${item.id})"
                style="margin-left: 1rem;"
            >
                Remove
            </button>
        </div>
    `;
}

async function toggleItemChecked(itemId) {
    try {
        await fetchJSON(`/api/shopping/items/${itemId}`, {
            method: 'PATCH'
        });

        // Update local state
        const item = currentShoppingList.items.find(i => i.id === itemId);
        if (item) {
            item.checked = !item.checked;
        }

        renderShoppingList();
    } catch (error) {
        showError(`Failed to update item: ${error.message}`);
        // Reload to ensure consistency
        await loadShoppingList();
    }
}

async function removeItem(itemId) {
    if (!confirm('Remove this item from the shopping list?')) {
        return;
    }

    try {
        await fetchJSON(`/api/shopping/items/${itemId}`, {
            method: 'DELETE'
        });

        // Update local state
        currentShoppingList.items = currentShoppingList.items.filter(i => i.id !== itemId);

        renderShoppingList();
        showSuccess('Item removed');
    } catch (error) {
        showError(`Failed to remove item: ${error.message}`);
        await loadShoppingList();
    }
}

function showAddItemForm() {
    const content = `
        <h2 class="modal-title">Add Manual Item</h2>

        <form id="add-item-form" onsubmit="submitAddItem(event)">
            <div class="form-group">
                <label for="add-item-name" class="form-label">Item Name *</label>
                <input type="text" id="add-item-name" class="form-input" required>
            </div>

            <div class="form-row">
                <div class="form-group" style="flex: 1;">
                    <label for="add-item-quantity" class="form-label">Quantity *</label>
                    <input type="number" id="add-item-quantity" class="form-input" step="0.1" min="0.1" value="1" required>
                </div>

                <div class="form-group" style="flex: 1;">
                    <label for="add-item-unit" class="form-label">Unit *</label>
                    <select id="add-item-unit" class="form-input" required>
                        ${UNIT_OPTIONS.map(unit =>
                            `<option value="${unit}">${unit}</option>`
                        ).join('')}
                    </select>
                </div>
            </div>

            <div class="form-group">
                <label for="add-item-section" class="form-label">Grocery Section *</label>
                <select id="add-item-section" class="form-input" required>
                    ${GROCERY_SECTIONS.map(section =>
                        `<option value="${section}">${section.charAt(0).toUpperCase() + section.slice(1)}</option>`
                    ).join('')}
                </select>
            </div>

            <div class="flex gap-1 mt-2">
                <button type="submit" class="btn btn-primary">Add Item</button>
                <button type="button" class="btn btn-secondary" onclick="modal.hide()">Cancel</button>
            </div>
        </form>
    `;

    modal.show(content);
}

async function submitAddItem(event) {
    event.preventDefault();

    const itemName = document.getElementById('add-item-name').value.trim();
    const quantity = parseFloat(document.getElementById('add-item-quantity').value);
    const unit = document.getElementById('add-item-unit').value;
    const section = document.getElementById('add-item-section').value;

    if (!itemName) {
        showError('Item name is required');
        return;
    }

    try {
        const newItem = await fetchJSON('/api/shopping/items', {
            method: 'POST',
            body: JSON.stringify({
                item: itemName,
                quantity: quantity,
                unit: unit,
                grocery_section: section,
                checked: false
            })
        });

        // Add to local state
        if (currentShoppingList) {
            currentShoppingList.items.push(newItem);
        }

        modal.hide();
        renderShoppingList();
        showSuccess('Item added successfully');
    } catch (error) {
        showError(`Failed to add item: ${error.message}`);
    }
}

// HTML escape helper (same as in recipes.js)
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
