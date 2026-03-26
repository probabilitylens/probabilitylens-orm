import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
import io

st.set_page_config(layout="wide")

# =========================================================
# DATA LOADER — FINAL (SCAN ALL SHEETS, PATTERN EXTRACTION)
# =========================================================
@st.cache_data
def load_wti():
    try:
        xls = pd.ExcelFile("data/wti.xls")

        best_df = None
        best_len = 0

        # iterate through all sheets
        for sheet in xls.sheet_names:
            raw = pd.read_excel(xls, sheet_name=sheet, header=None)

            # try each column as potential date column
            for col in range(min(5, raw.shape[1])):

                date_col = pd.to_datetime(raw.iloc[:, col], errors="coerce")

                if date_col.notna().sum() < 20:
                    continue  # not a valid date column

                # now search for numeric column next to it
                for pcol in range(raw.shape[1]):
                    if pcol == col:
                        continue

                    price_col = pd.to_numeric(raw.iloc[:, pcol], errors="coerce")

                    if price_col.notna().sum() < 20:
                        continue

                    df = pd.DataFrame({
                        "Date": date_col,
                        "Price": price_col
                    }).dropna()

                    if len(df) > best_len:
                        best_df = df
                        best_len = len(df)

        if best_df is None or best_len < 20:
            raise Exception("Could not extract valid time series from Excel")

        best_df = best_df.sort_values("Date").tail(200)

        return best_df.reset_index(drop=True)

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
factors = {
    "Signal": signal,
    "Timing": timing,
    "Confirmation": confirmation,
    "Alignment": alignment,
    "Crowding": crowding,
    "Market": market,
    "Capital": capital,
}

scores = np.array(list(factors.values()))
conviction = scores.mean()

returns = df["Price"].pct_change().dropna()
vol = returns.std() * np.sqrt(252)

if vol < 0.2:
    vol_regime = "LOW VOL"
elif vol < 0.4:
    vol_regime = "NORMAL VOL"
else:
    vol_regime = "HIGH VOL"

trend = df["Price"].iloc[-1] / df["Price"].iloc[0] - 1
positioning = "CROWDED LONG" if trend > 0.15 else "NEUTRAL"

expected_move = vol * np.sqrt(10) * conviction

regime = "PREPARATION" if conviction < 0.6 else "ACTIVE"
action = "NO POSITION" if conviction < 0.6 else "ENTER TRADE"

# =========================================================
# HEADER
# =========================================================
col_logo, col_title = st.columns([1,5])

with col_logo:
    try:
        st.image("Logo.png", width=120)
    except:
        pass

with col_title:
    st.title("ProbabilityLens")
    st.caption("Oil Risk Monitor — Institutional Decision System")

st.divider()

# =========================================================
# METRICS ROW
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

# ---------------- LEFT ----------------
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
    st.write("Direction: LONG")
    st.write("Horizon: 2–6 weeks")
    st.write("Entry: Alignment > 0.7 & Confirmation improving")
    st.write("Risk: Signal deterioration")

    st.markdown("## Factor Decomposition")

    factor_df = pd.DataFrame({
        "Factor": list(factors.keys()),
        "Score": list(factors.values()),
        "Contribution": scores / scores.sum()
    })

    st.dataframe(factor_df, use_container_width=True)

    st.markdown("## Scenario Analysis")

    scenarios = pd.DataFrame({
        "Scenario": ["Base", "Bull", "Bear"],
        "Probability": [0.5, 0.25, 0.25],
        "Move": ["+3%", "+8%", "-5%"]
    })

    st.dataframe(scenarios, use_container_width=True)

# ---------------- RIGHT ----------------
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
    st.write(f"Crowding: {'Neutral' if crowding<0.6 else 'Crowded'}")

# =========================================================
# INSTITUTIONAL REPORT
# =========================================================
def build_report():
    return f"""
EXECUTIVE SUMMARY

The oil market is currently in a {regime.lower()} regime with conviction at {round(conviction*100)}%.

MARKET CONTEXT

Recent price dynamics show a trend of {round(trend*100,2)}%.
Volatility is classified as {vol_regime}.

FACTOR ANALYSIS

Signal: {signal}
Timing: {timing}
Confirmation: {confirmation}
Alignment: {alignment}

POSITIONING

Market positioning appears {positioning.lower()}.

DECISION

Regime: {regime}
Action: {action}

CONCLUSION

Conditions are not yet sufficient for aggressive positioning.
"""

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

st.download_button(
    "Download Institutional Report",
    generate_pdf(),
    "oil_report.pdf",
    "application/pdf"
)
