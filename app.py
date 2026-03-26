import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

# =========================
# 📥 DATA LOADING (HARDENED)
# =========================

@st.cache_data
def load_wti_data():
    try:
        df = pd.read_excel("data/wti.xls", sheet_name=0)

        # Attempt flexible column detection
        df = df.iloc[:, :2]
        df.columns = ["Date", "Price"]

        # Type conversion
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

        # Clean
        df = df.dropna()

        # Sort (critical)
        df = df.sort_values("Date")

        # Use last 120 observations
        df = df.tail(120)

        return df

    except Exception as e:
        st.error(f"Data loading failed: {e}")
        return pd.DataFrame()

df = load_wti_data()

# =========================
# 🚨 DATA VALIDATION
# =========================

if df is None or len(df) == 0:
    st.error("WTI dataset is empty — check Excel parsing.")
    st.stop()

if "Date" not in df.columns:
    st.error(f"Missing 'Date' column. Found: {df.columns.tolist()}")
    st.stop()

if len(df) < 10:
    st.error("Not enough data after cleaning — check source file.")
    st.stop()

# Sanity check (important for credibility)
if df["Price"].iloc[-1] < 50:
    st.warning("⚠️ WTI price looks too low — possible bad dataset")

# Recency check
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

inputs = np.array([
    signal, timing, confirmation,
    alignment, crowding, market_health, capital
])

# =========================
# 🧠 MODEL
# =========================

score = inputs.mean() * 100

# Regime
if score < 50:
    regime = "PREPARATION"
    action = "NO POSITION"
elif score < 75:
    regime = "DEVELOPING"
    action = "WAIT"
else:
    regime = "NEAR TRIGGER"
    action = "ENTER"

# Conviction (inverse dispersion)
dispersion = np.std(inputs)
conviction = int((1 - dispersion) * 100)

# Expected move
expected_move = np.clip(
    (score / 100) * (alignment + signal) * 10,
    -12, 12
)

# =========================
# 🧾 NARRATIVE ENGINE (UPGRADED)
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
            "pricing regime may not fully reflect underlying macro conditions. "
            "This raises the likelihood of directional follow-through."
        )
    else:
        return (
            "Macro signals remain fragmented, with no strong consensus across inputs. "
            "Current pricing appears broadly consistent with available information."
        )

narrative = generate_narrative(signal, alignment, crowding)

# =========================
# 📊 CHART (UPGRADED BASE)
# =========================

fig = go.Figure()

# Price line (dominant)
fig.add_trace(go.Scatter(
    x=df["Date"],
    y=df["Price"],
    mode="lines",
    name="WTI",
    line=dict(color="white", width=3)
))

# NOW line (safe)
last_date = df["Date"].max()

fig.add_vline(
    x=last_date,
    line_width=2,
    line_color="white"
)

# Layout styling (institutional baseline)
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
# 🖥 LAYOUT
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

# Narrative
st.subheader("Decision Rationale")
st.write(narrative)
