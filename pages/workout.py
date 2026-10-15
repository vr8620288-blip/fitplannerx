import random
from datetime import date

import streamlit as st

import database as db
import gamification
import workout_engine as we
from utils import disclaimer, page_header, require_login

user = require_login()
page_header("Workout Planner", "A weekly schedule based on your goal, level, time and equipment.")
GOALS_W = ["Weight loss", "Muscle gain", "Strength", "General fitness", "Flexibility"]

with st.expander("⚙️ Plan settings", expanded="workout_plan" not in st.session_state):
    c1, c2 = st.columns(2)
    goal = c1.selectbox("Goal", GOALS_W)
    level = c2.selectbox("Fitness level", we.LEVELS)
    days = c1.slider("Workout days per week", 2, 5, 4)
    duration = c2.select_slider("Workout duration (min)", [20, 30, 45, 60, 75], value=45)
    equipment = st.multiselect("Equipment available", ["Dumbbells", "Gym"], default=["Dumbbells"],
                               help="Bodyweight exercises are always included.")
    b1, b2 = st.columns(2)
    if b1.button("🎲 Generate / Regenerate"):
        try:
            st.session_state["workout_plan"] = {
                "plan": we.generate_plan(goal, level, days, duration, equipment, random.randint(1, 10**6)),
                "goal": goal, "level": level, "days": days, "saved": False}
        except FileNotFoundError:
            st.error("Exercise database file is missing (data/exercise_database.csv).")
    if b2.button("💾 Save as my active plan") and "workout_plan" in st.session_state:
        w = st.session_state["workout_plan"]
        db.save_workout_plan(user["id"], w["goal"], w["level"], w["days"], w["plan"])
        st.toast("Workout plan saved ✅")

# Use the freshly generated plan, otherwise the latest saved one
if "workout_plan" in st.session_state:
    plan = st.session_state["workout_plan"]["plan"]
else:
    saved = db.get_latest_workout_plan(user["id"])
    plan = saved["plan"] if saved else None

if not plan:
    st.info("No workout plan yet. Open **Plan settings** and click Generate.")
    st.stop()

today_name = date.today().strftime("%A")
tabs = st.tabs([("📍 " if d == today_name else "") + d[:3] for d in we.WEEK])
for tab, day_name in zip(tabs, we.WEEK):
    with tab:
        day = plan[day_name]
        st.subheader(day["focus"])
        if not day["exercises"]:
            st.info("Rest day — recover, stretch and hydrate. 😴")
            continue
        is_today = day_name == today_name
        done = db.get_done_exercises(user["id"], date.today()) if is_today else set()
        if is_today:
            st.progress(len(done & {e["name"] for e in day["exercises"]}) / len(day["exercises"]),
                        text="Today's completion")
        else:
            st.caption("You can tick exercises off on the day itself.")
        for e in day["exercises"]:
            c1, c2 = st.columns([3, 1])
            with c1:
                checked = st.checkbox(f"**{e['name']}** · {e['muscle_group']}", value=e["name"] in done,
                                      key=f"chk_{day_name}_{e['name']}", disabled=not is_today)
                st.caption(f"{e['sets']} sets × {e['reps']} · rest {e['rest_sec']} s · {e['difficulty']} — {e['instructions']}")
            if is_today and checked != (e["name"] in done):
                db.set_exercise_done(user["id"], date.today(), e["name"], checked)
                for key in gamification.refresh_achievements(user["id"]):
                    st.toast(f"🏆 Badge unlocked: {gamification.ACHIEVEMENTS[key][1]}")
                st.rerun()
disclaimer()
