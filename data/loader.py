import yfinance as yf
import pandas as pd

ASSETS = ["CL=F", "XLE", "SPY", "TLT", "DX-Y.NYB", "GLD"]

def load_market_data():

    data = yf.download(
        ASSETS,
        period="2y",
        interval="1d",
        auto_adjust=True,
        progress=False
    )

    if isinstance(data.columns, pd.MultiIndex):
        data = data["Close"]

    data = data.dropna(how="all")
    data = data.ffill()

    return data


def compute_returns(prices):
    return prices.pct_change().dropna()
