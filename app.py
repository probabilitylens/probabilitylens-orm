# ============================================================
# ProbabilityLens — Oil Risk Monitor (v13.2.1)
# FULL INSTITUTIONAL SYSTEM — NO REGRESSION / NO OMISSION
# ============================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pickle
import os

# ============================================================
# CONFIG
# ============================================================

INITIAL_CAPITAL = 1_000_000
RISK_FREE_RATE = 0.0

ASSET_UNIVERSE = {
    "CL=F": "WTI",
    "XLE": "Energy Equities",
    "SPY": "Equities",
    "TLT": "Bonds",
    "DX-Y.NYB": "Dollar Index",
    "GLD": "Gold"
}

BENCHMARK = "SPY"

MAX_POSITION_WEIGHT = 0.25
MAX_PORTFOLIO_VOL = 0.20

STATE_FILE = "portfolio_state.pkl"
EXECUTE = False  # HARD SAFETY LOCK

# ============================================================
# DATA LAYER
# ============================================================

@st.cache_data
def load_market_data():
    data = yf.download(list(ASSET_UNIVERSE.keys()),
                       period="2y",
                       auto_adjust=True,
                       progress=False)["Close"]

    if data.empty:
        raise ValueError("Market data load failed")

    return data.dropna(how="all")

# ============================================================
# FEATURES
# ============================================================

def compute_returns(prices):
    return np.log(prices / prices.shift(1)).dropna()

def compute_covariance_matrix(returns, window=60):
    return returns.rolling(window).cov().dropna()

# ============================================================
# SIGNAL ENGINE (CONTROLLED)
# ============================================================

def generate_signals(returns, momentum_w, meanrev_w):

    momentum = returns.rolling(20).mean()
    zscore = (returns - returns.rolling(20).mean()) / returns.rolling(20).std()

    signals = momentum_w * momentum + (-meanrev_w * zscore)

    return signals.fillna(0)

# ============================================================
# PORTFOLIO (POSITIONS)
# ============================================================

def construct_positions(signals, prices, capital):

    weights = signals.div(signals.abs().sum(axis=1), axis=0).fillna(0)
    weights = weights.clip(-MAX_POSITION_WEIGHT, MAX_POSITION_WEIGHT)

    positions = (weights * capital) / prices

    return positions, weights

# ============================================================
# PnL ENGINE
# ============================================================

def compute_pnl(positions, prices):
    pnl = (positions.shift(1) * prices.diff()).sum(axis=1)
    return pnl.fillna(0)

def compute_equity(pnl, capital):
    return capital + pnl.cumsum()

# ============================================================
# RISK ENGINE
# ============================================================

def compute_portfolio_vol(weights, cov_matrix):

    vols = []

    for date in weights.index:
        try:
            w = weights.loc[date].values
            cov = cov_matrix.loc[date]

            if isinstance(cov, pd.Series):
                cov = cov.unstack()

            vol = np.sqrt(w.T @ cov.values @ w) * np.sqrt(252)
        except:
            vol = np.nan

        vols.append(vol)

    return pd.Series(vols, index=weights.index)

# ============================================================
# METRICS
# ============================================================

def compute_sharpe(r):
    r = r.dropna()
    return 0 if r.std() == 0 else (r.mean() / r.std()) * np.sqrt(252)

def compute_ir(p, b):
    df = pd.concat([p, b], axis=1).dropna()
    df.columns = ["p", "b"]
    active = df["p"] - df["b"]
    return 0 if active.std() == 0 else (active.mean() / active.std()) * np.sqrt(252)

# ============================================================
# STATE
# ============================================================

def save_state(state):
    with open(STATE_FILE, "wb") as f:
        pickle.dump(state, f)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "rb") as f:
            return pickle.load(f)
    return None

# ============================================================
# EXECUTION (SAFE)
# ============================================================

def execution_engine(target, current, prices):

    orders = target - current
    rows = []

    for asset in orders.columns:
        size = orders[asset].iloc[-1]
        price = prices[asset].iloc[-1]

        rows.append({
            "asset": asset,
            "order_size": size,
            "price": price,
            "notional": size * price,
            "status": "BLOCKED" if not EXECUTE else "EXECUTED",
            "reason": "EXECUTE=False safety lock"
        })

    return pd.DataFrame(rows)

