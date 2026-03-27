import pandas as pd
import numpy as np
import yfinance as yf


# ==========================================================
# MARKET DATA LOADER
# ==========================================================
def load_market_data(tickers, start, end):
    """
    Load market data and return clean price DataFrame.

    Parameters:
        tickers: list[str]
        start: str (YYYY-MM-DD)
        end: str (YYYY-MM-DD)

    Returns:
        DataFrame (time x assets)
    """

    # ----------------------------
    # INPUT VALIDATION
    # ----------------------------
    if tickers is None or len(tickers) == 0:
        return pd.DataFrame()

    try:
        # ----------------------------
        # DOWNLOAD DATA
        # ----------------------------
        data = yf.download(
            tickers,
            start=start,
            end=end,
            progress=False,
            auto_adjust=True,
        )

        if data is None or len(data) == 0:
            raise ValueError("Empty data from yfinance")

        # ----------------------------
        # HANDLE MULTIINDEX (OHLC)
        # ----------------------------
        if isinstance(data.columns, pd.MultiIndex):
            if "Close" in data.columns.levels[0]:
                prices = data["Close"]
            elif "Adj Close" in data.columns.levels[0]:
                prices = data["Adj Close"]
            else:
                prices = data.xs(data.columns.levels[0][0], axis=1)
        else:
            prices = data

        # ----------------------------
        # ENSURE DATAFRAME FORMAT
        # ----------------------------
        if isinstance(prices, pd.Series):
            prices = prices.to_frame()

        # ----------------------------
        # CLEAN DATA
        # ----------------------------
        prices = prices.sort_index()
        prices = prices.ffill().dropna(how="all")

        # Drop columns that are entirely NaN
        prices = prices.dropna(axis=1, how="all")

        # ----------------------------
        # MINIMUM DATA CHECK
        # ----------------------------
        if prices.shape[0] < 20 or prices.shape[1] == 0:
            raise ValueError("Insufficient data after cleaning")

        return prices

    except Exception as e:
        print("⚠️ Data load failed, using fallback:", e)

        return _generate_fallback_data(tickers, start, end)


# ==========================================================
# RETURNS COMPUTATION
# ==========================================================
def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Compute returns from price data.

    Parameters:
        prices: DataFrame (time x assets)

    Returns:
        DataFrame (time x assets)
    """

    if prices is None or prices.empty:
        return pd.DataFrame()

    # Percent change
    returns = prices.pct_change()

    # Clean infinities
    returns = returns.replace([np.inf, -np.inf], np.nan)

    # Drop rows where all values are NaN
    returns = returns.dropna(how="all")

    return returns


# ==========================================================
# FALLBACK DATA GENERATOR
# ==========================================================
def _generate_fallback_data(tickers, start, end):
    """
    Generate synthetic price data to prevent pipeline failure.
    """

    dates = pd.date_range(start=start, end=end, freq="B")

    if len(dates) == 0 or tickers is None:
        return pd.DataFrame()

    np.random.seed(42)

    data = {}
    for ticker in tickers:
        # geometric random walk (non-degenerate)
        returns = 0.001 * np.random.randn(len(dates))
        prices = 100 * np.cumprod(1 + returns)
        data[ticker] = prices

    df = pd.DataFrame(data, index=dates)

    return df
