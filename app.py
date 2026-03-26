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
EXECUTE = False

# =========================
# DATA (v1-v4)
# =========================
def extract_time_series(df):
    best, max_len = None, 0
    for c1 in df.columns:
        d = pd.to_datetime(df[c1], errors='coerce')
        if d.notna().sum() < 10:
            continue
        for c2 in df.columns:
            v = pd.to_numeric(df[c2], errors='coerce')
            m = d.notna() & v.notna()
            if m.sum() > max_len:
                best = pd.DataFrame({"date": d[m], "price": v[m]}).sort_values("date")
                max_len = len(best)
    return best

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
# FACTORS (v3)
# =========================
def compute_factors(df):
    l = df.iloc[-1]
    return {
        "signal": np.tanh(2*l["trend_20"]+l["trend_60"]),
        "timing": np.clip(-abs(l["zscore"]),-1,1),
        "confirmation": np.mean(np.sign([l["trend_20"],l["momentum_20"],l["returns"]])),
        "alignment": 1 if np.sign(l["trend_20"])==np.sign(l["trend_60"]) else -1,
        "crowding": -np.tanh(l["zscore"]),
        "health": 0,
        "capital": np.tanh(l["trend_20"]/(l["vol_20"]+EPS)),
        "vol": l["vol_20"]
    }

# =========================
# MODEL (v3)
# =========================
def compute_model(f):
    w = dict(signal=.25,timing=.15,confirmation=.15,alignment=.1,crowding=.1,health=.15,capital=.1)
    c = sum(f[k]*w[k] for k in w)
    regime = "ACTIVE LONG" if c>0.6 else "ACTIVE SHORT" if c<-0.6 else "NEUTRAL"
    return c, regime

# =========================
# FORWARD + MACRO (v5)
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
def strategy_trend(df): return compute_model(compute_factors(df))[0]
def strategy_mr(df): return -np.tanh(df["zscore"].iloc[-1])
def strategy_breakout(df):
    p=df["price"].iloc[-1]
    hi=df["price"].rolling(20).max().iloc[-1]
    lo=df["price"].rolling(20).min().iloc[-1]
    return 1 if p>=hi else -1 if p<=lo else 0

def strategy_signals(df):
    return {
        "trend": strategy_trend(df),
        "mean_reversion": strategy_mr(df),
        "breakout": strategy_breakout(df)
    }

# =========================
# ALLOCATION (v6+v10)
# =========================
def allocate_strategies(s):
    w={k:abs(v) for k,v in s.items()}
    tot=sum(w.values())+EPS
    return {k:v/tot for k,v in w.items()}

def portfolio_allocation(c):
    return {"OIL": abs(c)}

# =========================
# RISK ENGINE (v9)
# =========================
def risk_engine(p, vol, pnl):
    if KILL_SWITCH:
        return {}, "KILL"
    if pnl.tail(5).sum() < STOP_LOSS_THRESHOLD:
        return {}, "STOP"
    p={k:min(v,MAX_POSITION_SIZE) for k,v in p.items()}
    return p,"OK"

# =========================
# EXECUTION (v8)
# =========================
def place_order(symbol, qty):
    if not EXECUTE:
        return "blocked"
    return "sent"

# =========================
# PnL (v7)
# =========================
def compute_pnl(df):
    pnl=df["returns"]
    return pnl, pnl.cumsum()

# =========================
# DASHBOARD (v13)
# =========================
st.set_page_config(layout="wide")
st.title("ProbabilityLens — Institutional Dashboard (v13)")

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

portfolio = portfolio_allocation(combined)

pnl, cum = compute_pnl(df)
portfolio, risk_status = risk_engine(portfolio, f["vol"], pnl)

# =========================
# ROW 1 — SYSTEM
# =========================
c1,c2,c3,c4 = st.columns(4)
c1.metric("System","RUNNING")
c2.metric("Risk",risk_status)
c3.metric("Kill Switch",str(KILL_SWITCH))
c4.metric("Drawdown",f"{(cum-cum.cummax()).min():.2%}")

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
left.subheader("Portfolio")
left.bar_chart(portfolio)

right.subheader("Strategy Allocation")
right.bar_chart(strat_w)

# =========================
# ROW 4 — RISK
# =========================
r1,r2,r3 = st.columns(3)
r1.metric("Max Position",f"{MAX_POSITION_SIZE:.0%}")
r2.metric("Max DD",f"{MAX_DRAWDOWN:.0%}")
r3.metric("Stop Loss",f"{STOP_LOSS_THRESHOLD:.0%}")

# =========================
# ROW 5 — PERFORMANCE
# =========================
st.subheader("PnL")
st.line_chart(cum)

# =========================
# ROW 6 — REALTIME SIM
# =========================
def realtime(df):
    out=[]
    for i in range(60,len(df)):
        sub=df.iloc[:i]
        c,_=compute_model(compute_factors(sub))
        out.append(c)
    return pd.Series(out)

st.subheader("Realtime Simulation")
st.line_chart(realtime(df))

# =========================
# EXECUTION PANEL
# =========================
st.subheader("Execution")
if st.button("Execute Trade"):
    res = place_order("USO",10)
    st.write(res)
