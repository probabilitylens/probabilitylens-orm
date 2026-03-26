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
# DATA LOADER (ROBUST)
# =========================
@st.cache_data
def load_wti():
    try:
        df = pd.read_excel("data/wti.xls", sheet_name=0, header=None)

        # find header row dynamically
        header_row = None
        for i in range(20):
            row = df.iloc[i].astype(str).str.lower()
            if row.str.contains("date").any() and row.str.contains("price|value").any():
                header_row = i
                break

        if header_row is None:
            raise Exception("Header row not found")

        df = pd.read_excel("data/wti.xls", sheet_name=0, header=header_row)
        df = df.iloc[:, :2]
        df.columns = ["Date", "Price"]

        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

        df = df.dropna().sort_values("Date").tail(120)

        if df.empty:
            raise Exception("WTI dataset empty")

        return df

    except Exception as e:
        st.error(f"DATA ERROR: {e}")
        st.stop()


df = load_wti()

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
# INTERPRETATION ENGINE
# =========================
def interpret(x, low, mid):
    if x < low:
        return "weak"
    elif x < mid:
        return "building"
    else:
        return "strong"

# =========================
# REPORT ENGINE
# =========================
def generate_report():

    report = {}

    # HEADER
    report["header"] = {
        "date": str(datetime.today().date()),
        "regime": regime,
        "action": action,
        "conviction": conviction,
        "expected_move": round(expected_move, 1)
    }

    # EXECUTIVE SUMMARY
    report["executive_summary"] = (
        f"The system is currently in a {regime.lower()} regime, with a composite score of {round(score,1)}. "
        f"Market signals remain {interpret(signal,0.3,0.7)} while alignment is {interpret(alignment,0.3,0.7)}, "
        f"indicating incomplete structural coherence. As a result, the model recommends {action.lower()}, "
        f"as current conditions do not yet justify capital deployment despite emerging directional bias."
    )

    # MARKET STATE
    trend = "uptrend" if df["Price"].iloc[-1] > df["Price"].iloc[0] else "range-bound"
    report["market_state"] = (
        f"WTI prices are currently in a {trend} over the observed window, with recent acceleration evident. "
        f"Volatility remains contained, and price behavior reflects gradual repricing rather than disorderly moves."
    )

    # SIGNAL DIAGNOSTICS
    report["signal_diagnostics"] = {
        "Signal": interpret(signal,0.3,0.7),
        "Timing": interpret(timing,0.3,0.7),
        "Confirmation": interpret(confirmation,0.3,0.7),
        "Alignment": interpret(alignment,0.3,0.7),
        "Crowding": interpret(crowding,0.3,0.7),
        "Market Health": interpret(market_health,0.3,0.7),
        "Capital": interpret(capital,0.3,0.7)
    }

    # MISPRICING
    report["mispricing"] = (
        "The market appears to be pricing a continuation of current conditions without fully incorporating "
        "the potential for structural shifts in alignment and signal reinforcement. This creates a gap between "
        "observed data and implied expectations."
    )

    # MECHANISM
    report["mechanism"] = (
        "A transition toward stronger alignment and confirmation would trigger a repricing process, "
        "as participants adjust positioning in response to improving signal clarity."
    )

    # POSITIONING
    report["positioning"] = (
        "Positioning appears neutral, with no evidence of extreme crowding. This suggests limited forced flows "
        "but also a lack of urgency among participants."
    )

    # SCENARIOS
    report["scenarios"] = pd.DataFrame({
        "Scenario": ["Base", "Bull", "Bear"],
        "Probability": [0.5, 0.25, 0.25],
        "Move": [
            f"+{round(expected_move,1)}%",
            f"+{round(expected_move*2,1)}%",
            f"-{round(expected_move*1.5,1)}%"
        ]
    })

    # TRADE
    report["trade"] = {
        "direction": "LONG",
        "entry": "Upon confirmation + alignment > 0.7",
        "horizon": "2–6 weeks",
        "risk": "Signal deterioration"
    }

    # DECISION LOGIC
    report["decision_logic"] = (
        f"The system outputs {action} because the composite score of {round(score,1)} does not exceed "
        "the activation threshold required for deployment. While directional bias is emerging, confirmation "
        "and alignment remain insufficient."
    )

    # CONCLUSION
    report["conclusion"] = (
        "The current environment reflects early-stage conditions that may evolve into a tradable setup, "
        "but patience remains required. Monitoring for improvements in alignment and confirmation is critical."
    )

    return report


report = generate_report()

# =========================
# CHART
# =========================
fig = go.Figure()
fig.add_trace(go.Scatter(x=df["Date"], y=df["Price"], line=dict(width=3)))
fig.update_layout(template="plotly_dark", height=500)

# =========================
# UI — FULL STRUCTURE
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
    st.write(report["trade"])

with col4:
    st.subheader("Signal Diagnostics")
    for k, v in report["signal_diagnostics"].items():
        st.write(f"{k}: {v}")

# NARRATIVE
st.subheader("Executive Summary")
st.write(report["executive_summary"])

st.subheader("Mispricing")
st.write(report["mispricing"])

st.subheader("Mechanism")
st.write(report["mechanism"])

# SCENARIOS
st.subheader("Scenario Analysis")
st.dataframe(report["scenarios"])

# =========================
# PDF ENGINE (FULL)
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
