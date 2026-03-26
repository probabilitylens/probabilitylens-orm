import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import tempfile
import os

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

st.set_page_config(layout="wide")

# =========================
# ROBUST DATA LOADER
# =========================
@st.cache_data
def load_wti():
    try:
        raw = pd.read_excel("data/wti.xls", sheet_name=0, header=None)

        # Detect header row
        header_row = None
        for i in range(min(30, len(raw))):
            row = raw.iloc[i].astype(str).str.lower()
            if row.str.contains("date").any() and row.str.contains("price|value|close").any():
                header_row = i
                break

        if header_row is None:
            raise Exception("Header row not detected")

        df = pd.read_excel("data/wti.xls", sheet_name=0, header=header_row)

        cols = df.columns.astype(str).str.lower()

        date_col = None
        price_col = None

        for c in cols:
            if "date" in c:
                date_col = c
            if any(x in c for x in ["price", "value", "close"]):
                price_col = c

        if date_col is None or price_col is None:
            raise Exception("Date/Price columns not found")

        df = df[[date_col, price_col]]
        df.columns = ["Date", "Price"]

        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

        df = df.dropna()

        if len(df) < 10:
            raise Exception("Too few valid rows after cleaning")

        df = df.sort_values("Date").tail(120)

        return df

    except Exception as e:
        st.error(f"DATA ERROR: {e}")
        st.stop()


df = load_wti()

if df.empty:
    st.error("WTI dataset empty after parsing")
    st.stop()

# =========================
# INPUTS
# =========================
st.sidebar.title("Inputs")

signal = st.sidebar.slider("Signal", 0.0, 1.0, 0.3)
timing = st.sidebar.slider("Timing", 0.0, 1.0, 0.3)
confirmation = st.sidebar.slider("Confirmation", 0.0, 1.0, 0.3)
alignment = st.sidebar.slider("Alignment", 0.0, 1.0, 0.58)
crowding = st.sidebar.slider("Crowding", 0.0, 1.0, 0.5)
market_health = st.sidebar.slider("Market Health", 0.0, 1.0, 0.5)
capital = st.sidebar.slider("Capital", 0.0, 1.0, 0.5)

vals = np.array([signal, timing, confirmation, alignment, crowding, market_health, capital])
score = vals.mean() * 100

# =========================
# MODEL
# =========================
if score < 50:
    regime, action = "PREPARATION", "NO POSITION"
elif score < 75:
    regime, action = "DEVELOPING", "WAIT"
else:
    regime, action = "NEAR TRIGGER", "ENTER"

conviction = int((1 - np.std(vals)) * 100)
expected_move = (score / 100) * (alignment + signal) * 10

# =========================
# INTERPRETATION
# =========================
def interpret(x):
    if x < 0.3:
        return "weak"
    elif x < 0.7:
        return "building"
    else:
        return "strong"

