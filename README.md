# FitPlanner — Smart Diet & Workout Planner
*Your Personal AI-Powered Fitness & Wellness Planner*

> FitPlanner provides general fitness and nutrition estimates for educational and wellness purposes only. It is not a medical diagnosis or a substitute for professional medical or nutritional advice.

## Abstract
FitPlanner is a SaaS-style web application built with Python, Streamlit and SQLite. It calculates BMI, BMR and calorie targets, generates personalised 7-day Indian diet plans and weekly workout plans using rule-based algorithms, and tracks daily habits, progress, goals and achievements.

## Problem Statement
Most people use separate apps for BMI, diet, workouts and tracking, and generic plans ignore the user's body data, food preference and equipment.

## Objectives
- Compute BMI, BMR and calorie targets from user data
- Generate personalised diet and workout plans
- Track progress, habits and goals in one dashboard
- Motivate users with streaks, points and badges

## Scope
Single-user accounts, rule-based recommendations, offline operation (no API key), SQLite storage.

## Existing vs Proposed System
Existing: separate calculators, static PDF plans, manual tracking. Proposed: one integrated platform with personalised, saved, trackable plans.

## The 6 Core Features
1. **Health Assessment** — BMI with visual scale, BMR (Mifflin-St Jeor), TDEE, target calories, profile editing
2. **Smart Diet Planner** — 7-day plans from a 44-item Indian food database, diet type + allergy filters, save, download CSV
3. **Workout Planner** — weekly split by goal, level, duration, equipment; tick exercises done
4. **Daily Check-in** — water, sleep, steps, energy, diet; wellness score (0-100)
5. **Progress & Goals** — Plotly charts, weekly/monthly summaries, goal CRUD with progress bars
6. **Gamification** — streaks, fitness points, 7 achievement badges

## Functional Requirements
Register/login with hashed passwords; edit profile; calculate BMI/BMR; generate/save diet and workout plans; log check-ins and progress; manage goals; view analytics and badges.

## Non-Functional Requirements
Runs offline; responsive UI; input validation and friendly errors; modular code; deployable on Streamlit Community Cloud.

## Technology Stack
Python 3, Streamlit, SQLite, pandas, numpy, Plotly, custom HTML/CSS/JavaScript (animated counter, BMI scale).

## System Architecture
UI (app.py + pages/) → logic (calculations, diet_engine, workout_engine, gamification) → data (database.py → SQLite, CSV files).

## Database Design (ER description)
- `users` 1—N `progress_records`, `goals`, `diet_plans`, `workout_plans`, `workout_logs`, `daily_checkins`, `user_achievements`
- All child tables have `user_id` foreign key with ON DELETE CASCADE
- Unique constraints: `users.email`, one check-in per user per day, one log per exercise per day

## Algorithms / Formulas
- **BMI** = weight(kg) / height(m)²  — <18.5 Underweight, <25 Normal, <30 Overweight, else Obese
- **BMR (Mifflin-St Jeor)** = 10W + 6.25H − 5A + 5 (male) or − 161 (female)
- **TDEE** = BMR × activity multiplier (1.2 / 1.375 / 1.55 / 1.725)
- **Target calories** = TDEE − 500 (weight loss), + 400 (weight gain), + 300 (muscle gain); minimum 1200
- **Diet generation**: filter foods by diet type/allergens → split calories by meal (25/10/30/10/25 %) → pick foods per meal → scale portions to meal calories
- **Wellness score** = workout 25 + water 15 + sleep 20 + energy 10 + diet 15 + steps 15
- **Streak** = consecutive days with a check-in or logged workout

## Modules
`app.py` landing/login/navigation · `database.py` all SQL · `calculations.py` formulas · `diet_engine.py` · `workout_engine.py` · `gamification.py` · `utils.py` UI helpers · `pages/` six pages

## Limitations
Rule-based (not machine learning); estimates only; Streamlit Cloud storage is not permanent.

## Future Scope
AI recommendation module, admin dashboard, wearable integration, PostgreSQL, exercise videos.

## Conclusion
FitPlanner demonstrates authentication, database design, CRUD, algorithms, visualisation and modular architecture in a complete SaaS-style product.

## Demo Credentials (DEMO ACCOUNT)
Email: `demo@fitplanner.com`  Password: `Demo@123`

## Installation (local, Windows)
1. Download/clone and unzip the project
2. `cd FitPlanner`
3. `python -m venv venv`
4. `venv\Scripts\activate`
5. `pip install -r requirements.txt`
6. `streamlit run app.py`

## Deployment on Streamlit Community Cloud
1. Create a GitHub repository and upload all files of the FitPlanner folder (app.py must be at the repo root)
2. Go to https://share.streamlit.io and sign in with GitHub
3. Click **Create app** → choose your repository and branch
4. Set **Main file path** to `app.py`
5. Click **Deploy**
Note: the SQLite file resets when the cloud app restarts; the demo account is re-created automatically.
