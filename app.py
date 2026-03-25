import streamlit as st
from supabase import create_client
import datetime

# -----------------------------
# CONFIG
# -----------------------------
SUPABASE_URL = "https://kqayxhhvfqelwqsuxnwv.supabase.co"
SUPABASE_KEY = "sb_publishable_d9cUMbsI7GNFEm4pgvYUww_Jh8ro__n"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(layout="wide", page_title="ProbabilityLens Terminal")

# -----------------------------
# STYLE (SAFE + STRONG)
# -----------------------------
st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem;
}

/* PANELS */
.panel {
    background: #1c2430;
    padding: 22px;
    border-radius: 12px;
    border: 1px solid #2a3545;
}

/* TEXT */
.label {
    font-size: 11px;
    color: #9aa4af;
}

.metric {
    font-size: 36px;
    font-weight: 800;
}

/* SIDEBAR */
div[data-testid="stSidebar"] {
    background-color: #0f141c;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# STATE
# -----------------------------
if "user" not in st.session_state:
    st.session_state.user = None

if "timeline" not in st.session_state:
    st.session_state.timeline = []

# -----------------------------
# AUTH
# -----------------------------
def login(email, password):
    try:
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        st.session_state.user = res.user
    except Exception as e:
        st.error(e)

def signup(email, password):
    try:
        supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        st.success("Account created")
    except Exception as e:
        st.error(e)

# -----------------------------
# LOGIN
# -----------------------------
if not st.session_state.user:

    st.image("logo.png", width=140)

    st.title("ProbabilityLens")
    st.caption("Deterministic Macro Risk Engine")

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
col1, col2 = st.columns([1,6])

with col1:
    st.image("logo.png", width=90)

with col2:
    st.title("ProbabilityLens Terminal")
    st.caption("Deterministic Macro Risk Engine — Oil Markets")

# -----------------------------
# SIDEBAR
# -----------------------------
mode = st.sidebar.selectbox("Mode", ["Manual", "Investor Demo"])

# -----------------------------
# INPUTS
# -----------------------------
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
    regime, action = "PREPARATION", "NO POSITION"
elif score < 0.7:
    regime, action = "DEVELOPING", "WAIT"
elif score < 0.85:
    regime, action = "NEAR TRIGGER", "WAIT"
else:
    regime, action = "ACTIONABLE", "ADD"

color_map = {
    "NO POSITION": "red",
    "WAIT": "orange",
    "ADD": "green"
}
color = color_map[action]

# -----------------------------
# LAYOUT
# -----------------------------
c1, c2, c3 = st.columns([1,1.2,1])

# INPUT
with c1:
    st.markdown("### INPUT STATE")
    st.markdown(f"""
    <div class='panel'>
    <div class='label'>Signal</div>{signal}<br>
    <div class='label'>Timing</div>{timing}<br>
    <div class='label'>Confirmation</div>{conf}<br>
    <div class='label'>Alignment</div>{align}
    </div>
    """, unsafe_allow_html=True)

# OUTPUT
with c2:
    st.markdown("### TERMINAL OUTPUT")
    st.markdown(f"""
    <div class='panel'>
    <div class='label'>STATE</div>
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

    if signal < 0.6:
        st.write("❌ No structural edge")
    if timing < 0.6:
        st.write("❌ Timing inactive")
    if conf < 0.6:
        st.write("❌ No confirmation")

# -----------------------------
# SAVE
# -----------------------------
if st.button("Save Scenario"):
    st.session_state.timeline.append({
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "score": score,
        "regime": regime
    })
    st.success("Saved")

# -----------------------------
# TIMELINE
# -----------------------------
st.markdown("---")
st.markdown("### Scenario Timeline")

for t in reversed(st.session_state.timeline):
    st.write(f"{t['time']} — {t['regime']} ({t['score']:.2f})")

# -----------------------------
# FOOTER
# -----------------------------
st.markdown("---")
st.caption("ProbabilityLens — Institutional Risk Discipline Engine")
