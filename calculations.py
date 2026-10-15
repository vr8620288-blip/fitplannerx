"""Health formulas: BMI, BMR (Mifflin-St Jeor), TDEE and target calories."""

ACTIVITY_MULTIPLIERS = {
    "Sedentary": 1.2,
    "Lightly active": 1.375,
    "Moderately active": 1.55,
    "Very active": 1.725,
}
GOALS = ["Weight loss", "Weight gain", "Muscle gain", "Maintenance", "General fitness"]

DISCLAIMER = (
    "FitPlanner provides general fitness and nutrition estimates for educational and "
    "wellness purposes only. It is not a medical diagnosis or a substitute for "
    "professional medical or nutritional advice."
)


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """BMI = weight (kg) / height (m)^2"""
    if weight_kg <= 0 or height_cm <= 0:
        raise ValueError("Height and weight must be positive.")
    return round(weight_kg / ((height_cm / 100) ** 2), 1)


def bmi_category(bmi: float):
    """Return (category, interpretation, recommended action)."""
    if bmi < 18.5:
        return "Underweight", "Your weight is below the typical healthy range.", \
            "Consider a calorie surplus with nutrient-dense foods and strength training."
    if bmi < 25:
        return "Normal", "Your weight is within the typical healthy range.", \
            "Maintain your habits: balanced diet and regular exercise."
    if bmi < 30:
        return "Overweight", "Your weight is above the typical healthy range.", \
            "Consider a small calorie deficit with cardio and strength training."
    return "Obese", "Your weight is well above the typical healthy range.", \
        "Consider a gradual calorie deficit and consult a healthcare professional."


def healthy_weight_range(height_cm: float):
    """Weight range for BMI 18.5 - 24.9."""
    m2 = (height_cm / 100) ** 2
    return round(18.5 * m2, 1), round(24.9 * m2, 1)


def calculate_bmr(weight_kg, height_cm, age, gender) -> float:
    """Mifflin-St Jeor: 10W + 6.25H - 5A + 5 (male) / - 161 (female)."""
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return round(base + (5 if gender == "Male" else -161), 0)


def calculate_tdee(bmr, activity_level) -> float:
    return round(bmr * ACTIVITY_MULTIPLIERS.get(activity_level, 1.2), 0)


def target_calories(tdee, goal, bmr) -> float:
    """Apply a goal adjustment; never go below a safe floor (BMR or 1200)."""
    adjust = {"Weight loss": -500, "Weight gain": 400, "Muscle gain": 300}.get(goal, 0)
    return max(round(tdee + adjust, 0), 1200)


def weekly_change_kg(goal) -> float:
    """~7700 kcal per kg; 500 kcal/day -> ~0.45 kg per week."""
    return {"Weight loss": -0.45, "Weight gain": 0.35, "Muscle gain": 0.25}.get(goal, 0.0)


def wellness_score(workout_done, water_l, sleep_h, energy, diet_followed, steps) -> int:
    """Daily wellness score 0-100 from check-in answers."""
    score = 0
    score += 25 if workout_done else 0
    score += 15 * min(water_l / 3.0, 1)
    score += 20 * (1 - min(abs(sleep_h - 8) / 4, 1))
    score += 10 * (energy / 5)
    score += 15 if diet_followed else 0
    score += 15 * min(steps / 8000, 1)
    return int(round(score))
