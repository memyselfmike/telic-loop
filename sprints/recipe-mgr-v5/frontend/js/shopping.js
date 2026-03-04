/**
 * Shopping List View
 * Generate, manage, and check off shopping list items grouped by grocery section
 */

import { apiCall, appState } from './app.js';
import { showConfirm, showToast, createEmptyState } from './ui.js';

const SECTION_ORDER = ['produce', 'meat', 'dairy', 'pantry', 'frozen', 'other'];
const SECTION_ICONS = {
  produce: '🥬',
  meat: '🥩',
  dairy: '🥛',
  pantry: '🥫',
  frozen: '❄️',
  other: '🛒'
};

let currentList = null;

// ===== Main Render Function =====
export async function render(container) {
  container.innerHTML = '';

  // Header
  const header = createHeader();
  container.appendChild(header);

  // Shopping list container
  const listContainer = document.createElement('div');
  listContainer.id = 'shopping-list-container';
  container.appendChild(listContainer);

  // Load current shopping list
  await loadShoppingList();
}

// ===== Header =====
function createHeader() {
  const header = document.createElement('div');
  header.className = 'view-header';

  header.innerHTML = `
    <div class="flex justify-between items-center mb-lg">
      <h2>Shopping List</h2>
      <button class="btn btn-primary" id="generate-list-btn">
        📝 Generate from This Week
      </button>
    </div>
  `;

  setTimeout(() => {
    document.getElementById('generate-list-btn').addEventListener('click', generateShoppingList);
  }, 0);

  return header;
}

// ===== Load Shopping List =====
async function loadShoppingList() {
  try {
    currentList = await apiCall('/shopping/current');
    renderShoppingList();
  } catch (error) {
    // If no list exists, show empty state
    currentList = null;
    renderShoppingList();
  }
}

// ===== Generate Shopping List =====
async function generateShoppingList() {
  // Check if list exists and confirm replacement
  if (currentList && currentList.items && currentList.items.length > 0) {
    const confirmed = await showConfirm(
      'A shopping list already exists. Generating a new list will replace the current one. Continue?',
      'Generate New List',
      'Cancel'
    );

    if (!confirmed) return;
  }

  try {
    await apiCall('/shopping/generate', {
      method: 'POST',
      body: JSON.stringify({ week_start: appState.currentWeek })
    });

    showToast('Shopping list generated successfully', 'success');
    await loadShoppingList();
  } catch (error) {
    // Error already shown by apiCall
  }
}

// ===== Render Shopping List =====
function renderShoppingList() {
  const container = document.getElementById('shopping-list-container');
  container.innerHTML = '';

  if (!currentList || !currentList.items || currentList.items.length === 0) {
    const empty = createEmptyState(
      '🛒',
      'No shopping list yet',
      'Generate a shopping list from your weekly meal plan to get started'
    );
    container.appendChild(empty);
    return;
  }

  // Add manual item form
  const addItemForm = createAddItemForm();
  container.appendChild(addItemForm);

  // Item count summary
  const summary = createSummary();
  container.appendChild(summary);

  // Group items by section
  const itemsBySection = groupItemsBySection(currentList.items);

  // Render each section
  SECTION_ORDER.forEach(section => {
    if (itemsBySection[section] && itemsBySection[section].length > 0) {
      const sectionEl = createSection(section, itemsBySection[section]);
      container.appendChild(sectionEl);
    }
  });
}

function groupItemsBySection(items) {
  const grouped = {};

  items.forEach(item => {
    const section = item.grocery_section || 'other';
    if (!grouped[section]) {
      grouped[section] = [];
    }
    grouped[section].push(item);
  });

  // Sort items within each section: unchecked first, then checked
  Object.keys(grouped).forEach(section => {
    grouped[section].sort((a, b) => a.checked - b.checked);
  });

  return grouped;
}

// ===== Add Item Form =====
function createAddItemForm() {
  const form = document.createElement('div');
  form.className = 'add-item-form';

  form.innerHTML = `
    <h3 style="margin-bottom: var(--space-md);">Add Item</h3>
    <div class="flex gap-sm" style="align-items: flex-end;">
      <div class="form-field" style="flex: 2; margin-bottom: 0;">
        <label>Item Name</label>
        <input type="text" id="manual-item-name" class="form-input" placeholder="e.g., Apples" />
      </div>

      <div class="form-field" style="flex: 1; margin-bottom: 0;">
        <label>Quantity</label>
        <input type="number" id="manual-item-quantity" class="form-input" placeholder="1" min="0" step="0.01" />
      </div>

      <div class="form-field" style="flex: 1; margin-bottom: 0;">
        <label>Unit</label>
        <select id="manual-item-unit" class="form-select">
          <option value="whole">whole</option>
          <option value="lb">lb</option>
          <option value="oz">oz</option>
          <option value="cup">cup</option>
          <option value="tbsp">tbsp</option>
          <option value="tsp">tsp</option>
          <option value="piece">piece</option>
        </select>
      </div>

      <div class="form-field" style="flex: 1; margin-bottom: 0;">
        <label>Section</label>
        <select id="manual-item-section" class="form-select">
          <option value="produce">Produce</option>
          <option value="meat">Meat</option>
          <option value="dairy">Dairy</option>
          <option value="pantry">Pantry</option>
          <option value="frozen">Frozen</option>
          <option value="other">Other</option>
        </select>
      </div>

      <button class="btn btn-primary" id="add-manual-item-btn" style="margin-bottom: 0;">
        ➕ Add
      </button>
    </div>
  `;

  setTimeout(() => {
    form.querySelector('#add-manual-item-btn').addEventListener('click', addManualItem);

    // Allow Enter key to add item
    const nameInput = form.querySelector('#manual-item-name');
    nameInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') addManualItem();
    });
  }, 0);

  return form;
}

