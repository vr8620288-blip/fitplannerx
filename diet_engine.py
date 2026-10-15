"""Rule-based diet generator using data/food_database.csv."""
import random
from pathlib import Path
import pandas as pd

DATA = Path(__file__).parent / "data" / "food_database.csv"
MEAL_SPLIT = {"Breakfast": 0.25, "Mid-morning snack": 0.10, "Lunch": 0.30,
              "Evening snack": 0.10, "Dinner": 0.25}
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def load_foods() -> pd.DataFrame:
    try:
        return pd.read_csv(DATA, keep_default_na=False)
    except FileNotFoundError:
        return pd.DataFrame()


def _filter(foods, diet_type, allergens):
    allowed = {"Vegan": ["vegan"], "Vegetarian": ["vegan", "veg"],
               "Non-vegetarian": ["vegan", "veg", "nonveg"]}[diet_type]
    df = foods[foods["diet_type"].isin(allowed)]
    return df[~df["allergen"].isin([a.lower() for a in allergens])]


def _build_meal(pool, categories, meal_cal, rng):
    items = []
    for cat in categories:
        options = pool[pool["category"] == cat]
        if not options.empty:
            items.append(options.iloc[rng.randrange(len(options))])
    if not items:
        return []
    base = sum(i["calories"] for i in items)
    # scale servings so the meal hits its calorie share (rounded to 0.5 portions)
    factor = min(max(round(meal_cal / base * 2) / 2, 0.5), 3.0)
    return [{
        "food": i["name"], "quantity": f"{factor:g} x {i['serving']}",
        "calories": int(round(float(i["calories"]) * factor)), "protein": float(round(float(i["protein"]) * factor, 1)),
        "carbs": float(round(float(i["carbs"]) * factor, 1)), "fats": float(round(float(i["fats"]) * factor, 1)),
    } for i in items]


def generate_week_plan(target_cal, diet_type, allergens, goal, seed=None):
    """Return {day: {meal: [items]}} for 7 days."""
    foods = load_foods()
    if foods.empty:
        raise FileNotFoundError("food_database.csv is missing.")
    pool = _filter(foods, diet_type, allergens)
    rng = random.Random(seed)
    layout = {"Breakfast": ["breakfast", "snack"], "Mid-morning snack": ["snack"],
              "Lunch": ["carb", "protein", "side"], "Evening snack": ["snack"],
              "Dinner": ["carb", "protein", "side"]}
    if goal in ("Muscle gain", "Weight gain"):
        layout["Evening snack"] = ["snack", "snack"]
    plan = {}
    for day in DAYS:
        plan[day] = {m: _build_meal(pool, layout[m], target_cal * share, rng)
                     for m, share in MEAL_SPLIT.items()}
    return plan


def day_totals(day_plan):
    items = [i for meal in day_plan.values() for i in meal]
    return {k: round(float(sum(i[k] for i in items)), 1) for k in ("calories", "protein", "carbs", "fats")}
