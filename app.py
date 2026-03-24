import streamlit as st

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="ProbabilityLens Terminal", layout="wide")

# -----------------------------
# GLOBAL STYLING (BLOOMBERG-STYLE)
# -----------------------------
st.markdown("""
<style>
body {
    background-color: #0e1117;
    color: #e6e6e6;
}
.block-container {
    padding-top: 1.5rem;
}
h1, h2, h3 {
    color: #ffffff;
}
.metric-box {
    background-color: #1a1f2b;
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# LOGO
# -----------------------------
try:
    st.image("logo.png", width=140)
except:
    pass

# -----------------------------
# HEADER
# -----------------------------
st.title("ProbabilityLens Terminal")
st.caption("Deterministic Macro Risk Engine — Oil Markets")

st.markdown("---")

# -----------------------------
# DEMO MODE
# -----------------------------
st.sidebar.header("DEMO MODE")
demo = st.sidebar.selectbox("Scenario Storytelling", [
    "Manual",
    "Early Weak Macro",
    "Transition Phase",
    "Pre-Breakout Setup",
    "Full Alignment"
])

# -----------------------------
# DEFAULT VALUES
# -----------------------------
if demo == "Early Weak Macro":
    signal, timing, confirmation, alignment, crowding, health, capital = 0.2, 0.1, 0.2, 0.2, 0.6, 0.4, 0.3
elif demo == "Transition Phase":
    signal, timing, confirmation, alignment, crowding, health, capital = 0.5, 0.4, 0.5, 0.5, 0.5, 0.5, 0.5
elif demo == "Pre-Breakout Setup":
    signal, timing, confirmation, alignment, crowding, health, capital = 0.7, 0.65, 0.7, 0.7, 0.5, 0.6, 0.7
elif demo == "Full Alignment":
    signal, timing, confirmation, alignment, crowding, health, capital = 0.9, 0.9, 0.9, 0.85, 0.4, 0.8, 0.9
else:
    signal = st.sidebar.slider("Signal", 0.0, 1.0, 0.3)
    timing = st.sidebar.slider("Timing", 0.0, 1.0, 0.3)
    confirmation = st.sidebar.slider("Confirmation", 0.0, 1.0, 0.3)
    alignment = st.sidebar.slider("Alignment", 0.0, 1.0, 0.3)
    crowding = st.sidebar.slider("Crowding", 0.0, 1.0, 0.5)
    health = st.sidebar.slider("Health", 0.0, 1.0, 0.5)
    capital = st.sidebar.slider("Capital", 0.0, 1.0, 0.5)

# -----------------------------
# SCORING
# -----------------------------
score = (
    signal*0.2 + timing*0.2 + confirmation*0.15 + alignment*0.15 +
    (1-crowding)*0.1 + health*0.1 + capital*0.1
)

# -----------------------------
# REGIME
# -----------------------------
if score < 0.5:
    regime, action, color = "PREPARATION", "NO POSITION", "red"
elif score < 0.7:
    regime, action, color = "DEVELOPING", "WAIT", "orange"
elif score < 0.85:
    regime, action, color = "NEAR TRIGGER", "WAIT", "yellow"
else:
    regime, action, color = "ACTIONABLE", "ADD", "green"

# -----------------------------
# MAIN GRID
# -----------------------------
col1, col2, col3 = st.columns([1,1.2,1])

# -----------------------------
# LEFT — INPUT SUMMARY
# -----------------------------
with col1:
    st.subheader("INPUT STATE")
    st.markdown(f"Signal: {round(signal,2)}")
    st.markdown(f"Timing: {round(timing,2)}")
    st.markdown(f"Confirmation: {round(confirmation,2)}")
    st.markdown(f"Alignment: {round(alignment,2)}")
    st.markdown(f"Crowding: {round(crowding,2)}")
    st.markdown(f"Health: {round(health,2)}")
    st.markdown(f"Capital: {round(capital,2)}")

# -----------------------------
# CENTER — TERMINAL OUTPUT
# -----------------------------
with col2:
    st.subheader("TERMINAL OUTPUT")

    st.markdown(f"### MARKET STATE\n**{regime}**")

    st.markdown(f"### READINESS\n# {int(score*100)}%")

    st.markdown("### ACTION")
    st.markdown(f"<h2 style='color:{color}'>{action}</h2>", unsafe_allow_html=True)

    if action == "NO POSITION":
        st.info("Capital preservation mode")
    elif action == "WAIT":
        st.warning("Monitoring — no trigger yet")
    else:
        st.success("Conditions aligned — deploy risk")

# -----------------------------
# RIGHT — CONSTRAINTS
# -----------------------------
with col3:
    st.subheader("CONSTRAINTS")

    constraints = []

    if signal < 0.6:
        constraints.append("No structural edge")
    if timing < 0.6:
        constraints.append("Timing inactive")
    if confirmation < 0.6:
        constraints.append("No confirmation")
    if alignment < 0.6:
        constraints.append("Misalignment")

    if constraints:
        for c in constraints:
            st.markdown(f"- {c}")
        st.error("Undisciplined to add risk")
    else:
        st.success("No constraints")

# -----------------------------
# SAVE SCENARIO (SIMPLE SaaS BASE)
# -----------------------------
st.markdown("---")
st.subheader("SCENARIO STORAGE")

if "saved" not in st.session_state:
    st.session_state.saved = []

if st.button("Save Current Scenario"):
    st.session_state.saved.append({
        "score": round(score,2),
        "regime": regime,
        "action": action
    })

for i, s in enumerate(st.session_state.saved):
    st.markdown(f"Scenario {i+1}: {s}")

# -----------------------------
# FOOTER
# -----------------------------
st.markdown("---")
st.caption("ProbabilityLens — Institutional Risk Discipline Engine")
