import numpy as np
import pandas as pd


def detect_regime(prices):
    """
    Detect market regime based on volatility and trend.

    Parameters:
        prices: DataFrame (time x assets)

    Returns:
        dict with:
            - regime: Series (categorical regime per time)
            - confidence: Series (confidence score)
    """

    # ----------------------------
    # VALIDATION
    # ----------------------------
    if prices is None or len(prices) == 0:
        return {
            "regime": pd.Series(dtype=object),
            "confidence": pd.Series(dtype=float),
        }

    # ----------------------------
    # RETURNS
    # ----------------------------
    returns = prices.pct_change().fillna(0)

    # ----------------------------
    # FEATURES
    # ----------------------------
    vol = returns.rolling(20).std().mean(axis=1)
    trend = returns.rolling(50).mean().mean(axis=1)

    # ----------------------------
    # REGIME LOGIC
    # ----------------------------
    thresh = vol.quantile(0.8)

    regime = []

    for v, t in zip(vol, trend):
        if v > thresh:
            regime.append("CRISIS")
        elif t > 0:
            regime.append("TREND")
        else:
            regime.append("MEAN_REVERT")

    regime_series = pd.Series(regime, index=prices.index)

    # ----------------------------
    # CONFIDENCE
    # ----------------------------
    confidence = np.tanh(np.abs(vol) + np.abs(trend))

    # ----------------------------
    # OUTPUT
    # ----------------------------
    return {
        "regime": regime_series,
        "confidence": pd.Series(confidence, index=prices.index),
    }
