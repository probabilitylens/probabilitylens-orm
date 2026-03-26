import numpy as np
import pandas as pd

def compute_risk_contribution(w, cov):
    d=w.index[-1]
    c=cov.get(d)
    if c is None:
        return pd.Series(0,index=w.columns)

    ww=w.loc[d].values
    var=ww.T@c@ww
    if var==0:
        return pd.Series(0,index=w.columns)

    rc=ww*(c@ww)/var
    return pd.Series(rc,index=w.columns)
