import streamlit as st

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="ProbabilityLens — Oil Risk Monitor",
    layout="wide"
)

# -----------------------------
# LOGO (SAFE LOAD)
# -----------------------------
try:
    st.image("logo.png", width=180)
except:
    pass

# -----------------------------
# HERO SECTION
# -----------------------------
st.title("ProbabilityLens — Oil Risk Monitor")

st.markdown("""
**A deterministic macro framework that tells you when to take risk — and when to stay out.**

Built to eliminate premature positioning and enforce disciplined timing in oil markets.
""")

st.markdown("---")

# -----------------------------
# VALUE STRIP
# -----------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Deterministic, Not Predictive**  \nNo forecasts. Only condition-based decisions.")

with col2:
    st.markdown("**Timing Over Opinion**  \nAct only when alignment is real.")

with col3:
    st.markdown("**Risk First**  \nDefault state is **NO POSITION** unless proven otherwise.")

st.markdown("---")

# -----------------------------
# SCORING FUNCTION
# -----------------------------
def compute_score(signal, timing, confirmation, alignment, crowding, health, capital):
    weights = [0.2, 0.2, 0.15, 0.15, 0.1, 0.1, 0.1]
    values = [signal, timing, confirmation, alignment, crowding, health, capital]
    return sum(w * v for w, v in zip(weights, values))

# -----------------------------
# LAYOUT (3 COLUMNS)
# -----------------------------
left, center, right = st.columns([1, 1.2, 1])

# -----------------------------
# LEFT PANEL — SCENARIO
# -----------------------------
with left:
    st.subheader("SCENARIO SETUP")
    st.caption("Define current macro conditions to evaluate readiness.")

    preset = st.selectbox(
        "Macro Regime Presets",
        ["Custom", "Weak Macro", "Neutral", "Bullish Setup"]
    )

    if preset == "Weak Macro":
        signal = 0.2
        timing = 0.1
        confirmation = 0.2
        alignment = 0.2
        crowding = 0.3
        health = 0.4
        capital = 0.3
    elif preset == "Neutral":
        signal = 0.5
        timing = 0.4
        confirmation = 0.5
        alignment = 0.5
        crowding = 0.5
        health = 0.5
        capital = 0.5
    elif preset == "Bullish Setup":
        signal = 0.8
        timing = 0.7
        confirmation = 0.8
        alignment = 0.75
        crowding = 0.6
        health = 0.7
        capital = 0.8
    else:
        st.markdown("**Adjust Conditions**")
        signal = st.slider("Signal Strength", 0.0, 1.0, 0.3)
        timing = st.slider("Timing Trigger", 0.0, 1.0, 0.2)
        confirmation = st.slider("Market Confirmation", 0.0, 1.0, 0.3)
        alignment = st.slider("Cross-Market Alignment", 0.0, 1.0, 0.3)
        crowding = st.slider("Crowding / Positioning", 0.0, 1.0, 0.4)
        health = st.slider("Market Health", 0.0, 1.0, 0.5)
        capital = st.slider("Capital Availability", 0.0, 1.0, 0.4)

# -----------------------------
# COMPUTE SCORE
# -----------------------------
score = compute_score(signal, timing, confirmation, alignment, crowding, health, capital)

# -----------------------------
# REGIME + DECISION
# -----------------------------
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
# CENTER PANEL — OUTPUT
# -----------------------------
with center:
    st.subheader("DECISION ENGINE OUTPUT")

    st.markdown("### MARKET STATE")
    st.markdown(f"**{regime}**")

    st.markdown("### READINESS SCORE")
    st.markdown(f"**{int(score * 100)}%**")
    st.caption("Condition alignment toward actionable state")

    st.markdown("### ACTION")
    st.markdown(f"## {action}")

    # Interpretation
    st.markdown("### INTERPRETATION")

    if action == "NO POSITION":
        st.markdown("""
Conditions are not aligned.  
Risk of premature positioning is high.
""")
    elif action == "WAIT":
        st.markdown("""
Partial alignment detected.  
Timing and confirmation are not yet sufficient.
""")
    else:
        st.markdown("""
Conditions are aligned.  
Risk-taking is supported by structure and confirmation.
""")

# -----------------------------
# RIGHT PANEL — CONSTRAINTS
# -----------------------------
with right:
    st.subheader("WHY NOT ADD")
    st.caption("Constraints preventing risk deployment")

    constraints = []

    if signal < 0.6:
        constraints.append("❌ No structural edge")
    if timing < 0.6:
        constraints.append("❌ Timing not activated")
    if confirmation < 0.6:
        constraints.append("❌ No market confirmation")
    if alignment < 0.6:
        constraints.append("❌ Cross-market misalignment")
    if capital < 0.5:
        constraints.append("❌ Weak capital flow support")

    if constraints:
        for c in constraints:
            st.markdown(c)

        st.markdown("---")
        st.markdown("**Adding risk here would be undisciplined and premature.**")
    else:
        st.markdown("No major constraints detected.")

# -----------------------------
# NEXT TRIGGER
# -----------------------------
st.markdown("---")
st.subheader("NEXT TRIGGER")

st.markdown("""
Risk becomes actionable when:
- Signal strength reaches required threshold  
- Timing trigger activates  
- Market confirmation aligns  

Until then, no action is justified.
""")

# -----------------------------
# HOW TO USE
# -----------------------------
st.markdown("---")
st.subheader("HOW TO USE")

st.markdown("""
1. Select a macro scenario or adjust conditions  
2. Observe readiness score and market state  
3. Follow the action output — not your bias  
4. Use “Why Not Add” to understand constraints  
5. Wait for alignment before deploying capital  
""")

# -----------------------------
# WHAT THIS TOOL DOES
# -----------------------------
st.markdown("---")
st.subheader("WHAT THIS TOOL DOES")

st.markdown("""
- Translates macro conditions into structured decisions  
- Enforces timing discipline  
- Prevents premature entries  
- Highlights when risk is justified  
""")

# -----------------------------
# WHAT THIS TOOL DOES NOT DO
# -----------------------------
st.subheader("WHAT THIS TOOL DOES NOT DO")

st.markdown("""
- Does NOT predict prices  
- Does NOT forecast direction  
- Does NOT optimize entries  
- Does NOT replace judgment  

**It answers one question only:**  
Are conditions aligned enough to take risk?
""")

# -----------------------------
# METHODOLOGY
# -----------------------------
st.markdown("---")
st.subheader("METHODOLOGY")

st.markdown("""
ProbabilityLens uses a deterministic scoring model based on:

- Signal strength  
- Timing activation  
- Market confirmation  
- Cross-market alignment  
- Positioning / crowding  
- Market health  
- Capital availability  

Outputs are rule-based, not predictive.
""")

# -----------------------------
# FINAL STATEMENT
# -----------------------------
st.markdown("---")
st.markdown("""
**Most losses come from acting too early.**

ProbabilityLens exists to prevent that.
""")
