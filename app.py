import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
import base64

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(layout="wide")

# =========================
# LOGO (NO CROPPING EVER)
# =========================
def render_logo():
    with open("logo.png", "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    st.markdown(f"""
        <div style="display:flex;align-items:center;gap:20px;">
            <img src="data:image/png;base64,{encoded}" width="160"/>
            <div>
                <h2 style="margin:0;">ProbabilityLens</h2>
                <span style="color:gray;">Deterministic Macro Risk Engine — Oil Markets</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

render_logo()

st.markdown("LAST UPDATE: 2026-03-25 04:10 UTC")
st.divider()

# =========================
# SIDEBAR INPUTS
# =========================
st.sidebar.title("Input Parameters")

signal = st.sidebar.slider("Signal", 0.0, 1.0, 0.3)
timing = st.sidebar.slider("Timing", 0.0, 1.0, 0.3)
confirmation = st.sidebar.slider("Confirmation", 0.0, 1.0, 0.3)
alignment = st.sidebar.slider("Alignment", 0.0, 1.0, 0.3)
crowding = st.sidebar.slider("Crowding", 0.0, 1.0, 0.5)
health = st.sidebar.slider("Market Health", 0.0, 1.0, 0.5)
capital = st.sidebar.slider("Capital Availability", 0.0, 1.0, 0.5)

# =========================
# ENGINE
# =========================
score = (
    signal*0.2 + timing*0.2 + confirmation*0.2 +
    alignment*0.15 + (1-crowding)*0.1 + health*0.1 + capital*0.05
)
score_pct = int(score * 100)

if score_pct < 40:
    regime = "PREPARATION"
    action = "NO POSITION"
elif score_pct < 70:
    regime = "DEVELOPING"
    action = "WAIT"
else:
    regime = "TRIGGER"
    action = "ENTER"

# =========================
# OUTPUT
# =========================
col1, col2 = st.columns([2,1])

with col1:
    st.subheader("SYSTEM OUTPUT")
    st.caption("MARKET REGIME")
    st.markdown(f"## {regime}")
    st.metric("Readiness Score", f"{score_pct}%")

    st.markdown(f"""
        <div style="background:#f5c6c6;padding:10px;border-radius:8px;">
        {action}
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.subheader("CONSTRAINTS")
    constraints = []
    if signal < 0.5: constraints.append("Weak signal strength")
    if timing < 0.5: constraints.append("Timing inactive")
    if confirmation < 0.5: constraints.append("No confirmation")
    if alignment < 0.5: constraints.append("Cross-market misalignment")

    for c in constraints:
        st.warning(c)

# =========================
# INTERPRETATION
# =========================
st.subheader("System Interpretation")
st.write("Conditions insufficient for risk deployment. Monitor for signal development.")

st.subheader("Decision Rationale")
for c in constraints:
    st.markdown(f"- {c}")

# =========================
# BLOOMBERG-STYLE CHART
# =========================
st.subheader("Oil Price Context + Signal Overlay")

dates = pd.date_range(end=pd.Timestamp.today(), periods=60)
price = np.cumsum(np.random.normal(0,1,60)) + 70
returns = pd.Series(price).pct_change().fillna(0)

signal_series = returns.rolling(5).mean()
signal_series = (signal_series - signal_series.min()) / (signal_series.max() - signal_series.min() + 1e-9)
signal_series = signal_series * 100 * signal

df = pd.DataFrame({"Date":dates, "Price":price, "Signal":signal_series})

fig = go.Figure()

# price
fig.add_trace(go.Scatter(
    x=df["Date"], y=df["Price"],
    name="WTI",
    line=dict(color="#00D1FF", width=2)
))

# signal
fig.add_trace(go.Scatter(
    x=df["Date"], y=df["Signal"],
    name="Signal",
    yaxis="y2",
    line=dict(color="#FF4136", dash="dot")
))

# regime shading
if regime == "PREPARATION":
    fig.add_vrect(x0=df["Date"].iloc[-20], x1=df["Date"].iloc[-1],
                  fillcolor="gray", opacity=0.2, line_width=0)

# layout
fig.update_layout(
    template="plotly_dark",
    height=500,
    yaxis=dict(title="WTI ($)", gridcolor="#333"),
    yaxis2=dict(title="Signal", overlaying="y", side="right"),
    legend=dict(orientation="h"),
    margin=dict(l=10,r=10,t=10,b=10)
)

st.plotly_chart(fig, use_container_width=True)

# =========================
# SCENARIOS
# =========================
st.subheader("Scenario Comparison")

scenarios = pd.DataFrame({
    "Scenario":["Base","Bull","Stress"],
    "Score":[score_pct,77,25],
    "Regime":["PREPARATION","NEAR TRIGGER","PREPARATION"],
    "Action":["NO POSITION","WAIT","NO POSITION"]
})
st.dataframe(scenarios)

# =========================
# TIMELINE
# =========================
st.subheader("Scenario Timeline")

timeline = pd.DataFrame({
    "Time":["T-3","T-2","T-1","Now"],
    "Score":[26,34,48,score_pct],
    "Regime":["PREPARATION","PREPARATION","DEVELOPING",regime],
    "Action":["NO POSITION","NO POSITION","WAIT",action]
})
st.dataframe(timeline)

# =========================
# INVESTOR-GRADE PDF
# =========================
def generate_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    elements = []

    elements.append(Paragraph("ProbabilityLens Report", styles["Title"]))
    elements.append(Spacer(1,12))

    elements.append(Paragraph(f"Regime: {regime}", styles["Normal"]))
    elements.append(Paragraph(f"Score: {score_pct}%", styles["Normal"]))
    elements.append(Paragraph(f"Action: {action}", styles["Normal"]))

    elements.append(Spacer(1,12))
    elements.append(Paragraph("Scenario Comparison", styles["Heading2"]))

    table_data = [scenarios.columns.tolist()] + scenarios.values.tolist()
    table = Table(table_data)
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.grey),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),1,colors.black)
    ]))
    elements.append(table)

    elements.append(Spacer(1,12))
    elements.append(Paragraph("Timeline", styles["Heading2"]))

    table_data2 = [timeline.columns.tolist()] + timeline.values.tolist()
    table2 = Table(table_data2)
    table2.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.grey),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),1,colors.black)
    ]))
    elements.append(table2)

    doc.build(elements)
    buffer.seek(0)
    return buffer

# =========================
# DOWNLOAD
# =========================
if st.button("Export Report (PDF)"):
    pdf = generate_pdf()
    st.download_button("Download PDF", pdf, "ProbabilityLens_Report.pdf")
