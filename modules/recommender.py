import re
import pandas as pd
import yfinance as yf
from modules.news import get_market_news
from modules.ai_advisor import client

NIKKEI_STOCKS = [
    ("9983", "ファーストリテイリング"), ("9984", "ソフトバンクG"), ("8035", "東京エレクトロン"),
    ("6954", "ファナック"), ("6861", "キーエンス"), ("9433", "KDDI"), ("4063", "信越化学"),
    ("6367", "ダイキン工業"), ("7203", "トヨタ自動車"), ("8591", "オリックス"),
    ("6758", "ソニーグループ"), ("7974", "任天堂"), ("4543", "テルモ"), ("4519", "中外製薬"),
    ("8306", "三菱UFJ"), ("8316", "三井住友FG"), ("8411", "みずほFG"),
    ("9432", "NTT"), ("9434", "ソフトバンク"), ("9984", "ソフトバンクG"),
    ("6098", "リクルート"), ("4568", "第一三共"), ("4523", "エーザイ"), ("4502", "武田薬品"),
    ("6501", "日立製作所"), ("6702", "富士通"), ("6594", "日本電産"),
    ("7751", "キヤノン"), ("4901", "富士フイルム"), ("6645", "オムロン"),
    ("6971", "京セラ"), ("6920", "レーザーテック"), ("8036", "日立建機"),
    ("7011", "三菱重工業"), ("7013", "IHI"), ("7012", "川崎重工"),
    ("8058", "三菱商事"), ("8031", "三井物産"), ("8053", "住友商事"), ("8001", "伊藤忠"),
    ("9107", "川崎汽船"), ("9101", "日本郵船"), ("9104", "商船三井"),
    ("5401", "日本製鉄"), ("5713", "住友金属鉱山"), ("3402", "東レ"),
    ("4661", "オリエンタルランド"), ("9602", "東宝"), ("7832", "バンダイナムコ"),
    ("3382", "セブン&アイ"), ("8267", "イオン"), ("2802", "味の素"),
    ("7267", "本田技研"), ("7261", "マツダ"), ("7269", "スズキ"),
    ("6326", "クボタ"), ("6301", "小松製作所"), ("7733", "オリンパス"),
    ("4689", "LINEヤフー"), ("4755", "楽天グループ"), ("2413", "エムスリー"),
    ("9613", "NTTデータ"), ("9020", "JR東日本"), ("9022", "JR東海"),
    ("2914", "JT"), ("3659", "ネクソン"), ("3765", "ガンホー"),
    ("6752", "パナソニック"), ("6503", "三菱電機"), ("6506", "安川電機"),
    ("4704", "トレンドマイクロ"), ("3092", "ZOZO"), ("4385", "メルカリ"),
]

US_STOCKS = [
    ("AAPL", "Apple"), ("MSFT", "Microsoft"), ("NVDA", "NVIDIA"),
    ("AMZN", "Amazon"), ("META", "Meta"), ("GOOGL", "Alphabet"),
    ("TSLA", "Tesla"), ("AMD", "AMD"), ("PLTR", "Palantir"),
    ("NFLX", "Netflix"), ("CRM", "Salesforce"), ("ORCL", "Oracle"),
    ("NOW", "ServiceNow"), ("SNOW", "Snowflake"), ("UBER", "Uber"),
    ("COIN", "Coinbase"), ("MSTR", "MicroStrategy"), ("ARM", "ARM"),
    ("SMCI", "SuperMicro"), ("SHOP", "Shopify"), ("ABNB", "Airbnb"),
    ("PYPL", "PayPal"), ("V", "Visa"), ("JPM", "JPMorgan"),
    ("DIS", "Disney"), ("INTC", "Intel"), ("SPOT", "Spotify"),
    ("RKLB", "Rocket Lab"), ("LUNR", "Intuitive Machines"),
    ("TSM", "TSMC"), ("ASML", "ASML"), ("BABA", "Alibaba"),
    ("NIO", "NIO"), ("XPEV", "Xpeng"), ("RIVN", "Rivian"),
    ("LCID", "Lucid"), ("F", "Ford"), ("GM", "GM"),
    ("BA", "Boeing"), ("LMT", "Lockheed Martin"), ("RTX", "Raytheon"),
    ("GE", "GE Aerospace"), ("CAT", "Caterpillar"), ("DE", "John Deere"),
    ("XOM", "ExxonMobil"), ("CVX", "Chevron"), ("OXY", "Occidental"),
    ("GOLD", "Barrick Gold"), ("NEM", "Newmont"), ("SLB", "Schlumberger"),
]


