import os
import time
import requests
import pandas as pd
import yfinance as yf
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "config.env")
API_KEY = os.getenv("TWELVE_DATA_API_KEY")
BASE_URL = "https://api.twelvedata.com"

INTERVAL_MAP = {"1day": "1d", "4h": "1h", "1h": "1h", "30min": "30m", "15min": "15m"}
PERIOD_MAP = {30: "3mo", 90: "6mo", 200: "1y"}


def is_japanese(symbol: str) -> bool:
    return symbol.replace(".T", "").isdigit()


def _yf_symbol(symbol: str) -> str:
    return symbol if symbol.endswith(".T") else f"{symbol}.T"


# ---- 日本株（yfinance） ----

def _price_yf(symbol: str, interval: str, outputsize: int) -> pd.DataFrame:
    yf_interval = INTERVAL_MAP.get(interval, "1d")
    period = "1y" if outputsize >= 200 else ("6mo" if outputsize >= 90 else "3mo")
    df = yf.Ticker(_yf_symbol(symbol)).history(period=period, interval=yf_interval)
    df = df.reset_index().rename(columns={
        "Date": "datetime", "Datetime": "datetime",
        "Open": "open", "High": "high", "Low": "low",
        "Close": "close", "Volume": "volume",
    })
    df["datetime"] = pd.to_datetime(df["datetime"])
    if df["datetime"].dt.tz is not None:
        df["datetime"] = df["datetime"].dt.tz_convert(None)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.sort_values("datetime").tail(outputsize).reset_index(drop=True)


def _quote_yf(symbol: str) -> dict:
    hist = yf.Ticker(_yf_symbol(symbol)).history(period="1mo")
    if len(hist) < 2:
        raise ValueError(f"{symbol} のデータが取得できません")
    prev = hist["Close"].iloc[-2]
    curr = hist["Close"].iloc[-1]
    change = curr - prev
    return {
        "close": str(curr),
        "change": str(change),
        "percent_change": str(change / prev * 100),
        "volume": str(hist["Volume"].iloc[-1]),
    }


def _indicators_yf(symbol: str, interval: str) -> dict:
    yf_interval = INTERVAL_MAP.get(interval, "1d")
    period = "1y" if interval == "1day" else "3mo"
    close = yf.Ticker(_yf_symbol(symbol)).history(period=period, interval=yf_interval)["Close"]

    ema20 = close.ewm(span=20).mean().iloc[-1]
    ema50 = close.ewm(span=50).mean().iloc[-1]

    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi = (100 - 100 / (1 + gain / loss)).iloc[-1]

    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9).mean()

    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()

    return {
        "rsi": {"rsi": str(rsi)},
        "macd": {
            "macd": str(macd_line.iloc[-1]),
            "macd_signal": str(signal_line.iloc[-1]),
            "macd_hist": str((macd_line - signal_line).iloc[-1]),
        },
        "bbands": {
            "upper_band": str((sma20 + 2 * std20).iloc[-1]),
            "middle_band": str(sma20.iloc[-1]),
            "lower_band": str((sma20 - 2 * std20).iloc[-1]),
        },
        "ema20": {"ema": str(ema20)},
        "ema50": {"ema": str(ema50)},
    }


# ---- 米国株（Twelve Data） ----

def _price_td(symbol: str, interval: str, outputsize: int) -> pd.DataFrame:
    res = requests.get(f"{BASE_URL}/time_series", params={
        "symbol": symbol, "interval": interval,
        "outputsize": outputsize, "apikey": API_KEY,
    }, timeout=10)
    res.raise_for_status()
    data = res.json()
    if "values" not in data:
        raise ValueError(data.get("message", "データ取得失敗"))
    df = pd.DataFrame(data["values"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _quote_td(symbol: str) -> dict:
    res = requests.get(f"{BASE_URL}/quote", params={"symbol": symbol, "apikey": API_KEY}, timeout=10)
    res.raise_for_status()
    data = res.json()
    if "code" in data:
        raise ValueError(f"銘柄が見つかりません: {symbol}")
    return data


def _indicators_td(symbol: str, interval: str) -> dict:
    indicators = {}
    endpoints = {
        "rsi":   (f"{BASE_URL}/rsi",   {"time_period": 14}),
        "macd":  (f"{BASE_URL}/macd",  {"fast_period": 12, "slow_period": 26, "signal_period": 9}),
        "bbands":(f"{BASE_URL}/bbands",{"time_period": 20}),
        "ema20": (f"{BASE_URL}/ema",   {"time_period": 20}),
        "ema50": (f"{BASE_URL}/ema",   {"time_period": 50}),
    }
    base = {"symbol": symbol, "interval": interval, "outputsize": 1, "apikey": API_KEY}
    for name, (url, extra) in endpoints.items():
        try:
            time.sleep(0.5)
            res = requests.get(url, params={**base, **extra}, timeout=10)
            res.raise_for_status()
            data = res.json()
            if "values" in data and data["values"]:
                indicators[name] = data["values"][0]
        except Exception:
            indicators[name] = None
    return indicators


# ---- 公開インターフェース ----

def get_stock_name(symbol: str) -> str:
    """銘柄名を取得する。取得できない場合はシンボルをそのまま返す"""
    try:
        if is_japanese(symbol):
            info = yf.Ticker(_yf_symbol(symbol)).info
            return info.get("shortName") or info.get("longName") or symbol
        else:
            res = requests.get(f"{BASE_URL}/quote", params={"symbol": symbol, "apikey": API_KEY}, timeout=10)
            data = res.json()
            return data.get("name") or symbol
    except Exception:
        return symbol



def get_price_data(symbol: str, interval: str = "1day", outputsize: int = 90) -> pd.DataFrame:
    if is_japanese(symbol):
        return _price_yf(symbol, interval, outputsize)
    return _price_td(symbol, interval, outputsize)


def get_quote(symbol: str) -> dict:
    if is_japanese(symbol):
        return _quote_yf(symbol)
    return _quote_td(symbol)


def get_indicators(symbol: str, interval: str = "1day") -> dict:
    if is_japanese(symbol):
        return _indicators_yf(symbol, interval)
    return _indicators_td(symbol, interval)
