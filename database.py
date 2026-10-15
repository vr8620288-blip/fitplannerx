"""SQLite database layer: connection, schema, CRUD, demo data.

All SQL lives in this file so the rest of the app never touches SQL directly.
(To move to PostgreSQL later, only this file needs to change.)
"""
import hashlib
import hmac
import json
import os
import random
import re
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).parent / "database" / "fitplanner.db"
DEMO_EMAIL = "demo@fitplanner.com"
DEMO_PASSWORD = "Demo@123"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    height_cm REAL NOT NULL,
    weight_kg REAL NOT NULL,
    target_weight_kg REAL,
    activity_level TEXT NOT NULL,
    goal TEXT NOT NULL,
    food_preference TEXT DEFAULT 'Vegetarian',
    is_demo INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS progress_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    record_date TEXT NOT NULL,
    weight_kg REAL NOT NULL,
    bmi REAL NOT NULL,
    waist_cm REAL
);
CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    start_value REAL NOT NULL,
    target_value REAL NOT NULL,
    current_value REAL NOT NULL,
    deadline TEXT,
    completed INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS diet_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    diet_type TEXT, target_calories REAL, goal TEXT,
    plan_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS workout_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    goal TEXT, level TEXT, days_per_week INTEGER,
    plan_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS workout_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    log_date TEXT NOT NULL,
    exercise_name TEXT NOT NULL,
    UNIQUE(user_id, log_date, exercise_name)
);
CREATE TABLE IF NOT EXISTS daily_checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    checkin_date TEXT NOT NULL,
    workout_done INTEGER, water_l REAL, sleep_h REAL,
    energy INTEGER, diet_followed INTEGER, steps INTEGER,
    wellness_score INTEGER,
    UNIQUE(user_id, checkin_date)
);
CREATE TABLE IF NOT EXISTS user_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    achievement_key TEXT NOT NULL,
    earned_on TEXT NOT NULL,
    UNIQUE(user_id, achievement_key)
);
"""


# ---------- connection ----------
@contextmanager
def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create tables and seed the demo account (safe to call on every start)."""
    with get_conn() as c:
        c.executescript(SCHEMA)
    if get_user_by_email(DEMO_EMAIL) is None:
        _seed_demo()


# ---------- passwords ----------
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$")
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 120_000)
        return hmac.compare_digest(digest.hex(), digest_hex)
    except ValueError:
        return False


# ---------- users ----------
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_user(name, email, password, age, height, weight):
    """Return an error string or None."""
    if not name.strip():
        return "Full name is required."
    if not EMAIL_RE.match(email.strip()):
        return "Please enter a valid email address."
    if len(password) < 6:
        return "Password must be at least 6 characters."
    if not 10 <= age <= 100:
        return "Age must be between 10 and 100."
    if not 100 <= height <= 250:
        return "Height must be between 100 and 250 cm."
    if not 25 <= weight <= 300:
        return "Weight must be between 25 and 300 kg."
    return None


def create_user(name, email, password, age, gender, height, weight, activity, goal,
                food_pref="Vegetarian", is_demo=0):
    """Create a user. Returns (user_id, error)."""
    error = validate_user(name, email, password, age, height, weight)
    if error:
        return None, error
    try:
        with get_conn() as c:
            cur = c.execute(
                "INSERT INTO users (full_name,email,password_hash,age,gender,height_cm,weight_kg,"
                "target_weight_kg,activity_level,goal,food_preference,is_demo) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (name.strip(), email.strip().lower(), hash_password(password), age, gender,
                 height, weight, weight, activity, goal, food_pref, is_demo))
            return cur.lastrowid, None
    except sqlite3.IntegrityError:
        return None, "An account with this email already exists."
    except sqlite3.Error as e:
        return None, f"Database error: {e}"


