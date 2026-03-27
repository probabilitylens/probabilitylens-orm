def validate_prices(prices):
    if prices is None:
        return prices

    if prices.empty:
        return prices

    prices = prices.dropna(how="all")
    prices = prices.ffill()

    return prices


def validate_returns(df):
    if df is None:
        return df

    if df.empty:
        return df

    df = df.replace([float("inf"), -float("inf")], 0)
    df = df.fillna(0)

    return df
