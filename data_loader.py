import pandas as pd

def load_wti_data():
    try:
        df = pd.read_csv("data/wti.csv")
        df["Date"] = pd.to_datetime(df["Date"])
        return df
    except:
        return pd.DataFrame({
            "Date": pd.date_range(end=pd.Timestamp.today(), periods=100),
            "Price": [70 + i*0.1 for i in range(100)]
        })
