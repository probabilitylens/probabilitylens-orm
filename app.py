# ============================================================
# ProbabilityLens — Oil Risk Monitor (v13.2)
# FULL INSTITUTIONAL BUILD — NO REGRESSION / NO OMISSION
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

EXECUTE = False  # HARD SAFETY

# ============================================================
# DATA LAYER
# ============================================================

@st.cache_data
def load_market_data():
    data = yf.download(
        list(ASSET_UNIVERSE.keys()),
        period="2y",
        auto_adjust=True,
        progress=False
    )["Close"]

    if data.empty:
        raise ValueError("Market data load failed")

    data = data.dropna(how="all")

    return data

# ============================================================
# FEATURE ENGINEERING
# ============================================================

def compute_returns(prices):
    returns = np.log(prices / prices.shift(1))
    return returns.dropna()

def compute_volatility(returns, window=20):
    return returns.rolling(window).std() * np.sqrt(252)

def compute_covariance_matrix(returns, window=60):
    return returns.rolling(window).cov().dropna()

# ============================================================
# SIGNAL ENGINE
# ============================================================

def generate_signals(returns):
    momentum = returns.rolling(20).mean()
    zscore = (returns - returns.rolling(20).mean()) / returns.rolling(20).std()

    signals = 0.5 * momentum + (-0.5 * zscore)
    return signals.fillna(0)

# ============================================================
# PORTFOLIO CONSTRUCTION (POSITIONS, NOT WEIGHTS)
# ============================================================

def construct_positions(signals, prices, capital):

    weights = signals.div(signals.abs().sum(axis=1), axis=0).fillna(0)

    weights = weights.clip(-MAX_POSITION_WEIGHT, MAX_POSITION_WEIGHT)

    positions = (weights * capital) / prices

    return positions, weights

# ============================================================
# PnL ENGINE (TIME CONSISTENT)
# ============================================================

def compute_pnl(positions, prices):
    pnl = (positions.shift(1) * prices.diff()).sum(axis=1)
    return pnl.fillna(0)

def compute_equity_curve(pnl, initial_capital):
    equity = initial_capital + pnl.cumsum()
    return equity

# ============================================================
# RISK ENGINE (COVARIANCE BASED)
# ============================================================

def compute_portfolio_volatility(weights, cov_matrix):

    vol_series = []

    for date in weights.index:
        try:
            w = weights.loc[date].values

            cov_slice = cov_matrix.loc[date]

            if isinstance(cov_slice, pd.Series):
                cov_slice = cov_slice.unstack()

            cov = cov_slice.values

            vol = np.sqrt(w.T @ cov @ w) * np.sqrt(252)

        except:
            vol = np.nan

        vol_series.append(vol)

    return pd.Series(vol_series, index=weights.index)

# ============================================================
# PERFORMANCE METRICS
# ============================================================

def compute_sharpe(returns):
    returns = returns.dropna()
    if returns.std() == 0:
        return 0
    return (returns.mean() - RISK_FREE_RATE) / returns.std() * np.sqrt(252)

def compute_information_ratio(portfolio_returns, benchmark_returns):

    df = pd.concat([portfolio_returns, benchmark_returns], axis=1).dropna()
    df.columns = ["p", "b"]

    active = df["p"] - df["b"]

    if active.std() == 0:
        return 0

    return active.mean() / active.std() * np.sqrt(252)

# ============================================================
# STATE MANAGEMENT (CRITICAL)
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
# EXECUTION LAYER (SAFE / BLOCKED)
# ============================================================

def execution_engine(target_positions, current_positions, prices):

    orders = target_positions - current_positions

    execution_report = []

    for asset in orders.columns:
        size = orders[asset].iloc[-1]
        price = prices[asset].iloc[-1]
        notional = size * price

        if EXECUTE:
            status = "EXECUTED"
            reason = "Live execution enabled"
        else:
            status = "BLOCKED"
            reason = "EXECUTE=False safety lock"

        execution_report.append({
            "asset": asset,
            "order_size": size,
            "price": price,
            "notional": notional,
            "status": status,
            "reason": reason
        })

    return pd.DataFrame(execution_report)

# ============================================================
# MASTER PIPELINE
# ============================================================

def run_pipeline():

    prices = load_market_data()
    returns = compute_returns(prices)

    signals = generate_signals(returns)

    state = load_state()

    if state is None:
        capital = INITIAL_CAPITAL
        current_positions = pd.DataFrame(0, index=signals.index, columns=signals.columns)
    else:
        capital = state["equity"].iloc[-1]
        current_positions = state["positions"]

    target_positions, weights = construct_positions(signals, prices, capital)

    pnl = compute_pnl(target_positions, prices)
    equity = compute_equity_curve(pnl, capital)

    cov_matrix = compute_covariance_matrix(returns)
    portfolio_vol = compute_portfolio_volatility(weights, cov_matrix)

    portfolio_returns = pnl / equity.shift(1)
    benchmark_returns = returns[BENCHMARK]

    sharpe = compute_sharpe(portfolio_returns)
    ir = compute_information_ratio(portfolio_returns, benchmark_returns)

    execution_report = execution_engine(target_positions, current_positions, prices)

    state = {
        "positions": target_positions,
        "weights": weights,
        "equity": equity,
        "pnl": pnl
    }

    save_state(state)

    return {
        "prices": prices,
        "positions": target_positions,
        "weights": weights,
        "equity": equity,
        "pnl": pnl,
        "vol": portfolio_vol,
        "sharpe": sharpe,
        "ir": ir,
        "execution": execution_report
    }

# ============================================================
# UI (INSTITUTIONAL LAYOUT)
# ============================================================

def render_dashboard(results):

    st.title("ProbabilityLens — Oil Risk Monitor v13.2")

    col1, col2, col3 = st.columns(3)

    col1.metric("Sharpe", f"{results['sharpe']:.2f}")
    col2.metric("Information Ratio", f"{results['ir']:.2f}")
    col3.metric("Latest Vol", f"{results['vol'].dropna().iloc[-1]:.2%}")

    st.subheader("Equity Curve")
    st.line_chart(results["equity"])

    st.subheader("PnL")
    st.line_chart(results["pnl"])

    st.subheader("Portfolio Volatility")
    st.line_chart(results["vol"])

    st.subheader("Current Positions")
    st.dataframe(results["positions"].tail(1).T)

    st.subheader("Weights")
    st.dataframe(results["weights"].tail(1).T)

    st.subheader("Execution Report")
    st.dataframe(results["execution"])

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    results = run_pipeline()
    render_dashboard(results)
