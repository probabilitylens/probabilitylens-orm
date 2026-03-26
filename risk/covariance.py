import numpy as np

def build_covariance_dict(r, window=60):
    cov = {}
    for i in range(window, len(r)):
        cov[r.index[i]] = np.cov(r.iloc[i-window:i].values, rowvar=False)
    return cov
