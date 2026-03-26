import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io

st.set_page_config(layout="wide")

# =========================================================
# DATA LOADER — FINAL (COLUMN DETECTION ENGINE)
# =========================================================
@st.cache_data
def load_wti():
    try:
        raw = pd.read_excel("data/wti.xls", header=None)

        start = None

        # find first valid date row
        for i in range(len(raw)):
            try:
                pd.to_datetime(raw.iloc[i, 0])
                start = i
                break
            except:
                continue

        if start is None:
            raise Exception("No date column detected")

        df = raw.iloc[start:].reset_index(drop=True)

        # detect price column dynamically
        price_col = None

        for col in range(1, min(6, df.shape[1])):  # scan first few cols
            test = pd.to_numeric(df.iloc[:, col], errors="coerce")
            if test.notna().sum() > 20:
                price_col = col
                break

        if price_col is None:
            raise Exception("No numeric price column detected")

        df = df.iloc[:, [0, price_col]]
        df.columns = ["Date", "Price"]

        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

        df = df.dropna()

        if len(df) < 20:
            raise Exception("Parsed dataset too small — check Excel structure")

        df = df.sort_values("Date").tail(120)

        return df.reset_index(drop=True)

    except Exception as e:
        st.error(f"DATA ERROR: {e}")
        st.stop()


df = load_wti()

# =========================================================
# INPUTS
# =========================================================
st.sidebar.title("Inputs")

signal = st.sidebar.slider("Signal", 0.0, 1.0, 0.3)
timing = st.sidebar.slider("Timing", 0.0, 1.0, 0.3)
confirmation = st.sidebar.slider("Confirmation", 0.0, 1.0, 0.3)
alignment = st.sidebar.slider("Alignment", 0.0, 1.0, 0.58)
crowding = st.sidebar.slider("Crowding", 0.0, 1.0, 0.5)
market = st.sidebar.slider("Market Health", 0.0, 1.0, 0.5)
capital = st.sidebar.slider("Capital", 0.0, 1.0, 0.5)

# =========================================================
# MODEL
# =========================================================
factors = np.array([signal, timing, confirmation, alignment, crowding, market, capital])
conviction = factors.mean()

returns = df["Price"].pct_change().dropna()
vol = returns.std() * np.sqrt(252)

vol_regime = "LOW" if vol < 0.2 else "NORMAL" if vol < 0.4 else "HIGH"

trend = df["Price"].iloc[-1] / df["Price"].iloc[0] - 1
positioning = "CROWDED LONG" if trend > 0.15 else "NEUTRAL"

expected_move = vol * np.sqrt(10) * conviction

regime = "PREPARATION" if conviction < 0.6 else "ACTIVE"
action = "NO POSITION" if conviction < 0.6 else "ENTER TRADE"

# =========================================================
# UI
# =========================================================
col_logo, col_title = st.columns([1,5])

with col_logo:
    try:
        st.image("Logo.png", width=120)
    except:
        pass

with col_title:
    st.title("ProbabilityLens")
    st.caption("Oil Risk Monitor — Institutional Decision Engine")

st.divider()

# metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("Conviction", f"{round(conviction*100)}%")
m2.metric("Expected Move", f"{round(expected_move*100,2)}%")
m3.metric("Vol Regime", vol_regime)
m4.metric("Positioning", positioning)

left, right = st.columns([1,1])

# LEFT
with left:
    st.subheader("Decision")

    st.markdown(f"""
    <div style="background:#374151;padding:25px;border-radius:10px;color:white">
        <h2>{regime}</h2>
        <p><b>Action:</b> {action}</p>
        <p><b>Conviction:</b> {round(conviction*100)}%</p>
        <p><b>Expected Move:</b> {round(expected_move*100,2)}%</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Trade Expression")
    st.write("Direction: LONG")
    st.write("Horizon: 2–6 weeks")

    st.subheader("Factor Decomposition")
    st.dataframe(pd.DataFrame({
        "Factor":["Signal","Timing","Confirmation","Alignment","Crowding","Market","Capital"],
        "Score":factors
    }), use_container_width=True)

# RIGHT
with right:
    st.subheader("WTI Price")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Date"], y=df["Price"]))
    fig.update_layout(height=450)

    st.plotly_chart(fig, use_container_width=True)

# =========================================================
# REPORT (REAL TEXT)
# =========================================================
def build_report():
    return f"""
Oil Market Report

The market is currently in a {regime.lower()} regime with conviction at {round(conviction*100)}%.

Volatility is {vol_regime.lower()}, and positioning appears {positioning.lower()}.

Signals remain incomplete, suggesting patience is required before deploying capital.
"""

def generate_pdf():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    content = []
    for line in build_report().split("\n"):
        content.append(Paragraph(line, styles["Normal"]))
        content.append(Spacer(1,10))

    doc.build(content)
    buffer.seek(0)
    return buffer

st.download_button(
    "Download Report",
    generate_pdf(),
    "report.pdf",
    "application/pdf"
)
