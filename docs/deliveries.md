# Deliveries and meals

HelloFresh identifies a box by an ISO week such as `2026-W40`. The week you can still edit is usually later than the box that is already locked for delivery.

`get_meals_for_week_offset()` starts at the latest locked delivery and walks by whole ISO weeks.

| Offset | Week |
| --- | --- |
| `0` | Newest scheduled week whose cutoff has already passed. This is the box arriving now. |
| `1` | The following week, still open for selection when its cutoff is in the future. |
| `-1` | The delivery before the locked box. |

```python
current = await client.get_meals_for_week_offset(0)
following = await client.get_meals_for_week_offset(1)
previous = await client.get_meals_for_week_offset(-1)

for meal in current:
    if meal.recipe:
        print(f"{meal.quantity} x {meal.recipe.name}")
```

The method loads the delivery schedule from eight weeks before the current ISO week through six weeks after it, picks the anchor week, then loads that week's menu. Only meals with `selection.quantity > 0` are returned. `Meal.selected` is that check, and `Meal.quantity` is the count.

Paused, cancelled, and donated weeks are skipped while another delivery remains. A schedule with no usable week raises `HelloFreshError`.

## How the anchor is chosen

1. Keep weeks whose cutoff is already in the past, and take the newest of those.
2. If no cutoff is present, keep deliveries dated no later than seven days from now, and take the newest of those.
3. Otherwise take the newest week id in the schedule.

```python
from datetime import datetime, timezone
from pyhellofresh.weeks import select_latest_delivery_week, shift_iso_week

latest = select_latest_delivery_week(deliveries.weeks, datetime.now(timezone.utc))
target = shift_iso_week(latest, 1)
```

## Delivery schedule

```python
schedule = await client.get_past_deliveries("2026-W36", "2026-W42")
print(schedule.next_week)
for week in schedule.weeks:
    print(week.week, week.status, week.cutoff_date, week.delivery_date)
```

`range_start` and `range_end` are optional ISO week ids sent as `rangeStart` and `rangeEnd`. Omit them and the gateway uses its default window, which is often only the upcoming editable week.

Each `PastDeliveryItem` exposes:

| Field | Source |
| --- | --- |
| `week` | `week`, `hfWeek`, or an `id` that already looks like `2026-W40` |
| `cutoff_date` | `cutoffDate` or `cutoffDateTime` |
| `delivery_date` | `deliveryDate` or `deliveryDateTime` |
| `status` | `status`, or `state` when status is empty |
| `menu_id` | `menuId` |
| `meals`, `addons` | Raw objects from the payload, when the endpoint includes them |

`next_week` is the payload's `nextWeek` value. On the past-deliveries pagination API that field is a cursor toward older weeks. It is not, by itself, the next menu you can edit. Use `get_meals_for_week_offset(1)` for that box.

The schedule parser accepts either a `weeks` list or an `items` list.

## Week helpers

::: pyhellofresh.weeks.current_iso_week
    options:
      show_root_heading: true

::: pyhellofresh.weeks.shift_iso_week

::: pyhellofresh.weeks.select_latest_delivery_week
