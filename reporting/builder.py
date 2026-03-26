def build_report(ctx):
    return {
        "executive_summary":ctx["reasoning"]["summary"],
        "performance":{
            "return":float(ctx["equity"].iloc[-1]/ctx["equity"].iloc[0]-1)
        }
    }
