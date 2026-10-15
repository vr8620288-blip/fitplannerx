"""FitPlanner - entry point. Run with:  streamlit run app.py"""
import streamlit as st

import database as db
from calculations import ACTIVITY_MULTIPLIERS, GOALS
from utils import load_css, disclaimer

st.set_page_config(page_title="FitPlanner", page_icon="💪", layout="wide")


@st.cache_resource
def start_database():
    """Create tables + demo account once per server start."""
    db.init_db()
    return True


try:
    start_database()
except Exception as e:  # never show a raw traceback to the examiner
    st.error(f"Could not start the database: {e}")
    st.stop()

load_css()


def landing_page():
    st.markdown("""
    <div class='hero'>
      <h1>💪 FitPlanner</h1>
      <p><b>Your Personal AI-Powered Fitness &amp; Wellness Planner</b></p>
      <p>Calculate your BMI, get a personalised diet and workout plan, check in daily,
      and watch your progress grow.</p>
    </div>""", unsafe_allow_html=True)

    left, right = st.columns([1.1, 1])
    with left:
        st.subheader("✨ What you get")
        feats = [("📊", "Health Assessment", "BMI, BMR and daily calorie target with a visual BMI scale."),
                 ("🥗", "Smart Diet Planner", "7-day Indian meal plans matched to your calories and diet type."),
                 ("🏋️", "Workout Planner", "Weekly schedules by goal, level, time and equipment."),
                 ("✅", "Daily Check-in", "Log water, sleep, steps and get a wellness score."),
                 ("📈", "Progress & Goals", "Charts, goal tracking and weekly summaries."),
                 ("🏆", "Streaks & Badges", "Earn points and achievements for consistency.")]
        cols = st.columns(2)
        for i, (icon, title, text) in enumerate(feats):
            cols[i % 2].markdown(f"<div class='feature'><h4>{icon} {title}</h4>"
                                 f"<p style='color:#6b7280;font-size:.9rem'>{text}</p></div><br>",
                                 unsafe_allow_html=True)
    with right:
        tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register"])
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    user = db.authenticate(email, password) if email and password else None
                    if user:
                        st.session_state["user_id"] = user["id"]
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")
            st.info("🧪 **Demo account** — Email: `demo@fitplanner.com`  Password: `Demo@123`")
            if st.button("🚀 Try Demo Account"):
                demo = db.get_user_by_email(db.DEMO_EMAIL)
                if demo:
                    st.session_state["user_id"] = demo["id"]
                    st.rerun()
        with tab_register:
            with st.form("register_form"):
                name = st.text_input("Full name")
                email = st.text_input("Email ", key="reg_email")
                password = st.text_input("Password (min 6 characters)", type="password", key="reg_pw")
                c1, c2 = st.columns(2)
                age = c1.number_input("Age", 10, 100, 20)
                gender = c2.selectbox("Gender", ["Male", "Female"])
                height = c1.number_input("Height (cm)", 100.0, 250.0, 170.0)
                weight = c2.number_input("Weight (kg)", 25.0, 300.0, 65.0)
                activity = st.selectbox("Activity level", list(ACTIVITY_MULTIPLIERS))
                goal = st.selectbox("Fitness goal", GOALS)
                if st.form_submit_button("Create account"):
                    uid, err = db.create_user(name, email, password, int(age), gender, height, weight, activity, goal)
                    if err:
                        st.error(err)
                    else:
                        st.session_state["user_id"] = uid
                        st.rerun()

    st.markdown("### How it works")
    steps = ["Create account", "Complete profile", "Calculate BMI", "Pick a goal", "Generate plans", "Track progress"]
    for col, (i, s) in zip(st.columns(6), enumerate(steps, 1)):
        col.markdown(f"<div class='fp-card' style='text-align:center'><div class='fp-value'>{i}</div>{s}</div>",
                     unsafe_allow_html=True)
    with st.expander("❓ Is FitPlanner a medical tool?"):
        st.write("No. It gives general estimates for education and wellness only.")
    with st.expander("❓ Do I need an API key or internet AI service?"):
        st.write("No. All recommendations are rule-based and run fully offline.")
    disclaimer()


def logged_in_app():
    pages = [
        st.Page("pages/dashboard.py", title="Dashboard", icon="🏠", default=True),
        st.Page("pages/assessment.py", title="Health Assessment", icon="📊"),
        st.Page("pages/diet.py", title="Diet Planner", icon="🥗"),
        st.Page("pages/workout.py", title="Workout Planner", icon="🏋️"),
        st.Page("pages/checkin.py", title="Daily Check-in", icon="✅"),
        st.Page("pages/progress.py", title="Progress & Goals", icon="📈"),
    ]
    nav = st.navigation(pages)
    user = db.get_user(st.session_state["user_id"])
    if user is None:
        st.session_state.clear()
        st.rerun()
    with st.sidebar:
        st.markdown(f"### 💪 FitPlanner\n**{user['full_name']}**")
        if user["is_demo"]:
            st.markdown("<span class='demo-badge'>DEMO ACCOUNT</span>", unsafe_allow_html=True)
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()
    nav.run()


if "user_id" in st.session_state:
    logged_in_app()
else:
    landing_page()
