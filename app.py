import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import base64
import io

st.set_page_config(layout="wide")

# =========================================================
# DATA LOADER (ROBUST — NEVER BREAKS)
# =========================================================
@st.cache_data
def load_wti():
    try:
        raw = pd.read_excel("data/wti.xls", sheet_name=0, header=None)

        start_row = None
        for i in range(len(raw)):
            try:
                pd.to_datetime(raw.iloc[i, 0])
                start_row = i
                break
            except:
                continue

        if start_row is None:
            raise Exception("No valid date row found")

        df = raw.iloc[start_row:].copy()
        df = df.iloc[:, :2]
        df.columns = ["Date", "Price"]

        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

        df = df.dropna()
        df = df.sort_values("Date").tail(120)

        return df

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
# CALCULATIONS
# =========================================================
scores = np.array([signal, timing, confirmation, alignment, crowding, market, capital])
weights = np.array([1,1,1,1,1,1,1])
conviction = np.dot(scores, weights) / weights.sum()

expected_move = (df["Price"].pct_change().std() * np.sqrt(10)) * conviction

regime = "PREPARATION" if conviction < 0.6 else "ACTIVE"
action = "NO POSITION" if conviction < 0.6 else "ENTER TRADE"

# =========================================================
# HEADER
# =========================================================
col_logo, col_title = st.columns([1,5])

with col_logo:
    st.image("Logo.png", width=120)

with col_title:
    st.markdown("## ProbabilityLens")
    st.markdown("Oil Risk Monitor — Decision Engine")

st.divider()

# =========================================================
# MAIN LAYOUT
# =========================================================
col1, col2 = st.columns([1,1])

# ================= LEFT =================
with col1:

    st.markdown("### Decision")

    st.markdown(f"""
    <div style="background:#6b7280;padding:20px;border-radius:10px;color:white">
        <h2>{regime}</h2>
        <b>Action:</b> {action}<br>
        <b>Conviction:</b> {round(conviction*100)}%<br>
        <b>Expected Move:</b> {round(expected_move*100,2)}%
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Trade Expression")
    st.write(f"Direction: LONG")
    st.write(f"Horizon: 2–6 weeks")
    st.write(f"Conviction: {round(conviction*100)}%")

    st.markdown("### Signal Diagnostics")
    st.write(f"Signal: {'Weak' if signal<0.5 else 'Strong'}")
    st.write(f"Timing: {'Early' if timing<0.5 else 'Mature'}")
    st.write(f"Confirmation: {'Low' if confirmation<0.5 else 'High'}")
    st.write(f"Alignment: {'Fragmented' if alignment<0.6 else 'Aligned'}")
    st.write(f"Crowding: {'Neutral' if crowding<0.6 else 'Crowded'}")

    st.markdown("### Scenario Analysis")

    scenarios = pd.DataFrame({
        "Scenario":["Base","Bull","Bear"],
        "Probability":[0.5,0.25,0.25],
        "Move":["+3%","+8%","-5%"]
    })
    st.dataframe(scenarios, use_container_width=True)

# ================= RIGHT =================
with col2:

    st.markdown("### WTI Price")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Date"], y=df["Price"], line=dict(color="white")))
    fig.update_layout(template="plotly_dark", height=400)

    st.plotly_chart(fig, use_container_width=True)

# =========================================================
# PDF REPORT ENGINE (REAL TEXT)
# =========================================================
def generate_report_text():

    text = f"""
    Executive Summary

    Current market conditions indicate a {regime.lower()} regime, with an aggregate conviction level of {round(conviction*100)} percent. 
    Despite improving alignment and stable market conditions, confirmation signals remain insufficient to justify immediate positioning.

    Market Situation

    Oil prices have demonstrated recent upward momentum, but the move appears partially driven by positioning rather than fundamental confirmation.
    Macro signals remain fragmented, and no dominant narrative has emerged to support sustained directional conviction.

    Signal Assessment

    The signal complex remains weak to moderate. Timing is early-stage, while confirmation remains below threshold levels. 
    Alignment across factors has improved but is not yet decisive. Crowding metrics remain neutral, suggesting limited positioning risk.

    Positioning Implications

    Given the current signal structure, risk-reward does not justify active positioning. 
    The model recommends maintaining optionality while monitoring for improved confirmation and alignment.

    Decision

    Regime: {regime}
    Action: {action}

    Conclusion

    The market is transitioning but not yet actionable. The appropriate strategy is preparation rather than execution.
    """

    return text

def generate_pdf():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    content = []
    for line in generate_report_text().split("\n"):
        content.append(Paragraph(line, styles["Normal"]))
        content.append(Spacer(1,10))

    doc.build(content)
    buffer.seek(0)

    return buffer

# =========================================================
# DOWNLOAD BUTTON
# =========================================================
pdf = generate_pdf()

st.download_button(
    label="Download Full Report",
    data=pdf,
    file_name="Oil_Market_Report.pdf",
    mime="application/pdf"
)
