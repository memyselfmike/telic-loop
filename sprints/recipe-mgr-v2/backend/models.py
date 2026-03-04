from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime


class IngredientCreate(BaseModel):
    """Model for creating an ingredient within a recipe."""
    quantity: float = Field(..., gt=0, description="Quantity must be greater than 0")
    unit: str = Field(..., min_length=1, description="Unit cannot be empty")
    item: str = Field(..., min_length=1, description="Item name cannot be empty")
    grocery_section: str = Field(default="other", description="Grocery store section")


class IngredientResponse(BaseModel):
    """Model for ingredient in recipe responses."""
    id: int
    recipe_id: int
    quantity: float
    unit: str
    item: str
    grocery_section: str
    sort_order: int


class RecipeCreate(BaseModel):
    """Model for creating a new recipe."""
    title: str = Field(..., min_length=1, description="Recipe title is required")
    description: str = Field(default="", description="Recipe description")
    category: str = Field(..., min_length=1, description="Recipe category is required")
    prep_time_minutes: int = Field(default=0, ge=0, description="Preparation time in minutes")
    cook_time_minutes: int = Field(default=0, ge=0, description="Cooking time in minutes")
    servings: int = Field(default=1, ge=1, description="Number of servings")
    instructions: str = Field(default="", description="Cooking instructions")
    tags: str = Field(default="", description="Comma-separated tags")
    ingredients: List[IngredientCreate] = Field(default_factory=list, description="List of ingredients")

    @field_validator('title', 'category')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip whitespace from required string fields."""
        stripped = v.strip()
        if not stripped:
            raise ValueError('Field cannot be empty or only whitespace')
        return stripped


class RecipeResponse(BaseModel):
    """Model for recipe responses including all fields and nested ingredients."""
    id: int
    title: str
    description: str
    category: str
    prep_time_minutes: int
    cook_time_minutes: int
    servings: int
    instructions: str
    tags: str
    created_at: str
    updated_at: str
    ingredients: List[IngredientResponse] = Field(default_factory=list)
