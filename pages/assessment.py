import streamlit as st

import database as db
from calculations import (ACTIVITY_MULTIPLIERS, GOALS, bmi_category, calculate_bmi,
                          calculate_bmr, calculate_tdee, healthy_weight_range,
                          target_calories, weekly_change_kg)
from datetime import date
from utils import bmi_scale, disclaimer, metric_card, page_header, require_login

user = require_login()
page_header("Health Assessment", "BMI, BMR and your daily calorie target.")
tab1, tab2, tab3 = st.tabs(["📊 My assessment", "🎚️ BMI what-if", "👤 Edit profile"])

with tab1:
    bmi = calculate_bmi(user["weight_kg"], user["height_cm"])
    cat, meaning, action = bmi_category(bmi)
    low, high = healthy_weight_range(user["height_cm"])
    bmr = calculate_bmr(user["weight_kg"], user["height_cm"], user["age"], user["gender"])
    tdee = calculate_tdee(bmr, user["activity_level"])
    target_cal = target_calories(tdee, user["goal"], bmr)
    bmi_scale(bmi)
    st.markdown(f"### BMI {bmi} — {cat}")
    st.write(meaning, action)
    st.caption("BMI is a general screening metric and not a medical diagnosis.")

    c = st.columns(4)
    with c[0]: metric_card("BMR", f"{int(bmr)} kcal", "Mifflin-St Jeor")
    with c[1]: metric_card("Daily need (TDEE)", f"{int(tdee)} kcal", f"{user['activity_level']} x{ACTIVITY_MULTIPLIERS[user['activity_level']]}")
    with c[2]: metric_card("Target calories", f"{int(target_cal)} kcal", f"Goal: {user['goal']}")
    with c[3]: metric_card("Weekly change", f"{weekly_change_kg(user['goal']):+.2f} kg", "estimate")
    diff = round(user["weight_kg"] - (user["target_weight_kg"] or user["weight_kg"]), 1)
    st.write(f"**Current:** {user['weight_kg']} kg · **Target:** {user['target_weight_kg']} kg · "
             f"**Difference:** {diff:+} kg · **Healthy range for your height:** {low}-{high} kg")
    st.caption("All calorie values are estimates.")

with tab2:
    st.write("Move the sliders to see how BMI changes (nothing is saved).")
    h = st.slider("Height (cm)", 120, 220, int(user["height_cm"]))
    w = st.slider("Weight (kg)", 30, 200, int(user["weight_kg"]))
    b = calculate_bmi(w, h)
    bmi_scale(b)
    st.write(f"**BMI {b} — {bmi_category(b)[0]}**")

with tab3:
    with st.form("profile_form"):
        name = st.text_input("Full name", user["full_name"])
        c1, c2 = st.columns(2)
        age = c1.number_input("Age", 10, 100, int(user["age"]))
        gender = c2.selectbox("Gender", ["Male", "Female"], index=["Male", "Female"].index(user["gender"]))
        height = c1.number_input("Height (cm)", 100.0, 250.0, float(user["height_cm"]))
        weight = c2.number_input("Weight (kg)", 25.0, 300.0, float(user["weight_kg"]))
        target = c1.number_input("Target weight (kg)", 25.0, 300.0, float(user["target_weight_kg"] or user["weight_kg"]))
        activity = c2.selectbox("Activity level", list(ACTIVITY_MULTIPLIERS), index=list(ACTIVITY_MULTIPLIERS).index(user["activity_level"]))
        goal = c1.selectbox("Fitness goal", GOALS, index=GOALS.index(user["goal"]))
        foods = ["Vegetarian", "Non-vegetarian", "Vegan"]
        pref = c2.selectbox("Food preference", foods, index=foods.index(user["food_preference"] or "Vegetarian"))
        if st.form_submit_button("Save profile"):
            if not name.strip():
                st.error("Name cannot be empty.")
            else:
                db.update_profile(user["id"], full_name=name.strip(), age=int(age), gender=gender,
                                  height_cm=height, target_weight_kg=target, activity_level=activity,
                                  goal=goal, food_preference=pref)
                if weight != user["weight_kg"]:
                    db.add_progress(user["id"], date.today(), weight, calculate_bmi(weight, height))
                st.toast("Profile updated ✅")
                st.rerun()
disclaimer()
