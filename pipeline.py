from plogging.logger import get_logs

from data.loader import load_market_data, compute_returns
from features.signals import generate_signals
from portfolio.construction import build_portfolio
from pnl.engine import run_pnl_pipeline
from risk.covariance import build_covariance_dict
from risk.metrics import *
from risk.decomposition import compute_risk_contribution
from execution.engine import run_execution_pipeline
from state.manager import *
from regime.detection import run_regime_pipeline
from reasoning.engine import generate_reasoning
from reporting.builder import build_report


def run_pipeline(params):

    prices = load_market_data()
    returns = compute_returns(prices)

    signals = generate_signals(returns, params["signal"])

    state = load_state()
    if state is None:
        state = initialize_state(prices)

    weights, pos = build_portfolio(
        signals, prices, params["capital"], params["portfolio"]
    )

    pnl_data = run_pnl_pipeline(
        pos, prices, params["capital"], params["costs"]
    )

    cov = build_covariance_dict(returns)

    vol = compute_portfolio_vol(weights, cov)
    sharpe = compute_sharpe(pnl_data["returns"])

    # ✅ SAFE benchmark handling (fixes SPY crash)
    if "SPY" in returns.columns:
        benchmark = returns["SPY"]
    else:
        benchmark = returns.iloc[:, 0]

    ir = compute_information_ratio(pnl_data["returns"], benchmark)

    rc = compute_risk_contribution(weights, cov)

    regime = run_regime_pipeline(returns)

    exec_rep = run_execution_pipeline(
        pos, state.positions, prices, params["execution"]
    )

    state = update_state(state, pos, pnl_data["equity"])
    save_state(state)

    reasoning = generate_reasoning({
        "weights": weights,
        "signals": signals,
        "vol": vol,
        "risk_contribution": rc,
        "regime": regime["regime"],
        "confidence": regime["confidence"]
    })

    report = build_report({
        "equity": pnl_data["equity"],
        "reasoning": reasoning
    })

    return {
        "prices": prices,
        "signals": signals,
        "weights": weights,
        "positions": pos,
        "pnl": pnl_data["pnl"],
        "equity": pnl_data["equity"],
        "vol": vol,
        "risk_contribution": rc,
        "sharpe": sharpe,
        "ir": ir,
        "regime": regime["regime"],
        "execution_report": exec_rep,
        "reasoning": reasoning,
        "report": report,
        "logs": get_logs()
    }
