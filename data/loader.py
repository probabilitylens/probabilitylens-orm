import yfinance as yf
import numpy as np
from config.settings import *
from logging.logger import log
from data.validator import validate_prices, validate_returns

def load_market_data():
    raw = yf.download(ASSETS, period=DATA_PERIOD, auto_adjust=AUTO_ADJUST, progress=False)
    prices = raw["Close"] if isinstance(raw.columns, tuple) else raw
    prices = prices.ffill().dropna()
    return validate_prices(prices)

def compute_returns(prices):
    returns = np.log(prices / prices.shift(1)).dropna()
    return validate_returns(returns)
