import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
import tempfile
import os

st.set_page_config(layout="wide")

# =========================
# 🖼 LOGO (FIXED)
# =========================
logo_path = "Logo.png"

if os.path.exists(logo_path):
    st.image(logo_path, width=180)
else:
    st.warning("Logo not found")

# =========================
# 📥 DATA LOADER (FIXED)
# =========================
@st.cache_data
def load_wti_data():
    try:
        df = pd.read_excel("data/wti.xls", sheet_name="Data 1")

        df = df.iloc[:, :2]
        df.columns = ["Date", "Price"]

        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

        df = df.dropna()

        if df.empty:
            return pd.DataFrame()

        df = df.sort_values("Date")
        df = df.tail(120)

        return df

    except Exception as e:
        st.error(f"Data loading failed: {e}")
        return pd.DataFrame()


df = load_wti_data()

# =========================
# 🚨 VALIDATION
# =========================
if df is None or df.empty:
    st.error("WTI dataset is empty — check Excel parsing.")
    st.stop()

if len(df) < 10:
    st.error("Not enough data after cleaning.")
    st.stop()

if df["Price"].iloc[-1] < 50:
    st.warning("⚠️ WTI price looks too low — possible wrong dataset")

if df["Date"].max() < datetime.today() - timedelta(days=5):
    st.warning("⚠️ WTI data may be stale")

# =========================
# 🎛 INPUTS
# =========================
st.sidebar.title("Input Parameters")

signal = st.sidebar.slider("Signal", 0.0, 1.0, 0.3)
timing = st.sidebar.slider("Timing", 0.0, 1.0, 0.3)
confirmation = st.sidebar.slider("Confirmation", 0.0, 1.0, 0.3)
alignment = st.sidebar.slider("Alignment", 0.0, 1.0, 0.3)
crowding = st.sidebar.slider("Crowding", 0.0, 1.0, 0.5)
market_health = st.sidebar.slider("Market Health", 0.0, 1.0, 0.5)
capital = st.sidebar.slider("Capital Availability", 0.0, 1.0, 0.5)

inputs = {
    "Signal": signal,
    "Timing": timing,
    "Confirmation": confirmation,
    "Alignment": alignment,
    "Crowding": crowding,
    "Market Health": market_health,
    "Capital": capital
}

values = np.array(list(inputs.values()))

# =========================
# 🧠 MODEL
# =========================
score = values.mean() * 100

if score < 50:
    regime = "PREPARATION"
    action = "NO POSITION"
elif score < 75:
    regime = "DEVELOPING"
    action = "WAIT"
else:
    regime = "NEAR TRIGGER"
    action = "ENTER"

conviction = int((1 - np.std(values)) * 100)

expected_move = np.clip(
    (score / 100) * (alignment + signal) * 10,
    -12, 12
)

# =========================
# 🧾 TRADE EXPRESSION
# =========================
direction = "SHORT" if signal > 0.6 else "LONG" if signal < 0.4 else "NEUTRAL"

trade_expression = f"""
Direction: {direction}
Horizon: 2–6 weeks
Conviction: {conviction}%
"""

# =========================
# 📊 CHART
# =========================
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df["Date"],
    y=df["Price"],
    mode="lines",
    line=dict(color="white", width=3),
    name="WTI"
))

fig.add_vline(
    x=df["Date"].max(),
    line_width=2,
    line_color="white"
)

fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="#0b0f14",
    plot_bgcolor="#0b0f14",
    font=dict(color="#d1d5db"),
    margin=dict(l=20, r=20, t=40, b=20),
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=False)
)

# =========================
# 📊 SIGNAL ATTRIBUTION
# =========================
attr_df = pd.DataFrame({
    "Factor": list(inputs.keys()),
    "Score": list(inputs.values()),
    "Contribution": values / values.sum()
})

# =========================
# 🖥 UI
# =========================
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Decision")

    st.metric("Regime", regime)
    st.metric("Action", action)
    st.metric("Conviction", f"{conviction}%")
    st.metric("Expected Move", f"{expected_move:.1f}%")

    st.subheader("Trade Expression")
    st.write(trade_expression)

with col2:
    st.subheader("WTI Price")
    st.plotly_chart(fig, use_container_width=True)

# Attribution table
st.subheader("Signal Attribution")
st.dataframe(attr_df, use_container_width=True)

# =========================
# 📄 PDF EXPORT (WORKING)
# =========================
def generate_pdf():
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(temp_file.name, pagesize=letter)

    styles = getSampleStyleSheet()
    content = []

    content.append(Paragraph("ProbabilityLens – Oil Risk Monitor", styles["Title"]))
    content.append(Spacer(1, 12))

    content.append(Paragraph(f"Regime: {regime}", styles["Normal"]))
    content.append(Paragraph(f"Action: {action}", styles["Normal"]))
    content.append(Paragraph(f"Conviction: {conviction}%", styles["Normal"]))
    content.append(Paragraph(f"Expected Move: {expected_move:.1f}%", styles["Normal"]))

    content.append(Spacer(1, 12))
    content.append(Paragraph("Trade Expression", styles["Heading2"]))
    content.append(Paragraph(trade_expression, styles["Normal"]))

    doc.build(content)

    return temp_file.name


pdf_path = generate_pdf()

with open(pdf_path, "rb") as f:
    st.download_button(
        "Download PDF Report",
        f,
        file_name="oil_risk_report.pdf"
    )
