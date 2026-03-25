import streamlit as st
from datetime import datetime
import pandas as pd

st.set_page_config(layout="wide")

# -----------------------------------
# STYLE (SAFE + MINIMAL)
# -----------------------------------
st.markdown("""
<style>

/* Sidebar — balanced contrast */
[data-testid="stSidebar"] {
    background-color: #0f172a;
}

[data-testid="stSidebar"] * {
    color: #cbd5f5 !important;
}

/* Reduce slider intensity */
.stSlider > div > div {
    color: #9ca3af !important;
}

/* Main spacing */
.block-container {
    padding-top: 1.5rem;
    padding-left: 3rem;
    padding-right: 3rem;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------------
# HEADER WITH LOGO
# -----------------------------------
col_logo, col_title = st.columns([1.5, 6])

with col_logo:
    st.image("logo.png", use_container_width=True)  # ensure logo is properly cropped externally

with col_title:
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
# DECISION ENGINE FUNCTION
# -----------------------------------
def compute_decision(signal, timing, confirmation, alignment, crowding, health, capital):
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

    return score_pct, regime, action

# -----------------------------------
# CURRENT SCENARIO
# -----------------------------------
score_pct, regime, action = compute_decision(
    signal, timing, confirmation, alignment, crowding, health, capital
)

# -----------------------------------
# LAYOUT
# -----------------------------------
col1, col2, col3 = st.columns([1.2, 1.5, 1.2])

# -----------------------------------
# INPUT STATE
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
# SYSTEM OUTPUT
# -----------------------------------
with col2:
    st.subheader("SYSTEM OUTPUT")

    st.caption("MARKET REGIME")
    st.markdown(f"# {regime}")

    st.caption("READINESS SCORE")
    st.markdown(f"# {score_pct}%")

    st.caption("RECOMMENDED ACTION")

    if action == "NO POSITION":
        st.error(action)
    elif action == "WAIT":
        st.warning(action)
    else:
        st.success(action)

    # Decision interpretation (key upgrade)
    st.caption("SYSTEM INTERPRETATION")

    if action == "NO POSITION":
        st.write("Conditions insufficient for risk deployment. Monitor for signal development.")
    elif action == "WAIT":
        st.write("Setup forming. Await confirmation before allocation.")
    else:
        st.write("Conditions aligned. Incremental exposure warranted.")

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
# SCENARIO COMPARISON PANEL
# -----------------------------------
st.divider()
st.subheader("Scenario Comparison")

# Define scenarios
scenarios = {
    "Base Case": (signal, timing, confirmation, alignment, crowding, health, capital),
    "Bull Case": (0.8, 0.8, 0.8, 0.8, 0.6, 0.7, 0.7),
    "Stress Case": (0.2, 0.2, 0.2, 0.2, 0.7, 0.4, 0.4),
}

data = []

for name, vals in scenarios.items():
    s, r, a = compute_decision(*vals)
    data.append([name, s, r, a])

df = pd.DataFrame(data, columns=["Scenario", "Score (%)", "Regime", "Action"])

st.dataframe(df, use_container_width=True)

# -----------------------------------
# FOOTER
# -----------------------------------
st.divider()

if st.button("Save Scenario"):
    st.success("Scenario saved")
