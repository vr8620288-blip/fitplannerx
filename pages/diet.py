import random

import pandas as pd
import streamlit as st

import database as db
import diet_engine
from calculations import (GOALS, calculate_bmr, calculate_tdee, target_calories)
from utils import disclaimer, page_header, require_login

user = require_login()
page_header("Smart Diet Planner", "A 7-day Indian meal plan matched to your calorie target.")

bmr = calculate_bmr(user["weight_kg"], user["height_cm"], user["age"], user["gender"])
default_cal = int(target_calories(calculate_tdee(bmr, user["activity_level"]), user["goal"], bmr))
diet_types = ["Vegetarian", "Non-vegetarian", "Vegan"]

tab_new, tab_saved = st.tabs(["✨ Generate plan", "📁 Saved plans"])


def render_plan(plan):
    tabs = st.tabs(list(plan.keys()))
    for tab, (day, meals) in zip(tabs, plan.items()):
        with tab:
            rows = []
            for meal, items in meals.items():
                for i in items:
                    rows.append({"Meal": meal, "Food": i["food"], "Quantity": i["quantity"],
                                 "Calories": i["calories"], "Protein (g)": i["protein"],
                                 "Carbs (g)": i["carbs"], "Fats (g)": i["fats"]})
            st.dataframe(pd.DataFrame(rows), hide_index=True)
            t = diet_engine.day_totals(meals)
            c = st.columns(4)
            c[0].metric("Calories", int(t["calories"]))
            c[1].metric("Protein", f"{t['protein']} g")
            c[2].metric("Carbs", f"{t['carbs']} g")
            c[3].metric("Fats", f"{t['fats']} g")


def plan_csv(plan):
    rows = [{"Day": d, "Meal": m, "Food": i["food"], "Quantity": i["quantity"], "Calories": i["calories"],
             "Protein": i["protein"], "Carbs": i["carbs"], "Fats": i["fats"]}
            for d, meals in plan.items() for m, items in meals.items() for i in items]
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")


with tab_new:
    c1, c2 = st.columns(2)
    goal = c1.selectbox("Goal", GOALS, index=GOALS.index(user["goal"]))
    pref = user["food_preference"] if user["food_preference"] in diet_types else "Vegetarian"
    diet_type = c2.selectbox("Diet type", diet_types, index=diet_types.index(pref))
    allergens = c1.multiselect("Allergies / restrictions", ["dairy", "egg", "nuts", "gluten", "soy", "fish"])
    calories = c2.number_input("Daily calorie target (kcal)", 1000, 5000, default_cal, step=50)

    if st.button("🎲 Generate / Regenerate plan"):
        try:
            st.session_state["diet_plan"] = {
                "plan": diet_engine.generate_week_plan(calories, diet_type, allergens, goal, random.randint(1, 10**6)),
                "diet_type": diet_type, "calories": calories, "goal": goal}
        except FileNotFoundError:
            st.error("Food database file is missing (data/food_database.csv).")

    current = st.session_state.get("diet_plan")
    if current:
        render_plan(current["plan"])
        a, b = st.columns(2)
        if a.button("💾 Save this plan"):
            db.save_diet_plan(user["id"], current["diet_type"], current["calories"], current["goal"], current["plan"])
            st.toast("Plan saved ✅")
        b.download_button("⬇️ Download plan (CSV)", plan_csv(current["plan"]), "fitplanner_diet_plan.csv", "text/csv")
    else:
        st.info("Choose your options and click **Generate** to create your first plan.")

with tab_saved:
    plans = db.get_diet_plans(user["id"])
    if not plans:
        st.info("You have no saved plans yet.")
    for p in plans:
        with st.expander(f"{p['created_at']} · {p['diet_type']} · {int(p['target_calories'])} kcal · {p['goal']}"):
            render_plan(p["plan"])
            st.download_button("⬇️ Download (CSV)", plan_csv(p["plan"]), f"diet_plan_{p['id']}.csv", "text/csv", key=f"dl{p['id']}")
disclaimer()
