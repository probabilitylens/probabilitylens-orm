import pandas as pd

# ==========================================================
# IMPORTS (MATCH YOUR STRUCTURE)
# ==========================================================

# Data layer
from data.loader import load_market_data, compute_returns, _generate_fallback_data

# Features / signals
from features.signals import generate_signals

# Portfolio
from portfolio.construction import construct_portfolio

# PnL
from pnl.engine import compute_pnl


# ==========================================================
# MAIN PIPELINE
# ==========================================================
def run_pipeline(params: dict):
    """
    Main orchestrator for ProbabilityLens
    """

    # ----------------------------
    # PARAMS
    # ----------------------------
    tickers = params.get("tickers", [])
    start = params.get("start")
    end = params.get("end")
    capital = params.get("capital", 100000)
    config = params.get("config", {})

    print("\n==============================")
    print("🚀 RUN PIPELINE START")
    print("==============================")

    # ======================================================
    # 1. LOAD DATA
    # ======================================================
    prices = load_market_data(tickers, start, end)

    print("\n===== DATA CHECK =====")
    print("PRICES SHAPE:", prices.shape)
    print(prices.head())

    # 🔥 FIX: graceful recovery instead of hard failure
    if prices is None or prices.empty:
        print("⚠️ Prices empty in pipeline — forcing fallback")

        prices = _generate_fallback_data(tickers, start, end)

        print("FALLBACK PRICES SHAPE:", prices.shape)

        if prices is None or prices.empty:
            raise ValueError("❌ Even fallback failed — critical error")

    # ======================================================
    # 2. RETURNS
    # ======================================================
    returns = compute_returns(prices)

    print("\n===== RETURNS CHECK =====")
    print("RETURNS SHAPE:", returns.shape)
    print(returns.describe())

    if returns is None or returns.empty:
        raise ValueError("❌ Returns are empty — upstream issue")

    # ======================================================
    # 3. SIGNALS
    # ======================================================
    signals = generate_signals(returns)

    print("\n===== SIGNALS CHECK =====")
    print(signals.head())

    if signals is None or signals.empty:
        print("⚠️ Signals are empty")

    # ======================================================
    # 4. PORTFOLIO
    # ======================================================
    weights = construct_portfolio(signals, prices, capital, config)

    print("\n===== PORTFOLIO CHECK =====")
    print(weights.head())

    try:
        print("Row sums:", weights.sum(axis=1).head())
    except Exception:
        print("⚠️ Could not compute row sums")

    if weights is None or weights.empty:
        print("⚠️ Weights are empty")

    # ======================================================
    # 5. PnL
    # ======================================================
    pnl = compute_pnl(weights, returns)

    print("\n===== PNL CHECK =====")
    print(pnl.head())

    # ======================================================
    # FINAL OUTPUT
    # ======================================================
    print("\n==============================")
    print("✅ PIPELINE COMPLETE")
    print("==============================")

    return {
        "prices": prices,
        "returns": returns,
        "signals": signals,
        "weights": weights,
        "pnl": pnl,
    }
