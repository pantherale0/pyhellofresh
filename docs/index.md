# pyhellofresh

Async Python client for the HelloFresh customer API. It is typed, uses `aiohttp`, and accepts an injected `ClientSession` so it can run inside an application or a Home Assistant integration.

```bash
pip install pyhellofresh
```

```python
import asyncio
from pyhellofresh import HelloFreshClient

async def main():
    async with await HelloFreshClient.with_session(
        access_token="YOUR_ACCESS_TOKEN",
        country="GB",
        locale="en-GB",
    ) as client:
        profile = await client.get_profile()
        print(profile.adults, profile.exclusions)

        meals = await client.get_meals_for_week_offset(0)
        for meal in meals:
            if meal.recipe:
                print(meal.quantity, meal.recipe.name)

asyncio.run(main())
```

## What you can call

| Area | Methods |
| --- | --- |
| Login | `start_passwordless_login`, `finish_passwordless_login`, `finish_passwordless_login_from_url`, `refresh_access_token` |
| Account | `get_profile`, `get_customer_info`, `get_subscriptions`, `get_balance` |
| This box | `get_meals_for_week_offset`, `get_past_deliveries`, `get_menu` |
| Recipes | `get_recipe`, `search_recipes` |
| Price | `get_cart_price` |

The default gateway is the UK site (`https://www.hellofresh.co.uk`) with country `GB` and locale `en-GB`. Pass `country`, `locale`, and `base_url` when you are calling another HelloFresh country site.

Python 3.11 or newer is required.
