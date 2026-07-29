#!/usr/bin/env python3
"""Interactive / CLI test script for pyhellofresh library.

Usage:
  # Test with an existing Bearer token:
  python3 example_test.py --token "YOUR_BEARER_TOKEN"

  # Test passwordless login flow:
  python3 example_test.py --email "user@example.com"

  # Test token refresh:
  python3 example_test.py --refresh-token "YOUR_REFRESH_TOKEN"
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

# Ensure src/ is in python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from pyhellofresh import (
    HelloFreshClient,
    HelloFreshError,
)


async def run_tests(
    access_token: str | None,
    refresh_token: str | None,
    email: str | None,
    country: str,
    locale: str,
    week: str,
) -> None:
    print("=" * 60)
    print(" 🥗  pyhellofresh Library Test Runner")
    print("=" * 60)

    # Initialize client using async context manager
    async with await HelloFreshClient.with_session(
        access_token=access_token,
        refresh_token=refresh_token,
        country=country,
        locale=locale,
    ) as client:

        # --- STEP 1: AUTHENTICATION FLOW (IF EMAIL OR REFRESH TOKEN PROVIDED) ---
        if email and not client.access_token and not refresh_token:
            print(f"\n🔑 Initiating passwordless login for {email}...")
            try:
                public_id = await client.start_passwordless_login(email)
                print("✅ Magic link sent successfully!")
                print(f"   Public ID: {public_id}")
                print("\n📩 Check your email for the magic link from HelloFresh.")
                link_input = input(
                    "   Paste the full link (or code) from your email: "
                ).strip()

                if link_input:
                    if link_input.startswith(("http://", "https://")):
                        token_resp = await client.finish_passwordless_login_from_url(
                            url=link_input,
                            public_id=public_id,
                        )
                    else:
                        token_resp = await client.finish_passwordless_login(
                            code=link_input,
                            email=email,
                            public_id=public_id,
                        )
                    print("✅ Passwordless login completed!")
                    print(f"   Access Token: {token_resp.access_token[:30]}...")
                    print(f"   Refresh Token: {token_resp.refresh_token}")
            except HelloFreshError as err:
                print(f"❌ Passwordless login error: {err}")

        elif refresh_token and not client.access_token:
            print("\n🔄 Refreshing access token...")
            try:
                token_resp = await client.refresh_access_token()
                print("✅ Token refresh successful!")
                print(f"   New Access Token: {token_resp.access_token[:30]}...")
                print(f"   Refresh Token: {token_resp.refresh_token}")
            except HelloFreshError as err:
                print(f"❌ Token refresh error: {err}")

        if not client.access_token:
            print(
                "\n⚠️  No valid access token available. Skipping authenticated endpoint tests."
            )
            print("   Pass --token or --email to authenticate.")
            return

        # --- STEP 2: PROFILE & HOUSEHOLD ---
        print("\n👤 Testing get_profile()...")
        try:
            profile = await client.get_profile()
            user_id = profile.dict().get("id") if hasattr(profile, "dict") else None
            print("✅ Profile fetched:")
            print(
                f"   - Household Size: {profile.total_people} (Adults: {profile.adults}, Children: {profile.children})"
            )
            print(f"   - User ID: {user_id}")
            print(f"   - Dietary Preferences: {profile.dietary_preferences}")
            print(f"   - Exclusions: {profile.exclusions}")
            print(f"   - Meal Types: {profile.meal_types}")

        except HelloFreshError as err:
            print(f"❌ get_profile error: {err}")

        # --- STEP 3: ACCOUNT CREDIT BALANCE ---
        print("\n💳 Testing get_balance()...")
        try:
            balance = await client.get_balance()
            print("✅ Credit balance fetched:")
            print(f"   - Amount: {balance.amount / 100:.2f} {balance.currency_code}")
            print(f"   - Bonus: {balance.bonus / 100:.2f} {balance.currency_code}")
        except HelloFreshError as err:
            print(f"⚠️ get_balance response: {err}")

        # --- STEP 4: PAST DELIVERIES ---
        print("\n📦 Testing get_past_deliveries()...")
        try:
            past = await client.get_past_deliveries()
            print("✅ Past deliveries fetched:")
            print(f"   - Total weeks recorded: {len(past.weeks)}")
            if past.next_week:
                print(f"   - Next upcoming week: {past.next_week}")
            for w in past.weeks[:2]:
                print(f"     • Week {w.week}: {len(w.meals)} meals selected")
        except HelloFreshError as err:
            print(f"⚠️ get_past_deliveries response: {err}")

        # --- STEP 5: WEEKLY MENU & RECIPES ---
        print(f"\n🍱 Testing get_menu(week='{week}')...")
        sample_recipe_id = None
        try:
            menu = await client.get_menu(week=week)
            print("✅ Weekly menu fetched:")
            print(f"   - Week ID: {menu.week}")
            print(f"   - Meals Ready: {menu.meals_ready}")
            print(f"   - Available Meals: {len(menu.meals)}")

            for m in menu.meals[:3]:
                if m.recipe:
                    print(
                        f"     • [{m.recipe_family}] {m.recipe.name} ({m.recipe.headline})"
                    )
                    if not sample_recipe_id:
                        sample_recipe_id = m.recipe.id

        except HelloFreshError as err:
            print(f"❌ get_menu error: {err}")

        # --- STEP 6: RECIPE DETAILS ---
        if sample_recipe_id:
            print(f"\n📖 Testing get_recipe(recipe_id='{sample_recipe_id}')...")
            try:
                recipe = await client.get_recipe(sample_recipe_id)
                print("✅ Recipe details fetched:")
                print(f"   - Name: {recipe.name}")
                print(
                    f"   - Prep Time: {recipe.prep_time} | Total Time: {recipe.total_time}"
                )
                print(f"   - Difficulty: Level {recipe.difficulty}")
                print(f"   - Allergens: {[a.name for a in recipe.allergens]}")
                print(f"   - Ingredients Count: {len(recipe.ingredients)}")
                print(f"   - Steps Count: {len(recipe.steps)}")
                if recipe.steps:
                    print(f"   - Step 1: {recipe.steps[0].instructions[:80]}...")
            except HelloFreshError as err:
                print(f"❌ get_recipe error: {err}")

        # --- STEP 7: CART PRICING ---
        print(f"\n🛒 Testing get_cart_price(week='{week}')...")
        try:
            cart = await client.get_cart_price(week=week, box_size=2)
            print("✅ Cart pricing calculated:")
            print(f"   - Subtotal: £{cart.sub_total:.2f}")
            print(f"   - Shipping: £{cart.shipping_amount:.2f}")
            print(f"   - Discount: £{cart.discount_amount:.2f}")
            print(f"   - Grand Total: £{cart.grand_total:.2f}")
        except HelloFreshError as err:
            print(f"❌ get_cart_price error: {err}")

    print("\n" + "=" * 60)
    print(" ✨  Test execution complete!")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test pyhellofresh library against HelloFresh API."
    )
    parser.add_argument(
        "--token", type=str, help="Existing HelloFresh Bearer JWT Access Token"
    )
    parser.add_argument(
        "--refresh-token", type=str, help="Existing HelloFresh Refresh Token"
    )
    parser.add_argument(
        "--email", type=str, help="User email address for passwordless magic link flow"
    )
    parser.add_argument(
        "--country", type=str, default="GB", help="ISO Country code (default: GB)"
    )
    parser.add_argument(
        "--locale", type=str, default="en-GB", help="Language locale (default: en-GB)"
    )
    parser.add_argument(
        "--week",
        type=str,
        default="2026-W32",
        help="Target delivery week (default: 2026-W32)",
    )

    args = parser.parse_args()

    try:
        asyncio.run(
            run_tests(
                access_token=args.token,
                refresh_token=args.refresh_token or os.getenv("REFRESH_TOKEN"),
                email=args.email or os.getenv("EMAIL"),
                country=args.country,
                locale=args.locale,
                week=args.week,
            )
        )
    except KeyboardInterrupt:
        print("\nTest cancelled by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