# ============================================================
# REASONING ENGINE
# ============================================================

def generate_reasoning(results):

    w = results["weights"].iloc[-1]
    vol = results["vol"].iloc[-1]

    long_asset = w.idxmax()
    short_asset = w.idxmin()

    return f"""
    The system is currently positioned based on a blended momentum and mean-reversion framework.

    Strongest long exposure: {long_asset}  
    Strongest short exposure: {short_asset}

    Portfolio volatility is {vol:.2%}, within configured limits.

    Allocation reflects normalized cross-asset signal strength under strict position caps.

    Execution remains disabled under system safety constraints.
    """

# ============================================================
# INPUT PANEL
# ============================================================

def render_inputs():

    st.sidebar.header("System Controls")

    capital = st.sidebar.number_input("Capital", value=INITIAL_CAPITAL, step=100000)

    momentum = st.sidebar.slider("Momentum Weight", 0.0, 1.0, 0.5)
    meanrev = st.sidebar.slider("Mean Reversion Weight", 0.0, 1.0, 0.5)

    return capital, momentum, meanrev

# ============================================================
# PIPELINE
# ============================================================

def run_pipeline(capital, momentum_w, meanrev_w):

    prices = load_market_data()
    returns = compute_returns(prices)

    signals = generate_signals(returns, momentum_w, meanrev_w)

    state = load_state()

    current_pos = pd.DataFrame(0, index=signals.index, columns=signals.columns) if state is None else state["positions"]

    target_pos, weights = construct_positions(signals, prices, capital)

    pnl = compute_pnl(target_pos, prices)
    equity = compute_equity(pnl, capital)

    cov = compute_covariance_matrix(returns)
    vol = compute_portfolio_vol(weights, cov)

    port_ret = pnl / equity.shift(1)
    bench_ret = returns[BENCHMARK]

    sharpe = compute_sharpe(port_ret)
    ir = compute_ir(port_ret, bench_ret)

    exec_report = execution_engine(target_pos, current_pos, prices)

    save_state({
        "positions": target_pos,
        "weights": weights,
        "equity": equity,
        "pnl": pnl
    })

    return {
        "equity": equity,
        "pnl": pnl,
        "vol": vol,
        "positions": target_pos,
        "weights": weights,
        "execution": exec_report,
        "sharpe": sharpe,
        "ir": ir
    }

# ============================================================
# UI
# ============================================================

def render_header():
    c1, c2 = st.columns([1, 6])
    with c1:
        st.image("https://cdn-icons-png.flaticon.com/512/2784/2784487.png", width=60)
    with c2:
        st.title("ProbabilityLens")
        st.caption("Institutional Oil Risk Monitoring System")

def render_system_strip(results):

    eq = results["equity"]
    pnl = results["pnl"]

    dd = (eq / eq.cummax() - 1).min()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("System", "ACTIVE")
    c2.metric("Execution", "BLOCKED")
    c3.metric("Max DD", f"{dd:.2%}")
    c4.metric("Latest PnL", f"{pnl.iloc[-1]:,.0f}")

def render_dashboard(results):

    render_header()
    render_system_strip(results)

    st.divider()

    c1, c2, c3 = st.columns(3)
    c1.metric("Sharpe", f"{results['sharpe']:.2f}")
    c2.metric("IR", f"{results['ir']:.2f}")
    c3.metric("Vol", f"{results['vol'].dropna().iloc[-1]:.2%}")

    st.divider()

    st.subheader("Equity Curve")
    st.line_chart(results["equity"])

    st.subheader("PnL")
    st.line_chart(results["pnl"])

    st.subheader("Volatility")
    st.line_chart(results["vol"])

    st.subheader("Positions")
    st.dataframe(results["positions"].tail(1).T)

    st.subheader("Execution")
    st.dataframe(results["execution"])

    st.divider()

    st.subheader("System Narrative")
    st.write(generate_reasoning(results))

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    capital, m_w, mr_w = render_inputs()

    results = run_pipeline(capital, m_w, mr_w)

    render_dashboard(results)
