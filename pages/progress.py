from datetime import date, timedelta

import plotly.express as px
import streamlit as st

import database as db
from calculations import calculate_bmi
from utils import disclaimer, metric_card, page_header, require_login

user = require_login()
page_header("Progress & Goals", "Track your body metrics, habits and goals.")
tab_charts, tab_log, tab_goals = st.tabs(["📈 Analytics", "➕ Log progress", "🎯 Goals"])


def line(df, x, y, title, color="#10b981", target=None):
    fig = px.line(df, x=x, y=y, markers=True, title=title, color_discrete_sequence=[color])
    if target:
        fig.add_hline(y=target, line_dash="dash", annotation_text="Target")
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=40, b=0))
    return fig


with tab_charts:
    prog = db.get_progress(user["id"])
    ck = db.get_checkins(user["id"])
    if prog.empty:
        st.info("No progress records yet — add one in the **Log progress** tab.")
    else:
        start, now = prog.iloc[0]["weight_kg"], prog.iloc[-1]["weight_kg"]
        tgt = user["target_weight_kg"] or now
        span = start - tgt
        pct = 0 if span == 0 else max(0, min((start - now) / span * 100, 100))
        c = st.columns(5)
        with c[0]: metric_card("Starting weight", f"{start} kg")
        with c[1]: metric_card("Current weight", f"{now} kg")
        with c[2]: metric_card("Target weight", f"{tgt} kg")
        with c[3]: metric_card("Lost / gained", f"{start - now:+.1f} kg")
        with c[4]: metric_card("Progress", f"{pct:.0f}%")
        st.progress(pct / 100)
        a, b = st.columns(2)
        a.plotly_chart(line(prog, "record_date", "weight_kg", "Weight (kg)", target=tgt))
        b.plotly_chart(line(prog, "record_date", "bmi", "BMI", "#6366f1"))
        if prog["waist_cm"].notna().any():
            st.plotly_chart(line(prog.dropna(subset=["waist_cm"]), "record_date", "waist_cm", "Waist (cm)", "#f59e0b"))
    if not ck.empty:
        st.subheader("Habits")
        a, b = st.columns(2)
        fig = px.bar(ck, x="checkin_date", y="water_l", title="Water intake (L)", color_discrete_sequence=["#38bdf8"])
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=40, b=0))
        a.plotly_chart(fig)
        b.plotly_chart(line(ck, "checkin_date", "wellness_score", "Wellness score", "#10b981"))
        week = ck[ck["checkin_date"] >= (ck["checkin_date"].max() - timedelta(days=6))]
        month = ck[ck["checkin_date"] >= (ck["checkin_date"].max() - timedelta(days=29))]
        s1, s2 = st.columns(2)
        s1.info(f"**Weekly summary** — avg score {week['wellness_score'].mean():.0f}, workouts {int(week['workout_done'].sum())}, "
                f"avg water {week['water_l'].mean():.1f} L, diet followed {int(week['diet_followed'].sum())}/{len(week)} days")
        s2.info(f"**Monthly summary** — avg score {month['wellness_score'].mean():.0f}, workouts {int(month['workout_done'].sum())}, "
                f"avg sleep {month['sleep_h'].mean():.1f} h, avg steps {int(month['steps'].mean())}")

with tab_log:
    with st.form("progress_form"):
        d = st.date_input("Date", date.today(), max_value=date.today())
        w = st.number_input("Weight (kg)", 25.0, 300.0, float(user["weight_kg"]), step=0.1)
        waist = st.number_input("Waist (cm) — optional, 0 to skip", 0.0, 200.0, 0.0, step=0.5)
        st.caption(f"BMI will be calculated automatically: {calculate_bmi(w, user['height_cm'])}")
        if st.form_submit_button("Save record"):
            db.add_progress(user["id"], d, w, calculate_bmi(w, user["height_cm"]), waist or None)
            st.toast("Progress saved ✅")
            st.rerun()

with tab_goals:
    with st.form("goal_form"):
        st.write("**Add a goal**")
        title = st.text_input("Goal title", placeholder="e.g. Lose 5 kg")
        c1, c2, c3 = st.columns(3)
        gs = c1.number_input("Starting value", 0.0, 500.0, float(user["weight_kg"]))
        gt = c2.number_input("Target value", 0.0, 500.0, float(user["target_weight_kg"] or user["weight_kg"]))
        dl = c3.date_input("Deadline", date.today() + timedelta(days=60))
        if st.form_submit_button("Add goal"):
            if not title.strip():
                st.error("Please enter a goal title.")
            elif gs == gt:
                st.error("Start and target values must differ.")
            else:
                db.add_goal(user["id"], title.strip(), gs, gt, dl)
                st.toast("Goal added 🎯")
                st.rerun()
    goals = db.get_goals(user["id"])
    if not goals:
        st.info("No goals yet. Add your first one above.")
    for g in goals:
        span = g["start_value"] - g["target_value"]
        pct = 0 if span == 0 else max(0.0, min((g["start_value"] - g["current_value"]) / span, 1.0))
        with st.expander(f"{'✅' if g['completed'] else '🎯'} {g['title']} — {int(pct * 100)}%", expanded=not g["completed"]):
            st.progress(pct)
            st.caption(f"Start {g['start_value']} → Target {g['target_value']} · Current {g['current_value']} · Deadline {g['deadline']}")
            cur = st.number_input("Current value", 0.0, 500.0, float(g["current_value"]), key=f"cur{g['id']}")
            new_title = st.text_input("Title", g["title"], key=f"t{g['id']}")
            b1, b2, b3 = st.columns(3)
            if b1.button("Save changes", key=f"s{g['id']}"):
                db.update_goal(g["id"], user["id"], current_value=cur, title=new_title.strip() or g["title"])
                st.rerun()
            if b2.button("Mark completed", key=f"c{g['id']}"):
                db.update_goal(g["id"], user["id"], completed=1, current_value=g["target_value"])
                import gamification
                gamification.refresh_achievements(user["id"])
                st.rerun()
            if b3.button("Delete", key=f"d{g['id']}"):
                db.delete_goal(g["id"], user["id"])
                st.rerun()
disclaimer()
