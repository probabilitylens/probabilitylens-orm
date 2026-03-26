# ============================================================
# ProbabilityLens — v13.3 INSTITUTIONAL PLATFORM
# Bloomberg-style UI + Risk + Execution + Reporting
# ============================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pickle
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ============================================================
# CONFIG
# ============================================================

INITIAL_CAPITAL = 1_000_000
ASSETS = ["CL=F","XLE","SPY","TLT","DX-Y.NYB","GLD"]
BENCHMARK = "SPY"
STATE_FILE = "state.pkl"

MAX_WEIGHT = 0.25
TCOST = 0.0005  # 5bps
SLIPPAGE = 0.0005

EXECUTE = False

# ============================================================
# DATA
# ============================================================

@st.cache_data
def load_data():
    data = yf.download(ASSETS, period="2y", auto_adjust=True, progress=False)["Close"]
    return data.dropna()

# ============================================================
# FEATURES
# ============================================================

def returns(prices):
    return np.log(prices / prices.shift(1)).dropna()

def cov_matrix(r):
    return r.rolling(60).cov().dropna()

# ============================================================
# REGIME DETECTION
# ============================================================

def detect_regime(r):

    vol = r.rolling(20).std().mean(axis=1)
    trend = r.rolling(50).mean().mean(axis=1)

    regime = []

    for v, t in zip(vol, trend):
        if v > vol.quantile(0.8):
            regime.append("CRISIS")
        elif t > 0:
            regime.append("TREND")
        else:
            regime.append("MEAN_REVERT")

    return pd.Series(regime, index=r.index)

# ============================================================
# SIGNALS
# ============================================================

def signals(r, m_w, mr_w):

    mom = r.rolling(20).mean()
    z = (r - r.rolling(20).mean()) / r.rolling(20).std()

    s = m_w * mom - mr_w * z
    return s.fillna(0)

# ============================================================
# PORTFOLIO
# ============================================================

def positions(sig, prices, capital):

    w = sig.div(sig.abs().sum(axis=1), axis=0).fillna(0)
    w = w.clip(-MAX_WEIGHT, MAX_WEIGHT)

    pos = (w * capital) / prices

    return pos, w

# ============================================================
# COST MODEL
# ============================================================

def transaction_costs(pos):
    turnover = pos.diff().abs().sum(axis=1)
    return turnover * (TCOST + SLIPPAGE)

# ============================================================
# PnL
# ============================================================

def pnl_engine(pos, prices):

    raw = (pos.shift(1) * prices.diff()).sum(axis=1)
    cost = transaction_costs(pos)

    return (raw - cost).fillna(0)

def equity_curve(pnl, capital):
    return capital + pnl.cumsum()

# ============================================================
# RISK
# ============================================================

def portfolio_vol(w, cov):

    out = []

    for d in w.index:
        try:
            ww = w.loc[d].values
            c = cov.loc[d]

            if isinstance(c, pd.Series):
                c = c.unstack()

            vol = np.sqrt(ww.T @ c.values @ ww) * np.sqrt(252)
        except:
            vol = np.nan

        out.append(vol)

    return pd.Series(out, index=w.index)

def risk_contribution(w, cov):

    last_w = w.iloc[-1].values
    last_cov = cov.iloc[-1]

    if isinstance(last_cov, pd.Series):
        last_cov = last_cov.unstack()

    port_var = last_w.T @ last_cov.values @ last_w

    contrib = last_w * (last_cov.values @ last_w) / port_var

    return pd.Series(contrib, index=w.columns)

# ============================================================
# METRICS
# ============================================================

def sharpe(r):
    r = r.dropna()
    return 0 if r.std()==0 else r.mean()/r.std()*np.sqrt(252)

def ir(p, b):
    df = pd.concat([p,b], axis=1).dropna()
    df.columns=["p","b"]
    a = df["p"]-df["b"]
    return 0 if a.std()==0 else a.mean()/a.std()*np.sqrt(252)

# ============================================================
# STATE
# ============================================================

def save_state(s):
    with open(STATE_FILE,"wb") as f:
        pickle.dump(s,f)

def load_state():
    if os.path.exists(STATE_FILE):
        return pickle.load(open(STATE_FILE,"rb"))
    return None

# ============================================================
# EXECUTION
# ============================================================

