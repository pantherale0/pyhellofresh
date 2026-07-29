"""Data models for HelloFresh API objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "TokenResponse",
    "Profile",
    "AccountBalance",
    "PastDeliveryItem",
    "PastDeliveries",
    "RecipeAllergen",
    "RecipeIngredient",
    "RecipeNutrition",
    "RecipeStep",
    "Recipe",
    "Meal",
    "WeeklyMenu",
    "CartProduct",
    "CartPrice",
]


@dataclass
class TokenResponse:
    """OAuth / Passwordless Token Response object."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 1800
    refresh_token: str | None = None
    refresh_expires_in: int | None = None
    issued_at: int | None = None
    public_id: str | None = None
    user_data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TokenResponse:
        """Parse TokenResponse from raw API dictionary."""
        return cls(
            access_token=data.get("access_token", ""),
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in", 1800),
            refresh_token=data.get("refresh_token"),
            refresh_expires_in=data.get("refresh_expires_in"),
            issued_at=data.get("issued_at"),
            public_id=data.get("public_id"),
            user_data=data.get("user_data", {}) or {},
        )


@dataclass
class Profile:
    """Customer profile details including dietary preferences and household size."""

    total_people: int = 0
    adults: int = 0
    children: int = 0
    exclusions: list[str] = field(default_factory=list)
    dietary_preferences: list[str] = field(default_factory=list)
    cuisines: dict[str, int] = field(default_factory=dict)
    meal_types: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Profile:
        """Parse Profile from raw API dictionary."""
        household = data.get("household", {}) or {}
        taste = data.get("taste", {}) or {}

        return cls(
            total_people=household.get("totalPeople", 0),
            adults=household.get("adults", 0),
            children=household.get("children", 0),
            exclusions=taste.get("exclusions", []) or [],
            dietary_preferences=taste.get("dietaryPreferences", []) or [],
            cuisines=taste.get("cuisines", {}) or {},
            meal_types=taste.get("mealTypes", []) or [],
        )


@dataclass
class AccountBalance:
    """Customer credit balance details."""

    amount: int = 0
    cash: int = 0
    bonus: int = 0
    currency_code: str = "GBP"
    restricted_amount: int = 0
    cancellable_credits: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AccountBalance:
        """Parse AccountBalance from raw API dictionary."""
        return cls(
            amount=data.get("amount", 0),
            cash=data.get("cash", 0),
            bonus=data.get("bonus", 0),
            currency_code=data.get("currencyCode", "GBP"),
            restricted_amount=data.get("restrictedAmount", 0),
            cancellable_credits=data.get("cancellableCredits", 0),
        )


@dataclass
class PastDeliveryItem:
    """Past delivery week entry."""

    week: str
    menu_id: str | None = None
    meals: list[dict[str, Any]] = field(default_factory=list)
    addons: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PastDeliveryItem:
        """Parse PastDeliveryItem from raw API dictionary."""
        return cls(
            week=data.get("week", ""),
            menu_id=data.get("menuId"),
            meals=data.get("meals", []) or [],
            addons=data.get("addons", []) or [],
        )


@dataclass
class PastDeliveries:
    """Collection of past box deliveries."""

    weeks: list[PastDeliveryItem] = field(default_factory=list)
    next_week: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PastDeliveries:
        """Parse PastDeliveries from raw API dictionary."""
        raw_weeks = data.get("weeks", []) or []
        return cls(
            weeks=[
                PastDeliveryItem.from_dict(w) for w in raw_weeks if isinstance(w, dict)
            ],
            next_week=data.get("nextWeek"),
        )


@dataclass
class RecipeAllergen:
    """Recipe allergen information."""

    id: str
    name: str
    type: str | None = None
    slug: str | None = None
    icon_link: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RecipeAllergen:
        """Parse RecipeAllergen from raw API dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            type=data.get("type"),
            slug=data.get("slug"),
            icon_link=data.get("iconLink"),
        )


@dataclass
class RecipeIngredient:
    """Recipe ingredient details."""

    id: str
    name: str
    uuid: str | None = None
    type: str | None = None
    slug: str | None = None
    image_link: str | None = None
    shipped: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RecipeIngredient:
        """Parse RecipeIngredient from raw API dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            uuid=data.get("uuid"),
            type=data.get("type"),
            slug=data.get("slug"),
            image_link=data.get("imageLink"),
            shipped=data.get("shipped", True),
        )


@dataclass
class RecipeNutrition:
    """Recipe nutrition component."""

    type: str
    name: str
    amount: float | int = 0
    unit: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RecipeNutrition:
        """Parse RecipeNutrition from raw API dictionary."""
        return cls(
            type=data.get("type", ""),
            name=data.get("name", ""),
            amount=data.get("amount", 0),
            unit=data.get("unit", ""),
        )


@dataclass
class RecipeStep:
    """Step-by-step preparation instruction."""

    index: int
    instructions: str
    utensils: list[str] = field(default_factory=list)
    timers: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RecipeStep:
        """Parse RecipeStep from raw API dictionary."""
        utensil_objs = data.get("utensils", []) or []
        utensil_names = [
            u.get("name") if isinstance(u, dict) else str(u) for u in utensil_objs if u
        ]
        return cls(
            index=data.get("index", 0),
            instructions=data.get("instructions", ""),
            utensils=[u for u in utensil_names if u],
            timers=data.get("timers", []) or [],
        )


