"""Streaks, points and achievement badges."""
from datetime import date, timedelta
import database as db

ACHIEVEMENTS = {
    "first_workout": ("🏁", "First Workout", "Complete your first exercise"),
    "streak_7": ("🔥", "7-Day Streak", "Be active 7 days in a row"),
    "workouts_10": ("💪", "10 Workouts Completed", "Log 10 workout days"),
    "hydration": ("💧", "Healthy Hydration", "Drink 3 L of water in a day"),
    "goal_started": ("🎯", "Goal Started", "Create your first goal"),
    "goal_completed": ("🏆", "Goal Completed", "Complete a goal"),
    "consistency_30": ("🌟", "30-Day Consistency", "Check in on 30 different days"),
}


def active_days(user_id):
    """Days with a check-in or a logged workout."""
    days = set(db.get_workout_log_dates(user_id))
    ck = db.get_checkins(user_id)
    if not ck.empty:
        days |= {d.strftime("%Y-%m-%d") for d in ck["checkin_date"]}
    return days


def current_streak(user_id) -> int:
    days = active_days(user_id)
    d = date.today()
    if str(d) not in days:          # allow the streak to survive until today ends
        d -= timedelta(days=1)
    streak = 0
    while str(d) in days:
        streak += 1
        d -= timedelta(days=1)
    return streak


def best_streak(user_id) -> int:
    days = sorted(active_days(user_id))
    best = run = 0
    prev = None
    for s in days:
        cur = date.fromisoformat(s)
        run = run + 1 if prev and (cur - prev).days == 1 else 1
        best = max(best, run)
        prev = cur
    return best


def refresh_achievements(user_id):
    """Check every rule, award new badges, return keys earned just now."""
    earned = db.get_earned_achievements(user_id)
    logs = db.get_workout_log_dates(user_id)
    ck = db.get_checkins(user_id)
    goals = db.get_goals(user_id)
    checks = {
        "first_workout": len(logs) >= 1,
        "streak_7": best_streak(user_id) >= 7,
        "workouts_10": len(logs) >= 10,
        "hydration": (not ck.empty) and bool((ck["water_l"] >= 3).any()),
        "goal_started": len(goals) >= 1,
        "goal_completed": any(g["completed"] for g in goals),
        "consistency_30": (not ck.empty) and len(ck) >= 30,
    }
    new = [k for k, ok in checks.items() if ok and k not in earned]
    for k in new:
        db.award_achievement(user_id, k)
    return new


def fitness_points(user_id) -> int:
    """10 pts per workout day, 5 per check-in, 50 per badge."""
    ck = db.get_checkins(user_id)
    return (len(db.get_workout_log_dates(user_id)) * 10 + len(ck) * 5
            + len(db.get_earned_achievements(user_id)) * 50)
