/**
 * Recipe Collection View
 * Browse, search, filter, create, edit, and delete recipes
 */

router.register('recipes', mountRecipesView);

let currentFilters = {
    category: '',
    tag: '',
    search: ''
};

async function mountRecipesView(container) {
    container.innerHTML = `
        <div class="flex-between mb-2">
            <h2>Recipe Collection</h2>
            <button class="btn btn-primary" onclick="showAddRecipeModal()">+ Add Recipe</button>
        </div>

        <div class="filter-bar">
            <div class="form-group">
                <label class="form-label" for="search-input">Search</label>
                <input type="text" id="search-input" class="form-input" placeholder="Search recipes or ingredients...">
            </div>
            <div class="form-group">
                <label class="form-label" for="category-filter">Category</label>
                <select id="category-filter" class="form-select">
                    <option value="">All Categories</option>
                    <option value="breakfast">Breakfast</option>
                    <option value="lunch">Lunch</option>
                    <option value="dinner">Dinner</option>
                    <option value="snack">Snack</option>
                    <option value="dessert">Dessert</option>
                </select>
            </div>
            <div class="form-group">
                <label class="form-label" for="tag-filter">Tag</label>
                <input type="text" id="tag-filter" class="form-input" placeholder="Filter by tag...">
            </div>
        </div>

        <div id="recipes-grid" class="card-grid">
            <div class="text-center text-muted">Loading recipes...</div>
        </div>
    `;

    // Set up filter event listeners
    const searchInput = document.getElementById('search-input');
    const categoryFilter = document.getElementById('category-filter');
    const tagFilter = document.getElementById('tag-filter');

    let searchTimeout;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentFilters.search = e.target.value;
            loadRecipes();
        }, 300);
    });

    categoryFilter.addEventListener('change', (e) => {
        currentFilters.category = e.target.value;
        loadRecipes();
    });

    tagFilter.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentFilters.tag = e.target.value;
            loadRecipes();
        }, 300);
    });

    // Load recipes
    await loadRecipes();
}

