"""Rule-based workout generator using data/exercise_database.csv."""
import random
from pathlib import Path
import pandas as pd

DATA = Path(__file__).parent / "data" / "exercise_database.csv"
WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
LEVELS = ["Beginner", "Intermediate", "Advanced"]
EQUIPMENT = ["None", "Dumbbells", "Gym"]

# Which weekdays are training days, and what each session targets
SPLITS = {
    2: [("Monday", "Full Body A", ["Chest", "Back", "Legs", "Core"]),
        ("Thursday", "Full Body B", ["Shoulders", "Arms", "Legs", "Cardio"])],
    3: [("Monday", "Full Body", ["Chest", "Back", "Legs"]),
        ("Wednesday", "Cardio + Core", ["Cardio", "Core"]),
        ("Friday", "Upper + Legs", ["Shoulders", "Arms", "Legs"])],
    4: [("Monday", "Chest + Triceps", ["Chest", "Arms"]),
        ("Tuesday", "Back + Biceps", ["Back", "Arms"]),
        ("Thursday", "Legs + Core", ["Legs", "Core"]),
        ("Friday", "Shoulders + Cardio", ["Shoulders", "Cardio"])],
    5: [("Monday", "Chest + Triceps", ["Chest", "Arms"]),
        ("Tuesday", "Back + Biceps", ["Back", "Arms"]),
        ("Wednesday", "Cardio + Core", ["Cardio", "Core"]),
        ("Thursday", "Legs", ["Legs"]),
        ("Saturday", "Shoulders + Full Body", ["Shoulders", "Full Body"])],
}


def load_exercises() -> pd.DataFrame:
    try:
        return pd.read_csv(DATA, keep_default_na=False)
    except FileNotFoundError:
        return pd.DataFrame()


def generate_plan(goal, level, days, duration_min, equipment, seed=None):
    """Return {day: {'focus': str, 'exercises': [dict]}} for all 7 days."""
    ex = load_exercises()
    if ex.empty:
        raise FileNotFoundError("exercise_database.csv is missing.")
    rank = {l: i for i, l in enumerate(LEVELS)}
    ex = ex[ex["equipment"].isin(["None"] + list(equipment))]
    ex = ex[ex["difficulty"].map(rank) <= rank[level]]
    rng = random.Random(seed)
    per_session = max(3, min(8, duration_min // 10))
    plan = {d: {"focus": "Rest", "exercises": []} for d in WEEK}
    for day, focus, groups in SPLITS[days]:
        picks = []
        for i in range(per_session):
            g = groups[i % len(groups)]
            pool = ex[(ex["muscle_group"] == g) &
                      (~ex["name"].isin([p["name"] for p in picks]))]
            if pool.empty:
                continue
            row = pool.iloc[rng.randrange(len(pool))].to_dict()
            picks.append(_apply_goal(row, goal, level))
        if goal == "Flexibility":
            stretch = ex[ex["workout_type"] == "Flexibility"].to_dict("records")
            picks = [_apply_goal(r, goal, level) for r in stretch[:per_session]] or picks
        plan[day] = {"focus": focus, "exercises": picks}
    return plan


def _apply_goal(row, goal, level):
    """Tune sets/reps by goal and level."""
    sets = int(row["sets"]) + (1 if level == "Advanced" else 0) - (1 if level == "Beginner" and int(row["sets"]) > 2 else 0)
    reps = str(row["reps"])
    if reps.isdigit() and row["workout_type"] == "Strength":
        r = int(reps)
        if goal == "Strength":
            r = 6
        elif goal == "Muscle gain":
            r = 10
        elif goal == "Weight loss":
            r = max(r, 15)
        reps = str(r)
    return {"name": row["name"], "muscle_group": row["muscle_group"], "sets": sets, "reps": reps,
            "rest_sec": int(row["rest_sec"]), "difficulty": row["difficulty"],
            "instructions": row["instructions"]}
