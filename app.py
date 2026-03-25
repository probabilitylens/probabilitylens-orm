import streamlit as st
from datetime import datetime

st.set_page_config(layout="wide")

# -----------------------------
# GLOBAL STYLING
# -----------------------------
st.markdown("""
<style>

/* App background */
body {
    background-color: #020617;
}

/* Remove slider red dominance */
.stSlider > div > div {
    color: #94a3b8 !important;
}

/* Section titles */
.section-title {
    font-size: 14px;
    color: #9aa4b2;
    letter-spacing: 1px;
}

/* Card base */
.card {
    background-color:#0b1220;
    padding:20px;
    border-radius:12px;
    border:1px solid #1f2a44;
}

/* Big numbers */
.big-number {
    font-size:42px;
    color:white;
    margin:0;
}

/* Action text */
.action-red {
    color:#ef4444;
    font-size:40px;
    margin:0;
}

/* Sub labels */
.label {
    font-size:12px;
    color:#9aa4b2;
    margin-top:20px;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# HEADER
# -----------------------------
st.markdown("""
<h1 style="margin-bottom:0;">ProbabilityLens</h1>
<p style="color:#9aa4b2; margin-top:0;">
Deterministic Macro Risk Engine — Oil Markets
</p>
""", unsafe_allow_html=True)

st.markdown(f"**LAST UPDATE:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
st.markdown("---")

# -----------------------------
# SIDEBAR INPUTS
# -----------------------------
st.sidebar.markdown("### Input Parameters")

signal = st.sidebar.slider("Signal", 0.0, 1.0, 0.3)
timing = st.sidebar.slider("Timing", 0.0, 1.0, 0.3)
confirmation = st.sidebar.slider("Confirmation", 0.0, 1.0, 0.3)
alignment = st.sidebar.slider("Alignment", 0.0, 1.0, 0.3)
crowding = st.sidebar.slider("Crowding", 0.0, 1.0, 0.5)
health = st.sidebar.slider("Market Health", 0.0, 1.0, 0.5)
capital = st.sidebar.slider("Capital Availability", 0.0, 1.0, 0.5)

# -----------------------------
# DECISION ENGINE (SIMPLE VERSION)
# -----------------------------
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

# -----------------------------
# LAYOUT
# -----------------------------
col1, col2, col3 = st.columns([1.2, 1.5, 1.2])

# -----------------------------
# INPUT STATE (DE-EMPHASIZED)
# -----------------------------
with col1:
    st.markdown('<p class="section-title">INPUT STATE</p>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card" style="opacity:0.7;">
        Signal: {signal:.2f}<br>
        Timing: {timing:.2f}<br>
        Confirmation: {confirmation:.2f}<br>
        Alignment: {alignment:.2f}<br>
        Crowding: {crowding:.2f}<br>
        Health: {health:.2f}<br>
        Capital: {capital:.2f}
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# TERMINAL OUTPUT (DOMINANT)
# -----------------------------
with col2:
    st.markdown('<p class="section-title">SYSTEM OUTPUT</p>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">

        <p class="label">MARKET REGIME</p>
        <h1 class="big-number">{regime}</h1>

        <p class="label">READINESS SCORE</p>
        <h2 class="big-number">{score_pct}%</h2>

        <p class="label">RECOMMENDED ACTION</p>
        <h1 class="action-red">{action}</h1>

    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# CONSTRAINTS PANEL
# -----------------------------
with col3:
    st.markdown('<p class="section-title">CONSTRAINTS</p>', unsafe_allow_html=True)

    constraints = []

    if signal < 0.5:
        constraints.append("No structural edge")
    if timing < 0.5:
        constraints.append("Timing inactive")
    if confirmation < 0.5:
        constraints.append("No confirmation")

    st.markdown('<div class="card">', unsafe_allow_html=True)

    if constraints:
        for c in constraints:
            st.markdown(f"<p style='color:#ef4444;'>✖ {c}</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='color:#22c55e;'>✔ No constraints</p>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# SCENARIO SAVE (OPTIONAL)
# -----------------------------
st.markdown("---")
if st.button("Save Scenario"):
    st.success("Scenario saved (placeholder)")
