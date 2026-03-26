def run_execution_pipeline(target, current, prices, config):
    delta = target - current
    latest = delta.iloc[-1]

    rows=[]
    for a in latest.index:
        size = latest[a]
        price = prices.iloc[-1][a]
        rows.append({
            "asset":a,
            "size":size,
            "notional":size*price,
            "status":"EXECUTED" if config["execute"] else "BLOCKED"
        })
    import pandas as pd
    return pd.DataFrame(rows)
