import streamlit as st
from supabase import create_client

# -----------------------------
# SUPABASE CONFIG
# -----------------------------
SUPABASE_URL = "https://kqayxhhvfqelwqsuxnwv.supabase.co"
SUPABASE_KEY = "sb_publishable_d9cUMbsI7GNFEm4pgvYUww_Jh8ro__n"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(layout="wide", page_title="ProbabilityLens Terminal")

# -----------------------------
# GLOBAL STYLING (FIXED UI)
# -----------------------------
st.markdown("""
<style>
body {
    background-color: #0b0f14;
    color: #e6e6e6;
}

.block-container {
    padding-top: 2rem;
}

.panel {
    background: #1c2430;
    padding: 20px;
    border-radius: 10px;
    color: #ffffff;
}

.metric {
    font-size: 34px;
    font-weight: bold;
    color: white;
}

.label {
    font-size: 12px;
    color: #9aa4af;
    margin-top: 10px;
}

div[data-testid="stSidebar"] {
    background-color: #11161f;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# AUTH STATE
# -----------------------------
if "user" not in st.session_state:
    st.session_state.user = None

# -----------------------------
# AUTH FUNCTIONS (DEBUG ENABLED)
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
        st.success("Account created. You can now log in.")
    except Exception as e:
        st.error(f"Signup error: {e}")

# -----------------------------
# LOGIN SCREEN
# -----------------------------
if not st.session_state.user:

    # Logo spacing fix
    st.markdown("<div style='margin-top:30px'></div>", unsafe_allow_html=True)
    st.image("logo.png", width=140)

    st.markdown("""
    <h1 style='margin-bottom:0'>ProbabilityLens</h1>
    <p style='color:gray'>Deterministic Macro Risk Engine</p>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            with st.spinner("Authenticating..."):
                login(email, password)

    with tab2:
        email = st.text_input("New Email")
        password = st.text_input("New Password", type="password")

        if st.button("Create Account"):
            signup(email, password)

    st.stop()

# -----------------------------
# HEADER (FIXED LOGO POSITION)
# -----------------------------
col_logo, col_title = st.columns([1,5])

with col_logo:
    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
    st.image("logo.png", width=120)

with col_title:
    st.title("ProbabilityLens Terminal")
    st.caption("Deterministic Macro Risk Engine — Oil Markets")

# -----------------------------
# DEMO MODE
# -----------------------------
mode = st.sidebar.selectbox("Scenario Mode", [
    "Manual",
    "Weak",
    "Neutral",
    "Strong"
])

# -----------------------------
# INPUTS
# -----------------------------
if mode == "Weak":
    signal, timing, conf, align, crowd, health, capital = 0.2,0.1,0.2,0.2,0.6,0.4,0.3
elif mode == "Neutral":
    signal, timing, conf, align, crowd, health, capital = 0.5,0.4,0.5,0.5,0.5,0.5,0.5
elif mode == "Strong":
    signal, timing, conf, align, crowd, health, capital = 0.9,0.9,0.9,0.8,0.4,0.8,0.9
else:
    signal = st.sidebar.slider("Signal", 0.0, 1.0, 0.3)
    timing = st.sidebar.slider("Timing", 0.0, 1.0, 0.3)
    conf = st.sidebar.slider("Confirmation", 0.0, 1.0, 0.3)
    align = st.sidebar.slider("Alignment", 0.0, 1.0, 0.3)
    crowd = st.sidebar.slider("Crowding", 0.0, 1.0, 0.5)
    health = st.sidebar.slider("Health", 0.0, 1.0, 0.5)
    capital = st.sidebar.slider("Capital", 0.0, 1.0, 0.5)

# -----------------------------
# SCORE
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
    regime, action, color = "PREPARATION", "NO POSITION", "red"
elif score < 0.7:
    regime, action, color = "DEVELOPING", "WAIT", "orange"
elif score < 0.85:
    regime, action, color = "NEAR TRIGGER", "WAIT", "yellow"
else:
    regime, action, color = "ACTIONABLE", "ADD", "green"

# -----------------------------
# LAYOUT
# -----------------------------
c1, c2, c3 = st.columns([1,1.2,1])

# INPUT STATE
with c1:
    st.markdown("### INPUT STATE")
    st.markdown(f"""
    <div class='panel'>
    Signal: {signal}<br>
    Timing: {timing}<br>
    Confirmation: {conf}<br>
    Alignment: {align}
    </div>
    """, unsafe_allow_html=True)

# TERMINAL OUTPUT (FIXED VISIBILITY)
with c2:
    st.markdown("### TERMINAL OUTPUT")
    st.markdown(f"""
    <div class='panel'>

    <div class='label'>MARKET STATE</div>
    <div class='metric'>{regime}</div>

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
        st.markdown(f"- {c}")

# -----------------------------
# SAVE
# -----------------------------
if st.button("Save Scenario"):
    supabase.table("scenarios").insert({
        "user_email": st.session_state.user.email,
        "score": score,
        "regime": regime,
        "action": action
    }).execute()
    st.success("Scenario saved")

# -----------------------------
# FOOTER
# -----------------------------
st.markdown("---")
st.caption("ProbabilityLens — Institutional Risk Discipline Engine")
