import pandas as pd
import numpy as np


def compute_risk_contribution(weights, cov):

    # ----------------------------
    # SAFETY CHECKS
    # ----------------------------
    if weights is None or len(weights) == 0:
        return {}

    if cov is None:
        return {}

    # ✅ Handle dict covariance (your case)
    if isinstance(cov, dict):
        # take latest covariance matrix
        cov = list(cov.values())[-1]

    # Now cov should be a DataFrame
    if not isinstance(cov, pd.DataFrame):
        return {}

    if cov.empty:
        return {}

    # ----------------------------
    # ALIGN DATA
    # ----------------------------
    try:
        w = weights.iloc[-1].values
        cov_matrix = cov.values
    except Exception:
        return {}

    # ----------------------------
    # COMPUTE CONTRIBUTION
    # ----------------------------
    try:
        portfolio_var = w.T @ cov_matrix @ w

        if portfolio_var == 0:
            return {}

        marginal = cov_matrix @ w
        contribution = w * marginal / portfolio_var

        return dict(zip(cov.columns, contribution))

    except Exception:
        return {}
