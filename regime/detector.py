import numpy as np
import pandas as pd

def run_regime_pipeline(r):
    vol=r.rolling(20).std().mean(axis=1)
    trend=r.rolling(50).mean().mean(axis=1)

    reg=[]
    thresh=vol.quantile(0.8)

    for v,t in zip(vol,trend):
        if v>thresh: reg.append("CRISIS")
        elif t>0: reg.append("TREND")
        else: reg.append("MEAN_REVERT")

    conf=np.tanh(abs(vol)+abs(trend))

    return {"regime":pd.Series(reg,index=r.index),"confidence":conf}
