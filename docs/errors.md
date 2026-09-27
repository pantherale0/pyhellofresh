# Errors

Every library failure subclasses `HelloFreshError`.

| Exception | When it is raised |
| --- | --- |
| `HelloFreshAuthenticationError` | Missing or rejected access token, missing refresh token, or an auth error body such as `invalid_grant` |
| `HelloFreshResponseError` | Any other HTTP status of 400 or higher |
| `HelloFreshConnectionError` | Timeout, `aiohttp` connection error, or a magic-link redirect that could not be followed |
| `HelloFreshError` | Anything else, including a delivery schedule with no usable week |

```python
from pyhellofresh import (
    HelloFreshAuthenticationError,
    HelloFreshConnectionError,
    HelloFreshError,
    HelloFreshResponseError,
)

try:
    meals = await client.get_meals_for_week_offset(0)
except HelloFreshAuthenticationError as err:
    print(err.status_code, err.error_code)
except HelloFreshResponseError as err:
    print(err.status_code, err.message)
except HelloFreshConnectionError:
    raise
except HelloFreshError:
    raise
```

`HelloFreshAuthenticationError.status_code` and `error_code` are set when the gateway returned them. `HelloFreshResponseError` always has `status_code` and `message`.

Authenticated requests that fail with 401 or 403 try `refresh_access_token()` once before raising, when a refresh token is available. Unauthenticated calls that fail with 401 try `fetch_guest_token()` once before raising.
