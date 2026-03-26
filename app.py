# ============================================================
# ProbabilityLens — v13.3.1 (HARDENED)
# FULL SYSTEM — NO REGRESSION / NO OMISSION
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
TCOST = 0.0005
SLIPPAGE = 0.0005

EXECUTE = False

# ============================================================
# LOGGING SYSTEM
# ============================================================

LOGS = []

def log(msg):
    LOGS.append(msg)

# ============================================================
# DATA
# ============================================================

@st.cache_data
def load_data():
    try:
        data = yf.download(ASSETS, period="2y", auto_adjust=True, progress=False)["Close"]
        data = data.dropna(how="all")

        if data.empty:
            raise ValueError("Empty market data")

        return data

    except Exception as e:
        log(f"DATA ERROR: {e}")
        return pd.DataFrame()

# ============================================================
# FEATURES
# ============================================================

def returns(prices):
    try:
        return np.log(prices / prices.shift(1)).dropna()
    except:
        log("Returns calculation failed")
        return pd.DataFrame()

def cov_matrix(r):
    try:
        cov = r.rolling(60).cov()
        return cov.dropna()
    except:
        log("Covariance calculation failed")
        return pd.DataFrame()

# ============================================================
# REGIME
# ============================================================

def detect_regime(r):

    try:
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

    except:
        log("Regime detection failed")
        return pd.Series(["UNKNOWN"] * len(r), index=r.index)

# ============================================================
# SIGNALS
# ============================================================

def signals(r, m_w, mr_w):
    try:
        mom = r.rolling(20).mean()
        z = (r - r.rolling(20).mean()) / r.rolling(20).std()
        return (m_w * mom - mr_w * z).fillna(0)
    except:
        log("Signal generation failed")
        return pd.DataFrame(0, index=r.index, columns=r.columns)

# ============================================================
# PORTFOLIO
# ============================================================

def positions(sig, prices, capital):
    try:
        w = sig.div(sig.abs().sum(axis=1), axis=0).fillna(0)
        w = w.clip(-MAX_WEIGHT, MAX_WEIGHT)
        pos = (w * capital) / prices
        return pos, w
    except:
        log("Position construction failed")
        return pd.DataFrame(), pd.DataFrame()

# ============================================================
# COST MODEL
# ============================================================

def transaction_costs(pos):
    try:
        turnover = pos.diff().abs().sum(axis=1)
        return turnover * (TCOST + SLIPPAGE)
    except:
        log("Transaction cost calc failed")
        return 0

# ============================================================
# PnL
# ============================================================

def pnl_engine(pos, prices):
    try:
        raw = (pos.shift(1) * prices.diff()).sum(axis=1)
        cost = transaction_costs(pos)
        return (raw - cost).fillna(0)
    except:
        log("PnL calculation failed")
        return pd.Series(0, index=prices.index)

def equity_curve(pnl, capital):
    return capital + pnl.cumsum()

# ============================================================
# RISK
# ============================================================

def portfolio_vol(w, cov):

    vols = []

    for d in w.index:
        try:
            if isinstance(cov.index, pd.MultiIndex):
                c = cov.loc[d]
            else:
                vols.append(np.nan)
                continue

            if isinstance(c, pd.Series):
                c = c.unstack()

            ww = w.loc[d].values
            vol = np.sqrt(ww.T @ c.values @ ww) * np.sqrt(252)

        except:
            vol = np.nan

        vols.append(vol)

    return pd.Series(vols, index=w.index)

# ✅ FIXED FUNCTION
def risk_contribution(w, cov):

    try:
        last_w = w.iloc[-1]

        if isinstance(cov.index, pd.MultiIndex):
            last_cov = cov.loc[w.index[-1]]
        else:
            n = len(w.columns)
            vals = cov.tail(n).values.reshape(n, n)
            last_cov = pd.DataFrame(vals, index=w.columns, columns=w.columns)

        last_cov = last_cov.loc[w.columns, w.columns]

        w_vec = last_w.values
        port_var = w_vec.T @ last_cov.values @ w_vec

        if port_var == 0:
            return pd.Series(0, index=w.columns)

        contrib = w_vec * (last_cov.values @ w_vec) / port_var

        return pd.Series(contrib, index=w.columns)

    except Exception as e:
        log(f"Risk contribution failed: {e}")
        return pd.Series(0, index=w.columns)

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
    Regime: {regime.iloc[-1]}

    Largest Long: {w.idxmax()}
    Largest Short: {w.idxmin()}

    Portfolio constructed via momentum + mean reversion.

    Risk managed via covariance and constraints.

    Execution disabled (safety lock).
    """

# ============================================================
# PDF
# ============================================================

def generate_pdf(text):

    doc = SimpleDocTemplate("report.pdf")
    styles = getSampleStyleSheet()

    story = [
        Paragraph("ProbabilityLens Report", styles["Title"]),
        Spacer(1,12),
        Paragraph(text, styles["BodyText"])
    ]

    doc.build(story)
    return "report.pdf"

# ============================================================
# PIPELINE
# ============================================================

def run(capital, m_w, mr_w):

    prices = load_data()
    if prices.empty:
        st.error("Data unavailable")
        return None

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
# UI
# ============================================================

st.set_page_config(layout="wide")

st.title("ProbabilityLens — v13.3.1")

capital = st.sidebar.number_input("Capital", value=INITIAL_CAPITAL)
m_w = st.sidebar.slider("Momentum", 0.0, 1.0, 0.5)
mr_w = st.sidebar.slider("MeanRev", 0.0, 1.0, 0.5)

res = run(capital, m_w, mr_w)

if res:

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("System","ACTIVE")
    c2.metric("Execution","BLOCKED")
    c3.metric("Regime",res["regime"].iloc[-1])
    c4.metric("Sharpe",f"{res['sharpe']:.2f}")

    tab1,tab2,tab3,tab4,tab5 = st.tabs(
        ["Overview","Risk","Execution","Report","Logs"]
    )

    with tab1:
        st.line_chart(res["equity"])
        st.line_chart(res["pnl"])

    with tab2:
        st.line_chart(res["vol"])
        st.bar_chart(res["risk_contrib"])

    with tab3:
        st.dataframe(res["execution"])

    with tab4:
        text = narrative(res, res["regime"])
        st.write(text)

        if st.button("Generate PDF"):
            path = generate_pdf(text)
            with open(path,"rb") as f:
                st.download_button("Download", f)

    with tab5:
        st.write(LOGS)
