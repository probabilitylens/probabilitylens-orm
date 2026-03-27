import pandas as pd
import numpy as np


# ==========================================================
# PORTFOLIO CONSTRUCTION
# ==========================================================
def construct_portfolio(signals: pd.DataFrame,
                        prices: pd.DataFrame,
                        capital: float,
                        config: dict) -> pd.DataFrame:
    """
    Convert signals into portfolio weights.

    Parameters:
        signals: DataFrame (time x assets)
        prices: DataFrame (time x assets)
        capital: float
        config: dict

    Returns:
        weights: DataFrame (time x assets)
    """

    # ----------------------------
    # VALIDATION
    # ----------------------------
    if signals is None or signals.empty:
        return pd.DataFrame()

    if prices is None or prices.empty:
        return pd.DataFrame()

    # Align indices (critical)
    signals = signals.reindex(prices.index).fillna(0)

    # ----------------------------
    # CLEAN SIGNALS
    # ----------------------------
    signals = signals.replace([np.inf, -np.inf], np.nan)
    signals = signals.fillna(0)

    # ----------------------------
    # NORMALIZATION
    # ----------------------------
    # Convert signals → weights
    abs_sum = signals.abs().sum(axis=1)

    # Avoid division by zero
    abs_sum = abs_sum.replace(0, np.nan)

    weights = signals.div(abs_sum, axis=0)

    # Fill rows where sum was zero
    weights = weights.fillna(0)

    # ----------------------------
    # OPTIONAL: LEVERAGE CONTROL
    # ----------------------------
    max_leverage = config.get("max_leverage", 1.0)

    row_leverage = weights.abs().sum(axis=1)

    scale = row_leverage.copy()
    scale[scale <= max_leverage] = 1.0
    scale[scale > max_leverage] = row_leverage / max_leverage

    weights = weights.div(scale, axis=0)

    # ----------------------------
    # FINAL CLEAN
    # ----------------------------
    weights = weights.replace([np.inf, -np.inf], 0)
    weights = weights.fillna(0)

    return weights
