import os
import anthropic
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "config.env")
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def get_advice(symbol: str, quote: dict, indicators: dict, news_articles: list[dict]) -> str:
    """テクニカル指標とニュースを元にトレードアドバイスを生成する"""

    # テクニカル指標のサマリー
    rsi_val = indicators.get("rsi")
    rsi_str = f"{float(rsi_val['rsi']):.2f}" if rsi_val else "取得不可"

    macd_val = indicators.get("macd")
    if macd_val:
        macd_str = f"MACD={float(macd_val['macd']):.4f}, Signal={float(macd_val['macd_signal']):.4f}, Hist={float(macd_val['macd_hist']):.4f}"
    else:
        macd_str = "取得不可"

    bb_val = indicators.get("bbands")
    if bb_val:
        bb_str = f"上限={float(bb_val['upper_band']):.2f}, 中央={float(bb_val['middle_band']):.2f}, 下限={float(bb_val['lower_band']):.2f}"
    else:
        bb_str = "取得不可"

    ema20 = indicators.get("ema20")
    ema20_str = f"{float(ema20['ema']):.2f}" if ema20 else "取得不可"
    ema50 = indicators.get("ema50")
    ema50_str = f"{float(ema50['ema']):.2f}" if ema50 else "取得不可"

    # ニュースのサマリー（最大5件）
    news_text = ""
    for i, article in enumerate(news_articles[:5], 1):
        title = article.get("title", "")
        source = article.get("source", {}).get("name", "")
        published = article.get("publishedAt", "")[:10]
        news_text += f"{i}. [{published}] {source}: {title}\n"

    price = quote.get("close", quote.get("price", "不明"))
    change_pct = quote.get("percent_change", "不明")

    prompt = f"""あなたはプロのトレーダー兼テクニカルアナリストです。
以下のデータを分析し、デイトレードからスイングトレード（数日〜数週間）の観点で具体的なトレードアドバイスをしてください。

## 銘柄: {symbol}
- 現在値: {price}
- 前日比: {change_pct}%

## テクニカル指標
- RSI(14): {rsi_str}
- MACD(12,26,9): {macd_str}
- ボリンジャーバンド(20): {bb_str}
- EMA20: {ema20_str}
- EMA50: {ema50_str}

## 関連ニュース（直近）
{news_text if news_text else "ニュースなし"}

## 回答形式
1. **総合判断**（買い/様子見/売り）
2. **根拠**（テクニカル面・ニュース面それぞれ）
3. **エントリー戦略**（狙うタイミング・価格帯）
4. **リスク管理**（損切りライン・注意点）

※ これはあくまで参考情報です。最終判断はご自身でお願いします。"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text
