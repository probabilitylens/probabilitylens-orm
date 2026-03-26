import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

# =========================
# ⚙️ DEBUG MODE (TURN OFF LATER)
# =========================
DEBUG = True

# =========================
# 📥 ROBUST DATA LOADER
# =========================
@st.cache_data
def load_wti_data():
    try:
        raw = pd.read_excel("data/wti.xls", sheet_name=0)

        if DEBUG:
            st.write("Raw Data Preview:")
            st.write(raw.head(15))

        # -------------------------
        # 🔍 FIND HEADER ROW
        # -------------------------
        header_row = None

        for i in range(len(raw)):
            row = raw.iloc[i].astype(str).str.lower().tolist()

            if any("date" in x for x in row) and (
                any("price" in x for x in row) or any("value" in x for x in row)
            ):
                header_row = i
                break

        if header_row is None:
            st.error("❌ Could not detect header row (Date / Price).")
            return pd.DataFrame()

        # -------------------------
        # 📊 RELOAD WITH HEADER
        # -------------------------
        df = pd.read_excel("data/wti.xls", header=header_row)

        # Normalize column names
        df.columns = [str(c).lower().strip() for c in df.columns]

        if DEBUG:
            st.write("Detected Columns:", df.columns.tolist())

        # -------------------------
        # 🎯 IDENTIFY COLUMNS
        # -------------------------
        date_cols = [c for c in df.columns if "date" in c]
        price_cols = [c for c in df.columns if "price" in c or "value" in c]

        if not date_cols or not price_cols:
            st.error("❌ Could not find Date/Price columns.")
            return pd.DataFrame()

        date_col = date_cols[0]
        price_col = price_cols[0]

        df = df[[date_col, price_col]]
        df.columns = ["Date", "Price"]

        # -------------------------
        # 🧹 CLEAN DATA
        # -------------------------
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

        df = df.dropna()

        if DEBUG:
            st.write("After Cleaning:", df.head())

        if len(df) == 0:
            st.error("❌ Data became empty after cleaning.")
            return pd.DataFrame()

        # Sort + tail
        df = df.sort_values("Date")
        df = df.tail(120)

        return df

    except Exception as e:
        st.error(f"❌ Data loading failed: {e}")
        return pd.DataFrame()


df = load_wti_data()

# =========================
# 🚨 VALIDATION
# =========================
if df is None or len(df) == 0:
    st.error("WTI dataset is empty — check Excel parsing.")
    st.stop()

if len(df) < 10:
    st.error("Not enough data after cleaning.")
    st.stop()

# Sanity check
if df["Price"].iloc[-1] < 50:
    st.warning("⚠️ WTI price looks too low — possible wrong dataset")

# Recency check
if df["Date"].max() < datetime.today() - timedelta(days=5):
    st.warning("⚠️ Data may be stale")

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

inputs = np.array([
    signal, timing, confirmation,
    alignment, crowding, market_health, capital
])

# =========================
# 🧠 MODEL
# =========================
score = inputs.mean() * 100

if score < 50:
    regime = "PREPARATION"
    action = "NO POSITION"
elif score < 75:
    regime = "DEVELOPING"
    action = "WAIT"
else:
    regime = "NEAR TRIGGER"
    action = "ENTER"

dispersion = np.std(inputs)
conviction = int((1 - dispersion) * 100)

expected_move = np.clip(
    (score / 100) * (alignment + signal) * 10,
    -12, 12
)

# =========================
# 🧾 NARRATIVE
# =========================
def generate_narrative(signal, alignment, crowding):
    if signal > 0.7 and crowding > 0.6:
        return (
            "The market is currently pricing oil under a stable demand assumption, "
            "while leading indicators suggest deterioration in marginal demand. "
            "Positioning remains extended, increasing the probability of a sharp "
            "downside repricing as expectations adjust."
        )
    elif alignment > 0.6:
        return (
            "Cross-asset signals are increasingly aligned, suggesting the current "
            "pricing regime may not fully reflect underlying macro conditions."
        )
    else:
        return (
            "Macro signals remain fragmented, with no strong consensus across inputs."
        )

narrative = generate_narrative(signal, alignment, crowding)

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

# Safe NOW line
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
# 🖥 UI
# =========================
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Decision")

    st.metric("Regime", regime)
    st.metric("Action", action)
    st.metric("Conviction", f"{conviction}%")
    st.metric("Expected Move", f"{expected_move:.1f}%")

with col2:
    st.subheader("WTI Price")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Decision Rationale")
st.write(narrative)
