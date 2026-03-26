import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
import tempfile
import os

st.set_page_config(layout="wide")

# =========================
# 🎨 REGIME COLOR
# =========================
def get_color(regime):
    return {
        "PREPARATION": "#6b7280",
        "DEVELOPING": "#f59e0b",
        "NEAR TRIGGER": "#ef4444"
    }[regime]

# =========================
# 🧭 HEADER
# =========================
c1, c2 = st.columns([1, 6])

with c1:
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=120)

with c2:
    st.markdown("""
    <h1 style='margin-bottom:0;'>ProbabilityLens</h1>
    <p style='color:gray;'>Oil Risk Monitor — Decision Engine</p>
    """, unsafe_allow_html=True)

st.markdown("---")

# =========================
# 📥 DATA
# =========================
df = pd.read_excel("data/wti.xls", sheet_name="Data 1")
df = df.iloc[:, :2]
df.columns = ["Date", "Price"]
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
df = df.dropna().sort_values("Date").tail(120)

# =========================
# 🎛 INPUTS
# =========================
st.sidebar.title("Input Parameters")

signal = st.sidebar.slider("Signal", 0.0, 1.0, 0.3)
timing = st.sidebar.slider("Timing", 0.0, 1.0, 0.3)
confirmation = st.sidebar.slider("Confirmation", 0.0, 1.0, 0.3)
alignment = st.sidebar.slider("Alignment", 0.0, 1.0, 0.58)
crowding = st.sidebar.slider("Crowding", 0.0, 1.0, 0.5)
market_health = st.sidebar.slider("Market Health", 0.0, 1.0, 0.5)
capital = st.sidebar.slider("Capital Availability", 0.0, 1.0, 0.5)

vals = np.array([signal, timing, confirmation, alignment, crowding, market_health, capital])
score = vals.mean() * 100

# =========================
# 🧠 MODEL
# =========================
if score < 50:
    regime = "PREPARATION"
    action = "NO POSITION"
elif score < 75:
    regime = "DEVELOPING"
    action = "WAIT"
else:
    regime = "NEAR TRIGGER"
    action = "ENTER"

conviction = int((1 - np.std(vals)) * 100)
expected_move = (score / 100) * (alignment + signal) * 10
direction = "SHORT" if signal > 0.6 else "LONG" if signal < 0.4 else "NEUTRAL"

color = get_color(regime)

# =========================
# 📊 CHART
# =========================
fig = go.Figure()
fig.add_trace(go.Scatter(x=df["Date"], y=df["Price"], line=dict(color="white", width=3)))
fig.update_layout(template="plotly_dark", paper_bgcolor="#0b0f14")

# =========================
# 🧠 NARRATIVE ENGINE (NEW)
# =========================
executive = f"""
The system is currently in a {regime} regime, indicating limited immediate trade readiness.
While underlying signals suggest emerging directional bias, confirmation and timing remain insufficient.
"""

situation = """
Oil prices have recently accelerated higher, reflecting tightening supply expectations and resilient demand signals.
However, macro inputs remain fragmented, with inconsistent confirmation across key indicators.
"""

mispricing = """
The market appears to be overpricing stability in current demand conditions while underestimating potential volatility in forward expectations.
"""

mechanism = """
As alignment improves and confirmation signals strengthen, positioning imbalances are likely to unwind, creating asymmetric price moves.
"""

positioning = """
Current positioning remains moderately extended, increasing sensitivity to shifts in macro expectations.
"""

conclusion = f"""
Given the current configuration, the optimal stance remains {action}, with readiness still developing rather than actionable.
"""

# =========================
# 🖥 UI
# =========================
left, right = st.columns([1.2, 1.8])

with left:
    st.markdown("## Decision")

    st.markdown(f"""
    <div style="padding:20px;border-radius:10px;background:{color};color:white;">
        <h2>{regime}</h2>
        <p><b>Action:</b> {action}</p>
        <p><b>Conviction:</b> {conviction}%</p>
        <p><b>Expected Move:</b> {expected_move:.1f}%</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Trade")
    st.markdown(f"""
    **Direction:** {direction}  
    **Horizon:** 2–6 weeks  
    **Conviction:** {conviction}%
    """)

with right:
    st.markdown("## WTI Price")
    st.plotly_chart(fig, use_container_width=True)

# =========================
# 📄 PDF — REAL REPORT
# =========================
def generate_pdf():
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(tmp.name, pagesize=letter)
    styles = getSampleStyleSheet()

    content = []

    content.append(Paragraph("<b>Executive Summary</b>", styles["Heading2"]))
    content.append(Paragraph(executive, styles["Normal"]))

    content.append(Spacer(1, 10))
    content.append(Paragraph("<b>Situation</b>", styles["Heading2"]))
    content.append(Paragraph(situation, styles["Normal"]))

    content.append(Spacer(1, 10))
    content.append(Paragraph("<b>Market Mispricing</b>", styles["Heading2"]))
    content.append(Paragraph(mispricing, styles["Normal"]))

    content.append(Spacer(1, 10))
    content.append(Paragraph("<b>Mechanism</b>", styles["Heading2"]))
    content.append(Paragraph(mechanism, styles["Normal"]))

    content.append(Spacer(1, 10))
    content.append(Paragraph("<b>Positioning</b>", styles["Heading2"]))
    content.append(Paragraph(positioning, styles["Normal"]))

    content.append(Spacer(1, 10))
    content.append(Paragraph("<b>Trade Expression</b>", styles["Heading2"]))
    content.append(Paragraph(
        f"Direction: {direction}<br/>Conviction: {conviction}%",
        styles["Normal"]
    ))

    content.append(Spacer(1, 10))
    content.append(Paragraph("<b>Conclusion</b>", styles["Heading2"]))
    content.append(Paragraph(conclusion, styles["Normal"]))

    # chart
    img = "chart.png"
    fig.write_image(img)
    content.append(Spacer(1, 20))
    content.append(RLImage(img, width=500, height=300))

    doc.build(content)
    return tmp.name

pdf = generate_pdf()

with open(pdf, "rb") as f:
    st.download_button("Download PDF Report", f, "oil_report.pdf")
