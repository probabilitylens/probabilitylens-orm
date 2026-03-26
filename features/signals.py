import numpy as np
from plogging.logger import log

def generate_signals(returns, params):
    m = returns.rolling(20).mean()
    z = (returns - returns.rolling(20).mean()) / returns.rolling(20).std()

    s = params["momentum_weight"] * m - params["meanrev_weight"] * z
    s = s.replace([np.inf,-np.inf],0).fillna(0)

    norm = s.abs().sum(axis=1).replace(0,1)
    return s.div(norm, axis=0)
