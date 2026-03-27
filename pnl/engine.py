import pandas as pd
import numpy as np


# ==========================================================
# PnL ENGINE
# ==========================================================
def compute_pnl(weights: pd.DataFrame,
                returns: pd.DataFrame) -> pd.DataFrame:
    """
    Compute portfolio PnL and equity curve.

    Parameters:
        weights: DataFrame (time x assets)
        returns: DataFrame (time x assets)

    Returns:
        DataFrame with:
            - pnl (daily returns)
            - equity (cumulative)
    """

    # ----------------------------
    # VALIDATION
    # ----------------------------
    if weights is None or weights.empty:
        return pd.DataFrame()

    if returns is None or returns.empty:
        return pd.DataFrame()

    # ----------------------------
    # ALIGN DATA
    # ----------------------------
    weights = weights.reindex(returns.index).fillna(0)

    # ----------------------------
    # COMPUTE PnL
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
    df = pd.DataFrame({
        "pnl": pnl,
        "equity": equity
    })

    return df
