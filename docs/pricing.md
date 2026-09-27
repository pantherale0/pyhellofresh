# Pricing

`get_cart_price()` asks the cart service for a week's price.

```python
cart = await client.get_cart_price("2026-W40", box_size=2)
print(cart.grand_total, cart.sub_total, cart.shipping_amount)
print(cart.discount_amount, cart.coupon_code)
for product in cart.products:
    print(product.handle, product.paid_price, product.quantity)
```

| Argument | Role |
| --- | --- |
| `week` | Delivery week, for example `2026-W40` |
| `box_size` | Meal count sent as `boxSize`. Default `2` |
| `subscription_id` | Subscription id. Filled from customer info when omitted |
| `product_sku` | Product handle. Filled from `activeSubscriptionSkus` when omitted |
| `products` | Explicit product list. When omitted, one product is sent with `handle` and `hfWeek` |

Customer info also supplies `customerID` when `id` is an integer, and `planID` from the first `customerPlanIds` entry. The request is marked recurring and not a first order.

Money fields on `CartPrice` and `CartProduct` are floats in major units, matching the cart payload (`grandTotal`, `unitPrice`, and the rest).
