import streamlit as st
import requests

API_URL = "http://localhost:8000/probability-lens/evaluate"

st.set_page_config(page_title="ProbabilityLens ORM", layout="wide")

st.title("ProbabilityLens — Oil Risk Monitor")
st.caption("Deterministic Macro Decision Engine (FSM-based)")

st.divider()

# ── Defaults ─────────────────────────────────
_DEFAULTS = {
    "edge_score": 1,
    "timing_score": 1,
    "confirmation_score": 1,
    "network_score": 0.50,
    "reflex_score": 0.30,
    "health": 0.75,
    "max_prop": 75.0,
    "portfolio_headroom": 0.05,
}

for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Interpretation ───────────────────────────
def _interpret(decision: str, score: float) -> str:
    if decision == "ADD":
        return "Actionable — all conditions satisfied."
    if decision == "REDUCE":
        return "Risk deterioration — reducing exposure."
    if decision == "EXIT":
        return "Invalidated — exit conditions met."
    if decision == "NONE" and score >= 0.7:
        return "High readiness — waiting for final confirmation."
    return "Insufficient signal — no action warranted."


# ── Explanation ──────────────────────────────
def _explain(state: dict, decision: str):
    reasons = []

    if decision == "ADD":
        if state["edge_score"] == 2:
            reasons.append("Strong edge identified")
        if state["timing_score"] == 1:
            reasons.append("Timing conditions favorable")
        if state["confirmation_score"] == 1:
            reasons.append("Market confirmation present")
        if state["network_score"] >= 0.5:
            reasons.append("Cross-market alignment supportive")
        if state["reflex_score"] < 0.8:
            reasons.append("No overcrowding / reflex risk")
        if state["health"] >= 0.6:
            reasons.append("System health stable")

    elif decision == "REDUCE":
        if state["reflex_score"] >= 0.8:
            reasons.append("Crowded positioning / reflex risk elevated")
        if state["health"] < 0.6:
            reasons.append("System health deteriorating")

    elif decision == "EXIT":
        reasons.append("Insufficient propagation (<50)")

    else:
        reasons.append("Conditions not sufficient for action")

    return reasons


# ── Layout ───────────────────────────────────
left, center, right = st.columns([1, 1.5, 1], gap="large")


# ── Inputs ───────────────────────────────────
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


# ── API Call ────────────────────────────────
if evaluate:
    payload = {
        "max_prop": max_prop,
        "edge_score": edge_score,
        "timing_score": timing_score,
        "confirmation_score": confirmation_score,
        "network_score": network_score,
        "reflex_score": reflex_score,
        "portfolio_headroom": portfolio_headroom,
        "health": health,
    }

    try:
        res = requests.post(API_URL, json=payload).json()
        st.session_state.result = res
    except:
        st.session_state.result = None


# ── Output ───────────────────────────────────
with center:
    st.subheader("Decision Output")

    if "result" not in st.session_state or st.session_state.result is None:
        st.info("Run evaluation.")

    else:
        result = st.session_state.result
        decision = result["decision"]
        score = result["decision_score"]

        st.success(f"Decision: {decision}")
        st.metric("Score", f"{score*100:.1f}%")

        st.divider()

        st.subheader("Interpretation")
        st.write(_interpret(decision, score))

        st.divider()

        st.subheader("Why this decision")
        reasons = _explain(result["state"], decision)

        for r in reasons:
            st.write(f"• {r}")

        st.divider()

        with st.expander("State details"):
            st.write(result["state"])


# ── Trigger Gap ─────────────────────────────
with right:
    st.subheader("Trigger Gap")

    if "result" not in st.session_state or st.session_state.result is None:
        st.info("Run evaluation.")

    else:
        missing = result["trigger_gap"]["missing_conditions"]

        if not missing:
            st.success("All conditions satisfied.")
        else:
            for m in missing:
                st.error(m)
