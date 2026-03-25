import streamlit as st
from supabase import create_client
import datetime

# -----------------------------
# SUPABASE CONFIG
# -----------------------------
SUPABASE_URL = "https://kqayxhhvfqelwqsuxnwv.supabase.co"
SUPABASE_KEY = "sb_publishable_d9cUMbsI7GNFEm4pgvYUww_Jh8ro__n"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(layout="wide", page_title="ProbabilityLens Terminal")

# -----------------------------
# STYLE (FIXED CONTRAST + HEADER)
# -----------------------------
st.markdown("""
<style>
body {
    background-color: #0b0f14;
    color: #e6e6e6;
}

.header {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 20px;
}

.header img {
    height: 50px;
}

.panel {
    background: #1e2733;
    padding: 22px;
    border-radius: 12px;
    border: 1px solid #2a3545;
    box-shadow: 0 6px 30px rgba(0,0,0,0.6);
}

.panel * {
    color: #ffffff !important;
}

.metric {
    font-size: 36px;
    font-weight: 800;
}

.label {
    font-size: 11px;
    color: #8b98a7 !important;
    margin-top: 10px;
}

div[data-testid="stSidebar"] {
    background-color: #0f141c;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# SESSION STATE
# -----------------------------
if "user" not in st.session_state:
    st.session_state.user = None

if "timeline" not in st.session_state:
    st.session_state.timeline = []

# -----------------------------
# AUTH FUNCTIONS
# -----------------------------
def login(email, password):
    try:
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        st.session_state.user = res.user
    except Exception as e:
        st.error(f"Login error: {e}")

def signup(email, password):
    try:
        supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        st.success("Account created")
    except Exception as e:
        st.error(f"Signup error: {e}")

# -----------------------------
# LOGIN SCREEN
# -----------------------------
if not st.session_state.user:

    st.image("logo.png", width=140)

    st.markdown("""
    <h1>ProbabilityLens</h1>
    <p style='color:gray'>Deterministic Macro Risk Engine</p>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            login(email, password)

    with tab2:
        email = st.text_input("New Email")
        password = st.text_input("New Password", type="password")

        if st.button("Create Account"):
            signup(email, password)

    st.stop()

# -----------------------------
# HEADER (FIXED)
# -----------------------------
st.markdown("""
<div class="header">
    <img src="logo.png">
    <div>
        <div style="font-size:28px;font-weight:700;">ProbabilityLens Terminal</div>
        <div style="color:#9aa4af;font-size:13px;">
            Deterministic Macro Risk Engine — Oil Markets
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# SIDEBAR
# -----------------------------
mode = st.sidebar.selectbox("Mode", ["Manual", "Investor Demo"])

scenario = st.sidebar.selectbox("Scenario", [
    "Weak Macro",
    "Transition",
    "Pre-Breakout",
    "Full Alignment"
])

# -----------------------------
# INPUTS
# -----------------------------
if mode == "Investor Demo":

    if scenario == "Weak Macro":
        signal, timing, conf, align, crowd, health, capital = 0.2,0.1,0.2,0.2,0.6,0.4,0.3
        st.sidebar.info("Weak macro backdrop. No edge.")

    elif scenario == "Transition":
        signal, timing, conf, align, crowd, health, capital = 0.5,0.4,0.5,0.5,0.5,0.5,0.5
        st.sidebar.info("Conditions improving.")

    elif scenario == "Pre-Breakout":
        signal, timing, conf, align, crowd, health, capital = 0.7,0.65,0.7,0.7,0.5,0.6,0.7
        st.sidebar.info("Setup forming.")

    else:
        signal, timing, conf, align, crowd, health, capital = 0.9,0.9,0.9,0.85,0.4,0.8,0.9
        st.sidebar.success("Full alignment. Actionable.")

else:
    signal = st.sidebar.slider("Signal", 0.0, 1.0, 0.3)
    timing = st.sidebar.slider("Timing", 0.0, 1.0, 0.3)
    conf = st.sidebar.slider("Confirmation", 0.0, 1.0, 0.3)
    align = st.sidebar.slider("Alignment", 0.0, 1.0, 0.3)
    crowd = st.sidebar.slider("Crowding", 0.0, 1.0, 0.5)
    health = st.sidebar.slider("Health", 0.0, 1.0, 0.5)
    capital = st.sidebar.slider("Capital", 0.0, 1.0, 0.5)

# -----------------------------
# SCORE ENGINE
# -----------------------------
score = (
    signal*0.2 + timing*0.2 + conf*0.15 +
    align*0.15 + (1-crowd)*0.1 +
    health*0.1 + capital*0.1
)

# -----------------------------
# REGIME
# -----------------------------
if score < 0.5:
    regime, action = "PREPARATION", "NO POSITION"
elif score < 0.7:
    regime, action = "DEVELOPING", "WAIT"
elif score < 0.85:
    regime, action = "NEAR TRIGGER", "WAIT"
else:
    regime, action = "ACTIONABLE", "ADD"

color_map = {
    "NO POSITION": "#ff3b3b",
    "WAIT": "#f5a623",
    "ADD": "#00c853"
}
color = color_map[action]

# -----------------------------
# GRID LAYOUT
# -----------------------------
c1, c2, c3 = st.columns([1,1.3,1])

# INPUT
with c1:
    st.markdown("### INPUT STATE")
    st.markdown(f"""
    <div class='panel'>
    <div class='label'>Signal</div>{signal}
    <div class='label'>Timing</div>{timing}
    <div class='label'>Confirmation</div>{conf}
    <div class='label'>Alignment</div>{align}
    </div>
    """, unsafe_allow_html=True)

# OUTPUT
with c2:
    st.markdown("### TERMINAL OUTPUT")
    st.markdown(f"""
    <div class='panel'>
    <div class='label'>MARKET STATE</div>
    <div style='font-size:26px'>{regime}</div>

    <div class='label'>READINESS</div>
    <div class='metric'>{int(score*100)}%</div>

    <div class='label'>ACTION</div>
    <div class='metric' style='color:{color}'>{action}</div>
    </div>
    """, unsafe_allow_html=True)

# CONSTRAINTS
with c3:
    st.markdown("### CONSTRAINTS")
    cons = []
    if signal < 0.6: cons.append("No structural edge")
    if timing < 0.6: cons.append("Timing inactive")
    if conf < 0.6: cons.append("No confirmation")

    for c in cons:
        st.markdown(f"❌ {c}")

# -----------------------------
# SAVE + TIMELINE
# -----------------------------
if st.button("Save Scenario"):
    entry = {
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "score": round(score,2),
        "regime": regime,
        "action": action
    }
    st.session_state.timeline.append(entry)

    supabase.table("scenarios").insert({
        "user_email": st.session_state.user.email,
        "score": score,
        "regime": regime,
        "action": action
    }).execute()

    st.success("Saved")

# -----------------------------
# TIMELINE
# -----------------------------
st.markdown("---")
st.markdown("### Scenario Timeline")

for t in reversed(st.session_state.timeline):
    st.markdown(f"""
    <div class='panel'>
    {t['time']} — {t['regime']} | {t['action']} | {t['score']}
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# FOOTER
# -----------------------------
st.markdown("---")
st.caption("ProbabilityLens — Institutional Risk Discipline Engine")
