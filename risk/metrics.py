import pandas as pd
import numpy as np


def compute_volatility(returns):
    """
    Rolling volatility (annualized)
    """
    if returns is None or len(returns) == 0:
        return pd.Series(dtype=float)

    vol = returns.std(axis=1) * np.sqrt(252)
    return vol


def compute_information_ratio(returns, benchmark=None):
    """
    Information Ratio vs benchmark
    """
    if returns is None or len(returns) == 0:
        return None

    if benchmark is None:
        benchmark = returns.iloc[:, 0]

    excess = returns.sub(benchmark, axis=0)

    ir = excess.mean() / excess.std()
    return ir.mean()
