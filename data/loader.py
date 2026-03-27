import pandas as pd
import yfinance as yf


def load_market_data(tickers, start=None, end=None):
    """
    Download price data for a list of tickers.

    - Handles partial failures (rate limits, bad tickers)
    - Ensures consistent datetime index (tz-naive)
    - Returns clean price DataFrame
    """

    data = {}

    for t in tickers:
        try:
            df = yf.download(
                t,
                start=start,
                end=end,
                progress=False,
                auto_adjust=True,
                threads=False,  # reduces rate-limit issues
            )

            if df is None or df.empty:
                print(f"[WARN] Empty data for {t}")
                continue

            if "Close" not in df.columns:
                print(f"[WARN] No Close column for {t}")
                continue

            series = df["Close"].copy()

            # --- CRITICAL: normalize timezone ---
            if hasattr(series.index, "tz") and series.index.tz is not None:
                series.index = series.index.tz_localize(None)

            data[t] = series

        except Exception as e:
            print(f"[ERROR] Failed download for {t}: {e}")

    # ----------------------------
    # VALIDATION
    # ----------------------------
    if len(data) == 0:
        raise ValueError("No data could be downloaded for any ticker")

    prices = pd.DataFrame(data)

    # ----------------------------
    # CLEANING
    # ----------------------------

    # Drop rows where ALL assets missing
    prices = prices.dropna(how="all")

    # Forward fill small gaps (market holidays mismatch)
    prices = prices.ffill()

    # Drop remaining NaNs (start alignment)
    prices = prices.dropna()

    # Final timezone safety
    if hasattr(prices.index, "tz") and prices.index.tz is not None:
        prices.index = prices.index.tz_localize(None)

    return prices


def compute_returns(prices):
    """
    Compute returns from price DataFrame.

    - Handles NaNs safely
    - Ensures index consistency
    """

    if prices is None or len(prices) == 0:
        return pd.DataFrame()

    returns = prices.pct_change(fill_method=None)

    # Drop first NaN row
    returns = returns.dropna(how="all")

    # Final cleanup
    returns = returns.replace([float("inf"), float("-inf")], pd.NA)
    returns = returns.dropna()

    # Ensure timezone consistency
    if hasattr(returns.index, "tz") and returns.index.tz is not None:
        returns.index = returns.index.tz_localize(None)

    return returns
