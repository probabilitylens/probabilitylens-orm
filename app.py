import streamlit as st
import requests

API_URL = "http://localhost:8000/probability-lens/evaluate"

st.set_page_config(page_title="ProbabilityLens ORM", layout="wide")
st.title("ProbabilityLens ORM")
st.caption("Deterministic financial decision engine — FSM edition")

st.divider()

# ── Initialise session state defaults ─────────────────────────────────────────
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

# ── Human-readable trigger gap ─────────────────────────────────────────────────
_CONDITION_LABELS = {
    "edge_score != 2": "Edge not STRONG ({current} → 2)",
    "timing_score != 1.0": "Timing not ACTIVE",
    "confirmation_score != 1.0": "Confirmation not CONFIRMED",
    "network_score < 0.5": "Network below threshold (< 0.5, current: {current})",
    "reflex_score >= 0.8": "Reflexivity too high (≥ 0.8, current: {current})",
    "portfolio_headroom <= 0": "No portfolio headroom available (current: {current})",
    "health < 0.6": "Health below minimum (< 0.6, current: {current})",
}


def _humanise(raw: str) -> str:
    for key, template in _CONDITION_LABELS.items():
        if raw.startswith(key):
            current = ""
            if "(current:" in raw:
                current = raw.split("(current:")[1].rstrip(")").strip()
            return template.format(current=current)
    return raw


_NEXT_TRIGGER_LABELS = {
    "edge_score != 2":          "Edge must strengthen to STRONG ({current} → 2)",
    "timing_score != 1.0":      "Timing must reach ACTIVE",
    "confirmation_score != 1.0":"Confirmation must reach CONFIRMED",
    "network_score < 0.5":      "Network alignment must increase ({current} → ≥ 0.50)",
    "reflex_score >= 0.8":      "Reflexivity must decrease below 0.8 ({current} → < 0.80)",
    "portfolio_headroom <= 0":  "Portfolio headroom must be positive ({current} → > 0)",
    "health < 0.6":             "Health must recover above minimum ({current} → ≥ 0.60)",
}


def _next_trigger(decision: str, missing: list) -> str:
    if decision == "ADD":
        return "All trigger conditions satisfied."
    if not missing:
        return "All trigger conditions satisfied."
    raw = missing[0]
    for key, template in _NEXT_TRIGGER_LABELS.items():
        if raw.startswith(key):
            current = ""
            if "(current:" in raw:
                current = raw.split("(current:")[1].rstrip(")").strip()
            return "Next trigger: " + template.format(current=current)
    return f"Next trigger: {raw}"


# ── Interpretation logic ───────────────────────────────────────────────────────
def _interpret(decision: str, score: float) -> str:
    if decision == "ADD":
        return "Actionable — all conditions satisfied."
    if decision == "REDUCE":
        return "Risk deterioration — reducing exposure."
    if decision == "EXIT":
        return "Invalidated — exit conditions met."
    if decision == "NONE" and score >= 0.7:
        return "High readiness — conditions largely in place, waiting for final strengthening."
    return "Insufficient signal — no action warranted."

return "Insufficient signal — no action warranted."

def _explain(state: dict, decision: str) -> list:
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

def _load_preset(preset: str):
    if preset == "Bullish Supply Shock":
        return dict(edge_score=2, timing_score=1, confirmation_score=1,
                    network_score=0.7, reflex_score=0.3, health=0.8,
                    max_prop=80.0, portfolio_headroom=0.1)

    elif preset == "Demand Collapse":
        return dict(edge_score=2, timing_score=1, confirmation_score=1,
                    network_score=0.6, reflex_score=0.2, health=0.7,
                    max_prop=75.0, portfolio_headroom=0.1)

    elif preset == "Geopolitical Risk Spike":
        return dict(edge_score=1, timing_score=1, confirmation_score=0,
                    network_score=0.4, reflex_score=0.6, health=0.7,
                    max_prop=60.0, portfolio_headroom=0.05)

    elif preset == "Late Cycle Exhaustion":
        return dict(edge_score=1, timing_score=0, confirmation_score=0,
                    network_score=0.3, reflex_score=0.85, health=0.5,
                    max_prop=55.0, portfolio_headroom=0.0)

    return None

# ── Layout ─────────────────────────────────────────────────────────────────────
left, center, right = st.columns([1, 1.5, 1], gap="large")

