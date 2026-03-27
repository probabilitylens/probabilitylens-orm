import pandas as pd
import numpy as np


# ==========================================================
# SIGNAL GENERATION
# ==========================================================
def generate_signals(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Generate trading signals using a combination of:
    - Momentum (trend following)
    - Mean reversion

    Parameters:
        returns: DataFrame (time x assets)

    Returns:
        DataFrame (time x assets)
    """

    # ----------------------------
    # VALIDATION
    # ----------------------------
    if not isinstance(returns, pd.DataFrame):
        print("⚠️ Returns is not a DataFrame")
        return pd.DataFrame()

    if returns.empty:
        print("⚠️ Returns is empty")
        return pd.DataFrame()

    # Ensure numeric
    returns = returns.apply(pd.to_numeric, errors="coerce")

    # ----------------------------
    # MOMENTUM SIGNAL
    # ----------------------------
    # rolling mean of returns (trend)
    momentum = returns.rolling(window=20, min_periods=5).mean()

    # ----------------------------
    # MEAN REVERSION SIGNAL
    # ----------------------------
    # short-term reversal
    mean_reversion = -returns.rolling(window=5, min_periods=3).mean()

    # ----------------------------
    # VOLATILITY SCALING (optional robustness)
    # ----------------------------
    vol = returns.rolling(window=20, min_periods=5).std()
    vol = vol.replace(0, np.nan)

    # Avoid division by zero
    momentum_scaled = momentum.div(vol)
    mean_rev_scaled = mean_reversion.div(vol)

    # ----------------------------
    # COMBINE SIGNALS
    # ----------------------------
    signals = 0.5 * momentum_scaled + 0.5 * mean_rev_scaled

    # ----------------------------
    # CLEAN SIGNALS
    # ----------------------------
    signals = signals.replace([np.inf, -np.inf], np.nan)
    signals = signals.fillna(0)

    # Clip extreme values (stability)
    signals = signals.clip(lower=-5, upper=5)

    # ----------------------------
    # FINAL VALIDATION
    # ----------------------------
    if signals is None or not isinstance(signals, pd.DataFrame):
        print("⚠️ Signals generation failed")
        return pd.DataFrame()

    return signals