@dataclass
class Recipe:
    """Full HelloFresh Recipe definition."""

    id: str
    name: str
    headline: str = ""
    description: str = ""
    difficulty: int = 1
    prep_time: str | None = None
    total_time: str | None = None
    image_link: str | None = None
    website_url: str | None = None
    allergens: list[RecipeAllergen] = field(default_factory=list)
    ingredients: list[RecipeIngredient] = field(default_factory=list)
    steps: list[RecipeStep] = field(default_factory=list)
    nutrition: list[RecipeNutrition] = field(default_factory=list)
    yields: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Recipe:
        """Parse Recipe from raw API dictionary."""
        allergens_raw = data.get("allergens", []) or []
        ingredients_raw = data.get("ingredients", []) or []
        steps_raw = data.get("steps", []) or []
        nutrition_raw = data.get("nutrition", []) or []

        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            headline=data.get("headline", "") or "",
            description=data.get("description", "") or "",
            difficulty=data.get("difficulty", 1),
            prep_time=data.get("prepTime"),
            total_time=data.get("totalTime"),
            image_link=data.get("imageLink"),
            website_url=data.get("websiteUrl"),
            allergens=[
                RecipeAllergen.from_dict(a)
                for a in allergens_raw
                if isinstance(a, dict)
            ],
            ingredients=[
                RecipeIngredient.from_dict(i)
                for i in ingredients_raw
                if isinstance(i, dict)
            ],
            steps=[RecipeStep.from_dict(s) for s in steps_raw if isinstance(s, dict)],
            nutrition=[
                RecipeNutrition.from_dict(n)
                for n in nutrition_raw
                if isinstance(n, dict)
            ],
            yields=data.get("yields", []) or [],
        )


@dataclass
class Meal:
    """Meal entry inside a weekly menu."""

    recipe_family: str | None = None
    index: int = 0
    charge: float = 0.0
    recipe: Recipe | None = None
    related_category: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Meal:
        """Parse Meal from raw API dictionary."""
        recipe_raw = data.get("recipe")
        recipe_obj = (
            Recipe.from_dict(recipe_raw) if isinstance(recipe_raw, dict) else None
        )

        charge_raw = data.get("charge")
        charge_val = 0.0
        if isinstance(charge_raw, (int, float)):
            charge_val = float(charge_raw)
        elif isinstance(charge_raw, str):
            try:
                charge_val = float(charge_raw)
            except ValueError:
                charge_val = 0.0
        elif isinstance(charge_raw, dict):
            raw_amt = (
                charge_raw.get("totalAmount")
                if charge_raw.get("totalAmount") is not None
                else charge_raw.get("unitAmount", 0)
            )
            if isinstance(raw_amt, (int, float)):
                charge_val = (
                    float(raw_amt) / 100.0
                    if isinstance(raw_amt, int) and raw_amt >= 10
                    else float(raw_amt)
                )

        return cls(
            recipe_family=data.get("recipeFamily"),
            index=data.get("index", 0),
            charge=charge_val,
            recipe=recipe_obj,
            related_category=data.get("relatedCategory"),
        )


@dataclass
class WeeklyMenu:
    """Weekly menu containing available meals and add-ons."""

    id: str
    week: str
    meals_ready: bool = True
    meals: list[Meal] = field(default_factory=list)
    add_ons: dict[str, Any] = field(default_factory=dict)
    categories: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WeeklyMenu:
        """Parse WeeklyMenu from raw API dictionary."""
        meals_raw = data.get("meals", []) or []
        return cls(
            id=data.get("id", ""),
            week=data.get("week", ""),
            meals_ready=data.get("mealsReady", True),
            meals=[Meal.from_dict(m) for m in meals_raw if isinstance(m, dict)],
            add_ons=data.get("addOns", {}) or {},
            categories=data.get("categories", {}) or {},
        )


@dataclass
class CartProduct:
    """Cart product item."""

    handle: str
    unit_price: float = 0.0
    paid_price: float = 0.0
    quantity: int = 1
    shipping_amount: float = 0.0
    tax_amount: float = 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CartProduct:
        """Parse CartProduct from raw API dictionary."""
        return cls(
            handle=data.get("handle", ""),
            unit_price=float(data.get("unitPrice", 0.0)),
            paid_price=float(data.get("paidPrice", 0.0)),
            quantity=int(data.get("quantity", 1)),
            shipping_amount=float(data.get("shippingAmount", 0.0)),
            tax_amount=float(data.get("taxAmount", 0.0)),
        )


@dataclass
class CartPrice:
    """Cart pricing calculation result."""

    coupon_code: str = ""
    grand_total: float = 0.0
    sub_total: float = 0.0
    shipping_amount: float = 0.0
    tax_amount: float = 0.0
    discount_amount: float = 0.0
    products: list[CartProduct] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CartPrice:
        """Parse CartPrice from raw API dictionary."""
        products_raw = data.get("products", []) or []
        return cls(
            coupon_code=data.get("couponCode", ""),
            grand_total=float(data.get("grandTotal", 0.0)),
            sub_total=float(data.get("subTotal", 0.0)),
            shipping_amount=float(data.get("shippingAmount", 0.0)),
            tax_amount=float(data.get("taxAmount", 0.0)),
            discount_amount=float(data.get("discountAmount", 0.0)),
            products=[
                CartProduct.from_dict(p) for p in products_raw if isinstance(p, dict)
            ],
        )
