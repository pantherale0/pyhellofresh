# Sessions

`HelloFreshClient` speaks HTTP through `aiohttp`. You can own the session or let the client create one.

## Inject a session

Home Assistant and other hosts expect the integration to use their session.

```python
async with aiohttp.ClientSession() as session:
    client = HelloFreshClient(session=session, access_token="YOUR_ACCESS_TOKEN")
    profile = await client.get_profile()
    await client.close()  # leaves the injected session open
```

`close()` closes a session only when the client created it.

## Let the client own the session

```python
client = HelloFreshClient(access_token="YOUR_ACCESS_TOKEN")
try:
    profile = await client.get_profile()
finally:
    await client.close()
```

The first request opens a `ClientSession`. `close()` closes it.

`HelloFreshClient.with_session()` opens a session immediately and marks the client as its owner:

```python
async with await HelloFreshClient.with_session(access_token="YOUR_ACCESS_TOKEN") as client:
    profile = await client.get_profile()
```

Leaving the `async with` block calls `close()`.

## Country, locale, and timeout

| Argument | Default | Role |
| --- | --- | --- |
| `country` | `GB` | Sent as the HelloFresh country code |
| `locale` | `en-GB` | Sent as the locale |
| `base_url` | `https://www.hellofresh.co.uk` | Gateway host, without a trailing slash |
| `request_timeout` | `10` | Seconds for each HTTP call |

`country`, `locale`, `base_url`, and `request_timeout` are read-only properties after construction.
