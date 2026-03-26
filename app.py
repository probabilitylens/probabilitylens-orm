import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
import tempfile
import os

st.set_page_config(layout="wide")

# =========================
# 🧭 HEADER (FIXED)
# =========================
header_col1, header_col2 = st.columns([1, 6])

with header_col1:
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=120)

with header_col2:
    st.markdown("""
    <h1 style='margin-bottom:0;'>ProbabilityLens</h1>
    <p style='color:gray; margin-top:0;'>Oil Risk Monitor — Decision Engine</p>
    """, unsafe_allow_html=True)

st.markdown("---")

# =========================
# 📥 DATA LOADER
# =========================
@st.cache_data
def load_wti_data():
    df = pd.read_excel("data/wti.xls", sheet_name="Data 1")
    df = df.iloc[:, :2]
    df.columns = ["Date", "Price"]

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

    df = df.dropna().sort_values("Date").tail(120)
    return df

df = load_wti_data()

if df.empty:
    st.error("WTI dataset is empty")
    st.stop()

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

direction = "SHORT" if signal > 0.6 else "LONG" if signal < 0.4 else "NEUTRAL"

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

fig.add_vline(x=df["Date"].max(), line_width=2, line_color="white")

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
# 🖥 MAIN LAYOUT (FIXED)
# =========================
left, right = st.columns([1.1, 1.9])

with left:
    st.markdown("## Decision")

    st.markdown(f"""
    ### {regime}
    **Action:** {action}  
    **Conviction:** {conviction}%  
    **Expected Move:** {expected_move:.1f}%
    """)

    st.markdown("---")

    st.markdown("### Trade Expression")
    st.markdown(f"""
    **Direction:** {direction}  
    **Horizon:** 2–6 weeks  
    **Conviction:** {conviction}%
    """)

with right:
    st.markdown("## WTI Price")
    st.plotly_chart(fig, use_container_width=True)

# =========================
# 📊 SIGNAL ATTRIBUTION
# =========================
attr_df = pd.DataFrame({
    "Factor": list(inputs.keys()),
    "Score": list(inputs.values()),
    "Contribution": values / values.sum()
})

st.markdown("---")
st.markdown("## Signal Attribution")
st.dataframe(attr_df, use_container_width=True)

# =========================
# 📄 PDF GENERATION (UPGRADED)
# =========================
def generate_pdf():
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(temp_file.name, pagesize=letter)

    styles = getSampleStyleSheet()
    content = []

    # Title
    content.append(Paragraph("ProbabilityLens — Oil Risk Monitor", styles["Title"]))
    content.append(Spacer(1, 12))

    # Decision
    content.append(Paragraph(f"<b>Regime:</b> {regime}", styles["Normal"]))
    content.append(Paragraph(f"<b>Action:</b> {action}", styles["Normal"]))
    content.append(Paragraph(f"<b>Conviction:</b> {conviction}%", styles["Normal"]))
    content.append(Paragraph(f"<b>Expected Move:</b> {expected_move:.1f}%", styles["Normal"]))

    content.append(Spacer(1, 12))

    # Trade
    content.append(Paragraph("<b>Trade Expression</b>", styles["Heading2"]))
    content.append(Paragraph(
        f"Direction: {direction}<br/>Horizon: 2–6 weeks<br/>Conviction: {conviction}%",
        styles["Normal"]
    ))

    content.append(Spacer(1, 20))

    # Chart export
    img_path = "chart.png"
    fig.write_image(img_path)

    content.append(RLImage(img_path, width=500, height=300))

    doc.build(content)

    return temp_file.name

pdf_path = generate_pdf()

with open(pdf_path, "rb") as f:
    st.download_button(
        "Download PDF Report",
        f,
        file_name="oil_risk_report.pdf"
    )
