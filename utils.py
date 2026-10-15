"""Shared UI helpers: CSS, login guard, small HTML components."""
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

ASSETS = Path(__file__).parent / "assets"


def load_css():
    css = (ASSETS / "style.css")
    if css.exists():
        st.markdown(f"<style>{css.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def require_login():
    """Stop the page if nobody is logged in; return the fresh user record."""
    import database as db
    if "user_id" not in st.session_state:
        st.warning("Please log in first.")
        st.stop()
    user = db.get_user(st.session_state["user_id"])
    if user is None:
        st.session_state.clear()
        st.rerun()
    return user


def page_header(title, subtitle=""):
    st.markdown(f"<div class='page-title'>{title}</div><div class='page-sub'>{subtitle}</div>",
                unsafe_allow_html=True)


def metric_card(label, value, hint=""):
    st.markdown(f"<div class='fp-card'><div class='fp-label'>{label}</div>"
                f"<div class='fp-value'>{value}</div><div class='fp-hint'>{hint}</div></div>",
                unsafe_allow_html=True)


def disclaimer():
    from calculations import DISCLAIMER
    st.markdown(f"<div class='fp-disclaimer'>⚠️ {DISCLAIMER}</div>", unsafe_allow_html=True)


def animated_counter(value, label, suffix="", height=120):
    """JavaScript: counts up from 0 to `value` when the card appears."""
    components.html(f"""
    <div style="font-family:Inter,sans-serif;background:linear-gradient(135deg,#10b981,#059669);
         color:white;border-radius:16px;padding:18px;text-align:center;">
      <div style="font-size:13px;opacity:.9">{label}</div>
      <div style="font-size:38px;font-weight:700"><span id="n">0</span>{suffix}</div>
    </div>
    <script>
      const target = {value}; let cur = 0; const el = document.getElementById('n');
      const step = Math.max(target/40, 0.1);
      const t = setInterval(() => {{ cur += step;
        if (cur >= target) {{ cur = target; clearInterval(t); }}
        el.textContent = Number.isInteger(target) ? Math.round(cur) : cur.toFixed(1); }}, 25);
    </script>""", height=height)


def bmi_scale(bmi):
    """Visual BMI scale (HTML/CSS) with a marker at the user's BMI."""
    pos = max(0, min((bmi - 12) / (40 - 12) * 100, 100))
    st.markdown(f"""
    <div class='bmi-scale'>
      <div class='bmi-bar'><span style='width:23.2%;background:#60a5fa'></span>
        <span style='width:23.2%;background:#34d399'></span>
        <span style='width:17.9%;background:#fbbf24'></span>
        <span style='width:35.7%;background:#f87171'></span>
        <div class='bmi-marker' style='left:{pos}%'>▼<br><b>{bmi}</b></div></div>
      <div class='bmi-labels'><span>Underweight &lt;18.5</span><span>Normal 18.5-24.9</span>
        <span>Overweight 25-29.9</span><span>Obese 30+</span></div>
    </div>""", unsafe_allow_html=True)