# ── Left panel: inputs ────────────────────────────────────────────────────────
with left:
    st.subheader("Inputs")

    # Preset button — must appear BEFORE widgets so session_state is set first
    if st.button("⚡ Load Current Market Setup", use_container_width=True):
        st.session_state.edge_score = 1
        st.session_state.timing_score = 1
        st.session_state.confirmation_score = 1
        st.session_state.network_score = 0.65
        st.session_state.reflex_score = 0.50
        st.session_state.health = 0.88
        st.session_state.max_prop = 82.0
        st.session_state.portfolio_headroom = 0.05

    st.divider()

    # Discrete FSM inputs — selectbox only
    edge_score = st.selectbox(
        "edge_score",
        options=[0, 1, 2],
        key="edge_score",
        help="Discrete edge score. ADD requires == 2.",
    )
    timing_score = st.selectbox(
        "timing_score",
        options=[0, 1],
        key="timing_score",
        help="Timing alignment. ADD requires == 1.",
    )
    confirmation_score = st.selectbox(
        "confirmation_score",
        options=[0, 1],
        key="confirmation_score",
        help="Confirmation signal. ADD requires == 1.",
    )

    st.divider()

    # Continuous inputs — sliders
    network_score = st.slider(
        "network_score", 0.0, 1.0, step=0.01,
        key="network_score",
        help="Network alignment. ADD requires >= 0.5.",
    )
    reflex_score = st.slider(
        "reflex_score", 0.0, 1.0, step=0.01,
        key="reflex_score",
        help="Reflexivity/momentum. REDUCE if >= 0.8; ADD requires < 0.8.",
    )
    health = st.slider(
        "health", 0.0, 1.0, step=0.01,
        key="health",
        help="Position health. REDUCE if < 0.6; ADD requires >= 0.6.",
    )
    max_prop = st.slider(
        "max_prop (%)", 0.0, 100.0, step=0.5,
        key="max_prop",
        help="Maximum portfolio proportion. EXIT if < 50.",
    )
    portfolio_headroom = st.number_input(
        "portfolio_headroom",
        min_value=0.0,
        step=0.01,
        format="%.4f",
        key="portfolio_headroom",
        help="Available capacity. ADD requires > 0.",
    )

    st.divider()
    evaluate_btn = st.button("Evaluate", type="primary", use_container_width=True)

# ── Call API ──────────────────────────────────────────────────────────────────
if evaluate_btn:
    payload = {
        "max_prop": float(st.session_state.max_prop),
        "edge_score": int(st.session_state.edge_score),
        "timing_score": float(st.session_state.timing_score),
        "confirmation_score": float(st.session_state.confirmation_score),
        "network_score": float(st.session_state.network_score),
        "reflex_score": float(st.session_state.reflex_score),
        "portfolio_headroom": float(st.session_state.portfolio_headroom),
        "health": float(st.session_state.health),
    }
    try:
        resp = requests.post(API_URL, json=payload, timeout=5)
        resp.raise_for_status()
        st.session_state.result = resp.json()
        st.session_state.api_error = None
    except requests.exceptions.ConnectionError:
        st.session_state.api_error = "Cannot reach the API. Make sure the ProbabilityLens API workflow is running."
        st.session_state.result = None
    except Exception as exc:
        st.session_state.api_error = str(exc)
        st.session_state.result = None

# ── Center panel: decision output ─────────────────────────────────────────────
with center:
    st.subheader("Decision Output")

    if st.session_state.get("api_error"):
        st.error(st.session_state.api_error)

    elif "result" not in st.session_state or st.session_state.result is None:
        st.info("Set your inputs and click **Evaluate**.")

    else:
        result = st.session_state.result
        decision = result["decision"]
        score = result["decision_score"]
        status = result["transition_status"]

        # Decision — large and colour-coded
        if decision == "ADD":
            st.success(f"## ✅  {decision}")
        elif decision == "REDUCE":
            st.warning(f"## ⚠️  {decision}")
        elif decision == "EXIT":
            st.error(f"## 🚨  {decision}")
        else:
            st.info(f"## ⏸  {decision}")

        st.divider()

        # Score
        st.metric(
            label="Decision Score",
            value=f"{score * 100:.1f}%",
            help="Fraction of ADD conditions met. Informational only — does not affect the decision.",
        )

        st.divider()

        # Transition status
        status_icon = {
            "PREPARATION": "🔴",
            "NEAR": "🟠",
            "TRIGGERING": "🟡",
            "ACTIONABLE": "🟢",
        }
        icon = status_icon.get(status, "⚪")
        st.markdown("**Transition Status**")
        st.markdown(f"### {icon} {status}")

        st.divider()

        # Interpretation
        st.subheader("Interpretation")
        missing = result["trigger_gap"]["missing_conditions"]
        interpretation = _interpret(decision, score)
        next_trig = _next_trigger(decision, missing)
        if decision == "ADD":
            st.success(interpretation)
            st.success(next_trig)
        elif decision == "EXIT":
            st.error(interpretation)
            st.caption(next_trig)
        elif decision == "REDUCE":
            st.warning(interpretation)
            st.caption(next_trig)
        else:
            st.info(interpretation)
            st.caption(next_trig)

st.divider()

st.subheader("Why this decision")

state = result["state"]
reasons = _explain(state, decision)

for r in reasons:
    st.write(f"• {r}")

st.divider()

with st.expander("State details"):
    s = result["state"]
    st.table({
        "Field": list(s.keys()),
        "Value": [str(v) for v in s.values()]
    })

# ── Right panel: trigger gap ──────────────────────────────────────────────────
with right:
    st.subheader("Trigger Gap")

    if "result" not in st.session_state or st.session_state.result is None:
        st.info("Trigger gap will appear after evaluation.")

    else:
        result = st.session_state.result
        missing = result["trigger_gap"]["missing_conditions"]

        if not missing:
            st.success("All ADD conditions are satisfied.")
        else:
            st.markdown(f"**{len(missing)} condition(s) blocking ADD:**")
            for raw in missing:
                st.error(_humanise(raw))
