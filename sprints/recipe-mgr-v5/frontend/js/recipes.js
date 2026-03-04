/**
 * Recipe Collection View
 * Browse, search, filter, create, edit, and delete recipes
 */

import { apiCall, formatTime, debounce, parseTags, formatTagsString } from './app.js';
import { showModal, showConfirm, showToast, createEmptyState } from './ui.js';

let recipes = [];
let filteredRecipes = [];
let currentFilters = {
  search: '',
  category: '',
  tag: ''
};

// ===== Main Render Function =====
export async function render(container) {
  container.innerHTML = '';

  // Header with filter bar
  const header = createHeader();
  container.appendChild(header);

  // Recipe grid
  const grid = document.createElement('div');
  grid.id = 'recipe-grid';
  grid.className = 'card-grid';
  container.appendChild(grid);

  // Load recipes
  await loadRecipes();
}

// ===== Header with Filters =====
function createHeader() {
  const header = document.createElement('div');
  header.className = 'view-header';
  header.innerHTML = `
    <div class="flex justify-between items-center mb-lg">
      <h2>Recipe Collection</h2>
      <button class="btn btn-primary" id="add-recipe-btn">
        ➕ Add Recipe
      </button>
    </div>
    <div class="filter-bar">
      <input
        type="search"
        id="recipe-search"
        class="form-input"
        placeholder="🔍 Search recipes, ingredients..."
        style="flex: 1; max-width: 400px;"
      />
      <select id="category-filter" class="form-select" style="width: 200px;">
        <option value="">All Categories</option>
        <option value="breakfast">Breakfast</option>
        <option value="lunch">Lunch</option>
        <option value="dinner">Dinner</option>
        <option value="snack">Snack</option>
        <option value="dessert">Dessert</option>
      </select>
      <input
        type="text"
        id="tag-filter"
        class="form-input"
        placeholder="Filter by tag..."
        style="width: 200px;"
      />
    </div>
  `;

  // Add event listeners
  setTimeout(() => {
    document.getElementById('add-recipe-btn').addEventListener('click', () => showRecipeModal());

    const searchInput = document.getElementById('recipe-search');
    searchInput.addEventListener('input', debounce((e) => {
      currentFilters.search = e.target.value;
      applyFilters();
    }, 300));

    document.getElementById('category-filter').addEventListener('change', (e) => {
      currentFilters.category = e.target.value;
      applyFilters();
    });

    const tagInput = document.getElementById('tag-filter');
    tagInput.addEventListener('input', debounce((e) => {
      currentFilters.tag = e.target.value;
      applyFilters();
    }, 300));
  }, 0);

  return header;
}

// ===== Load Recipes =====
async function loadRecipes() {
  try {
    const params = new URLSearchParams();
    if (currentFilters.search) params.append('search', currentFilters.search);
    if (currentFilters.category) params.append('category', currentFilters.category);
    if (currentFilters.tag) params.append('tag', currentFilters.tag);

    const query = params.toString() ? `?${params.toString()}` : '';
    recipes = await apiCall(`/recipes/${query}`);
    filteredRecipes = recipes;
    renderRecipeGrid();
  } catch (error) {
    console.error('Failed to load recipes:', error);
  }
}

function applyFilters() {
  loadRecipes();
}

// ===== Render Recipe Grid =====
function renderRecipeGrid() {
  const grid = document.getElementById('recipe-grid');
  grid.innerHTML = '';

  if (filteredRecipes.length === 0) {
    const empty = createEmptyState(
      '🍳',
      'No recipes found',
      currentFilters.search || currentFilters.category || currentFilters.tag
        ? 'Try adjusting your filters'
        : 'Click "Add Recipe" to create your first recipe'
    );
    grid.appendChild(empty);
    return;
  }

  filteredRecipes.forEach(recipe => {
    const card = createRecipeCard(recipe);
    grid.appendChild(card);
  });
}

