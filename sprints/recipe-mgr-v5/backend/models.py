"""
Pydantic models for Recipe Manager API
"""
from typing import List, Optional
from pydantic import BaseModel, Field


# Ingredient models
class IngredientBase(BaseModel):
    quantity: float = Field(..., gt=0)
    unit: str
    item: str
    grocery_section: str = Field(default="other", pattern="^(produce|meat|dairy|pantry|frozen|other)$")


class IngredientCreate(IngredientBase):
    sort_order: int = 0


class Ingredient(IngredientBase):
    id: int
    recipe_id: int
    sort_order: int

    class Config:
        from_attributes = True


# Recipe models
class RecipeBase(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = ""
    category: str = Field(..., pattern="^(breakfast|lunch|dinner|snack|dessert)$")
    prep_time_minutes: int = Field(default=0, ge=0)
    cook_time_minutes: int = Field(default=0, ge=0)
    servings: int = Field(default=1, ge=1)
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

    class Config:
        from_attributes = True


class RecipeWithIngredients(Recipe):
    ingredients: List[Ingredient] = []

    class Config:
        from_attributes = True


# Meal Plan models
class MealPlanBase(BaseModel):
    week_start: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    day_of_week: int = Field(..., ge=0, le=6)
    meal_slot: str = Field(..., pattern="^(breakfast|lunch|dinner|snack)$")
    recipe_id: int


class MealPlanCreate(MealPlanBase):
    pass


class MealPlan(MealPlanBase):
    id: int

    class Config:
        from_attributes = True


class MealPlanWithRecipe(MealPlan):
    recipe_title: str
    prep_time_minutes: int
    cook_time_minutes: int


# Shopping List models
class ShoppingListCreate(BaseModel):
    week_start: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")


class ShoppingList(BaseModel):
    id: int
    week_start: str
    created_at: str

    class Config:
        from_attributes = True


class ShoppingItemBase(BaseModel):
    item: str
    quantity: float = Field(..., gt=0)
    unit: str
    grocery_section: str = Field(default="other", pattern="^(produce|meat|dairy|pantry|frozen|other)$")


class ShoppingItemCreate(ShoppingItemBase):
    source: str = Field(default="manual", pattern="^(recipe|manual)$")


class ShoppingItem(ShoppingItemBase):
    id: int
    list_id: int
    checked: int = 0
    source: str

    class Config:
        from_attributes = True


class ShoppingListWithItems(ShoppingList):
    items: List[ShoppingItem] = []
