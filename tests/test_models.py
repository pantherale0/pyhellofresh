"""Unit tests for pyhellofresh data models."""

from __future__ import annotations

from pyhellofresh.models import (
    AccountBalance,
    CartPrice,
    PastDeliveries,
    Profile,
    Recipe,
    TokenResponse,
    WeeklyMenu,
)

from .conftest import (
    SAMPLE_BALANCE_RESPONSE,
    SAMPLE_CART_PRICE_RESPONSE,
    SAMPLE_MENU_RESPONSE,
    SAMPLE_PAST_DELIVERIES_RESPONSE,
    SAMPLE_PROFILE_RESPONSE,
    SAMPLE_RECIPE_RESPONSE,
    SAMPLE_TOKEN_RESPONSE,
)


def test_token_response_model():
    token = TokenResponse.from_dict(SAMPLE_TOKEN_RESPONSE)
    assert token.access_token == "eyJhbGciOiJSUzI1Ni...mock_token"
    assert token.token_type == "Bearer"
    assert token.expires_in == 1800
    assert token.refresh_token == "v1.mock_refresh_token"
    assert token.refresh_expires_in == 5184000
    assert token.issued_at == 1785332406
    assert token.public_id == "c1a70fe5-a97a-40d5-a3d5-59d43b2d4c9c"
    assert token.user_data["id"] == "297d5bcb-f9ce-43f0-90b2-38e4b7827a59"


def test_profile_model():
    profile = Profile.from_dict(SAMPLE_PROFILE_RESPONSE)
    assert profile.total_people == 2
    assert profile.adults == 2
    assert profile.children == 0
    assert profile.exclusions == ["pork", "shellfish"]
    assert profile.dietary_preferences == ["mostly-meat"]
    assert profile.cuisines["british"] == 100
    assert profile.meal_types == ["quick-easy"]


def test_account_balance_model():
    balance = AccountBalance.from_dict(SAMPLE_BALANCE_RESPONSE)
    assert balance.amount == 800
    assert balance.cash == 0
    assert balance.bonus == 800
    assert balance.currency_code == "GBP"


def test_past_deliveries_model():
    deliveries = PastDeliveries.from_dict(SAMPLE_PAST_DELIVERIES_RESPONSE)
    assert len(deliveries.weeks) == 1
    assert deliveries.weeks[0].week == "2026-W31"
    assert deliveries.weeks[0].menu_id == "menu_123"
    assert deliveries.next_week == "2026-W32"


def test_recipe_model():
    recipe = Recipe.from_dict(SAMPLE_RECIPE_RESPONSE)
    assert recipe.id == "6a2a93831f9f329b3991d936"
    assert recipe.name == "Mexican Inspired Veggie Small Plates"
    assert recipe.difficulty == 2
    assert len(recipe.allergens) == 1
    assert recipe.allergens[0].name == "Milk"
    assert len(recipe.ingredients) == 1
    assert recipe.ingredients[0].name == "Sweetcorn"
    assert len(recipe.steps) == 1
    assert recipe.steps[0].instructions == "Preheat oven to 200°C."
    assert recipe.steps[0].utensils == ["Baking Tray"]
    assert len(recipe.nutrition) == 1
    assert recipe.nutrition[0].name == "Energy (kJ)"


def test_weekly_menu_model():
    menu = WeeklyMenu.from_dict(SAMPLE_MENU_RESPONSE)
    assert menu.id == "6a437c85b5ef8033342ca361"
    assert menu.week == "2026-W32"
    assert menu.meals_ready is True
    assert len(menu.meals) == 1
    assert menu.meals[0].recipe is not None
    assert menu.meals[0].recipe.name == "Mexican Inspired Veggie Small Plates"


def test_meal_model_dict_charge():
    from pyhellofresh.models import Meal

    meal_data = {
        "recipeFamily": "classic-plan",
        "index": 100,
        "charge": {
            "label": "+£1/serving",
            "unitAmount": 100,
            "totalAmount": 200,
            "reason": "premium",
            "strategy": "per_meal",
        },
    }
    meal = Meal.from_dict(meal_data)
    assert meal.charge == 2.0


def test_cart_price_model():
    cart = CartPrice.from_dict(SAMPLE_CART_PRICE_RESPONSE)
    assert cart.grand_total == 37.94
    assert cart.sub_total == 37.95
    assert cart.shipping_amount == 4.99
    assert cart.discount_amount == 5.0
    assert len(cart.products) == 1
    assert cart.products[0].handle == "GB-CBU-2-2-0"