// ===== Create Recipe Card =====
function createRecipeCard(recipe) {
  const card = document.createElement('div');
  card.className = 'card';

  const totalTime = recipe.prep_time_minutes + recipe.cook_time_minutes;
  const tags = parseTags(recipe.tags);

  card.innerHTML = `
    <div class="card-header">
      <h3 class="card-title">${escapeHtml(recipe.title)}</h3>
      <span class="badge badge-${recipe.category}">${recipe.category}</span>
    </div>
    <div class="card-body">
      <p>${escapeHtml(recipe.description) || 'No description'}</p>
      <div class="flex gap-md" style="margin-top: var(--space-md); font-size: 0.9rem; color: var(--text-muted);">
        <span>⏱️ ${formatTime(totalTime)}</span>
        <span>🍽️ ${recipe.servings} servings</span>
      </div>
    </div>
    ${tags.length > 0 ? `
      <div class="card-footer">
        ${tags.map(tag => `<span class="chip">${escapeHtml(tag)}</span>`).join('')}
      </div>
    ` : ''}
  `;

  card.addEventListener('click', () => showRecipeDetail(recipe.id));

  return card;
}

// ===== Show Recipe Detail Modal =====
async function showRecipeDetail(recipeId) {
  try {
    const recipe = await apiCall(`/recipes/${recipeId}`);

    const content = document.createElement('div');
    const tags = parseTags(recipe.tags);

    content.innerHTML = `
      <div style="margin-bottom: var(--space-lg);">
        <span class="badge badge-${recipe.category}">${recipe.category}</span>
        ${tags.map(tag => `<span class="chip" style="margin-left: var(--space-xs);">${escapeHtml(tag)}</span>`).join('')}
      </div>

      <p style="color: var(--text-secondary); margin-bottom: var(--space-lg);">
        ${escapeHtml(recipe.description) || 'No description'}
      </p>

      <div class="flex gap-md" style="margin-bottom: var(--space-lg); color: var(--text-muted);">
        <span>⏱️ Prep: ${formatTime(recipe.prep_time_minutes)}</span>
        <span>🔥 Cook: ${formatTime(recipe.cook_time_minutes)}</span>
        <span>🍽️ ${recipe.servings} servings</span>
      </div>

      <h3 style="margin-bottom: var(--space-md);">Ingredients</h3>
      <ul style="margin-bottom: var(--space-lg); padding-left: var(--space-lg);">
        ${recipe.ingredients.map(ing => `
          <li>${ing.quantity} ${ing.unit} ${escapeHtml(ing.item)}</li>
        `).join('')}
      </ul>

      <h3 style="margin-bottom: var(--space-md);">Instructions</h3>
      <div style="white-space: pre-wrap; color: var(--text-secondary);">
        ${escapeHtml(recipe.instructions) || 'No instructions provided'}
      </div>

      <div class="modal-actions">
        <button class="btn btn-secondary" id="edit-recipe-btn">✏️ Edit</button>
        <button class="btn btn-danger" id="delete-recipe-btn">🗑️ Delete</button>
      </div>
    `;

    const modal = showModal(recipe.title, content);

    // Event listeners
    content.querySelector('#edit-recipe-btn').addEventListener('click', () => {
      modal.close();
      showRecipeModal(recipe);
    });

    content.querySelector('#delete-recipe-btn').addEventListener('click', async () => {
      const confirmed = await showConfirm(
        'Are you sure you want to delete this recipe? This action cannot be undone. If this recipe is in your meal plan, those assignments will also be removed.',
        'Delete',
        'Cancel'
      );

      if (confirmed) {
        try {
          await apiCall(`/recipes/${recipe.id}`, { method: 'DELETE' });
          showToast('Recipe deleted successfully', 'success');
          modal.close();
          await loadRecipes();
        } catch (error) {
          // Error already shown by apiCall
        }
      }
    });
  } catch (error) {
    // Error already shown by apiCall
  }
}

