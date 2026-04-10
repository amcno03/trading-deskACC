import streamlit as st

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(layout="wide")

st.title("📊 Low Price Options Trading Desk (< $20)")

# 🔥 UNIVERSO LOW PRICE
tickers = [
    "SIRI","F","SOFI","PLTR","SNAP",
    "RIOT","LCID","NIO","AMD","INTC",
    "KGC","FCEL","MARA","XPEV","BBD"
]

resultados = []

# =========================
# SCANNER ENGINE
# =========================
for symbol in tickers:
    try:
        daily = yf.download(symbol, period="30d", interval="1d", progress=False)

        if daily is None or daily.empty or len(daily) < 10:
            continue

        daily = daily.dropna()

        # 🔴 primer día de semana
        daily["Week"] = daily.index.isocalendar().week
        daily["IsFirstDay"] = daily["Week"] != daily["Week"].shift(1)

        first_days = daily[daily["IsFirstDay"]]

        if first_days.empty:
            continue

        last_first = first_days.iloc[-1]

        is_red_first_day = last_first["Close"] < last_first["Open"]

        # =========================
        # INTRADAY 10m
        # =========================
        intraday = yf.download(symbol, period="5d", interval="10m", progress=False)

        if intraday is None or intraday.empty or len(intraday) < 20:
            continue

        intraday = intraday.dropna()

        weekly_open = intraday["Open"].iloc[0]
        current = intraday["Close"].iloc[-1]
        prev = intraday["Close"].iloc[-2]

        # 💰 FILTRO < 20 USD
        if current > 20:
            continue

        breakout_up = current > weekly_open and prev <= weekly_open

        # 📊 volumen relativo
        vol = intraday["Volume"].fillna(0)
        avg_vol = vol.rolling(20).mean().iloc[-1]
        avg_vol = avg_vol if avg_vol > 0 else 1

        vol_ratio = vol.iloc[-1] / avg_vol

        # =========================
        # SIGNAL ENGINE
        # =========================
        signal = ""

        if is_red_first_day:
            signal = "🔴 PUT WATCH"

        if breakout_up and vol_ratio > 1.3:
            signal = "🟢 CALL BREAKOUT"

        resultados.append({
            "Ticker": symbol,
            "Price": round(current, 2),
            "First Day Red": is_red_first_day,
            "Breakout": breakout_up,
            "Vol x": round(vol_ratio, 2),
            "Signal": signal
        })

    except:
        continue

# =========================
# DATAFRAME ROBUSTO
# =========================
df = pd.DataFrame(resultados)

if df.empty:
    df = pd.DataFrame(columns=["Ticker","Price","First Day Red","Breakout","Vol x","Signal"])

# =========================
# UI
# =========================
col1, col2 = st.columns([1.2, 2])

with col1:
    st.subheader("📊 Low Price Scanner")
    st.dataframe(df, use_container_width=True)

    st.subheader("🔥 Setups activos")

    signals = df[df["Signal"] != ""]
    if signals.empty:
        st.info("Sin señales activas")
    else:
        st.dataframe(signals, use_container_width=True)

with col2:

    if not df.empty:
        selected = st.selectbox("Selecciona ticker", df["Ticker"])

        chart = yf.download(selected, period="5d", interval="10m")

        if not chart.empty:

            chart = chart.dropna()

            weekly_open = chart["Open"].iloc[0]

            fig = go.Figure()

            fig.add_trace(go.Candlestick(
                x=chart.index,
                open=chart["Open"],
                high=chart["High"],
                low=chart["Low"],
                close=chart["Close"]
            ))

            fig.add_hline(
                y=weekly_open,
                line_dash="dash",
                line_color="yellow",
                annotation_text="Weekly Open"
            )

            fig.update_layout(
                template="plotly_dark",
                height=700
            )

            st.plotly_chart(fig, use_container_width=True)

# =========================
# FOOTER
# =========================
st.caption(f"Última actualización: {datetime.now()}")
