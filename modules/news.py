import os
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "config.env")
API_KEY = os.getenv("NEWS_API_KEY")
BASE_URL = "https://newsapi.org/v2/everything"


def get_news(query: str, days: int = 3, language: str = "jp", max_articles: int = 10) -> list[dict]:
    """指定クエリで世界情勢・金融ニュースを取得する"""
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    # 日本語記事が少ない場合は英語も取得
    articles = []
    for lang in ([language] if language != "all" else ["jp", "en"]):
        params = {
            "q": query,
            "from": from_date,
            "sortBy": "publishedAt",
            "language": lang,
            "pageSize": max_articles,
            "apiKey": API_KEY,
        }
        try:
            res = requests.get(BASE_URL, params=params, timeout=10)
            res.raise_for_status()
            data = res.json()
            articles.extend(data.get("articles", []))
        except Exception:
            pass

    # 重複除去・日時でソート
    seen = set()
    unique = []
    for a in articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)

    unique.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)
    return unique[:max_articles]


def get_market_news(days: int = 2) -> list[dict]:
    """世界市場・経済全般のニュースを取得する"""
    query = "stock market OR 株式市場 OR 経済 OR 金融 OR 世界情勢 OR global economy"
    return get_news(query, days=days, language="all", max_articles=15)