async function addManualItem() {
  const name = document.getElementById('manual-item-name').value.trim();
  const quantity = parseFloat(document.getElementById('manual-item-quantity').value) || 1;
  const unit = document.getElementById('manual-item-unit').value;
  const section = document.getElementById('manual-item-section').value;

  if (!name) {
    showToast('Please enter an item name', 'error');
    return;
  }

  try {
    await apiCall('/shopping/items', {
      method: 'POST',
      body: JSON.stringify({
        item: name,
        quantity,
        unit,
        grocery_section: section,
        source: 'manual'
      })
    });

    showToast('Item added to shopping list', 'success');

    // Clear form
    document.getElementById('manual-item-name').value = '';
    document.getElementById('manual-item-quantity').value = '';

    await loadShoppingList();
  } catch (error) {
    // Error already shown by apiCall
  }
}

// ===== Summary Bar =====
function createSummary() {
  const totalItems = currentList.items.length;
  const checkedItems = currentList.items.filter(item => item.checked).length;

  const summary = document.createElement('div');
  summary.className = 'shopping-summary';

  summary.innerHTML = `
    <div class="flex justify-between items-center">
      <span>${totalItems} item${totalItems !== 1 ? 's' : ''}, ${checkedItems} checked</span>
    </div>
  `;

  return summary;
}

// ===== Section =====
function createSection(sectionName, items) {
  const section = document.createElement('div');
  section.className = 'shopping-section';

  // Section header
  const header = document.createElement('div');
  header.className = 'shopping-section-header';
  header.innerHTML = `
    ${SECTION_ICONS[sectionName]} ${sectionName.charAt(0).toUpperCase() + sectionName.slice(1)}
  `;

  section.appendChild(header);

  // Items
  const itemsList = document.createElement('div');
  itemsList.className = 'shopping-items-list';

  items.forEach(item => {
    const itemEl = createItemRow(item);
    itemsList.appendChild(itemEl);
  });

  section.appendChild(itemsList);

  return section;
}

// ===== Item Row =====
function createItemRow(item) {
  const row = document.createElement('div');
  row.className = `shopping-item-row ${item.checked ? 'checked' : ''}`;

  row.innerHTML = `
    <label class="shopping-item-checkbox">
      <input type="checkbox" class="form-checkbox" ${item.checked ? 'checked' : ''} data-item-id="${item.id}" />
    </label>

    <div class="shopping-item-content">
      <span class="shopping-item-quantity">${formatQuantity(item.quantity)} ${item.unit}</span>
      <span class="shopping-item-name">${escapeHtml(item.item)}</span>
    </div>

    <button class="btn btn-danger btn-icon btn-sm delete-item-btn" data-item-id="${item.id}" aria-label="Delete item">
      🗑️
    </button>
  `;

  // Checkbox toggle
  const checkbox = row.querySelector('.form-checkbox');
  checkbox.addEventListener('change', async () => {
    await toggleItemChecked(item.id, checkbox.checked);
  });

  // Delete button
  const deleteBtn = row.querySelector('.delete-item-btn');
  deleteBtn.addEventListener('click', async () => {
    await deleteItem(item.id);
  });

  return row;
}

// ===== Toggle Item Checked =====
async function toggleItemChecked(itemId, checked) {
  try {
    await apiCall(`/shopping/items/${itemId}`, {
      method: 'PATCH'
    });

    // Reload to show updated state (checked items move to bottom)
    await loadShoppingList();
  } catch (error) {
    // Error already shown by apiCall
    // Revert checkbox on error
    await loadShoppingList();
  }
}

// ===== Delete Item =====
async function deleteItem(itemId) {
  try {
    await apiCall(`/shopping/items/${itemId}`, {
      method: 'DELETE'
    });

    showToast('Item removed from shopping list', 'success');
    await loadShoppingList();
  } catch (error) {
    // Error already shown by apiCall
  }
}

// ===== Utilities =====
function formatQuantity(qty) {
  // Format to 1 decimal place, remove trailing zeros
  const formatted = parseFloat(qty.toFixed(1));
  return formatted % 1 === 0 ? Math.floor(formatted) : formatted;
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
