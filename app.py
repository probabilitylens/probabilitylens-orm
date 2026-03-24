import streamlit as st

st.set_page_config(page_title="ProbabilityLens ORM", layout="wide")

st.title("ProbabilityLens — Oil Risk Monitor")
st.caption("Deterministic Macro Decision Engine (FSM-based)")

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
        return "Conditions aligned for position expansion."
    if decision == "REDUCE":
        return "Risk increasing — reduce exposure."
    if decision == "EXIT":
        return "No valid environment — exit positions."
    if decision == "NONE" and score >= 0.7:
        return "Close to actionable — waiting for final trigger."
    return "Monitoring — no action."


# ── EXPLANATION ──────────────────────────────────────────

def explain(state, decision):
    if decision == "ADD":
        return ["All ADD conditions satisfied"]

    if decision == "REDUCE":
        reasons = []
        if state["reflex_score"] >= 0.8:
            reasons.append("Reflex risk elevated")
        if state["health"] < 0.6:
            reasons.append("Health deteriorating")
        return reasons

    if decision == "EXIT":
        return ["Propagation insufficient (<50)"]

    return ["Conditions not sufficient for action"]


# ── WHY NOT ADD ──────────────────────────────────────────

def explain_not_add(state, missing):

    mapping = {
        "edge_score != 2": f"Edge not strong ({state['edge_score']} → 2 required)",
        "timing_score != 1": "Timing not active",
        "confirmation_score != 1": "Confirmation missing",
        "network_score < 0.5": f"Network too weak ({state['network_score']:.2f} < 0.50)",
        "reflex_score >= 0.8": f"Reflex risk too high ({state['reflex_score']:.2f} ≥ 0.80)",
        "portfolio_headroom <= 0": "No portfolio headroom",
        "health < 0.6": f"Health too low ({state['health']:.2f} < 0.60)",
    }

    explanations = [mapping[m] for m in missing]

    next_trigger = explanations[0] if explanations else "All conditions satisfied"

    return explanations, next_trigger


# ── LAYOUT ───────────────────────────────────────────────

left, center, right = st.columns([1, 1.5, 1], gap="large")


# ── INPUTS ───────────────────────────────────────────────

with left:
    st.subheader("Inputs")

    edge_score = st.selectbox("edge_score", [0, 1, 2])
    timing_score = st.selectbox("timing_score", [0, 1])
    confirmation_score = st.selectbox("confirmation_score", [0, 1])

    network_score = st.slider("network_score", 0.0, 1.0, 0.5)
    reflex_score = st.slider("reflex_score", 0.0, 1.0, 0.3)
    health = st.slider("health", 0.0, 1.0, 0.75)
    max_prop = st.slider("max_prop", 0.0, 100.0, 75.0)
    portfolio_headroom = st.number_input("portfolio_headroom", 0.0, 1.0, 0.05)

    evaluate = st.button("Evaluate")


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

        if decision == "ADD":
            st.success(f"Decision: {decision}")
        elif decision == "REDUCE":
            st.warning(f"Decision: {decision}")
        elif decision == "EXIT":
            st.error(f"Decision: {decision}")
        else:
            st.info(f"Decision: {decision}")

        st.metric("Score", f"{score*100:.1f}%")

        st.divider()

        st.subheader("Interpretation")
        st.write(interpret(decision, score))

        st.divider()

        st.subheader("Why this decision")
        for r in explain(result["state"], decision):
            st.write(f"• {r}")

        st.divider()

        with st.expander("State details"):
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
            st.success("All ADD conditions satisfied.")

        else:
            explanations, next_trigger = explain_not_add(result["state"], missing)

            st.markdown("**ADD blocked because:**")
            for e in explanations:
                st.error(e)

            st.divider()

            st.markdown("**Next trigger:**")
            st.success(next_trigger)
