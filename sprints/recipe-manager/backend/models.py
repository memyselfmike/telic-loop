from pydantic import BaseModel, Field
from typing import Optional


# ---------------------------------------------------------------------------
# Ingredient models
# ---------------------------------------------------------------------------

class IngredientCreate(BaseModel):
    quantity: float
    unit: str
    item: str
    grocery_section: str = "other"


class IngredientResponse(IngredientCreate):
    id: int
    recipe_id: int
    sort_order: int = 0


# ---------------------------------------------------------------------------
# Recipe models
# ---------------------------------------------------------------------------

class RecipeCreate(BaseModel):
    title: str
    description: str = ""
    category: str
    prep_time_minutes: int = 0
    cook_time_minutes: int = 0
    servings: int = 1
    instructions: str = ""
    tags: str = ""
    ingredients: list[IngredientCreate] = Field(default_factory=list)


class RecipeResponse(BaseModel):
    id: int
    title: str
    description: str = ""
    category: str
    prep_time_minutes: int = 0
    cook_time_minutes: int = 0
    servings: int = 1
    instructions: str = ""
    tags: str = ""
    created_at: str
    updated_at: str
    ingredients: list[IngredientResponse] = Field(default_factory=list)


class RecipeListItem(BaseModel):
    id: int
    title: str
    description: str = ""
    category: str
    prep_time_minutes: int = 0
    cook_time_minutes: int = 0
    tags: str = ""


# ---------------------------------------------------------------------------
# Meal plan models
# ---------------------------------------------------------------------------

class MealPlanCreate(BaseModel):
    week_start: str
    day_of_week: int
    meal_slot: str
    recipe_id: int


class MealPlanResponse(BaseModel):
    id: int
    week_start: str
    day_of_week: int
    meal_slot: str
    recipe_id: int
    recipe_title: str = ""
    total_time: int = 0


# ---------------------------------------------------------------------------
# Shopping list models
# ---------------------------------------------------------------------------

class ShoppingItemCreate(BaseModel):
    item: str
    quantity: float
    unit: str
    grocery_section: str = "other"
    source: str = "manual"


class ShoppingItemResponse(BaseModel):
    id: int
    list_id: int
    item: str
    quantity: float
    unit: str
    grocery_section: str = "other"
    source: str = "manual"
    checked: bool = False


class ShoppingListResponse(BaseModel):
    id: int
    week_start: str
    created_at: str
    items: list[ShoppingItemResponse] = Field(default_factory=list)


class GenerateShoppingRequest(BaseModel):
    week_start: str
