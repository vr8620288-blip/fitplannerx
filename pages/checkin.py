from datetime import date, timedelta

import plotly.graph_objects as go
import streamlit as st

import database as db
import gamification
from calculations import wellness_score
from utils import disclaimer, page_header, require_login

user = require_login()
page_header("Daily Check-in", "Log your day, get a wellness score, and earn badges.")
today = date.today()
done_today = db.get_done_exercises(user["id"], today)
ck = db.get_checkins(user["id"])
existing = ck[ck["checkin_date"].dt.date == today].iloc[0] if (not ck.empty and (ck["checkin_date"].dt.date == today).any()) else None

left, right = st.columns([1, 1])
with left:
    with st.form("checkin"):
        workout = st.checkbox("Did you complete today's workout?",
                              value=bool(existing["workout_done"]) if existing is not None else bool(done_today))
        water = st.slider("Water drunk (litres)", 0.0, 6.0, float(existing["water_l"]) if existing is not None else 2.0, 0.25)
        sleep = st.slider("Hours slept", 0.0, 12.0, float(existing["sleep_h"]) if existing is not None else 7.0, 0.5)
        energy = st.slider("Energy level (1-5)", 1, 5, int(existing["energy"]) if existing is not None else 3)
        diet = st.checkbox("Did you follow your diet?", value=bool(existing["diet_followed"]) if existing is not None else True)
        steps = st.number_input("Steps taken", 0, 60000, int(existing["steps"]) if existing is not None else 5000, step=500)
        if st.form_submit_button("Save check-in"):
            score = wellness_score(workout, water, sleep, energy, diet, steps)
            db.save_checkin(user["id"], today, workout, water, sleep, energy, diet, int(steps), score)
            for key in gamification.refresh_achievements(user["id"]):
                st.toast(f"🏆 Badge unlocked: {gamification.ACHIEVEMENTS[key][1]}")
            st.toast(f"Check-in saved — wellness score {score}/100 ✅")
            st.rerun()

with right:
    score = int(existing["wellness_score"]) if existing is not None else 0
    fig = go.Figure(go.Indicator(mode="gauge+number", value=score, title={"text": "Today's wellness score"},
                                 gauge={"axis": {"range": [0, 100]}, "bar": {"color": "#10b981"}}))
    fig.update_layout(height=260, margin=dict(l=10, r=10, t=40, b=0))
    st.plotly_chart(fig)
    if existing is None:
        st.info("Complete today's check-in to see your score.")
    c = st.columns(3)
    c[0].metric("🔥 Streak", f"{gamification.current_streak(user['id'])} d")
    c[1].metric("🏅 Best streak", f"{gamification.best_streak(user['id'])} d")
    c[2].metric("⭐ Points", gamification.fitness_points(user["id"]))

st.subheader("🏆 Achievements")
earned = db.get_earned_achievements(user["id"])
html = ""
for key, (icon, title, desc) in gamification.ACHIEVEMENTS.items():
    cls = "badge" if key in earned else "badge locked"
    html += f"<span class='{cls}'>{icon} <b>{title}</b><br><small>{desc}</small></span>"
st.markdown(html, unsafe_allow_html=True)
disclaimer()
