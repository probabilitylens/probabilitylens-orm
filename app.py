import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from io import BytesIO

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

import plotly.io as pio

st.set_page_config(layout="wide")

# =========================
# LOAD WTI DATA (FIXED)
# =========================
def load_wti():
    try:
        df = pd.read_excel("data/wti.xls")

        # Take first two columns only
        df = df.iloc[:, :2]
        df.columns = ["Date", "Price"]

        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna()

        # Keep recent data only
        df = df.sort_values("Date").tail(120)

        return df

    except:
        dates = pd.date_range(end=datetime.today(), periods=60)
        price = np.cumsum(np.random.normal(0, 1, 60)) + 70
        return pd.DataFrame({"Date": dates, "Price": price})

# =========================
# INPUTS
# =========================
st.sidebar.title("Input Parameters")

signal = st.sidebar.slider("Signal", 0.0, 1.0, 0.3)
timing = st.sidebar.slider("Timing", 0.0, 1.0, 0.3)
confirmation = st.sidebar.slider("Confirmation", 0.0, 1.0, 0.3)
alignment = st.sidebar.slider("Alignment", 0.0, 1.0, 0.3)
crowding = st.sidebar.slider("Crowding", 0.0, 1.0, 0.5)
health = st.sidebar.slider("Market Health", 0.0, 1.0, 0.5)
capital = st.sidebar.slider("Capital Availability", 0.0, 1.0, 0.5)

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

dispersion = max(inputs.values()) - min(inputs.values())
conviction = "HIGH" if dispersion < 20 else "MEDIUM" if dispersion < 40 else "LOW"

# =========================
# EXPECTED MOVE (MODEL)
# =========================
base_move = (score - 50) / 5
alignment_boost = (inputs["alignment"] - 50) / 10
signal_boost = (inputs["signal"] - 50) / 10

expected_move = round(base_move + alignment_boost + signal_boost, 1)
expected_move = max(min(expected_move, 12), -12)

expected_move_str = f"{expected_move:+}%"

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
# DECISION BLOCK
# =========================
colA, colB, colC, colD = st.columns(4)

colA.metric("REGIME", regime)
colB.metric("READINESS", f"{int(score)}%")
colC.metric("ACTION", action)
colD.metric("CONVICTION", conviction)

st.markdown(f"""
**Time Horizon:** 2–4 weeks  
**Expected Move:** {expected_move_str}
""")

st.divider()

# =========================
# NARRATIVE
# =========================
if inputs["signal"] > 70 and inputs["alignment"] > 70:
    macro = "broad macro alignment is strengthening across demand indicators"
else:
    macro = "macro signals remain fragmented and lack confirmation"

if inputs["crowding"] < 40:
    positioning = "Positioning remains crowded, increasing downside volatility risk"
else:
    positioning = "Positioning remains supportive"

narrative = f"""
The market is underestimating demand-driven downside pressure on oil prices, 
as {macro}. {positioning}, suggesting current pricing does not fully reflect 
the evolving macro environment.
"""

st.subheader("Decision Rationale")
st.write(narrative)

# =========================
# CHART (REAL DATA)
# =========================
df = load_wti()

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df["Date"],
    y=df["Price"],
    name="WTI",
    line=dict(color="#00C8FF", width=3)
))

fig.add_vline(x=df["Date"].iloc[-1], line_dash="dash")

fig.update_layout(
    template="plotly_dark",
    height=500,
    yaxis=dict(title="WTI ($)")
)

st.subheader("Oil Price Context")
st.plotly_chart(fig, use_container_width=True)

# =========================
# PDF (FIXED + UPGRADED)
# =========================
def generate_pdf():

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    elements = []

    elements.append(Paragraph("PROBABILITYLENS — OIL RISK MONITOR", styles["Title"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Decision", styles["Heading2"]))
    elements.append(Paragraph(
        f"{regime} | {int(score)}% | {action} | Conviction: {conviction}",
        styles["Normal"]
    ))

    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Trade Expression", styles["Heading2"]))
    elements.append(Paragraph(
        f"""
        Position: {"LONG" if expected_move > 0 else "SHORT"} WTI<br/>
        Horizon: 2–4 weeks<br/>
        Expected Move: {expected_move_str}<br/>
        Risk: Positioning unwind / macro reversal
        """,
        styles["Normal"]
    ))

    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Executive Summary", styles["Heading2"]))
    elements.append(Paragraph(narrative, styles["Normal"]))

    elements.append(Spacer(1, 12))

    # Chart export (kaleido)
    img_bytes = pio.to_image(fig, format="png")
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
