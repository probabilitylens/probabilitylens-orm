import numpy as np
import pandas as pd


def compute_risk_contribution(w, cov):
    """
    Compute per-asset risk contribution to portfolio variance.

    Parameters:
        w   : pd.Series (weights)
        cov : pd.DataFrame (covariance matrix)

    Returns:
        dict of risk contributions per asset
    """

    # ----------------------------
    # SAFETY CHECKS
    # ----------------------------
    if w is None or len(w) == 0:
        return {}

    if cov is None or cov.empty:
        return {}

    # Ensure correct types
    if not isinstance(w, pd.Series):
        try:
            w = pd.Series(w)
        except Exception:
            return {}

    if not isinstance(cov, pd.DataFrame):
        return {}

    try:
        # ----------------------------
        # ALIGN ASSETS
        # ----------------------------
        common_assets = w.index.intersection(cov.index)

        if len(common_assets) == 0:
            return {}

        w = w.loc[common_assets]
        cov = cov.loc[common_assets, common_assets]

        # ----------------------------
        # COMPUTE PORTFOLIO VARIANCE
        # ----------------------------
        w_vec = w.values
        cov_mat = cov.values

        port_var = float(w_vec.T @ cov_mat @ w_vec)

        if port_var == 0 or np.isnan(port_var):
            return {}

        # ----------------------------
        # MARGINAL CONTRIBUTION
        # ----------------------------
        marginal_contrib = cov_mat @ w_vec

        # ----------------------------
        # RISK CONTRIBUTION
        # ----------------------------
        risk_contrib = w_vec * marginal_contrib / port_var

        # Convert to Series
        rc_series = pd.Series(risk_contrib, index=common_assets)

        return rc_series.to_dict()

    except Exception:
        return {}
