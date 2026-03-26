import numpy as np

def build_portfolio(signals, prices, capital, config):
    w = signals.clip(-config["max_weight"], config["max_weight"])
    norm = w.abs().sum(axis=1).replace(0,1)
    w = w.div(norm, axis=0)

    pos = (w * capital) / prices
    pos = pos.replace([np.inf,-np.inf],0).fillna(0)

    return w, pos
