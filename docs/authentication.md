# Authentication

Most account calls need a Bearer access token. Recipe search, the passwordless login calls, and token refresh can run with the guest token the client already carries.

## Use an existing access token

```python
from pyhellofresh import HelloFreshClient

client = HelloFreshClient(
    access_token="YOUR_ACCESS_TOKEN",
    refresh_token="YOUR_REFRESH_TOKEN",
    country="GB",
    locale="en-GB",
)
```

`access_token` and `refresh_token` are properties. Assigning them updates the token the next request will send.

Authenticated calls that receive HTTP 401 or 403 retry once with `refresh_access_token()` when a refresh token is stored.

## Passwordless login

HelloFresh emails a magic link. Start the flow, then finish it with the link URL or with the query parameters from that link.

```python
async with await HelloFreshClient.with_session() as client:
    public_id = await client.start_passwordless_login("user@example.com")

    tokens = await client.finish_passwordless_login_from_url(
        "https://www.hellofresh.co.uk/....?code=...&email=...&public_id=..."
    )
    print(tokens.access_token, tokens.refresh_token)
```

`start_passwordless_login` returns the `public_id` it generated and asks HelloFresh to email the link. The default redirect is `{base_url}/my-account/deliveries/menu`. Pass `redirect_url` to override it.

`finish_passwordless_login_from_url` reads `code`, `email`, `public_id`, and `redirect_url` from the link. Tracking hosts such as `click.link.hellofresh.co.uk` are followed once via the `Location` header so the real query string can be read. If the link has no `public_id`, pass the value returned by `start_passwordless_login`.

When you already have the pieces separately:

```python
tokens = await client.finish_passwordless_login(
    code="CODE_FROM_THE_LINK",
    email="user@example.com",
    public_id=public_id,
)
```

Both finish methods store the new access token and refresh token on the client and return a [`TokenResponse`](api/models.md#pyhellofresh.TokenResponse).

## Refresh

```python
tokens = await client.refresh_access_token()
```

Pass a refresh token to use that value for this call. Otherwise the stored `refresh_token` is used. A missing refresh token raises `HelloFreshAuthenticationError`.

## Guest token

Unauthenticated gateway calls send `guest_token` when no access token is set. The client ships with a guest JWT and replaces it when that token is rejected:

```python
token = await client.fetch_guest_token()
```

`fetch_guest_token` loads the login page and reads `access_token` from the `__NEXT_DATA__` payload.