# =========================
# REPORT ENGINE
# =========================
def generate_report():

    trend = "uptrend" if df["Price"].iloc[-1] > df["Price"].iloc[0] else "range-bound"

    report = {
        "header": {
            "date": str(datetime.today().date()),
            "regime": regime,
            "action": action,
            "conviction": conviction,
            "expected_move": round(expected_move, 1)
        },

        "executive_summary": (
            f"The system is in a {regime.lower()} regime with a composite score of {round(score,1)}. "
            f"Signals remain {interpret(signal)} and alignment is {interpret(alignment)}, indicating incomplete structure. "
            f"As a result, the model recommends {action.lower()} as current conditions do not yet justify deployment."
        ),

        "market_state": (
            f"WTI prices are in a {trend}, with recent acceleration visible. "
            f"Volatility remains contained and price action reflects controlled repricing."
        ),

        "signal_diagnostics": {
            "Signal": interpret(signal),
            "Timing": interpret(timing),
            "Confirmation": interpret(confirmation),
            "Alignment": interpret(alignment),
            "Crowding": interpret(crowding),
            "Market Health": interpret(market_health),
            "Capital": interpret(capital)
        },

        "mispricing": (
            "The market appears to be pricing continuation without fully incorporating improving structural alignment, "
            "creating a gap between observed signals and implied expectations."
        ),

        "mechanism": (
            "Improvement in confirmation and alignment would trigger repricing, as participants adjust positioning to stronger signals."
        ),

        "positioning": (
            "Positioning is neutral, indicating limited forced flows and absence of extreme crowding."
        ),

        "scenarios": pd.DataFrame({
            "Scenario": ["Base", "Bull", "Bear"],
            "Probability": [0.5, 0.25, 0.25],
            "Move": [
                f"+{round(expected_move,1)}%",
                f"+{round(expected_move*2,1)}%",
                f"-{round(expected_move*1.5,1)}%"
            ]
        }),

        "trade": {
            "Direction": "LONG",
            "Entry": "Confirmation + alignment > 0.7",
            "Horizon": "2–6 weeks",
            "Risk": "Signal deterioration"
        },

        "decision_logic": (
            f"The system outputs {action} because the composite score of {round(score,1)} "
            "remains below the activation threshold required for capital deployment."
        ),

        "conclusion": (
            "Current conditions reflect early-stage development. Monitoring improvements in alignment and confirmation remains critical."
        )
    }

    return report


report = generate_report()

# =========================
# CHART
# =========================
fig = go.Figure()
fig.add_trace(go.Scatter(x=df["Date"], y=df["Price"], line=dict(width=3)))
fig.update_layout(template="plotly_dark", height=500)

# =========================
# UI
# =========================

# HEADER
st.title("ProbabilityLens")
st.caption("Oil Risk Monitor — Decision Engine")

# HERO
col1, col2 = st.columns([1.2, 1.8])

with col1:
    st.markdown(f"## {report['header']['regime']}")
    st.markdown(f"### {report['header']['action']}")
    st.metric("Conviction", f"{report['header']['conviction']}%")
    st.metric("Expected Move", f"{report['header']['expected_move']}%")

with col2:
    st.plotly_chart(fig, use_container_width=True)

# TRADE + SIGNALS
col3, col4 = st.columns(2)

with col3:
    st.subheader("Trade Expression")
    for k, v in report["trade"].items():
        st.write(f"{k}: {v}")

with col4:
    st.subheader("Signal Diagnostics")
    for k, v in report["signal_diagnostics"].items():
        st.write(f"{k}: {v}")

# NARRATIVE
st.subheader("Executive Summary")
st.write(report["executive_summary"])

st.subheader("Market State")
st.write(report["market_state"])

st.subheader("Mispricing")
st.write(report["mispricing"])

st.subheader("Mechanism")
st.write(report["mechanism"])

st.subheader("Positioning")
st.write(report["positioning"])

st.subheader("Decision Logic")
st.write(report["decision_logic"])

st.subheader("Conclusion")
st.write(report["conclusion"])

# SCENARIOS
st.subheader("Scenario Analysis")
st.dataframe(report["scenarios"])

# =========================
# PDF
# =========================
def build_pdf(report):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(tmp.name, pagesize=letter)
    styles = getSampleStyleSheet()

    content = []

    def add(title, text):
        content.append(Spacer(1, 10))
        content.append(Paragraph(f"<b>{title}</b>", styles["Heading2"]))
        content.append(Paragraph(text, styles["Normal"]))

    add("Executive Summary", report["executive_summary"])
    add("Market State", report["market_state"])
    add("Mispricing", report["mispricing"])
    add("Mechanism", report["mechanism"])
    add("Positioning", report["positioning"])
    add("Decision Logic", report["decision_logic"])
    add("Conclusion", report["conclusion"])

    # chart export
    img_path = "chart.png"
    try:
        fig.write_image(img_path)
        content.append(Spacer(1, 20))
        content.append(Image(img_path, width=500, height=300))
    except:
        pass

    doc.build(content)
    return tmp.name


pdf_file = build_pdf(report)

with open(pdf_file, "rb") as f:
    st.download_button("Download Full Report", f)
