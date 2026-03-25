import streamlit as st
from datetime import datetime

# -----------------------------------
# PAGE CONFIG
# -----------------------------------
st.set_page_config(layout="wide")

# -----------------------------------
# GLOBAL STYLE (SAFE ONLY)
# -----------------------------------
st.markdown("""
<style>
/* Darker sidebar to reduce dominance */
[data-testid="stSidebar"] {
    background-color: #020617;
}

/* Reduce slider visual noise */
.stSlider > div > div {
    color: #94a3b8 !important;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------------
# HEADER
# -----------------------------------
st.title("ProbabilityLens")
st.caption("Deterministic Macro Risk Engine — Oil Markets")

st.write(f"**LAST UPDATE:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
st.divider()

# -----------------------------------
# SIDEBAR INPUTS
# -----------------------------------
st.sidebar.header("Input Parameters")

signal = st.sidebar.slider("Signal", 0.0, 1.0, 0.3)
timing = st.sidebar.slider("Timing", 0.0, 1.0, 0.3)
confirmation = st.sidebar.slider("Confirmation", 0.0, 1.0, 0.3)
alignment = st.sidebar.slider("Alignment", 0.0, 1.0, 0.3)
crowding = st.sidebar.slider("Crowding", 0.0, 1.0, 0.5)
health = st.sidebar.slider("Market Health", 0.0, 1.0, 0.5)
capital = st.sidebar.slider("Capital Availability", 0.0, 1.0, 0.5)

# -----------------------------------
# DECISION ENGINE
# -----------------------------------
score = (
    signal * 0.2 +
    timing * 0.2 +
    confirmation * 0.2 +
    alignment * 0.2 +
    crowding * 0.05 +
    health * 0.075 +
    capital * 0.075
)

score_pct = int(score * 100)

if score < 0.5:
    regime = "PREPARATION"
    action = "NO POSITION"
elif score < 0.7:
    regime = "DEVELOPING"
    action = "WAIT"
elif score < 0.85:
    regime = "NEAR TRIGGER"
    action = "WAIT"
else:
    regime = "ACTIONABLE"
    action = "ADD"

# -----------------------------------
# LAYOUT
# -----------------------------------
col1, col2, col3 = st.columns([1.2, 1.5, 1.2])

# -----------------------------------
# INPUT STATE (DE-EMPHASIZED)
# -----------------------------------
with col1:
    st.subheader("INPUT STATE")

    st.write(f"Signal: {signal:.2f}")
    st.write(f"Timing: {timing:.2f}")
    st.write(f"Confirmation: {confirmation:.2f}")
    st.write(f"Alignment: {alignment:.2f}")
    st.write(f"Crowding: {crowding:.2f}")
    st.write(f"Health: {health:.2f}")
    st.write(f"Capital: {capital:.2f}")

# -----------------------------------
# SYSTEM OUTPUT (DOMINANT)
# -----------------------------------
with col2:
    st.subheader("SYSTEM OUTPUT")

    # Regime
    st.caption("MARKET REGIME")
    st.markdown(f"## {regime}")

    # Score
    st.caption("READINESS SCORE")
    st.markdown(f"# {score_pct}%")

    # Action
    st.caption("RECOMMENDED ACTION")

    if action == "NO POSITION":
        st.error(action)
    elif action == "WAIT":
        st.warning(action)
    else:
        st.success(action)

# -----------------------------------
# CONSTRAINTS
# -----------------------------------
with col3:
    st.subheader("CONSTRAINTS")

    constraints = []

    if signal < 0.5:
        constraints.append("No structural edge")
    if timing < 0.5:
        constraints.append("Timing inactive")
    if confirmation < 0.5:
        constraints.append("No confirmation")

    if constraints:
        for c in constraints:
            st.error(c)
    else:
        st.success("No constraints")

# -----------------------------------
# FOOTER ACTION
# -----------------------------------
st.divider()

if st.button("Save Scenario"):
    st.success("Scenario saved (placeholder)")
