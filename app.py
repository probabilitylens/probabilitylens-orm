# app.py

import streamlit as st
from pipeline import run_pipeline

st.title("ProbabilityLens")

params = {
    "tickers": ["CL=F", "DX-Y.NYB", "GLD", "SPY", "TLT", "XLE"],
    "start": "2020-01-01",
    "end": None,
    "capital": 1_000_000,
    "max_leverage": 1.0,
}

res = run_pipeline(params)

# ---------------------------
# Defensive Check (MANDATORY)
# ---------------------------
if "equity" not in res:
    st.error(f"Missing 'equity' in pipeline output. Keys: {list(res.keys())}")
    st.stop()

# ---------------------------
# Chart
# ---------------------------
st.subheader("Equity Curve")
st.line_chart(res["equity"])

# Optional debug visibility
with st.expander("Debug Info"):
    st.write("Keys:", list(res.keys()))
    st.write("Equity tail:", res["equity"].tail())
