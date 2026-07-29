"""Pytest configuration and shared fixtures for pyhellofresh tests."""

from __future__ import annotations

import pytest


@pytest.fixture
def anyio_backend():
    return "asyncio"


SAMPLE_TOKEN_RESPONSE = {
    "access_token": "eyJhbGciOiJSUzI1Ni...mock_token",
    "token_type": "Bearer",
    "expires_in": 1800,
    "refresh_token": "v1.mock_refresh_token",
    "refresh_expires_in": 5184000,
    "issued_at": 1785332406,
    "public_id": "c1a70fe5-a97a-40d5-a3d5-59d43b2d4c9c",
    "user_data": {
        "id": "297d5bcb-f9ce-43f0-90b2-38e4b7827a59",
        "email": "user@example.com",
    },
}

SAMPLE_PROFILE_RESPONSE = {
    "taste": {
        "exclusions": ["pork", "shellfish"],
        "dietaryPreferences": ["mostly-meat"],
        "cuisines": {"british": 100, "italian": 100},
        "mealTypes": ["quick-easy"],
    },
    "household": {
        "totalPeople": 2,
        "adults": 2,
        "children": 0,
    },
}

SAMPLE_BALANCE_RESPONSE = {
    "amount": 800,
    "cash": 0,
    "bonus": 800,
    "currencyCode": "GBP",
    "restrictedAmount": 0,
    "cancellableCredits": 0,
}

SAMPLE_PAST_DELIVERIES_RESPONSE = {
    "weeks": [
        {
            "week": "2026-W31",
            "menuId": "menu_123",
            "meals": [{"id": "meal_1"}],
            "addons": [],
        }
    ],
    "nextWeek": "2026-W32",
}

SAMPLE_RECIPE_RESPONSE = {
    "id": "6a2a93831f9f329b3991d936",
    "name": "Mexican Inspired Veggie Small Plates",
    "headline": "Cheesy Amarillo Chilli Corn",
    "description": "Add a fresh flavour to your plates...",
    "difficulty": 2,
    "prepTime": "PT40M",
    "totalTime": "PT35M",
    "imageLink": "https://media.hellofresh.com/image.jpg",
    "websiteUrl": "https://www.hellofresh.co.uk/recipes/mexican-inspired",
    "allergens": [
        {
            "id": "57962a07b7e8697d4b3052fa",
            "name": "Milk",
            "type": "milk",
            "slug": "milk",
            "iconLink": "https://media.hellofresh.com/milk.png",
        }
    ],
    "ingredients": [
        {
            "id": "ing_1",
            "name": "Sweetcorn",
            "uuid": "u_ing_1",
            "shipped": True,
        }
    ],
    "steps": [
        {
            "index": 1,
            "instructions": "Preheat oven to 200°C.",
            "utensils": [{"name": "Baking Tray"}],
            "timers": [],
        }
    ],
    "nutrition": [
        {
            "type": "energy-kj",
            "name": "Energy (kJ)",
            "amount": 2500,
            "unit": "kJ",
        }
    ],
}

SAMPLE_MENU_RESPONSE = {
    "id": "6a437c85b5ef8033342ca361",
    "week": "2026-W32",
    "mealsReady": True,
    "meals": [
        {
            "recipeFamily": "classic",
            "index": 1,
            "charge": 0.0,
            "recipe": SAMPLE_RECIPE_RESPONSE,
            "relatedCategory": "veggie",
        }
    ],
    "addOns": {},
    "categories": {},
}

SAMPLE_CART_PRICE_RESPONSE = {
    "couponCode": "",
    "grandTotal": 37.94,
    "subTotal": 37.95,
    "shippingAmount": 4.99,
    "taxAmount": 0.0,
    "discountAmount": 5.0,
    "products": [
        {
            "handle": "GB-CBU-2-2-0",
            "unitPrice": 18.0,
            "paidPrice": 16.0,
            "quantity": 1,
            "shippingAmount": 4.99,
            "taxAmount": 0.0,
        }
    ],
}
