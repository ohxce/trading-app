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

_NAME_DB = {
    # 日本株
    "7203": "トヨタ自動車", "9984": "ソフトバンクG", "6758": "ソニーグループ",
    "8306": "三菱UFJフィナンシャル", "6861": "キーエンス", "7974": "任天堂",
    "9432": "NTT", "6098": "リクルートHD", "4063": "信越化学工業",
    "6367": "ダイキン工業", "8035": "東京エレクトロン", "9983": "ファーストリテイリング",
    "4519": "中外製薬", "6501": "日立製作所", "6702": "富士通",
    "7751": "キヤノン", "4661": "オリエンタルランド", "2802": "味の素",
    "7267": "本田技研工業", "8411": "みずほフィナンシャル", "9022": "JR東海",
    "6594": "日本電産", "4543": "テルモ", "2914": "日本たばこ産業",
    "6920": "レーザーテック", "7011": "三菱重工業", "8058": "三菱商事",
    "8031": "三井物産", "8053": "住友商事", "8001": "伊藤忠商事",
    "6326": "クボタ", "6954": "ファナック", "4568": "第一三共",
    "4523": "エーザイ", "4755": "楽天グループ", "3382": "セブン&アイHD",
    "8267": "イオン", "9020": "JR東日本", "9107": "川崎汽船",
    "9101": "日本郵船", "9104": "商船三井", "7832": "バンダイナムコ",
    "9613": "NTTデータ", "2413": "エムスリー", "4689": "LINEヤフー",
    "6645": "オムロン", "6971": "京セラ", "5401": "日本製鉄",
    "4901": "富士フイルム", "6503": "三菱電機", "8316": "三井住友FG",
    "9433": "KDDI", "9434": "ソフトバンク", "4502": "武田薬品",
    "7013": "IHI", "7012": "川崎重工", "5713": "住友金属鉱山",
    "3402": "東レ", "9602": "東宝", "7261": "マツダ", "7269": "スズキ",
    "6301": "小松製作所", "7733": "オリンパス", "6752": "パナソニック",
    "6506": "安川電機", "3092": "ZOZO", "4385": "メルカリ",
    "3659": "ネクソン", "6036": "KeePer技研",
    # 米国株
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "NVIDIA",
    "AMZN": "Amazon", "META": "Meta", "GOOGL": "Google",
    "TSLA": "Tesla", "AMD": "AMD", "PLTR": "Palantir",
    "NFLX": "Netflix", "CRM": "Salesforce", "ORCL": "Oracle",
    "NOW": "ServiceNow", "SNOW": "Snowflake", "UBER": "Uber",
    "COIN": "Coinbase", "MSTR": "MicroStrategy", "ARM": "ARM",
    "SMCI": "SuperMicro", "SHOP": "Shopify", "ABNB": "Airbnb",
    "PYPL": "PayPal", "V": "Visa", "JPM": "JPMorgan",
    "DIS": "Disney", "INTC": "Intel", "SPOT": "Spotify",
    "RKLB": "Rocket Lab", "LUNR": "Intuitive Machines",
    "TSM": "TSMC", "ASML": "ASML", "BABA": "Alibaba",
    "NIO": "NIO", "XPEV": "Xpeng", "RIVN": "Rivian",
    "F": "Ford", "GM": "GM", "BA": "Boeing",
    "LMT": "Lockheed Martin", "RTX": "Raytheon",
    "GE": "GE Aerospace", "CAT": "Caterpillar", "XOM": "ExxonMobil",
    "CVX": "Chevron", "GOLD": "Barrick Gold",
}


def is_japanese(symbol: str) -> bool:
    return symbol.replace(".T", "").isdigit()


def _yf_symbol(symbol: str) -> str:
    if symbol.endswith(".T"):
        return symbol
    return f"{symbol}.T" if is_japanese(symbol) else symbol


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
    if symbol in _NAME_DB:
        return _NAME_DB[symbol]
    try:
        info = yf.Ticker(_yf_symbol(symbol)).info
        return info.get("shortName") or info.get("longName") or symbol
    except Exception:
        return symbol


def get_price_data(symbol: str, interval: str = "1day", outputsize: int = 90) -> pd.DataFrame:
    return _price_yf(symbol, interval, outputsize)


def get_quote(symbol: str) -> dict:
    return _quote_yf(symbol)


def get_indicators(symbol: str, interval: str = "1day") -> dict:
    return _indicators_yf(symbol, interval)


def get_market_indices() -> list[dict]:
    tickers = {"S&P500": "^GSPC", "NIKKEI225": "^N225"}
    results = []
    for name, sym in tickers.items():
        try:
            hist = yf.Ticker(sym).history(period="2d")
            if len(hist) >= 2:
                prev = float(hist["Close"].iloc[-2])
                curr = float(hist["Close"].iloc[-1])
                change_pct = (curr - prev) / prev * 100
                results.append({"name": name, "price": curr, "change_pct": change_pct})
        except Exception:
            pass
    return results
