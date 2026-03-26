import streamlit as st
from pipeline import run_pipeline

st.set_page_config(layout="wide")

params={
 "capital":1_000_000,
 "signal":{"momentum_weight":0.5,"meanrev_weight":0.5},
 "portfolio":{"max_weight":0.25},
 "execution":{"execute":False,"min_order_size":0},
 "costs":{"transaction_cost":0.0005,"slippage":0.0005}
}

res=run_pipeline(params)

st.title("ProbabilityLens")

st.line_chart(res["equity"])
st.dataframe(res["execution_report"])
st.write(res["reasoning"])
