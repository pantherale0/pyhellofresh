# Menus and recipes

## Weekly menu

`get_menu(week)` returns every course on that week's menu, including courses that are not in the box.

```python
menu = await client.get_menu("2026-W40")
print(menu.id, menu.week, menu.meals_ready)

for meal in menu.meals:
    if meal.selected and meal.recipe:
        print(meal.index, meal.quantity, meal.recipe.name, meal.charge)
```

`subscription_id` and `product_sku` are optional. When either is missing, the client fills them from `get_customer_info()` (`activeSubscriptionId` and `activeSubscriptionSkus`). A failure there is ignored and the menu is still requested.

`Meal.quantity` comes from `selection.quantity`. A skipped selection (`selection.skipped`) is stored as quantity `0`. `Meal.charge` is a major-unit float. Integer charge amounts of 10 or more are treated as minor units and divided by 100. `related_category` and `recipe_family` are copied from the course.

`add_ons` and `categories` stay as the raw objects from the menu payload.

For the meals actually selected in a box, prefer [`get_meals_for_week_offset()`](deliveries.md).

## One recipe

```python
recipe = await client.get_recipe(meal.recipe.id)
print(recipe.headline)
print(recipe.prep_time, recipe.total_time, recipe.difficulty)
for ingredient in recipe.ingredients:
    print(ingredient.name, ingredient.shipped)
for step in recipe.steps:
    print(step.index, step.instructions, step.utensils)
```

`Recipe` includes allergens, ingredients, steps, nutrition, and yields. Image fields are rewritten onto `media.hellofresh.com` when the payload supplies a relative path or a legacy CloudFront URL. A URL that is already on another host is left as-is.

Times are the ISO-8601 durations returned by the API, such as `PT40M`.

## Search

Search does not require an access token.

```python
recipes = await client.search_recipes("pasta", take=10, skip=0)
```

`take` is the page size and `skip` is the offset. The client reads `items` from the response.
