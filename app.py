import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import yfinance as yf

# =========================
# CONFIG
# =========================
EIA_URL = "https://www.eia.gov/dnav/pet/hist/RWTCD.htm"
DEFAULT_DATA_PATH = "data/wti.xls"
MIN_OBS = 50
EPS = 1e-8

# =========================
# CORE EXTRACTION LOGIC
# =========================
def extract_time_series(df):
    best_series, max_len = None, 0

    for col_date in df.columns:
        dates = pd.to_datetime(df[col_date], errors='coerce')
        if dates.notna().sum() < 10:
            continue

        for col_val in df.columns:
            vals = pd.to_numeric(df[col_val], errors='coerce')
            mask = dates.notna() & vals.notna()

            if mask.sum() > max_len:
                temp = pd.DataFrame({
                    "date": dates[mask],
                    "price": vals[mask]
                }).sort_values("date")

                best_series, max_len = temp, len(temp)

    return best_series

# =========================
# DATA INGESTION
# =========================
@st.cache_data(ttl=86400)
def fetch_eia_data():
    try:
        tables = pd.read_html(EIA_URL)
        best, max_len = None, 0

        for t in tables:
            extracted = extract_time_series(t)
            if extracted is not None and len(extracted) > max_len:
                best, max_len = extracted, len(extracted)

        if best is None or len(best) < MIN_OBS:
            raise ValueError("EIA insufficient")

        best = best.drop_duplicates("date").sort_values("date")

        return best.reset_index(drop=True), "EIA Live"

    except Exception as e:
        return None, f"EIA failed: {str(e)}"


@st.cache_data
def load_local():
    try:
        xls = pd.ExcelFile(DEFAULT_DATA_PATH)
        best, max_len = None, 0

        for sheet in xls.sheet_names:
            df = xls.parse(sheet)
            extracted = extract_time_series(df)

            if extracted is not None and len(extracted) > max_len:
                best, max_len = extracted, len(extracted)

        if best is None or len(best) < MIN_OBS:
            raise ValueError("Local insufficient")

        return best.reset_index(drop=True), "Local Backup"

    except Exception as e:
        return None, f"Local failed: {str(e)}"

# =========================
# FEATURE ENGINE
# =========================
def compute_features(df):
    df = df.copy()

    df["returns"] = np.log(df["price"] / df["price"].shift(1))
    df["vol_20"] = df["returns"].rolling(20).std() * np.sqrt(252)
    df["trend_20"] = df["price"] / df["price"].rolling(20).mean() - 1
    df["trend_60"] = df["price"] / df["price"].rolling(60).mean() - 1
    df["momentum_20"] = df["price"].pct_change(20)

    df["zscore"] = (df["returns"] - df["returns"].mean()) / (df["returns"].std() + EPS)

    df = df.dropna()

    if len(df) < MIN_OBS:
        raise ValueError("Feature insufficient")

    return df

# =========================
# FACTOR ENGINE
# =========================
def compute_factors(df):
    last = df.iloc[-1]

    signal = np.tanh(2 * last["trend_20"] + last["trend_60"])
    timing = np.clip(-abs(last["zscore"]), -1, 1)

    confirmation = np.mean(np.sign([
        last["trend_20"],
        last["momentum_20"],
        last["returns"]
    ]))

    alignment = 1 if np.sign(last["trend_20"]) == np.sign(last["trend_60"]) else -1
    crowding = -np.tanh(last["zscore"])

    vol = last["vol_20"]
    q_low = df["vol_20"].quantile(0.3)
    q_high = df["vol_20"].quantile(0.7)

    health = 1 if vol < q_low else -1 if vol > q_high else 0
    capital = np.tanh(signal / (vol + EPS))

    return {
        "signal": signal,
        "timing": timing,
        "confirmation": confirmation,
        "alignment": alignment,
        "crowding": crowding,
        "health": health,
        "capital": capital,
        "vol": vol
    }

# =========================
# MODEL ENGINE
# =========================
def compute_model(f):
    weights = {
        "signal": 0.25,
        "timing": 0.15,
        "confirmation": 0.15,
        "alignment": 0.10,
        "crowding": 0.10,
        "health": 0.15,
        "capital": 0.10
    }

    conviction = sum(f[k] * weights[k] for k in weights)

    if conviction > 0.6:
        regime = "ACTIVE LONG"
    elif conviction < -0.6:
        regime = "ACTIVE SHORT"
    elif abs(conviction) < 0.3:
        regime = "NEUTRAL"
    else:
        regime = "TRANSITION"

    expected_move = conviction * f["vol"] * np.sqrt(5)

    return conviction, regime, expected_move

