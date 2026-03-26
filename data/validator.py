import pandas as pd
from plogging.logger import log
from config.settings import ASSETS, MIN_OBSERVATIONS

def validate_prices(prices):
    if prices is None:
        return prices

    if prices.empty:
        return prices

    # Drop bad data instead of crashing
    prices = prices.dropna(how="all")
    prices = prices.fillna(method="ffill")

    return prices
    
def validate_returns(df):
    if df.empty:
        raise ValueError()
    return df
