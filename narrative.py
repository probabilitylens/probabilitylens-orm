def generate_narrative(inputs):
    signal = inputs.get("signal", 50)
    alignment = inputs.get("alignment", 50)
    crowding = inputs.get("crowding", 50)

    if signal > 70 and alignment > 70:
        macro = "broad macro alignment is strengthening across demand indicators"
    else:
        macro = "macro signals remain fragmented and lack confirmation"

    if crowding < 40:
        positioning = "Positioning remains crowded, increasing downside volatility risk"
    else:
        positioning = "Positioning remains supportive and not stretched"

    narrative = f"""
    The market is underestimating demand-driven downside pressure on oil prices, 
    as {macro}. {positioning}, suggesting current pricing does not fully reflect 
    the evolving macro environment.
    """

    return narrative.strip()