def execution(target, current, prices):

    delta = target - current
    rows = []

    for a in delta.columns:
        size = delta[a].iloc[-1]
        price = prices[a].iloc[-1]

        rows.append({
            "asset":a,
            "size":size,
            "notional":size*price,
            "status":"BLOCKED",
            "reason":"EXECUTE=False"
        })

    return pd.DataFrame(rows)

# ============================================================
# NARRATIVE
# ============================================================

def narrative(res, regime):

    w = res["weights"].iloc[-1]

    return f"""
    The system is operating under a {regime.iloc[-1]} regime.

    Allocation is driven by cross-asset momentum and mean-reversion dynamics.

    Largest long: {w.idxmax()}
    Largest short: {w.idxmin()}

    Risk is actively managed via covariance constraints and position caps.

    Execution remains disabled under safety controls.
    """

# ============================================================
# PDF REPORT
# ============================================================

def generate_pdf(text):

    doc = SimpleDocTemplate("report.pdf")
    styles = getSampleStyleSheet()

    story = []

    story.append(Paragraph("ProbabilityLens Report", styles["Title"]))
    story.append(Spacer(1,12))
    story.append(Paragraph(text, styles["BodyText"]))

    doc.build(story)

    return "report.pdf"

# ============================================================
# PIPELINE
# ============================================================

def run(capital, m_w, mr_w):

    prices = load_data()
    r = returns(prices)

    sig = signals(r, m_w, mr_w)

    state = load_state()
    current = pd.DataFrame(0, index=sig.index, columns=sig.columns) if state is None else state["pos"]

    pos, w = positions(sig, prices, capital)

    pnl = pnl_engine(pos, prices)
    eq = equity_curve(pnl, capital)

    cov = cov_matrix(r)
    vol = portfolio_vol(w, cov)

    regime = detect_regime(r)

    p_ret = pnl / eq.shift(1)
    b_ret = r[BENCHMARK]

    res = {
        "equity":eq,
        "pnl":pnl,
        "weights":w,
        "positions":pos,
        "vol":vol,
        "sharpe":sharpe(p_ret),
        "ir":ir(p_ret,b_ret),
        "execution":execution(pos,current,prices),
        "risk_contrib":risk_contribution(w,cov),
        "regime":regime
    }

    save_state({"pos":pos})

    return res

# ============================================================
# UI — BLOOMBERG STYLE
# ============================================================

def system_strip(res):

    eq = res["equity"]
    dd = (eq/eq.cummax()-1).min()

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("System","ACTIVE")
    c2.metric("Execution","BLOCKED")
    c3.metric("Max DD",f"{dd:.2%}")
    c4.metric("Regime",res["regime"].iloc[-1])

# ============================================================
# MAIN UI
# ============================================================

st.set_page_config(layout="wide")

st.title("ProbabilityLens — v13.3")

capital = st.sidebar.number_input("Capital",value=INITIAL_CAPITAL)
m_w = st.sidebar.slider("Momentum",0.0,1.0,0.5)
mr_w = st.sidebar.slider("MeanRev",0.0,1.0,0.5)

res = run(capital,m_w,mr_w)

system_strip(res)

tab1,tab2,tab3,tab4 = st.tabs(["Overview","Risk","Execution","Report"])

# ================= OVERVIEW =================
with tab1:
    c1,c2,c3 = st.columns(3)
    c1.metric("Sharpe",f"{res['sharpe']:.2f}")
    c2.metric("IR",f"{res['ir']:.2f}")
    c3.metric("Vol",f"{res['vol'].dropna().iloc[-1]:.2%}")

    st.line_chart(res["equity"])
    st.line_chart(res["pnl"])

# ================= RISK =================
with tab2:
    st.subheader("Portfolio Volatility")
    st.line_chart(res["vol"])

    st.subheader("Risk Contribution")
    st.bar_chart(res["risk_contrib"])

# ================= EXECUTION =================
with tab3:
    st.dataframe(res["execution"])

# ================= REPORT =================
with tab4:

    text = narrative(res, res["regime"])

    st.subheader("Narrative")
    st.write(text)

    if st.button("Generate PDF"):
        path = generate_pdf(text)
        with open(path,"rb") as f:
            st.download_button("Download Report", f, file_name="report.pdf")
