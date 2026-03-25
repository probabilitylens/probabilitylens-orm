import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from io import BytesIO

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(layout="wide")

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
# INPUTS (0–100 SCALE)
# =========================
inputs = {
    "signal": signal * 100,
    "timing": timing * 100,
    "alignment": alignment * 100,
    "crowding": crowding * 100,
    "market_health": health * 100,
    "capital": capital * 100
}

# =========================
# ENGINE
# =========================
score = np.mean(list(inputs.values()))

if score < 50:
    regime = "PREPARATION"
    action = "NO POSITION"
elif score < 75:
    regime = "DEVELOPING"
    action = "WAIT"
else:
    regime = "NEAR TRIGGER"
    action = "ENTER"

# Conviction
dispersion = max(inputs.values()) - min(inputs.values())
if dispersion < 20:
    conviction = "HIGH"
elif dispersion < 40:
    conviction = "MEDIUM"
else:
    conviction = "LOW"

# =========================
# HEADER
# =========================
col1, col2 = st.columns([1, 4])

with col1:
    st.image("https://via.placeholder.com/200x100.png?text=LOGO", width=180)

with col2:
    st.title("ProbabilityLens")
    st.caption("Deterministic Macro Risk Engine — Oil Markets")
    st.markdown(f"**LAST UPDATE:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

st.divider()

# =========================
# SYSTEM OUTPUT (UPGRADED)
# =========================
colA, colB, colC, colD = st.columns(4)

colA.metric("REGIME", regime)
colB.metric("READINESS", f"{int(score)}%")
colC.metric("ACTION", action)
colD.metric("CONVICTION", conviction)

st.markdown("""
**Time Horizon:** 2–4 weeks  
**Expected Move:** +6–9% oil
""")

st.divider()

# =========================
# NARRATIVE (DYNAMIC)
# =========================
st.subheader("Decision Rationale")

if inputs["signal"] > 70 and inputs["alignment"] > 70:
    macro = "broad macro alignment is strengthening across demand indicators"
else:
    macro = "macro signals remain fragmented and lack confirmation"

if inputs["crowding"] < 40:
    positioning = "Positioning remains crowded, increasing downside volatility risk"
else:
    positioning = "Positioning remains supportive and not stretched"

narrative = f"""
The market is underestimating demand-driven downside pressure on oil prices, 
as {macro}. {positioning}, suggesting current pricing does not fully reflect 
the evolving macro environment.
"""

st.write(narrative)

# =========================
# SIGNAL ATTRIBUTION
# =========================
st.subheader("Signal Attribution")

weights = {
    "signal": 0.2,
    "timing": 0.15,
    "alignment": 0.2,
    "crowding": 0.15,
    "market_health": 0.15,
    "capital": 0.15
}

rows = []
for k, v in inputs.items():
    rows.append({
        "Factor": k.upper(),
        "Score": int(v),
        "Contribution": round(v * weights[k], 2),
        "Interpretation": "Positive" if v > 60 else "Neutral"
    })

df_attr = pd.DataFrame(rows)
st.dataframe(df_attr, use_container_width=True)

# =========================
# DATA (TEMPORARY)
# =========================
dates = pd.date_range(end=datetime.today(), periods=60)

price = np.cumsum(np.random.normal(0, 1, 60)) + 70
signal_series = np.clip(np.random.normal(0.3, 0.1, 60), 0, 1) * 100

df = pd.DataFrame({
    "Date": dates,
    "Price": price,
    "Signal": signal_series
})

# =========================
# CHART (IMPROVED)
# =========================
def create_chart(df):

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Date"],
        y=df["Price"],
        name="WTI",
        line=dict(color="#00C8FF", width=3)
    ))

    fig.add_trace(go.Scatter(
        x=df["Date"],
        y=df["Signal"],
        name="Signal",
        yaxis="y2",
        line=dict(color="#FF5A5F", dash="dot"),
        opacity=0.7
    ))

    fig.add_vline(x=df["Date"].iloc[-1], line_dash="dash")

    fig.update_layout(
        template="plotly_dark",
        height=500,
        paper_bgcolor="#0b0f14",
        plot_bgcolor="#0b0f14",
        yaxis=dict(title="WTI ($)"),
        yaxis2=dict(overlaying="y", side="right", title="Signal")
    )

    return fig

st.subheader("Oil Price Context + Signal Overlay")
fig = create_chart(df)
st.plotly_chart(fig, use_container_width=True)

# =========================
# SCENARIOS
# =========================
scenarios = pd.DataFrame({
    "Scenario": ["Base", "Bull", "Stress"],
    "Score": [int(score), 77, 25],
    "Regime": [regime, "NEAR TRIGGER", "PREPARATION"],
    "Action": [action, "WAIT", "NO POSITION"]
})

st.subheader("Scenario Comparison")
st.dataframe(scenarios, use_container_width=True)

# =========================
# TIMELINE
# =========================
timeline = pd.DataFrame({
    "Time": ["T-3", "T-2", "T-1", "Now"],
    "Score": [26, 34, 48, int(score)],
    "Regime": ["PREPARATION", "PREPARATION", "DEVELOPING", regime],
    "Action": ["NO POSITION", "NO POSITION", "WAIT", action]
})

st.subheader("Scenario Timeline")
st.dataframe(timeline, use_container_width=True)

# =========================
# PDF GENERATOR (UPGRADED)
# =========================
def generate_pdf():

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    elements = []

    elements.append(Paragraph("PROBABILITYLENS — OIL RISK MONITOR", styles["Title"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Executive Summary", styles["Heading2"]))
    elements.append(Paragraph(
        f"{regime} | {int(score)}% | {action}",
        styles["Normal"]
    ))

    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Decision Rationale", styles["Heading2"]))
    elements.append(Paragraph(narrative, styles["Normal"]))

    elements.append(Spacer(1, 12))

    img_bytes = fig.to_image(format="png")
    img_buffer = BytesIO(img_bytes)
    elements.append(Image(img_buffer, width=500, height=300))

    doc.build(elements)
    buffer.seek(0)

    return buffer

# =========================
# EXPORT
# =========================
st.subheader("Export")

if st.button("Export Report (PDF)"):
    pdf = generate_pdf()
    st.download_button(
        label="Download PDF",
        data=pdf,
        file_name="ProbabilityLens_Report.pdf",
        mime="application/pdf"
    )
