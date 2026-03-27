import pandas as pd
import numpy as np


def compute_pnl(weights: pd.DataFrame,
                returns: pd.DataFrame) -> pd.DataFrame:
    """
    Compute portfolio PnL and equity curve.
    """

    # ----------------------------
    # VALIDATION
    # ----------------------------
    if weights is None or weights.empty:
        return pd.DataFrame()

    if returns is None or returns.empty:
        return pd.DataFrame()

    # ----------------------------
    # ALIGN INDEX
    # ----------------------------
    weights = weights.reindex(returns.index).fillna(0)

    # ----------------------------
    # PnL CALCULATION
    # ----------------------------
    pnl = (weights * returns).sum(axis=1)

    pnl = pnl.replace([np.inf, -np.inf], 0)
    pnl = pnl.fillna(0)

    # ----------------------------
    # EQUITY CURVE
    # ----------------------------
    equity = (1 + pnl).cumprod()

    # ----------------------------
    # OUTPUT
    # ----------------------------
    result = pd.DataFrame({
        "pnl": pnl,
        "equity": equity
    })

    return result