# =========================
# v5 + v6 EXTENSIONS
# =========================
def forward_signal(df):
    returns = df["returns"]
    short_trend = np.sign(df["trend_20"].iloc[-1])
    persistence = np.mean(np.sign(returns.tail(10)) == short_trend)
    drift = returns.tail(20).mean()
    return np.clip(0.6*persistence + 0.4*np.tanh(drift*50), -1, 1)


def macro_regime(df):
    vol = df["vol_20"].iloc[-1]
    trend = df["trend_60"].iloc[-1]

    if vol > df["vol_20"].quantile(0.75):
        return "STRESS"
    if trend > 0:
        return "EXPANSION"
    if trend < 0:
        return "SLOWDOWN"
    return "NEUTRAL"


def adjust_for_macro(conviction, regime):
    if regime == "STRESS": return conviction * 0.6
    if regime == "EXPANSION": return conviction * 1.2
    if regime == "SLOWDOWN": return conviction * 0.8
    return conviction


def trade_structure(conviction, vol):
    abs_c = abs(conviction)

    if abs_c < 0.3:
        return "No Trade"
    if abs_c > 0.7 and vol < 0.3:
        return "Futures"
    if vol > 0.5:
        return "Long Vol"
    return "Call Spread" if conviction > 0 else "Put Spread"

# =========================
# CROSS-ASSET ENGINE (v6)
# =========================
@st.cache_data(ttl=86400)
def fetch_cross_assets():
    tickers = {
        "DXY": "DX-Y.NYB",
        "SPX": "^GSPC",
        "TNX": "^TNX"
    }

    data = {}
    for name, ticker in tickers.items():
        df = yf.download(ticker, period="2y", progress=False)
        if df is None or df.empty:
            continue

        df = df.reset_index()[["Date", "Close"]]
        df.columns = ["date", "price"]
        df["returns"] = np.log(df["price"] / df["price"].shift(1))
        data[name] = df.dropna()

    return data


def compute_correlations(oil_df, cross_data):
    correlations = {}
    for name, df in cross_data.items():
        merged = pd.merge(oil_df, df, on="date", suffixes=("_oil","_x"))
        if len(merged) > 20:
            correlations[name] = merged["returns_oil"].corr(merged["returns_x"])
    return correlations


def cross_asset_signals(cross_data):
    signals = {}
    for name, df in cross_data.items():
        trend = df["price"].iloc[-1] / df["price"].rolling(20).mean().iloc[-1] - 1
        signals[name] = np.tanh(trend * 3)
    return signals


def portfolio_allocation(oil_conviction, cross_signals, correlations):
    weights = {"OIL": abs(oil_conviction)}

    for k in cross_signals:
        corr = correlations.get(k, 0)
        weights[k] = abs(cross_signals[k]) * (1 - abs(corr))

    total = sum(weights.values()) + EPS
    return {k: v/total for k,v in weights.items()}

# =========================
# UI
# =========================
st.set_page_config(layout="wide")
st.title("ProbabilityLens — Oil Risk Monitor (v6)")

df, source = fetch_eia_data()
if df is None:
    df, source = load_local()

if df is None:
    st.error(source)
    st.stop()

st.caption(f"Source: {source}")
st.caption(f"Last Date: {df['date'].iloc[-1].date()}")

try:
    df = compute_features(df)
    f = compute_factors(df)
    conviction, regime, move = compute_model(f)

    fwd = forward_signal(df)
    macro = macro_regime(df)
    conviction_adj = adjust_for_macro(conviction, macro)
    combined = 0.7 * conviction_adj + 0.3 * fwd

    trade = trade_structure(combined, f["vol"])

    # v6
    cross_data = fetch_cross_assets()
    correlations = compute_correlations(df, cross_data)
    cross_signals = cross_asset_signals(cross_data)
    portfolio = portfolio_allocation(combined, cross_signals, correlations)

    # KPIs
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Conviction", f"{combined:.2f}")
    c2.metric("Regime", regime)
    c3.metric("Expected Move", f"{move:.2%}")
    c4.metric("Volatility", f"{f['vol']:.2%}")

    c5,c6,c7 = st.columns(3)
    c5.metric("Forward", f"{fwd:.2f}")
    c6.metric("Macro", macro)
    c7.metric("Trade", trade)

    left,right = st.columns([2,1])

    with left:
        st.subheader("Decision")
        st.write(f"{trade}")

    with right:
        st.subheader("Portfolio")
        st.bar_chart(portfolio)

    st.subheader("Correlations")
    st.bar_chart(correlations)

except Exception as e:
    st.error(f"System diagnostic: {str(e)}")
