"""Pydantic models for Recipe Manager API"""
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional


# Ingredient models
class IngredientBase(BaseModel):
    quantity: float
    unit: str
    item: str
    grocery_section: str = "other"


class IngredientCreate(IngredientBase):
    pass


class Ingredient(IngredientBase):
    id: int
    recipe_id: int
    sort_order: int = 0

    model_config = ConfigDict(from_attributes=True)


# Recipe models
class RecipeBase(BaseModel):
    title: str
    description: str = ""
    category: str
    prep_time_minutes: int = 0
    cook_time_minutes: int = 0
    servings: int = 1
    instructions: str = ""
    tags: str = ""


class RecipeCreate(RecipeBase):
    ingredients: List[IngredientCreate] = []


class RecipeUpdate(RecipeBase):
    ingredients: List[IngredientCreate] = []


class Recipe(RecipeBase):
    id: int
    created_at: str
    updated_at: str
    ingredients: List[Ingredient] = []
    meal_plan_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class RecipeListItem(RecipeBase):
    id: int
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


# Meal Plan models
class MealPlanBase(BaseModel):
    week_start: str
    day_of_week: int = Field(..., ge=0, le=6)
    meal_slot: str
    recipe_id: int


class MealPlanCreate(MealPlanBase):
    pass


class MealPlan(MealPlanBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class MealPlanWithRecipe(MealPlan):
    recipe_title: str
    prep_time_minutes: int
    cook_time_minutes: int


# Shopping List models
class ShoppingItemBase(BaseModel):
    item: str
    quantity: float
    unit: str
    grocery_section: str = "other"
    checked: bool = False
    source: str = "recipe"


class ShoppingItemCreate(ShoppingItemBase):
    pass


class ShoppingItem(ShoppingItemBase):
    id: int
    list_id: int

    model_config = ConfigDict(from_attributes=True)


class ShoppingListBase(BaseModel):
    week_start: str


class ShoppingListCreate(ShoppingListBase):
    pass


class ShoppingList(ShoppingListBase):
    id: int
    created_at: str
    items: List[ShoppingItem] = []

    model_config = ConfigDict(from_attributes=True)


class ShoppingListGenerate(BaseModel):
    week_start: str
