import pandas as pd


def simulate_execution(weights, prices, initial_capital=1_000_000):
    """
    Simulate execution of portfolio weights.

    Parameters:
        weights: DataFrame (time x assets)
        prices: DataFrame (time x assets)
        initial_capital: float

    Returns:
        positions: DataFrame (time x assets, units held)
        notionals: DataFrame (time x assets, $ exposure)
        report: DataFrame (latest snapshot)
    """

    # ----------------------------
    # VALIDATION
    # ----------------------------
    if weights is None or len(weights) == 0:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    if prices is None or len(prices) == 0:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # ----------------------------
    # ALIGN DATA
    # ----------------------------
    weights = weights.copy()
    prices = prices.copy()

    # Normalize timezones (CRITICAL FIX)
    try:
        weights.index = weights.index.tz_localize(None)
    except Exception:
        pass

    try:
        prices.index = prices.index.tz_localize(None)
    except Exception:
        pass

    # Align indices + columns
    weights, prices = weights.align(prices, join="inner", axis=0)
    weights = weights.fillna(0)
    prices = prices.fillna(method="ffill")

    if len(weights) == 0:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # ----------------------------
    # INITIALIZE
    # ----------------------------
    assets = weights.columns

    positions = pd.DataFrame(index=weights.index, columns=assets, dtype=float)
    notionals = pd.DataFrame(index=weights.index, columns=assets, dtype=float)

    current_positions = pd.Series(0.0, index=assets)

    # ----------------------------
    # MAIN LOOP
    # ----------------------------
    for t in weights.index:
        w = weights.loc[t]
        p = prices.loc[t]

        # Skip if prices invalid
        if p.isna().any():
            positions.loc[t] = current_positions
            notionals.loc[t] = current_positions * p.fillna(0)
            continue

        # Target dollar allocation
        target_notional = w * initial_capital

        # Convert to units
        target_positions = target_notional / p

        # ----------------------------
        # ALIGN CURRENT VS TARGET
        # ----------------------------
        current_positions = current_positions.reindex(target_positions.index).fillna(0)

        # Timezone safety (defensive)
        try:
            target_positions.index = target_positions.index
        except Exception:
            pass

        try:
            current_positions.index = current_positions.index
        except Exception:
            pass

        # Compute trade delta (core fix location)
        delta = target_positions - current_positions

        # Update positions
        current_positions = current_positions + delta

        # Store results
        positions.loc[t] = current_positions
        notionals.loc[t] = current_positions * p

    # ----------------------------
    # FINAL REPORT (LATEST SNAPSHOT)
    # ----------------------------
    latest_pos = positions.iloc[-1]
    latest_notional = notionals.iloc[-1]

    report = pd.DataFrame({
        "asset": latest_pos.index,
        "size": latest_pos.values,
        "notional": latest_notional.values,
    })

    # Add execution status
    report["status"] = report["size"].apply(
        lambda x: "BLOCKED" if abs(x) < 1e-8 else "EXECUTED"
    )

    return positions, notionals, report
