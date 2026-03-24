import streamlit as st

st.set_page_config(page_title="ProbabilityLens ORM", layout="wide")

# ── HEADER ──────────────────────────────────────────────

col_logo, col_text = st.columns([1, 3])

with col_logo:
    st.image("logo.png", width=140)

with col_text:
    st.markdown("<h2 style='margin-bottom:0;'>Oil Risk Monitor</h2>", unsafe_allow_html=True)
    st.markdown("<p style='margin-top:0; color:gray;'>Deterministic Macro Decision Engine for Oil Markets</p>", unsafe_allow_html=True)

st.markdown(
"""
Transforms macro conditions into **structured, rule-based trading decisions**.

This system does **not predict prices** — it identifies when conditions justify action.

**Designed for disciplined decision-making under uncertainty.**
"""
)

st.divider()

# ── PRESETS ─────────────────────────────────────────────

def load_preset(preset):
    if preset == "Bullish Supply Shock":
        return dict(edge_score=2, timing_score=1, confirmation_score=1,
                    network_score=0.7, reflex_score=0.3, health=0.8,
                    max_prop=80.0, portfolio_headroom=0.1)

    if preset == "Demand Collapse":
        return dict(edge_score=2, timing_score=1, confirmation_score=1,
                    network_score=0.6, reflex_score=0.2, health=0.7,
                    max_prop=75.0, portfolio_headroom=0.1)

    if preset == "Geopolitical Risk Spike":
        return dict(edge_score=1, timing_score=1, confirmation_score=0,
                    network_score=0.4, reflex_score=0.6, health=0.7,
                    max_prop=60.0, portfolio_headroom=0.05)

    if preset == "Late Cycle Exhaustion":
        return dict(edge_score=1, timing_score=0, confirmation_score=0,
                    network_score=0.3, reflex_score=0.85, health=0.5,
                    max_prop=55.0, portfolio_headroom=0.0)

    return None


# ── ENGINE ─────────────────────────────────────────────

def evaluate_fsm(state):

    if state["max_prop"] < 50:
        decision = "EXIT"

    elif state["reflex_score"] >= 0.8 or state["health"] < 0.6:
        decision = "REDUCE"

    elif (
        state["edge_score"] == 2 and
        state["timing_score"] == 1 and
        state["confirmation_score"] == 1 and
        state["network_score"] >= 0.5 and
        state["reflex_score"] < 0.8 and
        state["portfolio_headroom"] > 0 and
        state["health"] >= 0.6
    ):
        decision = "ADD"

    else:
        decision = "WAIT"

    conditions = [
        state["edge_score"] == 2,
        state["timing_score"] == 1,
        state["confirmation_score"] == 1,
        state["network_score"] >= 0.5,
        state["reflex_score"] < 0.8,
        state["portfolio_headroom"] > 0,
        state["health"] >= 0.6
    ]

    score = sum(conditions) / len(conditions)

    missing = []
    if state["edge_score"] != 2:
        missing.append("edge_score != 2")
    if state["timing_score"] != 1:
        missing.append("timing_score != 1")
    if state["confirmation_score"] != 1:
        missing.append("confirmation_score != 1")
    if state["network_score"] < 0.5:
        missing.append("network_score < 0.5")
    if state["reflex_score"] >= 0.8:
        missing.append("reflex_score >= 0.8")
    if state["portfolio_headroom"] <= 0:
        missing.append("portfolio_headroom <= 0")
    if state["health"] < 0.6:
        missing.append("health < 0.6")

    if score < 0.4:
        regime = "PREPARATION"
    elif score < 0.7:
        regime = "DEVELOPING"
    elif score < 1.0:
        regime = "NEAR TRIGGER"
    else:
        regime = "ACTIONABLE"

    return {
        "decision": decision,
        "score": score,
        "regime": regime,
        "missing": missing,
        "state": state
    }


# ── INTERPRETATION ─────────────────────────────────────

def interpret(decision, score):
    if decision == "ADD":
        return "All conditions aligned — risk/reward favorable."
    if decision == "REDUCE":
        return "Risk asymmetry increasing — exposure should be reduced."
    if decision == "EXIT":
        return "Structural breakdown — position no longer justified."
    if score >= 0.7:
        return "High readiness — awaiting final confirmation."
    return "Setup incomplete — no edge to act."


# ── WHY NOT ADD ────────────────────────────────────────

