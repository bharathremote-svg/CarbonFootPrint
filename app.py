"""
Carbon Footprint Calculator using AI - AI-Assisted Carbon Footprint Calculator
====================================================
Run with:  streamlit run app.py

A pure-Python (Streamlit) recreation of the Carbon Footprint Calculator using AI
calculator: a 5-step wizard, a results dashboard (eco score, emissions
breakdown, peer comparison), a personalized action plan with a
reduction-goal planner, plus a history log and about page.
"""

import datetime as dt
import os
import re
import json
import streamlit as st
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from joblib import load

try:
    import requests
except ImportError:
    requests = None

from calculations import (
    UserInputs, emissions_breakdown, total_footprint, footprint_badge,
    eco_score, eco_score_label, comparison_data, generate_recommendations,
    goal_based_plan, CATEGORY_TIPS,
)
from charts import eco_score_donut, emissions_breakdown_donut, comparison_bar_chart, CATEGORY_COLORS
from styles import get_css
from storage import init_db, save_history_entry, load_history

st.set_page_config(page_title="Carbon Footprint Calculator using AI", page_icon="🌿", layout="wide")

STEPS = ["Home Energy", "Transport", "Flights", "Diet", "Lifestyle"]
STEP_ICONS = {"Home Energy": "⚡", "Transport": "🚗", "Flights": "✈️", "Diet": "🍴", "Lifestyle": "🛍️"}


