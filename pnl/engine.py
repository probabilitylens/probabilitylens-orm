import numpy as np

def run_pnl_pipeline(pos, prices, capital, config):
    turnover = pos.diff().abs().sum(axis=1)
    costs = turnover * (config["transaction_cost"] + config["slippage"])

    pnl = (pos.shift(1) * prices.diff()).sum(axis=1) - costs
    pnl = pnl.fillna(0)

    equity = capital + pnl.cumsum()
    returns = pnl / equity.shift(1)
    returns = returns.fillna(0)

    return {"pnl":pnl,"equity":equity,"returns":returns,"costs":costs}
