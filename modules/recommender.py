import pandas as pd
import yfinance as yf
from modules.news import get_market_news
from modules.ai_advisor import client

WATCH_STOCKS = [
    {"symbol": "7203", "name": "トヨタ自動車", "market": "日本株"},
    {"symbol": "9984", "name": "ソフトバンクG", "market": "日本株"},
    {"symbol": "6758", "name": "ソニーグループ", "market": "日本株"},
    {"symbol": "8306", "name": "三菱UFJ", "market": "日本株"},
    {"symbol": "6861", "name": "キーエンス", "market": "日本株"},
    {"symbol": "7974", "name": "任天堂", "market": "日本株"},
    {"symbol": "9432", "name": "NTT", "market": "日本株"},
    {"symbol": "6098", "name": "リクルート", "market": "日本株"},
    {"symbol": "AAPL", "name": "Apple", "market": "米国株"},
    {"symbol": "MSFT", "name": "Microsoft", "market": "米国株"},
    {"symbol": "NVDA", "name": "NVIDIA", "market": "米国株"},
    {"symbol": "TSLA", "name": "Tesla", "market": "米国株"},
    {"symbol": "AMZN", "name": "Amazon", "market": "米国株"},
    {"symbol": "META", "name": "Meta", "market": "米国株"},
    {"symbol": "AMD", "name": "AMD", "market": "米国株"},
    {"symbol": "PLTR", "name": "Palantir", "market": "米国株"},
]


def _fetch_quote(symbol: str, is_jp: bool) -> dict | None:
    try:
        yf_sym = f"{symbol}.T" if is_jp else symbol
        hist = yf.Ticker(yf_sym).history(period="1mo")
        if len(hist) < 2:
            return None
        prev = float(hist["Close"].iloc[-2])
        curr = float(hist["Close"].iloc[-1])
        change_pct = (curr - prev) / prev * 100

        close = hist["Close"]
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi_series = 100 - 100 / (1 + gain / loss)
        rsi = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else None

        return {"price": curr, "change_pct": change_pct, "rsi": rsi}
    except Exception:
        return None


def get_recommendations() -> str:
    stock_rows = []
    for s in WATCH_STOCKS:
        is_jp = s["symbol"].isdigit()
        q = _fetch_quote(s["symbol"], is_jp)
        if q:
            stock_rows.append({**s, **q})

    news = get_market_news(days=1)
    news_text = "\n".join(
        f"{i+1}. {a.get('source', {}).get('name', '')}: {a.get('title', '')}"
        for i, a in enumerate(news[:10])
    )

    stocks_text = "\n".join(
        f"- {s['symbol']}（{s['name']}）[{s['market']}]: 前日比 {s['change_pct']:+.2f}%"
        + (f", RSI {s['rsi']:.1f}" if s.get("rsi") else "")
        for s in sorted(stock_rows, key=lambda x: x["change_pct"], reverse=True)
    )

    prompt = f"""あなたはプロのトレーダー兼アナリストです。
以下の本日の市場データとニュースをもとに、今日注目すべき銘柄トップ3を選んでください。

## 本日の株価動向（前日比）
{stocks_text}

## 本日の市場ニュース
{news_text if news_text else "ニュースなし"}

## 出力形式（必ずこの形式で）
### 🥇 第1位: 銘柄名（コード）
**推薦理由**: ニュースや値動きをもとに具体的に記載
**注意点**: リスクや気をつけるポイント

### 🥈 第2位: 銘柄名（コード）
（同様に）

### 🥉 第3位: 銘柄名（コード）
（同様に）

⚠️ これは参考情報です。投資判断は自己責任でお願いします。"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text