def _batch_fetch_metrics(symbols_yf: list[str], names: dict[str, str], market: str) -> list[dict]:
    try:
        data = yf.download(symbols_yf, period="1mo", auto_adjust=True, progress=False, threads=True)
        if data.empty:
            return []

        close = data["Close"] if "Close" in data.columns else data.xs("Close", axis=1, level=0)
        results = []
        for sym in symbols_yf:
            try:
                col = sym if sym in close.columns else None
                if col is None:
                    continue
                series = close[col].dropna()
                if len(series) < 15:
                    continue
                prev = float(series.iloc[-2])
                curr = float(series.iloc[-1])
                change_pct = (curr - prev) / prev * 100

                delta = series.diff()
                gain = delta.where(delta > 0, 0).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rsi_val = 100 - 100 / (1 + gain / loss)
                rsi = float(rsi_val.iloc[-1]) if not pd.isna(rsi_val.iloc[-1]) else None

                original_sym = sym.replace(".T", "")
                results.append({
                    "symbol": original_sym,
                    "name": names.get(sym, sym),
                    "market": market,
                    "price": curr,
                    "change_pct": change_pct,
                    "rsi": rsi,
                })
            except Exception:
                continue
        return results
    except Exception:
        return []


def get_recommendations() -> str:
    jp_symbols = [f"{s}.T" for s, _ in NIKKEI_STOCKS]
    jp_names = {f"{s}.T": n for s, n in NIKKEI_STOCKS}
    us_symbols = [s for s, _ in US_STOCKS]
    us_names = {s: n for s, n in US_STOCKS}

    jp_results = _batch_fetch_metrics(jp_symbols, jp_names, "日本株")
    us_results = _batch_fetch_metrics(us_symbols, us_names, "米国株")
    all_results = jp_results + us_results

    if not all_results:
        return "データの取得に失敗しました。しばらく待ってから再試行してください。"

    news = get_market_news(days=1)
    news_text = "\n".join(
        f"{i+1}. {a.get('source', {}).get('name', '')}: {a.get('title', '')}"
        for i, a in enumerate(news[:10])
    )

    top_gainers = sorted(all_results, key=lambda x: x["change_pct"], reverse=True)[:20]
    top_losers = sorted(all_results, key=lambda x: x["change_pct"])[:5]
    oversold = [s for s in all_results if s.get("rsi") and s["rsi"] < 35][:5]
    overbought = [s for s in all_results if s.get("rsi") and s["rsi"] > 70][:5]

    def fmt(stocks):
        return "\n".join(
            f"- {s['symbol']}（{s['name']}）[{s['market']}]: {s['change_pct']:+.2f}%"
            + (f", RSI {s['rsi']:.1f}" if s.get("rsi") else "")
            for s in stocks
        )

    prompt = f"""あなたはプロのトレーダー兼アナリストです。
日本株・米国株あわせて約150銘柄のデータとニュースを分析し、
「今日買うべき銘柄TOP3」と「今日売るべき銘柄TOP2」を選んでください。

## 上昇率トップ20
{fmt(top_gainers)}

## 下落率トップ5
{fmt(top_losers)}

## 売られすぎ銘柄（RSI<35、買いチャンス候補）
{fmt(oversold) if oversold else "なし"}

## 買われすぎ銘柄（RSI>70、売り候補）
{fmt(overbought) if overbought else "なし"}

## 本日の市場ニュース
{news_text if news_text else "ニュースなし"}

以下のマーカーを必ず使って出力してください：

===BUY_START===
### 🥇 買い第1位: 銘柄名（コード）[市場]
**推薦理由**: 具体的に
**戦略**: エントリー・目標・損切り
**注意点**: リスク

### 🥈 買い第2位: ...

### 🥉 買い第3位: ...
===BUY_END===

===SELL_START===
### 🥇 売り第1位: 銘柄名（コード）[市場]
**理由**: 下落・リスクの根拠
**対応**: 手仕舞いタイミング

### 🥈 売り第2位: ...
===SELL_END===

⚠️ これは参考情報です。投資判断は自己責任でお願いします。"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = message.content[0].text
    buy_match = re.search(r'===BUY_START===(.*?)===BUY_END===', text, re.DOTALL)
    sell_match = re.search(r'===SELL_START===(.*?)===SELL_END===', text, re.DOTALL)
    return {
        "buy": buy_match.group(1).strip() if buy_match else text,
        "sell": sell_match.group(1).strip() if sell_match else "",
    }