def get_user_by_email(email):
    with get_conn() as c:
        row = c.execute("SELECT * FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
    return dict(row) if row else None


def get_user(user_id):
    with get_conn() as c:
        row = c.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    return dict(row) if row else None


def authenticate(email, password):
    user = get_user_by_email(email)
    if user and verify_password(password, user["password_hash"]):
        return user
    return None


def update_profile(user_id, **fields):
    allowed = {"full_name", "age", "gender", "height_cm", "weight_kg", "target_weight_kg",
               "activity_level", "goal", "food_preference"}
    fields = {k: v for k, v in fields.items() if k in allowed}
    if not fields:
        return
    sets = ", ".join(f"{k}=?" for k in fields)
    with get_conn() as c:
        c.execute(f"UPDATE users SET {sets} WHERE id=?", (*fields.values(), user_id))


# ---------- progress ----------
def add_progress(user_id, record_date, weight, bmi, waist=None):
    with get_conn() as c:
        c.execute("DELETE FROM progress_records WHERE user_id=? AND record_date=?",
                  (user_id, str(record_date)))
        c.execute("INSERT INTO progress_records (user_id,record_date,weight_kg,bmi,waist_cm) VALUES (?,?,?,?,?)",
                  (user_id, str(record_date), weight, bmi, waist))
    update_profile(user_id, weight_kg=weight)


def get_progress(user_id) -> pd.DataFrame:
    with get_conn() as c:
        df = pd.read_sql_query("SELECT * FROM progress_records WHERE user_id=? ORDER BY record_date",
                               c, params=(user_id,))
    if not df.empty:
        df["record_date"] = pd.to_datetime(df["record_date"])
    return df


def delete_progress(record_id, user_id):
    with get_conn() as c:
        c.execute("DELETE FROM progress_records WHERE id=? AND user_id=?", (record_id, user_id))


# ---------- goals ----------
def add_goal(user_id, title, start, target, deadline):
    with get_conn() as c:
        c.execute("INSERT INTO goals (user_id,title,start_value,target_value,current_value,deadline) VALUES (?,?,?,?,?,?)",
                  (user_id, title, start, target, start, str(deadline) if deadline else None))


def get_goals(user_id):
    with get_conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM goals WHERE user_id=? ORDER BY completed, id DESC", (user_id,))]


def update_goal(goal_id, user_id, **fields):
    allowed = {"title", "target_value", "current_value", "deadline", "completed"}
    fields = {k: v for k, v in fields.items() if k in allowed}
    if not fields:
        return
    sets = ", ".join(f"{k}=?" for k in fields)
    with get_conn() as c:
        c.execute(f"UPDATE goals SET {sets} WHERE id=? AND user_id=?", (*fields.values(), goal_id, user_id))


def delete_goal(goal_id, user_id):
    with get_conn() as c:
        c.execute("DELETE FROM goals WHERE id=? AND user_id=?", (goal_id, user_id))


# ---------- plans ----------
def save_diet_plan(user_id, diet_type, target_cal, goal, plan, created=None):
    with get_conn() as c:
        c.execute("INSERT INTO diet_plans (user_id,created_at,diet_type,target_calories,goal,plan_json) VALUES (?,?,?,?,?,?)",
                  (user_id, created or datetime.now().strftime("%Y-%m-%d %H:%M"), diet_type, target_cal, goal, json.dumps(plan)))


def get_diet_plans(user_id):
    with get_conn() as c:
        rows = c.execute("SELECT * FROM diet_plans WHERE user_id=? ORDER BY id DESC", (user_id,)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["plan"] = json.loads(d.pop("plan_json"))
        out.append(d)
    return out


def save_workout_plan(user_id, goal, level, days, plan, created=None):
    with get_conn() as c:
        c.execute("INSERT INTO workout_plans (user_id,created_at,goal,level,days_per_week,plan_json) VALUES (?,?,?,?,?,?)",
                  (user_id, created or datetime.now().strftime("%Y-%m-%d %H:%M"), goal, level, days, json.dumps(plan)))


def get_latest_workout_plan(user_id):
    with get_conn() as c:
        r = c.execute("SELECT * FROM workout_plans WHERE user_id=? ORDER BY id DESC LIMIT 1", (user_id,)).fetchone()
    if not r:
        return None
    d = dict(r)
    d["plan"] = json.loads(d.pop("plan_json"))
    return d


def get_latest_diet_plan(user_id):
    plans = get_diet_plans(user_id)
    return plans[0] if plans else None


# ---------- workout logs ----------
def set_exercise_done(user_id, log_date, exercise, done):
    with get_conn() as c:
        if done:
            c.execute("INSERT OR IGNORE INTO workout_logs (user_id,log_date,exercise_name) VALUES (?,?,?)",
                      (user_id, str(log_date), exercise))
        else:
            c.execute("DELETE FROM workout_logs WHERE user_id=? AND log_date=? AND exercise_name=?",
                      (user_id, str(log_date), exercise))


def get_done_exercises(user_id, log_date):
    with get_conn() as c:
        rows = c.execute("SELECT exercise_name FROM workout_logs WHERE user_id=? AND log_date=?",
                         (user_id, str(log_date))).fetchall()
    return {r["exercise_name"] for r in rows}


def get_workout_log_dates(user_id):
    with get_conn() as c:
        rows = c.execute("SELECT log_date, COUNT(*) n FROM workout_logs WHERE user_id=? GROUP BY log_date",
                         (user_id,)).fetchall()
    return {r["log_date"]: r["n"] for r in rows}


# ---------- check-ins ----------
def save_checkin(user_id, checkin_date, workout_done, water, sleep, energy, diet, steps, score):
    with get_conn() as c:
        c.execute("INSERT OR REPLACE INTO daily_checkins (user_id,checkin_date,workout_done,water_l,sleep_h,"
                  "energy,diet_followed,steps,wellness_score) VALUES (?,?,?,?,?,?,?,?,?)",
                  (user_id, str(checkin_date), int(workout_done), water, sleep, energy, int(diet), steps, score))


def get_checkins(user_id) -> pd.DataFrame:
    with get_conn() as c:
        df = pd.read_sql_query("SELECT * FROM daily_checkins WHERE user_id=? ORDER BY checkin_date",
                               c, params=(user_id,))
    if not df.empty:
        df["checkin_date"] = pd.to_datetime(df["checkin_date"])
    return df


# ---------- achievements ----------
def get_earned_achievements(user_id):
    with get_conn() as c:
        rows = c.execute("SELECT achievement_key, earned_on FROM user_achievements WHERE user_id=?", (user_id,)).fetchall()
    return {r["achievement_key"]: r["earned_on"] for r in rows}


def award_achievement(user_id, key):
    with get_conn() as c:
        c.execute("INSERT OR IGNORE INTO user_achievements (user_id,achievement_key,earned_on) VALUES (?,?,?)",
                  (user_id, key, str(date.today())))


# ---------- demo data ----------
def _seed_demo():
    """Create a clearly-labelled demo account with 30 days of realistic data."""
    from calculations import calculate_bmi, calculate_bmr, calculate_tdee, target_calories, wellness_score
    import diet_engine
    import workout_engine
    import gamification

    uid, err = create_user("Demo User (Demo Account)", DEMO_EMAIL, DEMO_PASSWORD, 21, "Male", 175, 82,
                           "Moderately active", "Weight loss", "Non-vegetarian", is_demo=1)
    if err:
        return
    update_profile(uid, target_weight_kg=74)
    rng = random.Random(7)
    today = date.today()
    for i in range(30, -1, -1):
        d = today - timedelta(days=i)
        w = round(82 - (30 - i) * 0.14 + rng.uniform(-0.3, 0.3), 1)
        add_progress(uid, d, w, calculate_bmi(w, 175), round(92 - (30 - i) * 0.12, 1))
        if rng.random() < 0.85:
            done = rng.random() < 0.6
            water, sleep = round(rng.uniform(2.0, 3.6), 1), round(rng.uniform(5.5, 8.5), 1)
            energy, diet, steps = rng.randint(2, 5), rng.random() < 0.7, rng.randint(3500, 11000)
            save_checkin(uid, d, done, water, sleep, energy, diet, steps,
                         wellness_score(done, water, sleep, energy, diet, steps))
            if done:
                for name in ("Bodyweight squats", "Push-ups", "Plank"):
                    set_exercise_done(uid, d, name, True)
    bmr = calculate_bmr(78.8, 175, 21, "Male")
    cal = target_calories(calculate_tdee(bmr, "Moderately active"), "Weight loss", bmr)
    save_diet_plan(uid, "Non-vegetarian", cal, "Weight loss",
                   diet_engine.generate_week_plan(cal, "Non-vegetarian", [], "Weight loss", 42))
    save_workout_plan(uid, "Weight loss", "Beginner", 4,
                      workout_engine.generate_plan("Weight loss", "Beginner", 4, 45, ["None", "Dumbbells"], 42))
    add_goal(uid, "Lose 8 kg", 82, 74, today + timedelta(days=90))
    update_goal(_last_goal_id(uid), uid, current_value=77.9)
    gamification.refresh_achievements(uid)


def _last_goal_id(uid):
    with get_conn() as c:
        return c.execute("SELECT MAX(id) m FROM goals WHERE user_id=?", (uid,)).fetchone()["m"]
