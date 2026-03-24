import streamlit as st

st.set_page_config(page_title="ProbabilityLens ORM", layout="wide")

# ── HERO / HEADER ───────────────────────────────────────

st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
st.image("logo.png", width=180)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("## Oil Risk Monitor")
st.caption("Deterministic Macro Decision Engine for Oil Markets")

st.markdown(
"""
Transforms macro conditions into **structured, rule-based trading decisions**.

This system does **not predict prices** — it identifies when conditions justify action.
"""
)

st.divider()

# ── PRESET SCENARIOS ─────────────────────────────────────

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


# ── ENGINE ──────────────────────────────────────────────

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


# ── INTERPRETATION ──────────────────────────────────────

def interpret(decision, score):
    if decision == "ADD":
        return "Conditions aligned — increase exposure."
    if decision == "REDUCE":
        return "Risk rising — reduce exposure."
    if decision == "EXIT":
        return "Invalid structure — exit positions."
    if score >= 0.7:
        return "Close to actionable — awaiting confirmation."
    return "Conditions not yet aligned — remain patient."


# ── WHY NOT ADD ─────────────────────────────────────────

def explain_not_add(state, missing):

    mapping = {
        "edge_score != 2": f"Opportunity not strong ({state['edge_score']} → strong required)",
        "timing_score != 1": "Timing not aligned",
        "confirmation_score != 1": "Confirmation missing",
        "network_score < 0.5": f"Alignment too weak ({state['network_score']:.2f})",
        "reflex_score >= 0.8": "Market overcrowded",
        "portfolio_headroom <= 0": "No capital available",
        "health < 0.6": "Market conditions weak"
    }

    trigger_map = {
        "edge_score != 2": "Strengthen opportunity",
        "timing_score != 1": "Wait for timing",
        "confirmation_score != 1": "Wait for confirmation",
        "network_score < 0.5": "Improve alignment",
        "reflex_score >= 0.8": "Reduce crowding",
        "portfolio_headroom <= 0": "Free capital",
        "health < 0.6": "Wait for stability"
    }

    explanations = [mapping[m] for m in missing]
    next_trigger = trigger_map.get(missing[0], explanations[0])

    return explanations, next_trigger


# ── MAIN LAYOUT ─────────────────────────────────────────

left, center, right = st.columns([1,1.5,1], gap="large")

# INPUTS
with left:
    st.subheader("Scenario")

    preset = st.selectbox(
        "Preset",
        ["Manual", "Bullish Supply Shock", "Demand Collapse",
         "Geopolitical Risk Spike", "Late Cycle Exhaustion"]
    )

    preset_data = load_preset(preset)

    if preset_data:
        state = preset_data
    else:
        state = {
            "edge_score": st.selectbox("Opportunity Strength", [0,1,2]),
            "timing_score": st.selectbox("Timing Alignment", [0,1]),
            "confirmation_score": st.selectbox("Confirmation", [0,1]),
            "network_score": st.slider("Cross-Market Alignment", 0.0,1.0,0.5),
            "reflex_score": st.slider("Crowding", 0.0,1.0,0.3),
            "health": st.slider("Market Health", 0.0,1.0,0.75),
            "max_prop": st.slider("Portfolio Used", 0.0,100.0,75.0),
            "portfolio_headroom": st.number_input("Free Capital", 0.0,1.0,0.05),
        }

    run = st.button("Evaluate", use_container_width=True)


# RUN ENGINE
if run:
    st.session_state.result = evaluate_fsm(state)


# OUTPUT
with center:
    st.subheader("Decision")

    if "result" not in st.session_state:
        st.info("Select scenario and evaluate.")

    else:
        r = st.session_state.result

        st.markdown(f"### {r['regime']}")
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

    if "result" not in st.session_state:
        st.info("Run evaluation.")

    else:
        missing = st.session_state.result["missing"]

        if not missing:
            st.success("All conditions satisfied")

        else:
            reasons, trigger = explain_not_add(
                st.session_state.result["state"], missing
            )

            for r in reasons:
                st.error(r)

            st.divider()
            st.success(f"Next trigger: {trigger}")


st.divider()

# ── HOW TO USE ──────────────────────────────────────────

with st.expander("How to Use"):

    st.markdown(
    """
1. Select a market scenario or input your own view  
2. Click **Evaluate**  
3. Review:
   - Market regime  
   - Readiness score  
   - Decision (ADD / WAIT / REDUCE / EXIT)  
4. Use **Why NOT ADD** to understand what is missing  

---

This system is designed to enforce **discipline and timing**, not prediction.
    """
    )


# ── ABOUT / METHODOLOGY ─────────────────────────────────

with st.expander("About / Methodology"):

    st.markdown(
    """
### Deterministic Decision Framework

This system is **not predictive**.

It defines:
- When to act  
- When to wait  
- When to reduce or exit  

---

### Core Logic

7 conditions drive decisions:

- Opportunity strength  
- Timing alignment  
- Market confirmation  
- Cross-market alignment  
- Crowding  
- Market health  
- Capital availability  

---

### Regime Model

- **Preparation** → weak setup  
- **Developing** → forming  
- **Near Trigger** → close  
- **Actionable** → aligned  

---

### Philosophy

Markets are not about prediction.

They are about:

> Acting only when conditions justify it.
    """
    )
