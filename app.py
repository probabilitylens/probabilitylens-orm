import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
import io

st.set_page_config(layout="wide")

# =========================================================
# DATA LOADER (HARDENED — NO FAILURES)
# =========================================================
@st.cache_data
def load_wti():
    try:
        raw = pd.read_excel("data/wti.xls", header=None)

        # detect first valid date row
        start = None
        for i in range(len(raw)):
            try:
                pd.to_datetime(raw.iloc[i, 0])
                start = i
                break
            except:
                continue

        if start is None:
            raise Exception("No valid date row found")

        df = raw.iloc[start:, :2].copy()
        df.columns = ["Date", "Price"]

        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

        df = df.dropna()

        if len(df) < 20:
            raise Exception("Dataset too small after parsing")

        df = df.sort_values("Date").tail(120)

        return df.reset_index(drop=True)

    except Exception as e:
        st.error(f"DATA ERROR: {e}")
        st.stop()


df = load_wti()

# =========================================================
# SIDEBAR INPUTS
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
# CORE MODEL
# =========================================================
factors = {
    "Signal": signal,
    "Timing": timing,
    "Confirmation": confirmation,
    "Alignment": alignment,
    "Crowding": crowding,
    "Market": market,
    "Capital": capital,
}

weights = np.array([1,1,1,1,1,1,1])
scores = np.array(list(factors.values()))

conviction = np.dot(scores, weights) / weights.sum()

returns = df["Price"].pct_change().dropna()
vol = returns.std() * np.sqrt(252)

# volatility regime
if vol < 0.2:
    vol_regime = "LOW VOL"
elif vol < 0.4:
    vol_regime = "NORMAL VOL"
else:
    vol_regime = "HIGH VOL"

# positioning proxy
trend = df["Price"].iloc[-1] / df["Price"].iloc[0] - 1
positioning = "CROWDED LONG" if trend > 0.15 else "NEUTRAL"

expected_move = vol * np.sqrt(10) * conviction

regime = "PREPARATION" if conviction < 0.6 else "ACTIVE"
action = "NO POSITION" if conviction < 0.6 else "ENTER TRADE"

# =========================================================
# HEADER (PROPER DASHBOARD STYLE)
# =========================================================
col1, col2 = st.columns([1,5])

with col1:
    try:
        st.image("Logo.png", width=120)
    except:
        pass

with col2:
    st.markdown("# ProbabilityLens")
    st.markdown("### Oil Risk Monitor — Institutional Decision System")

st.divider()

# =========================================================
# TOP METRICS ROW
# =========================================================
m1, m2, m3, m4 = st.columns(4)

m1.metric("Conviction", f"{round(conviction*100)}%")
m2.metric("Expected Move (10d)", f"{round(expected_move*100,2)}%")
m3.metric("Volatility Regime", vol_regime)
m4.metric("Positioning", positioning)

# =========================================================
# MAIN GRID
# =========================================================
left, right = st.columns([1,1])

# ---------------- LEFT PANEL ----------------
with left:

    st.markdown("## Decision")

    st.markdown(f"""
    <div style="background:#374151;padding:25px;border-radius:12px;color:white">
        <h2>{regime}</h2>
        <p><b>Action:</b> {action}</p>
        <p><b>Conviction:</b> {round(conviction*100)}%</p>
        <p><b>Expected Move:</b> {round(expected_move*100,2)}%</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("## Trade Expression")
    st.write(f"Direction: LONG")
    st.write(f"Horizon: 2–6 weeks")
    st.write(f"Entry: Alignment > 0.7 & Confirmation improving")
    st.write(f"Risk: Signal deterioration")

    st.markdown("## Factor Decomposition")

    factor_df = pd.DataFrame({
        "Factor": list(factors.keys()),
        "Score": list(factors.values()),
        "Contribution": scores / scores.sum()
    })

    st.dataframe(factor_df, use_container_width=True)

    st.markdown("## Scenario Analysis")

    scenarios = pd.DataFrame({
        "Scenario":["Base","Bull","Bear"],
        "Probability":[0.5,0.25,0.25],
        "Move":["+3%","+8%","-5%"]
    })

    st.dataframe(scenarios, use_container_width=True)

# ---------------- RIGHT PANEL ----------------
with right:

    st.markdown("## WTI Price")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Date"],
        y=df["Price"],
        line=dict(width=2)
    ))

    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("## Signal Diagnostics")

    st.write(f"Signal: {'Weak' if signal<0.5 else 'Strong'}")
    st.write(f"Timing: {'Early' if timing<0.5 else 'Mature'}")
    st.write(f"Confirmation: {'Low' if confirmation<0.5 else 'High'}")
    st.write(f"Alignment: {'Fragmented' if alignment<0.6 else 'Aligned'}")

# =========================================================
# INSTITUTIONAL REPORT ENGINE (MULTI-PAGE)
# =========================================================
def build_report():

    report = f"""
Executive Summary

The oil market is currently in a {regime.lower()} regime with conviction at {round(conviction*100)}%. 
Market conditions reflect incomplete confirmation despite improving structural alignment.

Market Context

Recent price dynamics show a trend of {round(trend*100,2)}% over the observation window. 
Volatility regime is classified as {vol_regime}, suggesting {'contained' if vol<0.3 else 'elevated'} risk conditions.

Factor Analysis

Signal strength remains {'weak' if signal<0.5 else 'constructive'}, while timing is {'early' if timing<0.5 else 'advanced'}.
Confirmation remains {'insufficient' if confirmation<0.5 else 'supportive'}, limiting conviction expansion.

Positioning & Risk

Positioning appears {positioning.lower()}, indicating {'potential overcrowding risk' if positioning!='NEUTRAL' else 'balanced flows'}.

Trade Implications

Given the current configuration, the optimal approach is to maintain optionality and wait for improved confirmation.

Decision

Regime: {regime}
Action: {action}

Conclusion

The system does not yet justify aggressive positioning. Monitoring for confirmation remains critical.
"""

    return report


def generate_pdf():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    content = []

    for line in build_report().split("\n"):
        content.append(Paragraph(line, styles["Normal"]))
        content.append(Spacer(1, 12))

    doc.build(content)
    buffer.seek(0)

    return buffer


pdf = generate_pdf()

st.download_button(
    "Download Full Institutional Report",
    pdf,
    "Oil_Report.pdf",
    "application/pdf"
)
