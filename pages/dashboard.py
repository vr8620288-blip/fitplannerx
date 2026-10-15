from datetime import date

import plotly.express as px
import streamlit as st

import database as db
import diet_engine
import gamification
from calculations import (bmi_category, calculate_bmi, calculate_bmr, calculate_tdee,
                          target_calories)
from utils import animated_counter, metric_card, page_header, require_login

user = require_login()
page_header(f"Welcome, {user['full_name'].split()[0]} 👋", "Here is your fitness overview for today.")

bmi = calculate_bmi(user["weight_kg"], user["height_cm"])
bmr = calculate_bmr(user["weight_kg"], user["height_cm"], user["age"], user["gender"])
cal = target_calories(calculate_tdee(bmr, user["activity_level"]), user["goal"], bmr)
streak = gamification.current_streak(user["id"])
goals = [g for g in db.get_goals(user["id"]) if not g["completed"]]


def goal_pct(g):
    span = g["start_value"] - g["target_value"]
    return 0 if span == 0 else max(0.0, min((g["start_value"] - g["current_value"]) / span, 1.0))


c = st.columns(6)
with c[0]: metric_card("BMI", bmi, bmi_category(bmi)[0])
with c[1]: metric_card("Current weight", f"{user['weight_kg']} kg")
with c[2]: metric_card("Target weight", f"{user['target_weight_kg'] or '-'} kg")
with c[3]: metric_card("Daily calories", int(cal), "estimate")
with c[4]: metric_card("Streak", f"{streak} 🔥", "days active")
with c[5]: metric_card("Goal progress", f"{int(goal_pct(goals[0]) * 100)}%" if goals else "-", goals[0]["title"] if goals else "No goal yet")

left, right = st.columns([1, 1])
with left:
    st.subheader("🏋️ Today's workout")
    wp = db.get_latest_workout_plan(user["id"])
    today_name = date.today().strftime("%A")
    if wp and wp["plan"].get(today_name, {}).get("exercises"):
        day = wp["plan"][today_name]
        done = db.get_done_exercises(user["id"], date.today())
        st.write(f"**{day['focus']}** — {len(done & {e['name'] for e in day['exercises']})}/{len(day['exercises'])} done")
        for e in day["exercises"]:
            st.write(f"{'✅' if e['name'] in done else '⬜'} {e['name']} — {e['sets']} x {e['reps']}")
    elif wp:
        st.info("Rest day today. Recover well! 😴")
    else:
        st.info("No workout plan yet. Generate one from the Workout Planner.")

    st.subheader("💧 Water today")
    ck = db.get_checkins(user["id"])
    water = 0.0
    if not ck.empty and ck.iloc[-1]["checkin_date"].date() == date.today():
        water = float(ck.iloc[-1]["water_l"])
    st.progress(min(water / 3.0, 1.0), text=f"{water:.1f} L of 3.0 L")
with right:
    st.subheader("🥗 Today's diet")
    dp = db.get_latest_diet_plan(user["id"])
    if dp:
        day = dp["plan"].get(today_name)
        tot = diet_engine.day_totals(day)
        st.write(f"**{int(tot['calories'])} kcal** · P {tot['protein']} g · C {tot['carbs']} g · F {tot['fats']} g")
        for meal, items in day.items():
            st.write(f"**{meal}:** " + ", ".join(i["food"] for i in items))
    else:
        st.info("No diet plan yet. Generate one from the Diet Planner.")

st.subheader("📅 Weekly wellness")
ck = db.get_checkins(user["id"])
if ck.empty:
    st.info("No check-ins yet — do your first daily check-in!")
else:
    fig = px.bar(ck.tail(7), x="checkin_date", y="wellness_score", range_y=[0, 100],
                 color_discrete_sequence=["#10b981"], labels={"checkin_date": "Date", "wellness_score": "Score"})
    fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig)

q = st.columns(4)
q[0].page_link("pages/assessment.py", label="Calculate BMI", icon="📊")
q[1].page_link("pages/diet.py", label="Generate Diet Plan", icon="🥗")
q[2].page_link("pages/workout.py", label="Generate Workout", icon="🏋️")
q[3].page_link("pages/checkin.py", label="Daily Check-in", icon="✅")

st.divider()
animated_counter(gamification.fitness_points(user["id"]), "⭐ Fitness points")