def explain_not_add(state, missing):

    mapping = {
        "edge_score != 2": f"Signal not strong ({state['edge_score']} → strong required)",
        "timing_score != 1": "Timing not triggered",
        "confirmation_score != 1": "Market confirmation missing",
        "network_score < 0.5": f"Cross-market alignment too weak ({state['network_score']:.2f})",
        "reflex_score >= 0.8": "Crowded positioning",
        "portfolio_headroom <= 0": "No capital available",
        "health < 0.6": "Market conditions unstable"
    }

    trigger_map = {
        "edge_score != 2": "Strengthen signal to actionable level",
        "timing_score != 1": "Wait for timing trigger",
        "confirmation_score != 1": "Wait for confirmation",
        "network_score < 0.5": "Improve cross-market alignment",
        "reflex_score >= 0.8": "Reduce crowding",
        "portfolio_headroom <= 0": "Free capital",
        "health < 0.6": "Wait for stability"
    }

    explanations = [mapping[m] for m in missing]
    next_trigger = trigger_map.get(missing[0], explanations[0])

    return explanations, next_trigger


# ── LAYOUT ─────────────────────────────────────────────

left, center, right = st.columns([1,1.5,1], gap="large")

# INPUTS
with left:
    st.subheader("Scenario")

    preset = st.selectbox(
        "Preset Market Scenario",
        ["Manual", "Bullish Supply Shock", "Demand Collapse",
         "Geopolitical Risk Spike", "Late Cycle Exhaustion"]
    )

    preset_data = load_preset(preset)

    if preset_data:
        state = preset_data
    else:
        state = {
            "edge_score": st.selectbox("Signal Strength", [0,1,2]),
            "timing_score": st.selectbox("Timing Trigger", [0,1]),
            "confirmation_score": st.selectbox("Market Confirmation", [0,1]),
            "network_score": st.slider("Cross-Market Alignment", 0.0,1.0,0.5),
            "reflex_score": st.slider("Crowding / Reflexivity", 0.0,1.0,0.3),
            "health": st.slider("Market Health", 0.0,1.0,0.75),
            "max_prop": st.slider("Portfolio Utilisation", 0.0,100.0,75.0),
            "portfolio_headroom": st.number_input("Available Capital", 0.0,1.0,0.05),
        }

    run = st.button("Evaluate", use_container_width=True)


# RUN ENGINE
if run:
    st.session_state.result = evaluate_fsm(state)


# OUTPUT
with center:
    st.subheader("Decision")
    st.caption("System Output")

    if "result" not in st.session_state:
        st.info("No evaluation yet — select a scenario and click Evaluate.")

    else:
        r = st.session_state.result

        st.markdown(f"### {r['regime']}")
        st.markdown("<br>", unsafe_allow_html=True)

        st.metric("Readiness", f"{r['score']*100:.1f}%")

        if r["decision"] == "ADD":
            st.success("ADD")
        elif r["decision"] == "REDUCE":
            st.warning("REDUCE")
        elif r["decision"] == "EXIT":
            st.error("EXIT")
        else:
            st.info("WAIT")

        st.write(interpret(r["decision"], r["score"]))


# WHY NOT ADD
with right:
    st.subheader("Why NOT ADD")
    st.caption("Constraint Analysis")

    if "result" not in st.session_state:
        st.info("Run evaluation to identify blocking conditions.")

    else:
        missing = st.session_state.result["missing"]

        if not missing:
            st.success("All conditions satisfied")

        else:
            st.markdown("**Blocking conditions preventing action:**")

            reasons, trigger = explain_not_add(
                st.session_state.result["state"], missing
            )

            for r in reasons:
                st.error(r)

            st.divider()
            st.success(f"Next trigger: {trigger}")


st.divider()

# ── HOW TO USE ─────────────────────────────────────────

with st.expander("How to Use"):
    st.markdown(
    """
1. Select a market scenario or input your own view  
2. Click **Evaluate**  
3. Review:
   - Market regime  
   - Readiness score  
   - Decision  
4. Use constraint analysis to understand blockers  

---

This system enforces **discipline, not prediction.**
    """
    )


# ── ABOUT ──────────────────────────────────────────────

with st.expander("About / Methodology"):
    st.markdown(
    """
### Deterministic Decision Framework

This system does not forecast.

It determines:
- When to act  
- When to wait  
- When to reduce risk  

---

### Core Inputs

- Signal strength  
- Timing trigger  
- Confirmation  
- Cross-market alignment  
- Crowding  
- Market health  
- Capital availability  

---

### Regime Model

- Preparation  
- Developing  
- Near Trigger  
- Actionable  

---

### Philosophy

Markets reward discipline.

> Act only when conditions justify it.
    """
    )
