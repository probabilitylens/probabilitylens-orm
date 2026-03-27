import pandas as pd
import numpy as np


def compute_risk_contribution(weights, cov):

    # ----------------------------
    # SAFETY CHECKS
    # ----------------------------
    if weights is None:
        return {}

    try:
        if len(weights) == 0:
            return {}
    except:
        return {}

    if cov is None:
        return {}

    # ----------------------------
    # HANDLE DICT COVARIANCE
    # ----------------------------
    if isinstance(cov, dict):
        try:
            cov = list(cov.values())[-1]
        except:
            return {}

    # ----------------------------
    # VALIDATE TYPE
    # ----------------------------
    if not isinstance(cov, pd.DataFrame):
        return {}

    if cov.shape[0] == 0:
        return {}

    # ----------------------------
    # COMPUTE
    # ----------------------------
    try:
        w = weights.iloc[-1].values
        cov_matrix = cov.values

        portfolio_var = w.T @ cov_matrix @ w

        if portfolio_var == 0:
            return {}

        marginal = cov_matrix @ w
        contribution = w * marginal / portfolio_var

        return dict(zip(cov.columns, contribution))

    except Exception:
        return {}
