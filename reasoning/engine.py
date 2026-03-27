def generate_reasoning(ctx):
    """
    Generate human-readable reasoning summary from pipeline outputs.

    Expected ctx keys:
        - weights: DataFrame
        - signals: DataFrame
        - regime: Series
        - vol: Series (optional)
    """

    weights = ctx.get("weights")
    signals = ctx.get("signals")
    regime = ctx.get("regime")
    vol = ctx.get("vol")

    # ----------------------------
    # HARD GUARDS (prevent crashes)
    # ----------------------------
    if weights is None or not hasattr(weights, "__len__") or len(weights) == 0:
        return {
            "summary": "No weights available",
            "signals": "N/A"
        }

    if signals is None or not hasattr(signals, "__len__") or len(signals) == 0:
        return {
            "summary": "No signals available",
            "signals": "N/A"
        }

    if regime is None or not hasattr(regime, "__len__") or len(regime) == 0:
        return {
            "summary": "No regime data",
            "signals": "N/A"
        }

    # ----------------------------
    # SAFE EXTRACTION
    # ----------------------------
    try:
        w = weights.iloc[-1]
    except Exception:
        return {
            "summary": "Weights unavailable (index error)",
            "signals": "N/A"
        }

    try:
        s = signals.iloc[-1]
    except Exception:
        return {
            "summary": "Signals unavailable (index error)",
            "signals": "N/A"
        }

    try:
        r = regime.iloc[-1]
    except Exception:
        r = "UNKNOWN"

    # ----------------------------
    # SIGNAL INTERPRETATION
    # ----------------------------
    try:
        top_asset = s.idxmax()
        top_value = float(s.max())
    except Exception:
        top_asset = "N/A"
        top_value = 0.0

    # ----------------------------
    # WEIGHT INTERPRETATION
    # ----------------------------
    try:
        top_weight_asset = w.abs().idxmax()
        top_weight_value = float(w[top_weight_asset])
    except Exception:
        top_weight_asset = "N/A"
        top_weight_value = 0.0

    # ----------------------------
    # VOLATILITY CONTEXT (optional)
    # ----------------------------
    try:
        current_vol = float(vol.iloc[-1]) if vol is not None and len(vol) > 0 else None
    except Exception:
        current_vol = None

    # ----------------------------
    # BUILD SUMMARY
    # ----------------------------
    summary_parts = [f"Regime: {r}"]

    if current_vol is not None:
        summary_parts.append(f"Vol: {current_vol:.3f}")

    summary_parts.append(f"Top weight: {top_weight_asset} ({top_weight_value:.2%})")

    summary = " | ".join(summary_parts)

    signals_text = f"Top signal: {top_asset} ({top_value:.2%})"

    return {
        "summary": summary,
        "signals": signals_text
    }