async function loadRecipes() {
    const grid = document.getElementById('recipes-grid');
    grid.innerHTML = '<div class="text-center text-muted">Loading recipes...</div>';

    try {
        // Build query params
        const params = new URLSearchParams();
        if (currentFilters.category) params.append('category', currentFilters.category);
        if (currentFilters.tag) params.append('tag', currentFilters.tag);
        if (currentFilters.search) params.append('search', currentFilters.search);

        const recipes = await fetchJSON(`/api/recipes?${params.toString()}`);

        if (recipes.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🍳</div>
                    <div class="empty-state-text">No recipes found</div>
                </div>
            `;
            return;
        }

        grid.innerHTML = recipes.map(recipe => createRecipeCard(recipe)).join('');
    } catch (error) {
        grid.innerHTML = `<div class="text-center text-muted">Error loading recipes: ${error.message}</div>`;
        showError(`Failed to load recipes: ${error.message}`);
    }
}

function createRecipeCard(recipe) {
    const tags = recipe.tags ? recipe.tags.split(',').map(t => t.trim()).filter(Boolean) : [];

    return `
        <div class="card" onclick="showRecipeDetail(${recipe.id})">
            <div class="flex-between mb-1">
                <h3 style="margin: 0;">${escapeHtml(recipe.title)}</h3>
                <span class="badge badge-${recipe.category}">${recipe.category}</span>
            </div>
            <p class="text-muted mb-1">${escapeHtml(recipe.description || '')}</p>
            <div class="text-muted mb-1">
                ⏱️ ${recipe.prep_time_minutes + recipe.cook_time_minutes} min
                (${recipe.prep_time_minutes} prep + ${recipe.cook_time_minutes} cook)
            </div>
            ${tags.length > 0 ? `
                <div class="mt-1">
                    ${tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
                </div>
            ` : ''}
        </div>
    `;
}

async function showRecipeDetail(recipeId) {
    try {
        const recipe = await fetchJSON(`/api/recipes/${recipeId}`);

        const tags = recipe.tags ? recipe.tags.split(',').map(t => t.trim()).filter(Boolean) : [];

        const content = `
            <h2 class="modal-title">${escapeHtml(recipe.title)}</h2>

            <div class="mb-2">
                <span class="badge badge-${recipe.category}">${recipe.category}</span>
                ${tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
            </div>

            <p class="mb-2">${escapeHtml(recipe.description || '')}</p>

            <div class="flex gap-2 mb-2 text-muted">
                <div>⏱️ Prep: ${recipe.prep_time_minutes} min</div>
                <div>🍳 Cook: ${recipe.cook_time_minutes} min</div>
                <div>🍽️ Servings: ${recipe.servings}</div>
            </div>

            <h3 class="mb-1">Ingredients</h3>
            <ul class="mb-2">
                ${recipe.ingredients.map(ing => `
                    <li>${ing.quantity} ${ing.unit} ${escapeHtml(ing.item)}</li>
                `).join('')}
            </ul>

            <h3 class="mb-1">Instructions</h3>
            <p style="white-space: pre-wrap;">${escapeHtml(recipe.instructions)}</p>

            <div class="flex gap-1 mt-2">
                <button class="btn btn-primary" onclick="showEditRecipeModal(${recipeId})">Edit</button>
                <button class="btn btn-danger" onclick="deleteRecipe(${recipeId}, ${recipe.meal_plan_count})">Delete</button>
                <button class="btn btn-secondary" onclick="modal.hide()">Close</button>
            </div>
        `;

        modal.show(content);
    } catch (error) {
        showError(`Failed to load recipe: ${error.message}`);
    }
}

function showAddRecipeModal() {
    showRecipeForm(null);
}

async function showEditRecipeModal(recipeId) {
    try {
        const recipe = await fetchJSON(`/api/recipes/${recipeId}`);
        showRecipeForm(recipe);
    } catch (error) {
        showError(`Failed to load recipe: ${error.message}`);
    }
}

function showRecipeForm(recipe) {
    const isEdit = recipe !== null;
    const ingredients = isEdit ? recipe.ingredients : [{ quantity: '', unit: 'cup', item: '', grocery_section: 'other' }];

    const content = `
        <h2 class="modal-title">${isEdit ? 'Edit' : 'Add'} Recipe</h2>
        <form id="recipe-form" onsubmit="saveRecipe(event, ${isEdit ? recipe.id : 'null'})">
            <div class="form-group">
                <label class="form-label" for="recipe-title">Title*</label>
                <input type="text" id="recipe-title" class="form-input" required value="${isEdit ? escapeHtml(recipe.title) : ''}">
            </div>

            <div class="form-group">
                <label class="form-label" for="recipe-description">Description</label>
                <input type="text" id="recipe-description" class="form-input" value="${isEdit ? escapeHtml(recipe.description) : ''}">
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label class="form-label" for="recipe-category">Category*</label>
                    <select id="recipe-category" class="form-select" required>
                        <option value="breakfast" ${isEdit && recipe.category === 'breakfast' ? 'selected' : ''}>Breakfast</option>
                        <option value="lunch" ${isEdit && recipe.category === 'lunch' ? 'selected' : ''}>Lunch</option>
                        <option value="dinner" ${isEdit && recipe.category === 'dinner' ? 'selected' : ''}>Dinner</option>
                        <option value="snack" ${isEdit && recipe.category === 'snack' ? 'selected' : ''}>Snack</option>
                        <option value="dessert" ${isEdit && recipe.category === 'dessert' ? 'selected' : ''}>Dessert</option>
                    </select>
                </div>

                <div class="form-group">
                    <label class="form-label" for="recipe-prep">Prep Time (min)</label>
                    <input type="number" id="recipe-prep" class="form-input" min="0" value="${isEdit ? recipe.prep_time_minutes : 0}">
                </div>

                <div class="form-group">
                    <label class="form-label" for="recipe-cook">Cook Time (min)</label>
                    <input type="number" id="recipe-cook" class="form-input" min="0" value="${isEdit ? recipe.cook_time_minutes : 0}">
                </div>

                <div class="form-group">
                    <label class="form-label" for="recipe-servings">Servings</label>
                    <input type="number" id="recipe-servings" class="form-input" min="1" value="${isEdit ? recipe.servings : 1}">
                </div>
            </div>

            <div class="form-group">
                <label class="form-label" for="recipe-tags">Tags (comma-separated)</label>
                <input type="text" id="recipe-tags" class="form-input" placeholder="quick, healthy, vegetarian" value="${isEdit ? escapeHtml(recipe.tags) : ''}">
            </div>

            <div class="form-group">
                <label class="form-label">Ingredients*</label>
                <div id="ingredients-container">
                    ${ingredients.map((ing, i) => createIngredientRow(i, ing)).join('')}
                </div>
                <button type="button" class="btn btn-secondary btn-small mt-1" onclick="addIngredientRow()">+ Add Ingredient</button>
            </div>

            <div class="form-group">
                <label class="form-label" for="recipe-instructions">Instructions*</label>
                <textarea id="recipe-instructions" class="form-textarea" required>${isEdit ? escapeHtml(recipe.instructions) : ''}</textarea>
            </div>

            <div class="flex gap-1">
                <button type="submit" class="btn btn-primary">Save Recipe</button>
                <button type="button" class="btn btn-secondary" onclick="modal.hide()">Cancel</button>
            </div>
        </form>
    `;

    modal.show(content);
}

function createIngredientRow(index, ingredient = {}) {
    return `
        <div class="ingredient-row form-row mb-1">
            <div class="form-group" style="flex: 0 0 80px;">
                <input type="number" step="0.01" class="form-input" placeholder="Qty" required
                       value="${ingredient.quantity || ''}" data-field="quantity">
            </div>
            <div class="form-group" style="flex: 0 0 100px;">
                <select class="form-select" required data-field="unit">
                    <option value="tsp" ${ingredient.unit === 'tsp' ? 'selected' : ''}>tsp</option>
                    <option value="tbsp" ${ingredient.unit === 'tbsp' ? 'selected' : ''}>tbsp</option>
                    <option value="cup" ${ingredient.unit === 'cup' ? 'selected' : ''}>cup</option>
                    <option value="oz" ${ingredient.unit === 'oz' ? 'selected' : ''}>oz</option>
                    <option value="lb" ${ingredient.unit === 'lb' ? 'selected' : ''}>lb</option>
                    <option value="whole" ${ingredient.unit === 'whole' ? 'selected' : ''}>whole</option>
                    <option value="piece" ${ingredient.unit === 'piece' ? 'selected' : ''}>piece</option>
                </select>
            </div>
            <div class="form-group" style="flex: 1;">
                <input type="text" class="form-input" placeholder="Item" required
                       value="${ingredient.item || ''}" data-field="item">
            </div>
            <div class="form-group" style="flex: 0 0 120px;">
                <select class="form-select" required data-field="grocery_section">
                    <option value="produce" ${ingredient.grocery_section === 'produce' ? 'selected' : ''}>Produce</option>
                    <option value="meat" ${ingredient.grocery_section === 'meat' ? 'selected' : ''}>Meat</option>
                    <option value="dairy" ${ingredient.grocery_section === 'dairy' ? 'selected' : ''}>Dairy</option>
                    <option value="pantry" ${ingredient.grocery_section === 'pantry' ? 'selected' : ''}>Pantry</option>
                    <option value="frozen" ${ingredient.grocery_section === 'frozen' ? 'selected' : ''}>Frozen</option>
                    <option value="other" ${ingredient.grocery_section === 'other' ? 'selected' : ''}>Other</option>
                </select>
            </div>
            <button type="button" class="btn btn-danger btn-small" onclick="removeIngredientRow(this)">×</button>
        </div>
    `;
}

function addIngredientRow() {
    const container = document.getElementById('ingredients-container');
    const index = container.children.length;
    container.insertAdjacentHTML('beforeend', createIngredientRow(index));
}

function removeIngredientRow(button) {
    const container = document.getElementById('ingredients-container');
    if (container.children.length > 1) {
        button.closest('.ingredient-row').remove();
    } else {
        showError('Recipe must have at least one ingredient');
    }
}

async function saveRecipe(event, recipeId) {
    event.preventDefault();

    const form = event.target;
    const ingredientRows = form.querySelectorAll('.ingredient-row');
    const ingredients = [];

    ingredientRows.forEach(row => {
        ingredients.push({
            quantity: parseFloat(row.querySelector('[data-field="quantity"]').value),
            unit: row.querySelector('[data-field="unit"]').value,
            item: row.querySelector('[data-field="item"]').value,
            grocery_section: row.querySelector('[data-field="grocery_section"]').value
        });
    });

    const recipeData = {
        title: document.getElementById('recipe-title').value,
        description: document.getElementById('recipe-description').value,
        category: document.getElementById('recipe-category').value,
        prep_time_minutes: parseInt(document.getElementById('recipe-prep').value) || 0,
        cook_time_minutes: parseInt(document.getElementById('recipe-cook').value) || 0,
        servings: parseInt(document.getElementById('recipe-servings').value) || 1,
        tags: document.getElementById('recipe-tags').value,
        instructions: document.getElementById('recipe-instructions').value,
        ingredients: ingredients
    };

    try {
        if (recipeId) {
            await fetchJSON(`/api/recipes/${recipeId}`, {
                method: 'PUT',
                body: JSON.stringify(recipeData)
            });
            showSuccess('Recipe updated successfully');
        } else {
            await fetchJSON('/api/recipes', {
                method: 'POST',
                body: JSON.stringify(recipeData)
            });
            showSuccess('Recipe created successfully');
        }

        modal.hide();
        await loadRecipes();
    } catch (error) {
        showError(`Failed to save recipe: ${error.message}`);
    }
}

async function deleteRecipe(recipeId, mealPlanCount) {
    const confirmMessage = mealPlanCount > 0
        ? `This recipe is assigned to ${mealPlanCount} meal plan slot(s). Deleting it will remove those assignments. Are you sure?`
        : 'Are you sure you want to delete this recipe?';

    if (!confirm(confirmMessage)) {
        return;
    }

    try {
        await fetchJSON(`/api/recipes/${recipeId}`, { method: 'DELETE' });
        showSuccess('Recipe deleted successfully');
        modal.hide();
        await loadRecipes();
    } catch (error) {
        showError(`Failed to delete recipe: ${error.message}`);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
