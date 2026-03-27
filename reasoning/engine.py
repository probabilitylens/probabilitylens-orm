def generate_reasoning(ctx):

    weights = ctx.get("weights")
    signals = ctx.get("signals")
    vol = ctx.get("vol")
    regime = ctx.get("regime")
    confidence = ctx.get("confidence")

    # ----------------------------
    # SAFE WEIGHTS
    # ----------------------------
    if weights is None or len(weights) == 0:
        latest_weights = {}
    else:
        try:
            latest_weights = weights.iloc[-1].to_dict()
        except Exception:
            latest_weights = {}

    # ----------------------------
    # SAFE SIGNALS
    # ----------------------------
    if signals is None or len(signals) == 0:
        latest_signals = {}
    else:
        try:
            latest_signals = signals.iloc[-1].to_dict()
        except Exception:
            latest_signals = {}

    # ----------------------------
    # BUILD OUTPUT
    # ----------------------------
    return {
        "summary": "System operational",
        "weights": latest_weights,
        "signals": latest_signals,
        "volatility": vol,
        "regime": regime,
        "confidence": confidence
    }
