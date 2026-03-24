import streamlit as st

st.set_page_config(page_title="ProbabilityLens ORM", layout="wide")

st.title("ProbabilityLens — Oil Risk Monitor")
st.caption("Deterministic Macro Decision Engine")

st.divider()

# ── FSM ENGINE ───────────────────────────────────────────

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
        decision = "NONE"

    conditions = [
        state["edge_score"] == 2,
        state["timing_score"] == 1,
        state["confirmation_score"] == 1,
        state["network_score"] >= 0.5,
        state["reflex_score"] < 0.8,
        state["portfolio_headroom"] > 0,
        state["health"] >= 0.6
    ]

    decision_score = sum(conditions) / len(conditions)

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

    if decision_score < 0.4:
        status = "PREPARATION"
    elif decision_score < 0.7:
        status = "NEAR"
    elif decision_score < 1.0:
        status = "TRIGGERING"
    else:
        status = "ACTIONABLE"

    return {
        "decision": decision,
        "decision_score": decision_score,
        "transition_status": status,
        "trigger_gap": {"missing_conditions": missing},
        "state": state
    }


# ── INTERPRETATION ───────────────────────────────────────

def interpret(decision, score):
    if decision == "ADD":
        return "Conditions aligned — opportunity to increase exposure."
    if decision == "REDUCE":
        return "Risk increasing — consider reducing exposure."
    if decision == "EXIT":
        return "Market structure invalid — exit positions."
    if decision == "NONE" and score >= 0.7:
        return "Close to actionable — waiting for final confirmation."
    return "No clear opportunity — monitoring."


# ── MARKET BIAS ──────────────────────────────────────────

def market_bias(state):
    if state["edge_score"] == 2 and state["network_score"] >= 0.5:
        return "Bullish Bias"
    if state["health"] < 0.6 or state["reflex_score"] >= 0.8:
        return "Bearish Risk"
    return "Neutral"


# ── EXPLANATION ──────────────────────────────────────────

def explain(state, decision):

    if decision == "ADD":
        return ["All conditions aligned"]

    if decision == "REDUCE":
        reasons = []
        if state["reflex_score"] >= 0.8:
            reasons.append("Positioning is crowded")
        if state["health"] < 0.6:
            reasons.append("Market conditions deteriorating")
        return reasons

    if decision == "EXIT":
        return ["Insufficient market propagation"]

    # NONE
    reasons = []
    if state["edge_score"] != 2:
        reasons.append("Opportunity not strong")
    if state["timing_score"] != 1:
        reasons.append("Timing not aligned")
    if state["confirmation_score"] != 1:
        reasons.append("No confirmation signal")

    return reasons


# ── WHY NOT ADD ──────────────────────────────────────────

def explain_not_add(state, missing):

    mapping = {
        "edge_score != 2": f"Opportunity not strong ({state['edge_score']} → strong required)",
        "timing_score != 1": "Timing not aligned",
        "confirmation_score != 1": "Confirmation missing",
        "network_score < 0.5": f"Market alignment too weak ({state['network_score']:.2f})",
        "reflex_score >= 0.8": "Market overcrowded",
        "portfolio_headroom <= 0": "No available capital",
        "health < 0.6": "Market conditions weak",
    }

    explanations = [mapping[m] for m in missing]
    next_trigger = explanations[0] if explanations else "All conditions satisfied"

    return explanations, next_trigger


# ── LAYOUT ───────────────────────────────────────────────

left, center, right = st.columns([1, 1.5, 1], gap="large")


# ── INPUTS ───────────────────────────────────────────────

with left:
    st.subheader("Inputs")

    edge_score = st.selectbox("Opportunity Strength", [0, 1, 2])
    timing_score = st.selectbox("Timing Alignment", [0, 1])
    confirmation_score = st.selectbox("Market Confirmation", [0, 1])

    network_score = st.slider("Cross-Market Alignment", 0.0, 1.0, 0.5)
    reflex_score = st.slider("Crowding / Reflexivity", 0.0, 1.0, 0.3)
    health = st.slider("Market Health", 0.0, 1.0, 0.75)
    max_prop = st.slider("Portfolio Utilisation", 0.0, 100.0, 75.0)
    portfolio_headroom = st.number_input("Available Capital", 0.0, 1.0, 0.05)

    evaluate = st.button("Evaluate", use_container_width=True)


# ── RUN ENGINE ───────────────────────────────────────────

if evaluate:
    state = {
        "edge_score": edge_score,
        "timing_score": timing_score,
        "confirmation_score": confirmation_score,
        "network_score": network_score,
        "reflex_score": reflex_score,
        "health": health,
        "max_prop": max_prop,
        "portfolio_headroom": portfolio_headroom,
    }

    st.session_state.result = evaluate_fsm(state)


# ── OUTPUT ───────────────────────────────────────────────

with center:
    st.subheader("Decision Output")

    if "result" not in st.session_state:
        st.info("Run evaluation.")

    else:
        result = st.session_state.result
        decision = result["decision"]
        score = result["decision_score"]

        bias = market_bias(result["state"])

        st.markdown(f"### {bias}")

        if decision == "ADD":
            st.success(f"Decision: {decision}")
        elif decision == "REDUCE":
            st.warning(f"Decision: {decision}")
        elif decision == "EXIT":
            st.error(f"Decision: {decision}")
        else:
            st.info(f"Decision: {decision}")

        st.metric("Confidence", f"{score*100:.1f}%")

        st.divider()

        st.subheader("Interpretation")
        st.write(interpret(decision, score))

        st.divider()

        st.subheader("Key Drivers")
        for r in explain(result["state"], decision):
            st.write(f"• {r}")

        st.divider()

        with st.expander("Detailed State"):
            st.write(result["state"])


# ── WHY NOT ADD PANEL ────────────────────────────────────

with right:
    st.subheader("Why NOT ADD")

    if "result" not in st.session_state:
        st.info("Run evaluation.")

    else:
        result = st.session_state.result
        missing = result["trigger_gap"]["missing_conditions"]

        if not missing:
            st.success("All conditions satisfied.")

        else:
            explanations, next_trigger = explain_not_add(result["state"], missing)

            st.markdown("**Blocking factors:**")
            for e in explanations:
                st.error(e)

            st.divider()

            st.markdown("**Next trigger:**")
            st.success(next_trigger)
