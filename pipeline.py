import pandas as pd

# ----------------------------
# DATA
# ----------------------------
from data.loader import load_market_data, compute_returns

# ----------------------------
# FEATURES / SIGNALS
# ----------------------------
from features.signals import generate_signals

# ----------------------------
# PORTFOLIO
# ----------------------------
from portfolio.construction import construct_portfolio

# ----------------------------
# RISK
# ----------------------------
from risk.metrics import compute_volatility, compute_information_ratio
from risk.decomposition import compute_risk_contribution

# ----------------------------
# REGIME
# ----------------------------
from regime.detector import detect_regime

# ----------------------------
# EXECUTION (FIXED)
# ----------------------------
from execution.engine import simulate_execution

# ----------------------------
# REASONING
# ----------------------------
from reasoning.engine import generate_reasoning


def run_pipeline(params):
    """
    Main orchestration pipeline for ProbabilityLens
    """

    # ----------------------------
    # PARAMETERS
    # ----------------------------
    tickers = params.get("tickers", ["SPY", "TLT", "GLD"])
    start = params.get("start", "2020-01-01")
    end = params.get("end", None)

    # ----------------------------
    # LOAD DATA
    # ----------------------------
    prices = load_market_data(tickers, start=start, end=end)

    if prices is None or len(prices) == 0:
        return {}

    # ----------------------------
    # RETURNS
    # ----------------------------
    returns = compute_returns(prices)

    if returns is None or len(returns) == 0:
        return {}

    # ----------------------------
    # SIGNALS
    # ----------------------------
    signals = generate_signals(returns)

    if signals is None or len(signals) == 0:
        return {}

    # ----------------------------
    # PORTFOLIO CONSTRUCTION
    # ----------------------------
    weights = construct_portfolio(signals, returns)

    if weights is None or len(weights) == 0:
        return {}

    # ----------------------------
    # RISK METRICS
    # ----------------------------
    vol = compute_volatility(returns)

    try:
        ir = compute_information_ratio(returns)
    except Exception:
        ir = None

    # Covariance matrix
    try:
        cov = returns.cov()
    except Exception:
        cov = None

    rc = compute_risk_contribution(weights, cov)

    # ----------------------------
    # REGIME DETECTION
    # ----------------------------
    regime = detect_regime(returns)

    # ----------------------------
    # EXECUTION (FIXED HERE)
    # ----------------------------
    positions, notionals, execution_report = simulate_execution(
        weights=weights,
        prices=prices,
        initial_capital=1_000_000,
    )

    # ----------------------------
    # PnL (simple version)
    # ----------------------------
    try:
        pnl = (positions.shift(1) * prices.pct_change()).sum(axis=1).cumsum()
    except Exception:
        pnl = pd.Series(dtype=float)

    # ----------------------------
    # REASONING
    # ----------------------------
    reasoning = generate_reasoning({
        "weights": weights,
        "signals": signals,
        "regime": regime,
        "vol": vol,
    })

    # ----------------------------
    # FINAL OUTPUT
    # ----------------------------
    return {
        "prices": prices,
        "returns": returns,
        "signals": signals,
        "weights": weights,
        "volatility": vol,
        "information_ratio": ir,
        "risk_contribution": rc,
        "regime": regime,
        "positions": positions,
        "notionals": notionals,
        "execution_report": execution_report,
        "pnl": pnl,
        "reasoning": reasoning,
    }
