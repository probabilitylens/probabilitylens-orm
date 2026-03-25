import pandas as pd

WEIGHTS = {
    "signal": 0.2,
    "timing": 0.15,
    "alignment": 0.2,
    "crowding": 0.15,
    "market_health": 0.15,
    "capital": 0.15
}

def interpret_factor(factor, value):
    if factor == "crowding":
        return "Crowded positioning risk" if value < 40 else "Healthy positioning"
    if factor == "signal":
        return "Strong macro signal" if value > 70 else "Weak signal"
    if factor == "alignment":
        return "Cross-asset confirmation" if value > 70 else "Low alignment"
    return "Neutral"

def compute_signal_attribution(inputs):
    rows = []

    for k, v in inputs.items():
        weight = WEIGHTS.get(k, 0)
        contribution = round(v * weight, 2)

        rows.append({
            "Factor": k.upper(),
            "Score": v,
            "Contribution": contribution,
            "Interpretation": interpret_factor(k, v)
        })

    return pd.DataFrame(rows)
