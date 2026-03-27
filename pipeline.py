# pipeline.py

import pandas as pd

from data.loader import load_data
from features.signals import generate_signals
from portfolio.construction import construct_portfolio
from pnl.engine import compute_pnl


def run_pipeline(params: dict) -> dict:
    """
    Main orchestrator for ProbabilityLens pipeline.

    Guarantees:
    - Always returns a dict with required keys
    - Never silently fails
    """

    # ---------------------------
    # 1. LOAD DATA
    # ---------------------------
    prices = load_data(params)

    if not isinstance(prices, pd.DataFrame) or prices.empty:
        raise ValueError("Invalid prices data")

    print("DATA CHECK:", prices.shape)

    # ---------------------------
    # 2. RETURNS
    # ---------------------------
    returns = prices.pct_change().replace([pd.NA, pd.NaT], 0).fillna(0)

    if returns.empty:
        raise ValueError("Returns are empty")

    print("RETURNS CHECK:", returns.shape)

    # ---------------------------
    # 3. SIGNALS
    # ---------------------------
    signals = generate_signals(returns)

    if not isinstance(signals, pd.DataFrame) or signals.empty:
        raise ValueError("Signals invalid")

    print("SIGNALS CHECK:", signals.shape)

    # ---------------------------
    # 4. PORTFOLIO
    # ---------------------------
    weights = construct_portfolio(
        signals=signals,
        prices=prices,
        capital=params.get("capital", 1_000_000),
        config=params,
    )

    if not isinstance(weights, pd.DataFrame) or weights.empty:
        raise ValueError("Weights invalid")

    print("PORTFOLIO CHECK:", weights.shape)

    # ---------------------------
    # 5. PNL
    # ---------------------------
    pnl, equity_curve = compute_pnl(weights, returns)

    if pnl is None or equity_curve is None:
        raise ValueError("PnL computation failed")

    print("PNL CHECK:", pnl.shape)

    # ---------------------------
    # ✅ STANDARDIZED OUTPUT CONTRACT
    # ---------------------------
    result = {
        "prices": prices,
        "returns": returns,
        "signals": signals,
        "weights": weights,
        "pnl": pnl,
        "equity": equity_curve,  # ✅ CRITICAL FIX
    }

    return result
