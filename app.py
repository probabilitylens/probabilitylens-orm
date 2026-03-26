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
# 📥 DATA LOADER (FIXED)
# =========================
@st.cache_data
def load_data():
    df = pd.read_excel("data/wti.xls", sheet_name="Data 1")

    df = df.iloc[:, :2]
    df.columns = ["Date", "Price"]

    # 🔥 CRITICAL FIX
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

    # Remove garbage rows
    df = df.dropna()

    # Sort and trim
    df = df.sort_values("Date").tail(120)

    return df

df = load_data()

if df.empty:
    st.error("Data failed to load properly — check Excel structure")
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
# 📄 PDF
# =========================
def generate_pdf():
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(tmp.name, pagesize=letter)
    styles = getSampleStyleSheet()

    content = []

    content.append(Paragraph(f"<b>{regime} — {action}</b>", styles["Title"]))
    content.append(Spacer(1, 12))

    content.append(Paragraph(
        f"Direction: {direction}<br/>Conviction: {conviction}%",
        styles["Normal"]
    ))

    content.append(Spacer(1, 12))

    content.append(Paragraph(
        "Market is underestimating demand-driven downside pressure on oil prices.",
        styles["Normal"]
    ))

    img = "chart.png"
    fig.write_image(img)
    content.append(RLImage(img, width=500, height=300))

    doc.build(content)
    return tmp.name

pdf = generate_pdf()

with open(pdf, "rb") as f:
    st.download_button("Download PDF Report", f, "oil_report.pdf")
