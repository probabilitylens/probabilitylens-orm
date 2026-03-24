import streamlit as st

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(layout="wide")

# =========================
# HERO SECTION
# =========================
col_logo, col_title = st.columns([1, 4])

with col_logo:
    try:
        st.image("logo.png", width=140)
    except:
        pass

with col_title:
    st.title("Oil Risk Monitor")
    st.caption("Deterministic Macro Decision Engine for Oil Markets")

st.markdown("""
Transforms macro conditions into **structured, rule-based trading decisions**.

This system does **not predict prices** — it identifies when conditions justify action.

**Designed for disciplined decision-making under uncertainty.**
""")

st.divider()

# =========================
# SCENARIOS
# =========================
SCENARIOS = {
    "Manual": None,
    "Bullish Supply Shock": dict(edge=2, timing=1, confirm=1, network=0.7, reflex=0.3, health=0.8),
    "Demand Collapse": dict(edge=2, timing=1, confirm=1, network=0.6, reflex=0.2, health=0.7),
    "Geopolitical Risk": dict(edge=1, timing=1, confirm=0, network=0.4, reflex=0.6, health=0.7),
    "Late Cycle": dict(edge=1, timing=0, confirm=0, network=0.3, reflex=0.85, health=0.5),
}

# =========================
# LAYOUT
# =========================
left, center, right = st.columns([1, 1.2, 1])

# =========================
# LEFT PANEL (INPUTS)
# =========================
with left:
    st.subheader("Scenario")

    preset = st.selectbox("Preset Market Scenario", list(SCENARIOS.keys()))

    default = SCENARIOS[preset] or {}

    edge = st.selectbox("Signal Strength", [0, 1, 2], index=default.get("edge", 0))
    timing = st.selectbox("Timing Trigger", [0, 1], index=default.get("timing", 0))
    confirm = st.selectbox("Market Confirmation", [0, 1], index=default.get("confirm", 0))

    network = st.slider("Cross-Market Alignment", 0.0, 1.0, float(default.get("network", 0.5)))
    reflex = st.slider("Crowding / Reflexivity", 0.0, 1.0, float(default.get("reflex", 0.3)))
    health = st.slider("Market Health", 0.0, 1.0, float(default.get("health", 0.75)))

    max_prop = st.slider("Portfolio Utilisation", 0.0, 100.0, 75.0)
    capital = st.number_input("Available Capital", value=0.05)

    evaluate = st.button("Evaluate")

# =========================
# ENGINE
# =========================
def compute():
    score = (
        edge * 0.25 +
        timing * 0.2 +
        confirm * 0.2 +
        network * 0.1 +
        (1 - reflex) * 0.1 +
        health * 0.1 +
        min(capital * 2, 1) * 0.05
    )

    # Regime
    if score < 0.5:
        regime = "PREPARATION"
        decision = "NONE"
        text = "No clear opportunity — monitoring."
    elif score < 0.7:
        regime = "DEVELOPING"
        decision = "WAIT"
        text = "Setup incomplete — no edge to act."
    elif score < 0.85:
        regime = "NEAR TRIGGER"
        decision = "WAIT"
        text = "Close to actionable — waiting for confirmation."
    else:
        regime = "ACTIONABLE"
        decision = "ADD"
        text = "Conditions aligned — opportunity actionable."

    return score, regime, decision, text

def constraints():
    issues = []

    if edge < 2:
        issues.append(f"Signal not strong ({edge} → strong required)")
    if timing < 1:
        issues.append("Timing not triggered")
    if confirm < 1:
        issues.append("Market confirmation missing")
    if network < 0.5:
        issues.append(f"Market alignment too weak ({network:.2f})")

    return issues

def next_trigger():
    if edge < 2:
        return "Strengthen signal to actionable level"
    if confirm < 1:
        return "Wait for confirmation signal"
    if timing < 1:
        return "Timing trigger activation"
    return "Conditions aligned"

# =========================
# CENTER PANEL (OUTPUT)
# =========================
with center:
    st.subheader("Decision")

    if not evaluate:
        st.info("Select scenario and evaluate.")
    else:
        score, regime, decision, text = compute()

        st.caption("System Output")
        st.markdown(f"### {regime}")

        st.markdown("<br>", unsafe_allow_html=True)

        st.caption("Readiness")
        st.metric("", f"{score*100:.1f}%")

        # Decision box
        if decision == "ADD":
            st.success(decision)
        elif decision == "WAIT":
            st.warning(decision)
        elif decision == "REDUCE":
            st.warning(decision)
        else:
            st.info(decision)

        st.write(text)

# =========================
# RIGHT PANEL (WHY NOT ADD)
# =========================
with right:
    st.subheader("Why NOT ADD")

    if not evaluate:
        st.info("Run evaluation.")
    else:
        st.caption("Constraint Analysis")
        st.write("Blocking conditions preventing action:")

        issues = constraints()

        if not issues:
            st.success("No constraints — ADD conditions satisfied.")
        else:
            for i, issue in enumerate(issues):
                if i == 0:
                    st.error(issue)
                else:
                    st.warning(issue)

        st.markdown("### Next Trigger")
        st.markdown(f"**{next_trigger()}**")

# =========================
# HOW TO USE
# =========================
st.divider()

st.subheader("How to Use")

st.markdown("""
- Select a market scenario or input your own view  
- Click **Evaluate**  
- Review:
  - Market regime  
  - Readiness score  
  - Decision  
- Use constraint analysis to understand blockers  

This system enforces **discipline, not prediction**.
""")

# =========================
# ABOUT
# =========================
st.divider()

st.subheader("About / Methodology")

st.markdown("""
### Deterministic Decision Framework

This system does not forecast markets.

It determines:

- When to act  
- When to wait  
- When to reduce risk  

### Core Inputs

- Signal strength  
- Timing trigger  
- Confirmation  
- Cross-market alignment  
- Crowding  
- Market health  
- Capital availability  

### Regime Model

- Preparation  
- Developing  
- Near Trigger  
- Actionable  

### Philosophy

Markets reward discipline.

**Act only when conditions justify it.**
""")
