import pandas as pd

# DATA
from data.loader import load_market_data, compute_returns

# (placeholders — adjust to your actual modules)
from features.signals import generate_signals
from portfolio.constructor import construct_portfolio
from pnl.engine import compute_pnl


# ==========================================================
# MAIN PIPELINE
# ==========================================================
def run_pipeline(params):
    """
    Main orchestrator for ProbabilityLens
    """

    tickers = params.get("tickers", [])
    start = params.get("start")
    end = params.get("end")
    capital = params.get("capital", 100000)
    config = params.get("config", {})

    # ======================================================
    # 1. LOAD DATA
    # ======================================================
    prices = load_market_data(tickers, start, end)

    print("\n===== DATA CHECK =====")
    print("PRICES SHAPE:", prices.shape)
    print(prices.head())

    if prices.empty:
        raise ValueError("Prices are empty — data layer failure")

    # ======================================================
    # 2. RETURNS
    # ======================================================
    returns = compute_returns(prices)

    print("\n===== RETURNS CHECK =====")
    print("RETURNS SHAPE:", returns.shape)
    print(returns.describe())

    if returns.empty:
        raise ValueError("Returns are empty — upstream issue")

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
    print("Row sums:", weights.sum(axis=1).head())

    if weights is None or weights.empty:
        print("⚠️ Weights are empty")

    # ======================================================
    # 5. PnL
    # ======================================================
    pnl = compute_pnl(weights, returns)

    print("\n===== PNL CHECK =====")
    print(pnl.head())

    # ======================================================
    # OUTPUT
    # ======================================================
    return {
        "prices": prices,
        "returns": returns,
        "signals": signals,
        "weights": weights,
        "pnl": pnl,
    }
