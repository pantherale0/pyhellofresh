# pyhellofresh

Async Python client library for accessing HelloFresh APIs. Designed to be completely standalone, fully typed, and ready for integration into Python applications or Home Assistant integrations.

Guides and the API reference are published at <https://pantherale0.github.io/pyhellofresh/>.

## Features

- **100% Asynchronous**: Built on top of `aiohttp` for non-blocking HTTP requests.
- **Session Injection**: Supports injecting custom `aiohttp.ClientSession` or auto-managing internal sessions.
- **Authentication**: Supports direct Bearer JWT token initialization, token refreshing (`refresh_access_token`), and passwordless magic link login (`start_passwordless_login` & `finish_passwordless_login`).
- **Data Endpoints**:
  - Customer Profile & Dietary Exclusions (`get_profile`)
  - Account Credit Balance (`get_balance`)
  - Weekly Delivery Schedule & Past Deliveries (`get_past_deliveries`)
  - Weekly Menus & Selected Meals (`get_menu`)
  - Full Recipe Details, Ingredients, Nutrition & Step Instructions (`get_recipe`)
  - Cart Price Calculations (`get_cart_price`)
- **Strictly Typed**: Dataclass models for all API resources.

## Installation

```bash
pip install pyhellofresh
```

## Quickstart Example

```python
import asyncio
from pyhellofresh import HelloFreshClient


async def main():
    # Initialize client with existing Bearer token
    client = HelloFreshClient(
        access_token="YOUR_ACCESS_TOKEN", country="GB", locale="en-GB"
    )

    # Fetch profile
    profile = await client.get_profile()
    print(f"Adults: {profile.adults}, Exclusions: {profile.exclusions}")

    # Fetch weekly menu for 2026-W32
    menu = await client.get_menu(week="2026-W32")
    print(f"Week: {menu.week}, Total meals available: {len(menu.meals)}")

    # Close session
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
```

### Passwordless Login Flow

```python
import asyncio
from pyhellofresh import HelloFreshClient


async def login():
    async with await HelloFreshClient.with_session() as client:
        # Step 1: Trigger magic link email
        public_id = await client.start_passwordless_login("user@example.com")
        print(f"Magic link sent. Public ID: {public_id}")

        # Step 2: Extract code from link clicked in email and complete login
        token_resp = await client.finish_passwordless_login(
            code="CODE_FROM_EMAIL_LINK",
            email="user@example.com",
            public_id=public_id,
        )
        print(f"Access Token: {token_resp.access_token}")
        print(f"Refresh Token: {token_resp.refresh_token}")
```

### Token Refreshing

```python
async def refresh(client: HelloFreshClient):
    new_tokens = await client.refresh_access_token()
    print(f"Updated Access Token: {new_tokens.access_token}")
```

## Testing with the Test Script

A ready-to-use CLI test script [`example_test.py`](file:///home/jordanh/Documents/pyhellofresh/example_test.py) is provided to quickly test API connectivity and models:

```bash
# Test with an existing Bearer JWT token:
python3 example_test.py --token "YOUR_ACCESS_TOKEN"

# Test passwordless magic link flow:
python3 example_test.py --email "user@example.com"

# Test token refresh:
python3 example_test.py --refresh-token "YOUR_REFRESH_TOKEN"
```

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'

# Run tests & coverage
pytest --cov=pyhellofresh
```

## License

MIT