// ===== Show Recipe Form Modal =====
function showRecipeModal(existingRecipe = null) {
  const isEdit = !!existingRecipe;
  const recipe = existingRecipe || {
    title: '',
    description: '',
    category: 'dinner',
    prep_time_minutes: 0,
    cook_time_minutes: 0,
    servings: 4,
    instructions: '',
    tags: '',
    ingredients: []
  };

  const content = document.createElement('div');
  content.className = 'recipe-form';

  content.innerHTML = `
    <div class="form-field">
      <label>Title <span class="required">*</span></label>
      <input type="text" id="recipe-title" class="form-input" value="${escapeHtml(recipe.title)}" required />
    </div>

    <div class="form-field">
      <label>Description</label>
      <textarea id="recipe-description" class="form-textarea" rows="3">${escapeHtml(recipe.description)}</textarea>
    </div>

    <div class="flex gap-md">
      <div class="form-field" style="flex: 1;">
        <label>Category <span class="required">*</span></label>
        <select id="recipe-category" class="form-select" required>
          <option value="breakfast" ${recipe.category === 'breakfast' ? 'selected' : ''}>Breakfast</option>
          <option value="lunch" ${recipe.category === 'lunch' ? 'selected' : ''}>Lunch</option>
          <option value="dinner" ${recipe.category === 'dinner' ? 'selected' : ''}>Dinner</option>
          <option value="snack" ${recipe.category === 'snack' ? 'selected' : ''}>Snack</option>
          <option value="dessert" ${recipe.category === 'dessert' ? 'selected' : ''}>Dessert</option>
        </select>
      </div>

      <div class="form-field" style="flex: 1;">
        <label>Servings</label>
        <input type="number" id="recipe-servings" class="form-input" value="${recipe.servings}" min="1" />
      </div>
    </div>

    <div class="flex gap-md">
      <div class="form-field" style="flex: 1;">
        <label>Prep Time (minutes)</label>
        <input type="number" id="recipe-prep-time" class="form-input" value="${recipe.prep_time_minutes}" min="0" />
      </div>

      <div class="form-field" style="flex: 1;">
        <label>Cook Time (minutes)</label>
        <input type="number" id="recipe-cook-time" class="form-input" value="${recipe.cook_time_minutes}" min="0" />
      </div>
    </div>

    <div class="form-field">
      <label>Tags (comma-separated)</label>
      <input type="text" id="recipe-tags" class="form-input" value="${escapeHtml(recipe.tags)}" placeholder="vegetarian, quick, healthy" />
    </div>

    <div class="form-field">
      <label>Ingredients <span class="required">*</span></label>
      <div id="ingredients-list"></div>
      <button type="button" class="btn btn-secondary btn-sm" id="add-ingredient-btn" style="margin-top: var(--space-sm);">
        ➕ Add Ingredient
      </button>
    </div>

    <div class="form-field">
      <label>Instructions</label>
      <textarea id="recipe-instructions" class="form-textarea" rows="6">${escapeHtml(recipe.instructions)}</textarea>
    </div>

    <div class="modal-actions">
      <button type="button" class="btn btn-secondary" id="cancel-btn">Cancel</button>
      <button type="button" class="btn btn-primary" id="save-recipe-btn">${isEdit ? 'Update' : 'Create'} Recipe</button>
    </div>
  `;

  const modal = showModal(isEdit ? 'Edit Recipe' : 'Add Recipe', content);

  // Initialize ingredients
  const ingredientsList = content.querySelector('#ingredients-list');
  let ingredientCount = 0;

  function addIngredientRow(ingredient = null) {
    const row = document.createElement('div');
    row.className = 'ingredient-row flex gap-sm';
    row.style.marginBottom = 'var(--space-sm)';
    row.dataset.index = ingredientCount++;

    row.innerHTML = `
      <input type="number" class="form-input ing-quantity" placeholder="Qty" value="${ingredient?.quantity || ''}" min="0" step="0.01" style="width: 80px;" />
      <select class="form-select ing-unit" style="width: 100px;">
        <option value="tsp" ${ingredient?.unit === 'tsp' ? 'selected' : ''}>tsp</option>
        <option value="tbsp" ${ingredient?.unit === 'tbsp' ? 'selected' : ''}>tbsp</option>
        <option value="cup" ${ingredient?.unit === 'cup' ? 'selected' : ''}>cup</option>
        <option value="oz" ${ingredient?.unit === 'oz' ? 'selected' : ''}>oz</option>
        <option value="lb" ${ingredient?.unit === 'lb' ? 'selected' : ''}>lb</option>
        <option value="whole" ${ingredient?.unit === 'whole' ? 'selected' : ''}>whole</option>
        <option value="clove" ${ingredient?.unit === 'clove' ? 'selected' : ''}>clove</option>
        <option value="piece" ${ingredient?.unit === 'piece' ? 'selected' : ''}>piece</option>
      </select>
      <input type="text" class="form-input ing-item" placeholder="Item" value="${escapeHtml(ingredient?.item || '')}" style="flex: 1;" />
      <select class="form-select ing-section" style="width: 120px;">
        <option value="produce" ${ingredient?.grocery_section === 'produce' ? 'selected' : ''}>Produce</option>
        <option value="meat" ${ingredient?.grocery_section === 'meat' ? 'selected' : ''}>Meat</option>
        <option value="dairy" ${ingredient?.grocery_section === 'dairy' ? 'selected' : ''}>Dairy</option>
        <option value="pantry" ${ingredient?.grocery_section === 'pantry' ? 'selected' : ''}>Pantry</option>
        <option value="frozen" ${ingredient?.grocery_section === 'frozen' ? 'selected' : ''}>Frozen</option>
        <option value="other" ${ingredient?.grocery_section === 'other' ? 'selected' : ''}>Other</option>
      </select>
      <button type="button" class="btn btn-danger btn-icon remove-ingredient-btn">✕</button>
    `;

    ingredientsList.appendChild(row);

    row.querySelector('.remove-ingredient-btn').addEventListener('click', () => {
      row.remove();
    });
  }

  // Add existing ingredients or one empty row
  if (recipe.ingredients && recipe.ingredients.length > 0) {
    recipe.ingredients.forEach(ing => addIngredientRow(ing));
  } else {
    addIngredientRow();
  }

  content.querySelector('#add-ingredient-btn').addEventListener('click', () => {
    addIngredientRow();
  });

  // Cancel button
  content.querySelector('#cancel-btn').addEventListener('click', () => {
    modal.close();
  });

  // Save button
  content.querySelector('#save-recipe-btn').addEventListener('click', async () => {
    const formData = {
      title: content.querySelector('#recipe-title').value.trim(),
      description: content.querySelector('#recipe-description').value.trim(),
      category: content.querySelector('#recipe-category').value,
      servings: parseInt(content.querySelector('#recipe-servings').value) || 1,
      prep_time_minutes: parseInt(content.querySelector('#recipe-prep-time').value) || 0,
      cook_time_minutes: parseInt(content.querySelector('#recipe-cook-time').value) || 0,
      tags: content.querySelector('#recipe-tags').value.trim(),
      instructions: content.querySelector('#recipe-instructions').value.trim(),
      ingredients: []
    };

    // Validate title
    if (!formData.title) {
      showToast('Please enter a recipe title', 'error');
      return;
    }

    // Collect ingredients
    const ingredientRows = content.querySelectorAll('.ingredient-row');
    ingredientRows.forEach((row, index) => {
      const quantity = parseFloat(row.querySelector('.ing-quantity').value);
      const unit = row.querySelector('.ing-unit').value;
      const item = row.querySelector('.ing-item').value.trim();
      const grocery_section = row.querySelector('.ing-section').value;

      if (quantity > 0 && item) {
        formData.ingredients.push({
          quantity,
          unit,
          item,
          grocery_section,
          sort_order: index
        });
      }
    });

    if (formData.ingredients.length === 0) {
      showToast('Please add at least one ingredient', 'error');
      return;
    }

    // Submit
    try {
      if (isEdit) {
        await apiCall(`/recipes/${recipe.id}`, {
          method: 'PUT',
          body: JSON.stringify(formData)
        });
        showToast('Recipe updated successfully', 'success');
      } else {
        await apiCall('/recipes/', {
          method: 'POST',
          body: JSON.stringify(formData)
        });
        showToast('Recipe created successfully', 'success');
      }
      modal.close();
      await loadRecipes();
    } catch (error) {
      // Error already shown by apiCall
    }
  });
}

// ===== Utility =====
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
