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
# 🎨 REGIME COLOR SYSTEM
# =========================
def get_regime_color(regime):
    if regime == "PREPARATION":
        return "#6b7280"  # gray
    elif regime == "DEVELOPING":
        return "#f59e0b"  # amber
    else:
        return "#ef4444"  # red

# =========================
# 🧭 HEADER
# =========================
col1, col2 = st.columns([1, 6])

with col1:
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=120)

with col2:
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
df["Date"] = pd.to_datetime(df["Date"])
df = df.dropna().sort_values("Date").tail(120)

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
color = get_regime_color(regime)

# =========================
# 📊 CHART
# =========================
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df["Date"],
    y=df["Price"],
    line=dict(color="white", width=3)
))

fig.add_vline(x=df["Date"].max(), line_color="white")

fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="#0b0f14",
    plot_bgcolor="#0b0f14"
)

# =========================
# 🖥 UI — DECISION CARD
# =========================
left, right = st.columns([1.2, 1.8])

with left:
    st.markdown("## Decision")

    st.markdown(f"""
    <div style="
        padding:20px;
        border-radius:10px;
        background-color:{color};
        color:white;
    ">
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
# 📄 PDF (REAL MEMO)
# =========================
def generate_pdf():
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(tmp.name, pagesize=letter)
    styles = getSampleStyleSheet()

    content = []

    # HEADLINE
    content.append(Paragraph(f"<b>{regime} — {action}</b>", styles["Title"]))
    content.append(Spacer(1, 12))

    # TRADE
    content.append(Paragraph("<b>Trade Expression</b>", styles["Heading2"]))
    content.append(Paragraph(
        f"Direction: {direction}<br/>Horizon: 2–6 weeks<br/>Conviction: {conviction}%",
        styles["Normal"]
    ))

    content.append(Spacer(1, 12))

    # NARRATIVE (NEW)
    content.append(Paragraph("<b>Rationale</b>", styles["Heading2"]))
    content.append(Paragraph(
        "The market is currently underestimating demand-driven downside pressure "
        "on oil prices. Positioning remains extended, increasing the probability "
        "of a sharp repricing.",
        styles["Normal"]
    ))

    content.append(Spacer(1, 20))

    # CHART
    img = "chart.png"
    fig.write_image(img)
    content.append(RLImage(img, width=500, height=300))

    doc.build(content)
    return tmp.name

pdf = generate_pdf()

with open(pdf, "rb") as f:
    st.download_button("Download PDF Report", f, "oil_report.pdf")
