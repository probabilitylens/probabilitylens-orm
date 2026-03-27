# pnl/engine.py

import pandas as pd


def compute_pnl(weights: pd.DataFrame, returns: pd.DataFrame):
    """
    Computes daily PnL and equity curve.
    """

    # Align
    weights, returns = weights.align(returns, join="inner", axis=0)

    # Daily PnL
    pnl = (weights.shift(1) * returns).sum(axis=1)

    pnl = pnl.replace([float("inf"), -float("inf")], 0).fillna(0)

    # Equity curve
    equity_curve = (1 + pnl).cumprod()

    # Defensive guarantees
    if pnl.empty or equity_curve.empty:
        raise ValueError("PnL or equity is empty")

    return pnl, equity_curve
