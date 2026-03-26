import pandas as pd
from datetime import datetime

_LOG_STORE = []

def log(message, layer="GENERAL", severity="INFO"):
    try:
        _LOG_STORE.append({
            "timestamp": datetime.utcnow(),
            "layer": layer,
            "severity": severity,
            "message": str(message)
        })
    except:
        pass

def get_logs():
    if not _LOG_STORE:
        return pd.DataFrame(columns=["timestamp","layer","severity","message"])
    return pd.DataFrame(_LOG_STORE).sort_values("timestamp", ascending=False)
