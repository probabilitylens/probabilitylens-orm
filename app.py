import streamlit as st
import pandas as pd
import numpy as np
import requests
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# =========================
# CONFIG
# =========================
EIA_URL = "https://www.eia.gov/dnav/pet/hist/RWTCD.htm"
DEFAULT_DATA_PATH = "data/wti.xls"
MIN_OBS = 50
EPS = 1e-8

# =========================
# DATA INGESTION (v4)
# =========================
@st.cache_data(ttl=86400)
def fetch_eia_data():
    try:
        tables = pd.read_html(EIA_URL)

        # Find largest usable table
        best = None
        max_len = 0

        for t in tables:
            for col in t.columns:
                try:
                    dates = pd.to_datetime(t[col], errors='coerce')
                    if dates.notna().sum() < 10:
                        continue

                    for col2 in t.columns:
                        vals = pd.to_numeric(t[col2], errors='coerce')
                        mask = dates.notna() & vals.notna()

                        if mask.sum() > max_len:
                            temp = pd.DataFrame({
                                "date": dates[mask],
                                "price": vals[mask]
                            }).sort_values("date")

                            best = temp
                            max_len = len(temp)
                except:
                    continue

        if best is None or len(best) < MIN_OBS:
            raise ValueError("EIA data insufficient")

        return best.reset_index(drop=True), "EIA Live"

    except Exception as e:
        return None, f"EIA fetch failed: {str(e)}"


@st.cache_data
def load_local():
    try:
        df = pd.read_excel(DEFAULT_DATA_PATH)
        df.columns = ["date", "price"]
        df["date"] = pd.to_datetime(df["date"])
        return df.sort_values("date"), "Local Backup"
    except Exception as e:
        return None, f"Local load failed: {str(e)}"


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
        raise ValueError("Feature layer insufficient")

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
# SCENARIO ENGINE (v4)
# =========================
def compute_scenarios(conviction, vol):
    base = 0.5 + conviction * 0.3
    bull = max(0, base)
    bear = max(0, 1 - base)

    # Normalize
    total = bull + bear
    bull /= total
    bear /= total
    base = 1 - (bull + bear) * 0.5

    return {
        "bull": bull,
        "base": base,
        "bear": bear
    }


# =========================
# POSITIONING MODEL (v4)
# =========================
def compute_position(conviction, vol, crowding):
    raw_size = abs(conviction) / (vol + EPS)

    # Penalize crowding
    adj = raw_size * (1 - abs(crowding))

    if conviction > 0:
        direction = "LONG"
    elif conviction < 0:
        direction = "SHORT"
    else:
        direction = "FLAT"

    return direction, np.tanh(adj)


# =========================
# INTERPRETATION ENGINE
# =========================
def interpret(f, regime, position):
    narrative = []

    if f["signal"] > 0.7:
        narrative.append("Trend strength is pronounced across time horizons.")

    if f["health"] == -1:
        narrative.append("Volatility regime is elevated, reducing reliability.")

    if f["crowding"] < -0.5:
        narrative.append("Positioning appears crowded.")

    narrative.append(f"Recommended positioning is {position[0]} with calibrated sizing.")

    return " ".join(narrative)


# =========================
# REPORT ENGINE
# =========================
def generate_report(regime, conviction, expected_move, scenarios, position, narrative):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    def sec(title, txt):
        return [Paragraph(f"<b>{title}</b>", styles["Heading2"]),
                Spacer(1, 10),
                Paragraph(txt, styles["BodyText"]),
                Spacer(1, 20)]

    content = []

    content += sec("Executive Summary",
        f"{regime} regime with conviction {conviction:.2f}. Expected move {expected_move:.2%}.")

    content += sec("Scenario Analysis",
        f"Bull: {scenarios['bull']:.0%}, Base: {scenarios['base']:.0%}, Bear: {scenarios['bear']:.0%}")

    content += sec("Positioning",
        f"Direction: {position[0]}, Size (normalized): {position[1]:.2f}")

    content += sec("Narrative", narrative)

    doc.build(content)
    buffer.seek(0)
    return buffer


# =========================
# UI
# =========================
st.set_page_config(layout="wide")
st.title("ProbabilityLens — Oil Risk Monitor (v4)")

# DATA LAYER
df, source = fetch_eia_data()
if df is None:
    df, source = load_local()

if df is None:
    st.error(source)
    st.stop()

st.caption(f"Data Source: {source}")
st.caption(f"Last Observation: {df['date'].iloc[-1].date()}")

try:
    df = compute_features(df)
    factors = compute_factors(df)
    conviction, regime, expected_move = compute_model(factors)

    scenarios = compute_scenarios(conviction, factors["vol"])
    position = compute_position(conviction, factors["vol"], factors["crowding"])
    narrative = interpret(factors, regime, position)

    # KPI STRIP
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Conviction", f"{conviction:.2f}")
    c2.metric("Regime", regime)
    c3.metric("Expected Move", f"{expected_move:.2%}")
    c4.metric("Volatility", f"{factors['vol']:.2%}")

    # MAIN GRID
    left, right = st.columns([2,1])

    with left:
        st.subheader("Decision")
        st.markdown(f"## {position[0]} ({position[1]:.2f})")
        st.write(narrative)

    with right:
        st.subheader("Scenarios")
        st.bar_chart(scenarios)

    # REPORT
    pdf = generate_report(regime, conviction, expected_move, scenarios, position, narrative)
    st.download_button("Download Report", pdf, "v4_report.pdf")

except Exception as e:
    st.error(f"System diagnostic: {str(e)}")
