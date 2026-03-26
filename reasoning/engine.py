def generate_reasoning(ctx):
    w=ctx["weights"].iloc[-1]
    return {
        "summary":f"Regime {ctx['regime'].iloc[-1]}",
        "signals":f"Top {ctx['signals'].iloc[-1].idxmax()}",
        "positioning":f"Long {w.idxmax()}",
        "risk":f"Risk {ctx['risk_contribution'].idxmax()}",
        "regime":str(ctx["regime"].iloc[-1]),
        "changes":"N/A"
    }
