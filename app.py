import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import time
import random

# =========================
# CONFIG
# =========================
EPS = 1e-8
MIN_OBS = 50
BASE_CAPITAL = 100000

# RISK CONFIG (v9)
MAX_POSITION_SIZE = 0.25
MAX_PORTFOLIO_VOL = 0.20
MAX_DRAWDOWN = -0.15
STOP_LOSS_THRESHOLD = -0.05
KILL_SWITCH = False

# BROKER (v8)
ALPACA_KEY = "YOUR_API_KEY"
ALPACA_SECRET = "YOUR_SECRET"
BASE_URL = "https://paper-api.alpaca.markets"
EXECUTE = False  # 🔴 stays OFF by default

# =========================
# DATA (v1–v4)
# =========================
@st.cache_data
def load_data():
    df = yf.download("CL=F", period="5y", progress=False)
    df = df.reset_index()[["Date", "Close"]]
    df.columns = ["date", "price"]
    return df

# =========================
# FEATURES (v3)
# =========================
def compute_features(df):
    df["returns"] = np.log(df["price"] / df["price"].shift(1))
    df["vol_20"] = df["returns"].rolling(20).std() * np.sqrt(252)
    df["trend_20"] = df["price"]/df["price"].rolling(20).mean() - 1
    df["trend_60"] = df["price"]/df["price"].rolling(60).mean() - 1
    df["momentum_20"] = df["price"].pct_change(20)
    df["zscore"] = (df["returns"]-df["returns"].mean())/(df["returns"].std()+EPS)
    return df.dropna()

# =========================
# FACTORS
# =========================
def compute_factors(df):
    l = df.iloc[-1]
    vol = l["vol_20"]

    # sanity cap (critical fix)
    vol = min(vol, 0.60)

    return {
        "signal": np.tanh(2*l["trend_20"]+l["trend_60"]),
        "timing": np.clip(-abs(l["zscore"]),-1,1),
        "confirmation": np.mean(np.sign([l["trend_20"],l["momentum_20"],l["returns"]])),
        "alignment": 1 if np.sign(l["trend_20"])==np.sign(l["trend_60"]) else -1,
        "crowding": -np.tanh(l["zscore"]),
        "health": 0,
        "capital": np.tanh(l["trend_20"]/(vol+EPS)),
        "vol": vol
    }

# =========================
# MODEL
# =========================
def compute_model(f):
    w = dict(signal=.25,timing=.15,confirmation=.15,alignment=.1,crowding=.1,health=.15,capital=.1)
    c = sum(f[k]*w[k] for k in w)
    regime = "ACTIVE LONG" if c>0.6 else "ACTIVE SHORT" if c<-0.6 else "NEUTRAL"
    return c, regime

# =========================
# v5
# =========================
def forward_signal(df):
    r=df["returns"]
    return np.clip(0.6*np.mean(np.sign(r.tail(10))==np.sign(df["trend_20"].iloc[-1]))+
                   0.4*np.tanh(r.tail(20).mean()*50),-1,1)

def macro_regime(df):
    v=df["vol_20"].iloc[-1]
    if v>0.3: return "STRESS"
    if v<0.1: return "LOW VOL"
    return "NORMAL"

# =========================
# STRATEGIES (v10)
# =========================
def strategy_signals(df):
    return {
        "trend": compute_model(compute_factors(df))[0],
        "mean_reversion": -np.tanh(df["zscore"].iloc[-1]),
        "breakout": np.sign(df["trend_20"].iloc[-1])
    }

def allocate_strategies(s):
    w={k:abs(v) for k,v in s.items()}
    tot=sum(w.values())+EPS
    return {k:v/tot for k,v in w.items()}

# =========================
# PORTFOLIO (v6)
# =========================
def portfolio_allocation(c):
    return {"OIL": abs(c)}

