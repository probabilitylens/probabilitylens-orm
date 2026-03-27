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
    print("TYPE:", type(prices))
    print("PRICES SHAPE:", getattr(prices, "shape", "N/A"))

    if isinstance(prices, pd.DataFrame):
        print(prices.head())
    else:
        print("⚠️ Prices is not a DataFrame")

    # 🔥 FIX: type-safe + fallback recovery
    if not isinstance(prices, pd.DataFrame) or prices.empty:
        print("⚠️ Prices invalid in pipeline — forcing fallback")

        prices = _generate_fallback_data(tickers, start, end)

        print("FALLBACK TYPE:", type(prices))
        print("FALLBACK SHAPE:", getattr(prices, "shape", "N/A"))

        if not isinstance(prices, pd.DataFrame) or prices.empty:
            raise ValueError("❌ Even fallback failed — critical error")

    # ======================================================
    # 2. RETURNS
    # ======================================================
    returns = compute_returns(prices)

    print("\n===== RETURNS CHECK =====")
    print("TYPE:", type(returns))
    print("RETURNS SHAPE:", getattr(returns, "shape", "N/A"))

    if isinstance(returns, pd.DataFrame):
        print(returns.describe())
    else:
        print("⚠️ Returns is not a DataFrame")

    # 🔥 FIX: type-safe validation
    if not isinstance(returns, pd.DataFrame) or returns.empty:
        raise ValueError("❌ Returns are empty — upstream issue")

    # ======================================================
    # 3. SIGNALS
    # ======================================================
    signals = generate_signals(returns)

    print("\n===== SIGNALS CHECK =====")

    if isinstance(signals, pd.DataFrame):
        print(signals.head())
    else:
        print("⚠️ Signals is not a DataFrame")

    if signals is None or (isinstance(signals, pd.DataFrame) and signals.empty):
        print("⚠️ Signals are empty")

    # ======================================================
    # 4. PORTFOLIO
    # ======================================================
    weights = construct_portfolio(signals, prices, capital, config)

    print("\n===== PORTFOLIO CHECK =====")

    if isinstance(weights, pd.DataFrame):
        print(weights.head())
        try:
            print("Row sums:", weights.sum(axis=1).head())
        except Exception:
            print("⚠️ Could not compute row sums")
    else:
        print("⚠️ Weights is not a DataFrame")

    if weights is None or (isinstance(weights, pd.DataFrame) and weights.empty):
        print("⚠️ Weights are empty")

    # ======================================================
    # 5. PnL
    # ======================================================
    pnl = compute_pnl(weights, returns)

    print("\n===== PNL CHECK =====")

    if isinstance(pnl, pd.DataFrame):
        print(pnl.head())
    else:
        print("⚠️ PnL is not a DataFrame")

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
