# FULL SYSTEM — NON-NEGOTIABLE STRUCTURE

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from reportlab.platypus import *
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
import tempfile
import os
from datetime import datetime

st.set_page_config(layout="wide")

# =========================
# DATA
# =========================
df = pd.read_excel("data/wti.xls", sheet_name="Data 1")
df = df.iloc[:, :2]
df.columns = ["Date", "Price"]

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
df = df.dropna().sort_values("Date").tail(120)

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

vals = np.array([signal,timing,confirmation,alignment,crowding,market_health,capital])
score = vals.mean()*100

# =========================
# MODEL
# =========================
if score < 50:
    regime, action = "PREPARATION","NO POSITION"
elif score < 75:
    regime, action = "DEVELOPING","WAIT"
else:
    regime, action = "NEAR TRIGGER","ENTER"

conviction = int((1-np.std(vals))*100)
expected_move = (score/100)*(alignment+signal)*10

# =========================
# CHART
# =========================
fig = go.Figure()
fig.add_trace(go.Scatter(x=df["Date"], y=df["Price"], line=dict(color="white", width=3)))
fig.update_layout(template="plotly_dark")

# =========================
# UI LAYOUT
# =========================
left,right = st.columns([1.3,1.7])

with left:
    st.markdown(f"# {regime}")
    st.markdown(f"### {action}")
    st.metric("Conviction", f"{conviction}%")
    st.metric("Expected Move", f"{expected_move:.1f}%")

with right:
    st.plotly_chart(fig, use_container_width=True)

# =========================
# TRADE
# =========================
st.markdown("## Trade Expression")
st.markdown("""
Direction: LONG  
Entry: Upon confirmation + alignment > 0.7  
Horizon: 2–6 weeks  
Risk: Signal deterioration
""")

# =========================
# SIGNAL DIAGNOSTICS
# =========================
st.markdown("## Signal Diagnostics")

st.write(f"""
Signal: Weak directional bias  
Timing: Early-stage  
Confirmation: Insufficient  
Alignment: Fragmented  
Crowding: Neutral  
Market Health: Stable  
Capital: Available
""")

# =========================
# SCENARIOS
# =========================
st.markdown("## Scenario Analysis")

scenarios = pd.DataFrame({
    "Scenario":["Base","Bull","Bear"],
    "Probability":[0.5,0.25,0.25],
    "Move":["+3%","+8%","-5%"]
})

st.dataframe(scenarios)

# =========================
# PDF — FULL REPORT
# =========================
def generate_pdf():
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(tmp.name, pagesize=letter)
    styles = getSampleStyleSheet()

    content = []

    # HEADER
    content.append(Paragraph(f"WTI Report — {datetime.today().date()}", styles["Title"]))

    # EXEC SUMMARY
    content.append(Paragraph(
        f"The system is in {regime}. Current signals do not justify positioning.",
        styles["Normal"]
    ))

    # FULL STRUCTURE (ALL SECTIONS)
    sections = [
        "Market State",
        "Signal Diagnostics",
        "Mispricing",
        "Mechanism",
        "Positioning",
        "Scenarios",
        "Trade",
        "Decision Logic",
        "Conclusion"
    ]

    for s in sections:
        content.append(Spacer(1,10))
        content.append(Paragraph(f"<b>{s}</b>", styles["Heading2"]))
        content.append(Paragraph("Detailed explanation required.", styles["Normal"]))

    # chart
    img="chart.png"
    fig.write_image(img)
    content.append(RLImage(img, width=500, height=300))

    doc.build(content)
    return tmp.name

pdf = generate_pdf()

with open(pdf,"rb") as f:
    st.download_button("Download Full Report", f)
