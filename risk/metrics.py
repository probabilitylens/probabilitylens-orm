import pandas as pd
import numpy as np


def compute_volatility(returns):
    if returns is None or len(returns) == 0:
        return pd.Series(dtype=float)

    return returns.std(axis=1) * np.sqrt(252)


def compute_information_ratio(returns):
    if returns is None or len(returns) == 0:
        return None

    if returns.shape[1] == 0:
        return None

    benchmark = returns.iloc[:, 0]

    excess = returns.sub(benchmark, axis=0)

    ir = excess.mean() / excess.std()
    return ir.mean()
