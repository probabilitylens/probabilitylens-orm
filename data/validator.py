import pandas as pd
from logging.logger import log
from config.settings import ASSETS, MIN_OBSERVATIONS

def validate_prices(df):
    if df.empty:
        log("Empty prices","DATA","ERROR")
        raise ValueError()

    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError()

    if len(df) < MIN_OBSERVATIONS:
        raise ValueError()

    for a in ASSETS:
        if a not in df.columns:
            raise ValueError()

    return df

def validate_returns(df):
    if df.empty:
        raise ValueError()
    return df