# ---------------------------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------------------------
def init_state():
    defaults = {
        "page": "Home",
        "step_idx": 0,
        "dark_mode": False,
        "inputs": UserInputs(),
        "history": [],
        "goal_pct": 20,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()
st.markdown(get_css(st.session_state.dark_mode), unsafe_allow_html=True)

def _get_google_drive_file_id(share_url: str) -> str | None:
    match = re.search(r"/d/([A-Za-z0-9_-]+)", share_url)
    if match:
        return match.group(1)
    match = re.search(r"[?&]id=([A-Za-z0-9_-]+)", share_url)
    return match.group(1) if match else None


def _get_confirm_token(response):
    for key, value in getattr(response, 'cookies', {}).items():
        if key.startswith('download_warning'):
            return value
    if hasattr(response, 'text'):
        m = re.search(r'confirm=([0-9A-Za-z_]+)', response.text)
        if m:
            return m.group(1)
    return None


def _download_google_drive_file(file_id: str, destination: str) -> bool:
    url = 'https://docs.google.com/uc?export=download'
    if requests is not None:
        session = requests.Session()
        response = session.get(url, params={'id': file_id}, stream=True, timeout=30)
        token = _get_confirm_token(response)
        if token:
            response = session.get(url, params={'id': file_id, 'confirm': token}, stream=True, timeout=30)
        if response.status_code != 200:
            return False
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(32768):
                if chunk:
                    f.write(chunk)
        return True

    try:
        download_url = f"{url}&id={file_id}"
        request = Request(download_url, headers={'User-Agent': 'Mozilla/5.0'})
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        with urlopen(request, timeout=30) as response, open(destination, 'wb') as out_file:
            out_file.write(response.read())
        return True
    except (HTTPError, URLError):
        return False


def _download_model_if_missing(remote_url: str, local_path: str) -> None:
    if os.path.exists(local_path):
        return
    file_id = _get_google_drive_file_id(remote_url)
    if not file_id:
        return
    _download_google_drive_file(file_id, local_path)


# Initialize DB
init_db()

# Load ML model if present
MODEL_ARTIFACT = None
MODEL_PATH = os.path.join("models", "model.pkl")
REMOTE_MODEL_URL = "https://drive.google.com/file/d/1LCL870o4q2vqSybgWBAMMQOvGf7G4GRJ/view?usp=sharing"
_download_model_if_missing(REMOTE_MODEL_URL, MODEL_PATH)

if os.path.exists(MODEL_PATH):
    try:
        MODEL_ARTIFACT = load(MODEL_PATH)
    except Exception:
        MODEL_ARTIFACT = None
    
else:
    MODEL_ARTIFACT = None


def model_predict(u):
    """Return model prediction (float) or None if model missing."""
    if MODEL_ARTIFACT is None:
        return None
    feat_names = MODEL_ARTIFACT.get("feature_names")
    pipe = MODEL_ARTIFACT.get("pipeline")
    # Build feature vector matching the training extract_features() in train.py
    vehicle_factor = 0.0
    try:
        from calculations import VEHICLE_KG_PER_KM, DIET_BASE_T, SHOPPING_BASE_T, FOOD_WASTE_MULTIPLIER
        vehicle_factor = VEHICLE_KG_PER_KM.get(st.session_state.inputs.vehicle_type, 0.0)
        diet_value = DIET_BASE_T.get(st.session_state.inputs.diet_type, sum(DIET_BASE_T.values())/len(DIET_BASE_T))
        food_mult = FOOD_WASTE_MULTIPLIER.get(st.session_state.inputs.food_waste, 1.0)
        shopping_value = SHOPPING_BASE_T.get(st.session_state.inputs.shopping_habits, SHOPPING_BASE_T["Medium"])
    except Exception:
        diet_value = 2.5
        food_mult = 1.0
        shopping_value = 0.7

    x = [
        st.session_state.inputs.electricity_kwh,
        st.session_state.inputs.renewable_pct,
        st.session_state.inputs.gas_m3,
        st.session_state.inputs.car_km,
        st.session_state.inputs.public_transport_km,
        st.session_state.inputs.short_haul_flights,
        st.session_state.inputs.long_haul_flights,
        vehicle_factor,
        diet_value,
        food_mult,
        shopping_value,
        st.session_state.inputs.clothing_items,
        st.session_state.inputs.streaming_hours,
    ]
    try:
        pred = pipe.predict([x])[0]
        return float(pred)
    except Exception:
        return None


def ml_recommendations(u, top_n=3):
    """Generate simple ML-driven suggestions using feature importances from the model."""
    if MODEL_ARTIFACT is None:
        return []
    pipe = MODEL_ARTIFACT.get("pipeline")
    model = pipe.named_steps.get("model") if hasattr(pipe, "named_steps") else None
    if model is None or not hasattr(model, "feature_importances_"):
        return []
    importances = model.feature_importances_
    names = MODEL_ARTIFACT.get("feature_names", [])
    pairs = sorted(zip(names, importances), key=lambda kv: kv[1], reverse=True)
    suggestions = []
    mapping = {
        "car_km": ("Transport", "Reduce car kilometres — try public transport or carpooling."),
        "electricity_kwh": ("Home Energy", "Lower electricity use or switch to renewables."),
        "long_haul_flights": ("Transport", "Avoid one long-haul flight per year."),
        "short_haul_flights": ("Transport", "Reduce short-haul flights; consider train travel."),
        "diet_value": ("Diet", "Shift toward more plant-based meals."),
        "shopping_value": ("Lifestyle", "Buy fewer new items; choose second-hand."),
    }
    for name, score in pairs[:top_n]:
        cat, text = mapping.get(name, ("Lifestyle", f"Reduce {name} where possible."))
        suggestions.append((cat, text))
    return suggestions


def go(page):
    st.session_state.page = page


# ---------------------------------------------------------------------------
# NAVBAR
# ---------------------------------------------------------------------------
def navbar():
    cols = st.columns([2, 1, 1, 1, 1, 1, 0.6])
    with cols[0]:
        st.markdown(
            '<div class="ecotrace-logo"><span class="ecotrace-logo-icon">🌿</span> Carbon Footprint Calculator using AI</div>',
            unsafe_allow_html=True,
        )
    nav_items = ["Home", "Calculator", "Results", "History", "About"]
    for i, item in enumerate(nav_items):
        with cols[i + 1]:
            if st.button(item, key=f"nav_{item}", width="stretch"):
                go(item)
    with cols[-1]:
        icon = "☀️" if st.session_state.dark_mode else "🌙"
        if st.button(icon, key="theme_toggle"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    st.markdown("<hr/>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# HOME PAGE
# ---------------------------------------------------------------------------
def page_home():
    st.markdown("<h1 class='ecotrace-serif'>Understand your carbon footprint.</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='eco-muted' style='font-size:1.1rem; max-width:600px;'>"
        "Carbon Footprint Calculator using AI walks you through your home energy, transport, flights, diet, and "
        "lifestyle habits, then estimates your annual CO2e emissions - with a "
        "personalized plan to bring them down.</p>",
        unsafe_allow_html=True,
    )
    st.write("")
    if st.button("Start Calculator →", type="primary"):
        go("Calculator")

    st.write("")
    c1, c2, c3 = st.columns(3)
    for col, title, desc in [
        (c1, "🔎 Estimate", "Answer a short 5-step questionnaire about your lifestyle."),
        (c2, "📊 Understand", "See an eco score, category breakdown, and peer comparison."),
        (c3, "🎯 Improve", "Get a personalized action plan and set a reduction goal."),
    ]:
        with col:
            st.markdown(
                f"<div class='eco-card'><b>{title}</b><br/><span class='eco-muted'>{desc}</span></div>",
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# CALCULATOR PAGE
# ---------------------------------------------------------------------------
def step_home_energy(u: UserInputs):
    st.markdown("### Home Energy")
    st.markdown("<span class='eco-muted'>Let's start with your home. Energy usage is often a major "
                "contributor to personal emissions.</span>", unsafe_allow_html=True)
    st.write("")
    u.electricity_kwh = st.slider("Monthly Electricity (kWh)", 0, 1000, int(u.electricity_kwh), step=10)
    u.renewable_pct = st.slider("Renewable Energy %", 0, 100, int(u.renewable_pct),
                                 help="What percentage of your electricity comes from renewable sources?")
    u.gas_m3 = st.slider("Natural Gas (m³/month)", 0, 200, int(u.gas_m3), step=5)


def step_transport(u: UserInputs):
    st.markdown("### Transportation")
    st.markdown("<span class='eco-muted'>How do you get around day-to-day?</span>", unsafe_allow_html=True)
    st.write("")
    u.vehicle_type = st.radio("Primary Vehicle Type", ["None", "Electric", "Hybrid", "Petrol", "Diesel"],
                               index=["None", "Electric", "Hybrid", "Petrol", "Diesel"].index(u.vehicle_type),
                               horizontal=True)
    u.car_km = st.slider("Car Travel (km/month)", 0, 3000, int(u.car_km), step=50)
    u.public_transport_km = st.slider("Public Transport (km/month)", 0, 1000, int(u.public_transport_km), step=10)


def step_flights(u: UserInputs):
    st.markdown("### Flights")
    st.markdown("<span class='eco-muted'>Air travel has an outsized impact on personal emissions.</span>",
                unsafe_allow_html=True)
    st.write("")
    u.short_haul_flights = st.slider("Short-haul flights per year", 0, 20, int(u.short_haul_flights),
                                      help="Under 3 hours (e.g. domestic/regional)")
    u.long_haul_flights = st.slider("Long-haul flights per year", 0, 20, int(u.long_haul_flights),
                                     help="Over 3 hours (e.g. transcontinental)")


def step_diet(u: UserInputs):
    st.markdown("### Diet")
    st.markdown("<span class='eco-muted'>Food production systems are a massive piece of the puzzle.</span>",
                unsafe_allow_html=True)
    st.write("")
    diet_opts = ["Vegan", "Vegetarian", "Pescatarian", "Mixed", "High Meat"]
    u.diet_type = st.radio("Diet Type", diet_opts, index=diet_opts.index(u.diet_type), horizontal=True)
    waste_opts = ["Low", "Medium", "High"]
    u.food_waste = st.radio("Food Waste Level - how much purchased food ends up in the bin?",
                             waste_opts, index=waste_opts.index(u.food_waste), horizontal=True)


def step_lifestyle(u: UserInputs):
    st.markdown("### Lifestyle")
    st.markdown("<span class='eco-muted'>Everything we consume requires energy to produce.</span>",
                unsafe_allow_html=True)
    st.write("")
    shop_opts = ["Low", "Medium", "High", "Very High"]
    u.shopping_habits = st.radio("Shopping Habits", shop_opts, index=shop_opts.index(u.shopping_habits),
                                  horizontal=True)
    u.clothing_items = st.slider("New Clothing Items (per year)", 0, 60, int(u.clothing_items))
    u.streaming_hours = st.slider("Video Streaming (hours/day)", 0, 12, int(u.streaming_hours))


STEP_RENDERERS = {
    "Home Energy": step_home_energy,
    "Transport": step_transport,
    "Flights": step_flights,
    "Diet": step_diet,
    "Lifestyle": step_lifestyle,
}


def page_calculator():
    u = st.session_state.inputs
    left, right = st.columns([1, 3])

    with left:
        st.markdown("<span class='eco-chip'>🌿 Carbon Footprint Calculator using AI</span>", unsafe_allow_html=True)
        st.markdown("<p class='eco-muted'>A 5-step journey to understand your impact.</p>",
                    unsafe_allow_html=True)
        st.write("")
        for i, step in enumerate(STEPS):
            active = " active" if i == st.session_state.step_idx else ""
            label = f"{STEP_ICONS[step]}  {step}"
            if st.button(label, key=f"step_{step}", width="stretch"):
                st.session_state.step_idx = i
                st.rerun()

        live_total = total_footprint(u)
        st.markdown(
            f"<div class='eco-live-estimate'><span class='eco-muted' style='font-size:0.75rem; "
            f"letter-spacing:0.05em;'>LIVE ESTIMATE</span><br/>"
            f"<span class='value'>{live_total:.1f}</span> "
            f"<span class='eco-muted'>tonnes CO₂e/yr</span></div>",
            unsafe_allow_html=True,
        )

    with right:
        step_name = STEPS[st.session_state.step_idx]
        STEP_RENDERERS[step_name](u)
        st.write("")
        st.write("")
        b1, b2 = st.columns([1, 1])
        with b1:
            if st.session_state.step_idx > 0:
                if st.button("← Back"):
                    st.session_state.step_idx -= 1
                    st.rerun()
        with b2:
            is_last = st.session_state.step_idx == len(STEPS) - 1
            btn_label = "Complete Assessment →" if is_last else "Continue →"
            if st.button(btn_label, type="primary"):
                if is_last:
                    entry = {
                        "timestamp": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "total": total_footprint(u),
                        "breakdown": emissions_breakdown(u),
                    }
                    st.session_state.history.append(entry)
                    # Persist to DB
                    try:
                        save_history_entry(entry["timestamp"], entry["total"], entry["breakdown"])
                    except Exception:
                        pass
                    go("Results")
                else:
                    st.session_state.step_idx += 1
                st.rerun()


# ---------------------------------------------------------------------------
# RESULTS PAGE
# ---------------------------------------------------------------------------
def page_results():
    u = st.session_state.inputs
    total = total_footprint(u)
    breakdown = emissions_breakdown(u)
    badge = footprint_badge(total)
    score = eco_score(total)
    label = eco_score_label(score)

    top_l, top_r = st.columns([3, 1])
    with top_l:
        with st.expander("Your Annual Footprint", expanded=False):
            st.markdown(
                f"<h1 class='ecotrace-serif'>You emit <span class='eco-hero-number'>{total:.1f} tonnes</span> "
                f"of CO₂e per year.</h1>",
                unsafe_allow_html=True,
            )
            st.markdown(f"<span class='eco-badge-warn'>{badge}</span>", unsafe_allow_html=True)
    with top_r:
        st.write("")
        if st.button("View History"):
            go("History")

    # Show ML model prediction and ML-driven suggestions (if model available)
    model_pred = None
    try:
        model_pred = model_predict(u)
    except Exception:
        model_pred = None

    if model_pred is not None:
        m_l, m_r = st.columns([3, 1])
        with m_l:
            st.markdown("<div class='eco-card'>", unsafe_allow_html=True)
            st.markdown("**ML Model Prediction**")
            st.markdown(
                f"<p style='font-size:1.2rem; margin:0;'>Model predicts <b>{model_pred:.1f} tonnes CO₂e/yr</b></p>",
                unsafe_allow_html=True,
            )
            diff = model_pred - total
            st.markdown(f"<p class='eco-muted'>Difference vs calculator: {diff:+.1f}t</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # ML-driven suggestions
        ml_recs = ml_recommendations(u, top_n=3)
        if ml_recs:
            st.markdown("<div class='eco-card'>", unsafe_allow_html=True)
            st.markdown("**ML-driven Suggestions**")
            for cat, text in ml_recs:
                st.markdown(f"<div style='padding:6px 0;'><b>{cat}</b> — {text}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='eco-card'>", unsafe_allow_html=True)
        st.markdown("**Eco Score**")
        fig = eco_score_donut(score, st.session_state.dark_mode)
        st.pyplot(fig, width="content")
        st.markdown(f"<p style='text-align:center; font-weight:600;'>{label}</p>", unsafe_allow_html=True)
        st.markdown("<p class='eco-muted' style='text-align:center;'>A holistic measure of your "
                    "sustainability habits, scored 0-100.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='eco-card'>", unsafe_allow_html=True)
        st.markdown("**Emissions Breakdown**")
        fig2 = emissions_breakdown_donut(breakdown, st.session_state.dark_mode)
        colA, colB = st.columns([1, 1])
        with colA:
            st.pyplot(fig2, width="content")
        with colB:
            st.write("")
            for cat, val in breakdown.items():
                st.markdown(
                    f"<span style='color:{CATEGORY_COLORS[cat]}'>●</span> {cat} "
                    f"<span class='eco-muted' style='float:right'>{val}t</span>",
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("How do you compare?", expanded=False):
      
            st.markdown("<div class='eco-card'>", unsafe_allow_html=True)
            st.markdown("**How do you compare?**")
            fig3 = comparison_bar_chart(comparison_data(total), st.session_state.dark_mode)
            st.pyplot(fig3, width="stretch")
            st.markdown("</div>", unsafe_allow_html=True)

    # ---- Personalized Action Plan ----
    st.write("")
    with st.expander("🌿 Personalized Action Plan", expanded=False):
        recs = generate_recommendations(u, top_n=3)
        if recs:
            cols = st.columns(len(recs))
            for col, r in zip(cols, recs):
                with col:
                    st.markdown(
                        f"<div class='eco-card'>"
                        f"<span class='eco-chip'>{r.category}</span>"
                        f"<span class='eco-savings-pill' style='float:right;'>-{r.savings_t}t</span>"
                        f"<h4 style='margin-top:0.6rem;'>{r.title}</h4>"
                        f"<span class='eco-muted'>{r.description}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
        else:
            st.info("Your habits already look great — no major opportunities detected!")

    # ---- Reduction Goal ----
    st.write("")
    goal_l, goal_r = st.columns([1, 1.4])
    with goal_l:
        st.markdown("<div class='eco-card'>", unsafe_allow_html=True)
        st.markdown("**🎯 Reduction Goal**")
        st.markdown("<span class='eco-muted'>Set a target to reduce your emissions. "
                    "We'll show you exactly how to get there.</span>", unsafe_allow_html=True)
        st.session_state.goal_pct = st.slider("Target Reduction", 0, 50, st.session_state.goal_pct,
                                               format="%d%%")
        plan = goal_based_plan(u, st.session_state.goal_pct)
        st.markdown(
            f"<div class='eco-live-estimate'><span class='eco-muted' style='font-size:0.75rem;'>"
            f"NEW TARGET FOOTPRINT</span><br/><span class='value'>{plan['target_footprint']}</span> "
            f"<span class='eco-muted'>tonnes</span></div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # Show detailed step-by-step plan in the next row (full width)
    st.write("")
    st.markdown("<div class='eco-card'>", unsafe_allow_html=True)
    st.markdown(f"**How to achieve your {st.session_state.goal_pct}% reduction:**")
    for category, tonnes in plan["steps"]:
        if tonnes <= 0:
            continue
        st.markdown(
            f"<div style='display:flex; gap:0.8rem; align-items:center; padding:0.5rem 0; "
            f"border-bottom:1px solid rgba(128,128,128,0.15);'>"
            f"<span class='eco-savings-pill'>-{tonnes}t</span>"
            f"<span><b style='text-transform:uppercase; font-size:0.75rem;'>{category}</b><br/>"
            f"<span class='eco-muted'>{CATEGORY_TIPS.get(category, '')}</span></span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    st.markdown(
        "<div class='eco-live-estimate' style='margin-top:1rem;'>⚠️ Meeting this goal would place "
        "you closer to the global climate targets necessary to limit warming to 1.5°C.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# HISTORY PAGE
# ---------------------------------------------------------------------------
def page_history():
    st.markdown("## History")
    # Load persisted history from DB (most recent first)
    history = load_history()
    if not history:
        st.info("No assessments completed yet. Run the calculator to see your results here.")
        return

    # Show monthly tracking summary
    import pandas as pd
    df = pd.DataFrame(history)
    df["month"] = pd.to_datetime(df["timestamp"]).dt.to_period("M").astype(str)
    monthly = df.groupby("month")["total"].mean().reset_index()
    st.markdown("### Monthly average footprint")
    st.line_chart(monthly.set_index("month")["total"])

    st.markdown("### Entries")
    for entry in history:
        st.markdown(
            f"<div class='eco-card'><b>{entry['timestamp']}</b> — "
            f"{entry['total']:.1f} tonnes CO₂e/yr "
            f"<span class='eco-badge-warn'>{footprint_badge(entry['total'])}</span></div>",
            unsafe_allow_html=True,
        )
    if st.button("Clear History"):
        # Clear DB
        import sqlite3
        conn = sqlite3.connect("data.db")
        conn.execute("DELETE FROM history")
        conn.commit()
        conn.close()
        st.experimental_rerun()


# ---------------------------------------------------------------------------
# ABOUT PAGE
# ---------------------------------------------------------------------------
def page_about():
    st.markdown("## About Carbon Footprint Calculator using AI")
    st.markdown(
        "Carbon Footprint Calculator using AI is a learning-focused web app built with Python and Streamlit. "
        "It helps users understand how everyday choices affect their carbon footprint by estimating annual "
        "CO₂e emissions based on home energy, transportation, flights, diet, and lifestyle habits."
    )

    st.markdown("---")

    st.markdown("### What this app does")
    st.markdown(
        "- Estimates annual personal emissions using public average emission factors.\n"
        "- Breaks results down into Home Energy, Transport, Flights, Diet, and Lifestyle categories.\n"
        "- Provides an eco score, peer comparison, and personalized reduction suggestions.\n"
        "- Lets you track past entries and set a realistic reduction goal."
    )

    st.markdown("### Why it exists")
    st.markdown(
        "The goal is to make climate impact easier to understand for everyday users. "
        "By translating energy, travel, diet, and shopping habits into simple emission values, "
        "the app encourages more informed decisions and gradual improvements."
    )

    st.markdown("### Important note")
    st.markdown(
        "**This calculator provides an educational estimate, not a certified carbon audit.** "
        "The results are based on simplified averages and general assumptions, so your actual emissions may vary. "
        "Use the output as a guide for awareness and improvement, rather than a precise measurement."
    )

    st.markdown("### Built with")
    st.markdown(
        "- Python and Streamlit for the interactive web interface.\n"
        "- Machine learning support for optional model-driven suggestions if a trained model is available.\n"
        "- Local storage for history tracking and repeat comparisons."
    )

    st.markdown("### Team")
    st.markdown(
        "This app was developed by a team of students and climate-focused creators: "
        "S. Kaniska, J. Hansika, N. Haniya, V. Nivedha, and Pragati."
    )

    st.markdown("### Privacy")
    st.markdown(
        "No personal identity data is collected by the calculator. Your inputs are used only to generate the estimate and history entries, "
        "and any local tracking is managed within the app environment."
    )


# ---------------------------------------------------------------------------
# ROUTER
# ---------------------------------------------------------------------------
navbar()

PAGES = {
    "Home": page_home,
    "Calculator": page_calculator,
    "Results": page_results,
    "History": page_history,
    "About": page_about,
}
PAGES.get(st.session_state.page, page_home)()
# --- render footer HTML if present ---
try:
    with open("footer.html", "r", encoding="utf-8") as fh:
        _footer_html = fh.read()
    st.markdown(_footer_html, unsafe_allow_html=True)
except Exception:
    # If footer isn't present or fails to render, ignore silently
    pass
