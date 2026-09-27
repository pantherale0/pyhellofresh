# Account

These calls need an access token.

## Profile

```python
profile = await client.get_profile()
print(profile.total_people, profile.adults, profile.children)
print(profile.exclusions)
print(profile.dietary_preferences)
print(profile.meal_types)
print(profile.cuisines)
```

`Profile` is parsed from the household and taste blocks. `exclusions`, `dietary_preferences`, and `meal_types` are lists of strings. `cuisines` maps a cuisine name to an integer score.

## Customer info and subscriptions

```python
info = await client.get_customer_info()
subscriptions = await client.get_subscriptions()
```

Both return the gateway JSON. `get_subscriptions()` returns the list itself when the payload is a list, or `items` when the payload is an object.

Other methods read these keys from customer info when you do not pass them yourself:

| Key | Used by |
| --- | --- |
| `uuid` or `id` | `get_balance` when `customer_id` is omitted |
| `activeSubscriptionId` | `get_menu`, `get_cart_price` |
| `activeSubscriptionSkus` | `get_menu`, `get_cart_price` |
| `id` | `get_cart_price` as `customerID` when it is an integer |
| `customerPlanIds` | `get_cart_price`, first entry |

## Balance

```python
balance = await client.get_balance()
print(balance.amount, balance.bonus, balance.currency_code)
```

`amount`, `cash`, `bonus`, `restricted_amount`, and `cancellable_credits` are integer minor units. Divide by 100 to show major units for a currency such as GBP. Pass `customer_id` to skip the customer-info lookup. The string `"me"` also triggers that lookup.
