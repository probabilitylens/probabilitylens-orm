import streamlit as st
from datetime import datetime
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(layout="wide")

# -----------------------------------
# STYLE
# -----------------------------------
st.markdown("""
<style>
[data-testid="stSidebar"] {
    background-color: #0f172a;
}
[data-testid="stSidebar"] * {
    color: #cbd5f5 !important;
}
.block-container {
    padding-top: 1.5rem;
    padding-left: 3rem;
    padding-right: 3rem;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------------
# HEADER (FIXED)
# -----------------------------------
col_logo, col_title = st.columns([1, 6])

with col_logo:
    st.image("logo.png", width=140)

with col_title:
    st.markdown("### ProbabilityLens")
    st.caption("Deterministic Macro Risk Engine — Oil Markets")

st.write(f"**LAST UPDATE:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
st.divider()

# -----------------------------------
# INPUTS
# -----------------------------------
st.sidebar.header("Input Parameters")

signal = st.sidebar.slider("Signal", 0.0, 1.0, 0.3)
timing = st.sidebar.slider("Timing", 0.0, 1.0, 0.3)
confirmation = st.sidebar.slider("Confirmation", 0.0, 1.0, 0.3)
alignment = st.sidebar.slider("Alignment", 0.0, 1.0, 0.3)
crowding = st.sidebar.slider("Crowding", 0.0, 1.0, 0.5)
health = st.sidebar.slider("Market Health", 0.0, 1.0, 0.5)
capital = st.sidebar.slider("Capital Availability", 0.0, 1.0, 0.5)

# -----------------------------------
# ENGINE
# -----------------------------------
def compute_decision(signal, timing, confirmation, alignment, crowding, health, capital):
    score = (
        signal * 0.2 +
        timing * 0.2 +
        confirmation * 0.2 +
        alignment * 0.2 +
        crowding * 0.05 +
        health * 0.075 +
        capital * 0.075
    )

    score_pct = int(score * 100)

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

    return score_pct, regime, action

score_pct, regime, action = compute_decision(
    signal, timing, confirmation, alignment, crowding, health, capital
)

# -----------------------------------
# OUTPUT
# -----------------------------------
col2, col3 = st.columns([1.7, 1.3])

with col2:
    st.subheader("SYSTEM OUTPUT")

    st.caption("MARKET REGIME")
    st.markdown(f"## {regime}")

    st.caption("READINESS SCORE")
    st.markdown(f"# {score_pct}%")

    st.caption("RECOMMENDED ACTION")

    if action == "NO POSITION":
        st.error(action)
    elif action == "WAIT":
        st.warning(action)
    else:
        st.success(action)

    st.caption("SYSTEM INTERPRETATION")

    if action == "NO POSITION":
        interpretation = "Conditions insufficient for risk deployment."
    elif action == "WAIT":
        interpretation = "Setup forming. Await confirmation."
    else:
        interpretation = "Conditions aligned. Add exposure."

    st.write(interpretation)

    # Rationale
    st.caption("DECISION RATIONALE")

    rationale = []
    if signal < 0.5:
        rationale.append("Weak signal strength")
    if timing < 0.5:
        rationale.append("Timing inactive")
    if confirmation < 0.5:
        rationale.append("No confirmation")
    if alignment < 0.5:
        rationale.append("Cross-market misalignment")
    if crowding > 0.7:
        rationale.append("Crowded positioning risk")

    for r in rationale:
        st.write(f"- {r}")

with col3:
    st.subheader("CONSTRAINTS")

    constraints = []
    if signal < 0.5:
        constraints.append("No structural edge")
    if timing < 0.5:
        constraints.append("Timing inactive")
    if confirmation < 0.5:
        constraints.append("No confirmation")

    for c in constraints:
        st.error(c)

# -----------------------------------
# REAL OIL DATA
# -----------------------------------
st.divider()
st.subheader("Oil Price Context + Signal Overlay")

oil = yf.download("CL=F", period="3mo", interval="1d")
oil = oil[['Close']].dropna()
oil.rename(columns={"Close": "Oil Price"}, inplace=True)

# dynamic signal (NOT flat)
oil["Signal"] = oil["Oil Price"].pct_change().rolling(5).mean()
oil["Signal"] = oil["Signal"].fillna(0)

# normalize
oil["Signal"] = (oil["Signal"] - oil["Signal"].min()) / (
    oil["Signal"].max() - oil["Signal"].min()
)
oil["Signal"] = oil["Signal"] * 100 * signal

# -----------------------------------
# BLOOMBERG STYLE CHART
# -----------------------------------
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=oil.index,
    y=oil["Oil Price"],
    name="WTI Oil",
    line=dict(width=2),
))

fig.add_trace(go.Scatter(
    x=oil.index,
    y=oil["Signal"],
    name="Signal",
    line=dict(dash="dot"),
    yaxis="y2"
))

fig.update_layout(
    template="plotly_dark",
    height=420,
    yaxis=dict(title="Oil Price"),
    yaxis2=dict(
        title="Signal",
        overlaying="y",
        side="right"
    ),
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------------
# SCENARIO COMPARISON
# -----------------------------------
st.divider()
st.subheader("Scenario Comparison")

scenarios = {
    "Base": (signal, timing, confirmation, alignment, crowding, health, capital),
    "Bull": (0.8, 0.8, 0.8, 0.8, 0.6, 0.7, 0.7),
    "Stress": (0.2, 0.2, 0.2, 0.2, 0.7, 0.4, 0.4),
}

rows = []
for name, vals in scenarios.items():
    s, r, a = compute_decision(*vals)
    rows.append([name, s, r, a])

df = pd.DataFrame(rows, columns=["Scenario", "Score", "Regime", "Action"])
st.dataframe(df, use_container_width=True, hide_index=True)

# -----------------------------------
# TIMELINE
# -----------------------------------
st.divider()
st.subheader("Scenario Timeline")

timeline = [
    ("T-3", 0.2, 0.2, 0.2, 0.2),
    ("T-2", 0.3, 0.3, 0.3, 0.3),
    ("T-1", 0.45, 0.5, 0.45, 0.5),
    ("Now", signal, timing, confirmation, alignment),
]

t_rows = []
for t, s, ti, c, a in timeline:
    sc, rg, ac = compute_decision(s, ti, c, a, crowding, health, capital)
    t_rows.append([t, sc, rg, ac])

t_df = pd.DataFrame(t_rows, columns=["Time", "Score", "Regime", "Action"])
st.dataframe(t_df, use_container_width=True, hide_index=True)

# -----------------------------------
# PDF EXPORT
# -----------------------------------
def generate_pdf():
    doc = SimpleDocTemplate("/mnt/data/report.pdf")
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("ProbabilityLens Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Regime: {regime}", styles["Normal"]))
    elements.append(Paragraph(f"Score: {score_pct}%", styles["Normal"]))
    elements.append(Paragraph(f"Action: {action}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Interpretation:", styles["Heading3"]))
    elements.append(Paragraph(interpretation, styles["Normal"]))

    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Rationale:", styles["Heading3"]))

    for r in rationale:
        elements.append(Paragraph(f"- {r}", styles["Normal"]))

    doc.build(elements)
    return "/mnt/data/report.pdf"

if st.button("Export Report (PDF)"):
    file_path = generate_pdf()
    with open(file_path, "rb") as f:
        st.download_button("Download PDF", f, file_name="ProbabilityLens_Report.pdf")