# =========================
# RISK ENGINE (v9 FIXED)
# =========================
def risk_engine(p, vol, pnl, drawdown):
    if KILL_SWITCH:
        return {}, "KILL_SWITCH"

    if pnl.tail(5).sum() / BASE_CAPITAL < STOP_LOSS_THRESHOLD:
        return {}, "STOP_LOSS"

    if drawdown < MAX_DRAWDOWN:
        return {}, "DRAWDOWN_LIMIT"

    if vol > MAX_PORTFOLIO_VOL:
        p = {k: v * 0.5 for k, v in p.items()}
        return p, "DEGRADED"

    p={k:min(v,MAX_POSITION_SIZE) for k,v in p.items()}

    return p,"APPROVED"

# =========================
# EXECUTION (v8 IMPROVED)
# =========================
def place_order(symbol, qty):
    if not EXECUTE:
        return {"status": "BLOCKED", "reason": "EXECUTE=False"}
    return {"status": "SENT", "symbol": symbol, "qty": qty}

# =========================
# PnL ENGINE (v7 FIXED)
# =========================
def compute_pnl(df, signal):
    returns = df["returns"]
    position = np.sign(signal)

    pnl = position * returns * BASE_CAPITAL
    cum = pnl.cumsum()

    drawdown = (cum - cum.cummax()) / BASE_CAPITAL

    return pnl, cum, drawdown

# =========================
# UI
# =========================
st.set_page_config(layout="wide")
st.title("ProbabilityLens — Institutional Dashboard (v13.1)")

df = load_data()
df = compute_features(df)

f = compute_factors(df)
conviction, regime = compute_model(f)
fwd = forward_signal(df)
macro = macro_regime(df)

combined = 0.7*conviction + 0.3*fwd

# strategies
sigs = strategy_signals(df)
strat_w = allocate_strategies(sigs)

portfolio_raw = portfolio_allocation(combined)

# PnL FIXED
pnl, cum, drawdown = compute_pnl(df, combined)

# Risk
portfolio, risk_status = risk_engine(
    portfolio_raw,
    f["vol"],
    pnl,
    drawdown.iloc[-1]
)

# =========================
# ROW 1 — SYSTEM
# =========================
c1,c2,c3,c4 = st.columns(4)
c1.metric("System","RUNNING")
c2.metric("Risk Engine",risk_status)
c3.metric("Kill Switch",str(KILL_SWITCH))
c4.metric("Drawdown",f"{drawdown.min():.2%}")

# =========================
# ROW 2 — CORE
# =========================
c5,c6,c7,c8 = st.columns(4)
c5.metric("Conviction",f"{combined:.2f}")
c6.metric("Regime",regime)
c7.metric("Forward",f"{fwd:.2f}")
c8.metric("Vol",f"{f['vol']:.2%}")

# =========================
# ROW 3 — PORTFOLIO
# =========================
left,right = st.columns(2)
left.subheader("Portfolio Allocation")
left.bar_chart(portfolio)

right.subheader("Strategy Allocation")
right.bar_chart(strat_w)

# =========================
# ROW 4 — RISK
# =========================
r1,r2,r3 = st.columns(3)
r1.metric("Max Position",f"{MAX_POSITION_SIZE:.0%}")
r2.metric("Max DD Limit",f"{MAX_DRAWDOWN:.0%}")
r3.metric("Stop Loss",f"{STOP_LOSS_THRESHOLD:.0%}")

# =========================
# ROW 5 — PERFORMANCE (FIXED)
# =========================
st.subheader("PnL (Capital-Based)")
st.line_chart(cum)

# =========================
# ROW 6 — SIGNAL EVOLUTION (FIXED LABEL)
# =========================
def signal_evolution(df):
    out=[]
    for i in range(60,len(df)):
        sub=df.iloc[:i]
        c,_=compute_model(compute_factors(sub))
        out.append(c)
    return pd.Series(out)

st.subheader("Signal Evolution (Not PnL)")
st.line_chart(signal_evolution(df))

# =========================
# EXECUTION PANEL (FIXED)
# =========================
st.subheader("Execution")

exec_info = {
    "execution_enabled": EXECUTE,
    "risk_status": risk_status,
    "kill_switch": KILL_SWITCH
}
st.write(exec_info)

if st.button("Execute Trade"):
    result = place_order("USO", 10)
    st.write(result)
