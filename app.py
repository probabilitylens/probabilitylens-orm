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
# 🎨 COLOR
# =========================
def get_color(regime):
    return {
        "PREPARATION": "#6b7280",
        "DEVELOPING": "#f59e0b",
        "NEAR TRIGGER": "#ef4444"
    }[regime]

# =========================
# HEADER
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
# DATA
# =========================
df = pd.read_excel("data/wti.xls", sheet_name="Data 1")
df = df.iloc[:, :2]
df.columns = ["Date", "Price"]

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

df = df.dropna().sort_values("Date").tail(120)

# =========================
# INPUTS
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
# MODEL
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
# CHART (FIXED)
# =========================
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df["Date"],
    y=df["Price"],
    line=dict(color="white", width=3)
))

fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="#0b0f14",
    plot_bgcolor="#0b0f14",
    margin=dict(l=20, r=20, t=20, b=20)
)

# =========================
# UI — DECISION FIRST
# =========================
left, right = st.columns([1.3, 1.7])

with left:
    st.markdown(f"""
    <div style="
        padding:30px;
        border-radius:12px;
        background:{color};
        color:white;
    ">
        <h1 style='font-size:42px;margin-bottom:10px;'>{regime}</h1>
        <h3 style='margin:0;'>Action: {action}</h3>
        <p style='margin-top:10px;'>Conviction: {conviction}%</p>
        <p>Expected Move: {expected_move:.1f}%</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Trade Expression")
    st.markdown(f"""
    **Direction:** {direction}  
    **Horizon:** 2–6 weeks  
    **Conviction:** {conviction}%
    """)

with right:
    st.plotly_chart(fig, use_container_width=True)

# =========================
# NARRATIVE (FLOW, NOT BULLETS)
# =========================
headline = f"{regime} — {action}"

summary = f"""
The market is currently in a {regime} regime, with insufficient alignment and confirmation to justify
active positioning. While directional bias is beginning to emerge, the current setup does not yet
offer a compelling asymmetric opportunity.
"""

thesis = """
Oil markets are pricing a continuation of current demand strength without adequately reflecting
the fragility in macro confirmation signals. This creates a disconnect between price action and
underlying signal coherence, leaving the market vulnerable to repricing once alignment strengthens.
"""

positioning_text = """
Positioning remains moderately extended, increasing sensitivity to incremental shifts in macro
data and confirmation signals. This creates the potential for nonlinear moves once a trigger emerges.
"""

conclusion = f"""
At present, the optimal stance remains {action}. The setup is evolving, but not yet actionable.
The transition into a higher-conviction regime will depend on improved confirmation and timing alignment.
"""

# =========================
# PDF — REAL NARRATIVE
# =========================
def generate_pdf():
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(tmp.name, pagesize=letter)
    styles = getSampleStyleSheet()

    content = []

    content.append(Paragraph(f"<b>{headline}</b>", styles["Title"]))
    content.append(Spacer(1, 12))

    content.append(Paragraph(summary, styles["Normal"]))
    content.append(Spacer(1, 12))

    content.append(Paragraph("<b>Core Thesis</b>", styles["Heading2"]))
    content.append(Paragraph(thesis, styles["Normal"]))
    content.append(Spacer(1, 12))

    content.append(Paragraph("<b>Positioning</b>", styles["Heading2"]))
    content.append(Paragraph(positioning_text, styles["Normal"]))
    content.append(Spacer(1, 12))

    content.append(Paragraph("<b>Trade Expression</b>", styles["Heading2"]))
    content.append(Paragraph(
        f"Direction: {direction}<br/>Conviction: {conviction}%",
        styles["Normal"]
    ))
    content.append(Spacer(1, 12))

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
