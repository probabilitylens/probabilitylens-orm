import numpy as np
import pandas as pd

def compute_portfolio_vol(w, cov):
    out=[]
    for d in w.index:
        c=cov.get(d)
        if c is None: out.append(np.nan); continue
        ww=w.loc[d].values
        out.append(np.sqrt(ww.T@c@ww)*np.sqrt(252))
    return pd.Series(out,index=w.index)

def compute_sharpe(r):
    return 0 if r.std()==0 else r.mean()/r.std()*np.sqrt(252)

def compute_information_ratio(p,b):
    df = pd.concat([p,b],axis=1).dropna()
    a = df.iloc[:,0]-df.iloc[:,1]
    return 0 if a.std()==0 else a.mean()/a.std()*np.sqrt(252)
