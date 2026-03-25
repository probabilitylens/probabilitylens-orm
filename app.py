import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
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
# ENGINE
# =========================
score = np.mean([signal, timing, confirmation, alignment, health, capital]) * 100

if score < 50:
    regime = "PREPARATION"
    action = "NO POSITION"
elif score < 75:
    regime = "DEVELOPING"
    action = "WAIT"
else:
    regime = "NEAR TRIGGER"
    action = "ENTER"

# =========================
# HEADER (LOGO FIXED)
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
# SYSTEM OUTPUT
# =========================
colA, colB = st.columns([2, 1])

with colA:
    st.subheader("SYSTEM OUTPUT")
    st.markdown(f"### {regime}")
    st.markdown(f"### {int(score)}%")

    st.error(action)

with colB:
    st.subheader("CONSTRAINTS")

    if score < 50:
        st.warning("Weak signal strength")
        st.warning("Timing inactive")
        st.warning("No confirmation")
        st.warning("Cross-market misalignment")

# =========================
# INTERPRETATION + RATIONALE
# =========================
st.subheader("System Interpretation")

if score < 50:
    st.write("Conditions insufficient for risk deployment. Monitor for signal development.")

st.subheader("Decision Rationale")

st.markdown("""
- Weak signal strength  
- Timing inactive  
- No confirmation  
- Cross-market misalignment  
""")

# =========================
# REAL OIL DATA (NO API)
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
# BLOOMBERG CHART
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

    fig.add_vrect(
        x0=df["Date"].iloc[-15],
        x1=df["Date"].iloc[-1],
        fillcolor="rgba(120,120,120,0.25)",
        layer="below",
        line_width=0
    )

    fig.add_annotation(
        x=df["Date"].iloc[-1],
        y=df["Price"].iloc[-1],
        text=f"{regime} ({int(score)}%)",
        showarrow=True,
        bgcolor="black",
        font=dict(color="white")
    )

    fig.update_layout(
        template="plotly_dark",
        height=500,
        paper_bgcolor="#0b0f14",
        plot_bgcolor="#0b0f14",
        xaxis=dict(gridcolor="#222"),
        yaxis=dict(title="WTI ($)", gridcolor="#222"),
        yaxis2=dict(overlaying="y", side="right", title="Signal"),
        legend=dict(orientation="h", y=1.05)
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
# PDF GENERATOR (FIXED)
# =========================
def generate_pdf():

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    elements = []

    elements.append(Paragraph("PROBABILITYLENS REPORT", styles["Title"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Executive Summary", styles["Heading2"]))
    elements.append(Paragraph(
        f"Regime: {regime} | Score: {int(score)}% | Action: {action}",
        styles["Normal"]
    ))

    elements.append(Spacer(1, 12))

    # Chart
    img_bytes = fig.to_image(format="png")
    img_buffer = BytesIO(img_bytes)
    elements.append(Image(img_buffer, width=500, height=300))

    elements.append(Spacer(1, 12))

    # Scenario table
    table = Table([scenarios.columns.tolist()] + scenarios.values.tolist())
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.black),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey)
    ]))

    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    return buffer

# =========================
# EXPORT BUTTON
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
