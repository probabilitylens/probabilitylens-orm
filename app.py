import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
from io import BytesIO

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# =========================
# CONFIG
# =========================
MIN_OBS = 50
EPS = 1e-8

# =========================
# DATA LOADER
# =========================
def load_excel(file):
    try:
        xls = pd.ExcelFile(file)
        best_series = None
        max_len = 0

        for sheet in xls.sheet_names:
            df = xls.parse(sheet)

            for col_date in df.columns:
                try:
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

                            max_len = len(temp)
                            best_series = temp

                except:
                    continue

        if best_series is None:
            raise ValueError("No valid time series found")

        if len(best_series) < MIN_OBS:
            raise ValueError("Insufficient data length")

        best_series = best_series.drop_duplicates("date")
        best_series = best_series.sort_values("date")

        return best_series.reset_index(drop=True)

    except Exception as e:
        raise ValueError(f"Data loading failed: {str(e)}")


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

    return df.dropna()


# =========================
# FACTOR ENGINE
# =========================
def compute_factors(df):
    last = df.iloc[-1]

    signal = np.tanh(2 * last["trend_20"] + last["trend_60"])

    timing = -abs(last["zscore"])
    timing = np.clip(timing, -1, 1)

    signs = np.sign([
        last["trend_20"],
        last["momentum_20"],
        last["returns"]
    ])
    confirmation = np.mean(signs)

    alignment = 1 if np.sign(last["trend_20"]) == np.sign(last["trend_60"]) else -1

    crowding = -np.tanh(last["zscore"])

    vol = last["vol_20"]
    if vol < df["vol_20"].quantile(0.3):
        health = 1
    elif vol > df["vol_20"].quantile(0.7):
        health = -1
    else:
        health = 0

    capital = signal / (vol + EPS)
    capital = np.tanh(capital)

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
# INTERPRETATION ENGINE
# =========================
def interpret(f, conviction, regime):
    text = []

    if f["signal"] > 0.7:
        text.append("Trend strength is pronounced across time horizons.")
    elif f["signal"] < -0.7:
        text.append("Downside momentum is dominant and persistent.")

    if f["timing"] < -0.5:
        text.append("Entry conditions appear stretched, increasing mean reversion risk.")

    if f["health"] == -1:
        text.append("Elevated volatility reduces directional reliability.")

    if f["crowding"] < -0.5:
        text.append("Positioning appears crowded, limiting asymmetry.")

    if regime == "ACTIVE LONG":
        decision = "Long bias with high conviction."
    elif regime == "ACTIVE SHORT":
        decision = "Short bias with high conviction."
    else:
        decision = "No clear edge. Maintain optionality."

    return " ".join(text), decision


# =========================
# REPORT ENGINE
# =========================
def generate_report(conviction, regime, expected_move, interp_text, decision):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    content = []

    def add(title, text):
        content.append(Paragraph(f"<b>{title}</b>", styles["Heading2"]))
        content.append(Spacer(1, 10))
        content.append(Paragraph(text, styles["BodyText"]))
        content.append(Spacer(1, 20))

    add("Executive Summary",
        f"The model indicates a {regime} regime with conviction of {conviction:.2f}. "
        f"Expected move over the near term is {expected_move:.2%}. {decision}")

    add("Market Context",
        "Recent price dynamics reflect evolving trend structure and volatility regime shifts.")

    add("Factor Analysis", interp_text)

    add("Scenario Analysis",
        "Base: continuation. Bull: trend acceleration. Bear: reversal under volatility stress.")

    add("Risk Assessment",
        "Primary risks include volatility expansion and positioning overcrowding.")

    add("Decision", decision)

    doc.build(content)
    buffer.seek(0)
    return buffer


# =========================
# UI
# =========================
st.set_page_config(layout="wide")
st.title("ProbabilityLens — Oil Risk Monitor")

file = st.file_uploader("Upload WTI Excel File")

if file:
    try:
        df = load_excel(file)
        df = compute_features(df)
        factors = compute_factors(df)
        conviction, regime, expected_move = compute_model(factors)
        interp_text, decision = interpret(factors, conviction, regime)

        # KPI STRIP
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Conviction", f"{conviction:.2f}")
        c2.metric("Regime", regime)
        c3.metric("Expected Move", f"{expected_move:.2%}")
        c4.metric("Volatility", f"{factors['vol']:.2%}")

        # MAIN PANEL
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Decision")
            st.markdown(f"### {decision}")
            st.write(interp_text)

        with col2:
            st.subheader("Factors")
            st.bar_chart({
                k: [v] for k, v in factors.items() if k != "vol"
            })

        # REPORT
        pdf = generate_report(conviction, regime, expected_move, interp_text, decision)
        st.download_button("Download Report", pdf, "report.pdf")

    except Exception as e:
        st.error(f"System error: {str(e)}")
