STOCK_DB = [
    # 日本株
    {"symbol": "7203", "name": "トヨタ自動車", "name_en": "Toyota Motor", "market": "日本株", "sector": "自動車"},
    {"symbol": "9984", "name": "ソフトバンクグループ", "name_en": "SoftBank Group", "market": "日本株", "sector": "通信"},
    {"symbol": "6758", "name": "ソニーグループ", "name_en": "Sony Group", "market": "日本株", "sector": "電機"},
    {"symbol": "8306", "name": "三菱UFJフィナンシャル", "name_en": "Mitsubishi UFJ", "market": "日本株", "sector": "金融"},
    {"symbol": "6861", "name": "キーエンス", "name_en": "Keyence", "market": "日本株", "sector": "電機"},
    {"symbol": "7974", "name": "任天堂", "name_en": "Nintendo", "market": "日本株", "sector": "ゲーム"},
    {"symbol": "9432", "name": "NTT", "name_en": "Nippon Telegraph", "market": "日本株", "sector": "通信"},
    {"symbol": "6098", "name": "リクルートホールディングス", "name_en": "Recruit Holdings", "market": "日本株", "sector": "サービス"},
    {"symbol": "4063", "name": "信越化学工業", "name_en": "Shin-Etsu Chemical", "market": "日本株", "sector": "化学"},
    {"symbol": "6367", "name": "ダイキン工業", "name_en": "Daikin Industries", "market": "日本株", "sector": "機械"},
    {"symbol": "8035", "name": "東京エレクトロン", "name_en": "Tokyo Electron", "market": "日本株", "sector": "半導体"},
    {"symbol": "9983", "name": "ファーストリテイリング", "name_en": "Fast Retailing", "market": "日本株", "sector": "小売"},
    {"symbol": "4519", "name": "中外製薬", "name_en": "Chugai Pharmaceutical", "market": "日本株", "sector": "医薬品"},
    {"symbol": "6501", "name": "日立製作所", "name_en": "Hitachi", "market": "日本株", "sector": "電機"},
    {"symbol": "6702", "name": "富士通", "name_en": "Fujitsu", "market": "日本株", "sector": "IT"},
    {"symbol": "7751", "name": "キヤノン", "name_en": "Canon", "market": "日本株", "sector": "精密機器"},
    {"symbol": "4661", "name": "オリエンタルランド", "name_en": "Oriental Land", "market": "日本株", "sector": "レジャー"},
    {"symbol": "2802", "name": "味の素", "name_en": "Ajinomoto", "market": "日本株", "sector": "食品"},
    {"symbol": "7267", "name": "本田技研工業", "name_en": "Honda Motor", "market": "日本株", "sector": "自動車"},
    {"symbol": "8411", "name": "みずほフィナンシャル", "name_en": "Mizuho Financial", "market": "日本株", "sector": "金融"},
    {"symbol": "9022", "name": "東海旅客鉄道", "name_en": "Central Japan Railway", "market": "日本株", "sector": "鉄道"},
    {"symbol": "6594", "name": "日本電産", "name_en": "Nidec", "market": "日本株", "sector": "電機"},
    {"symbol": "4543", "name": "テルモ", "name_en": "Terumo", "market": "日本株", "sector": "医療機器"},
    {"symbol": "2914", "name": "日本たばこ産業", "name_en": "Japan Tobacco", "market": "日本株", "sector": "たばこ"},
    {"symbol": "6920", "name": "レーザーテック", "name_en": "Lasertec", "market": "日本株", "sector": "半導体"},
    # 米国株
    {"symbol": "AAPL", "name": "Apple", "name_en": "Apple Inc.", "market": "米国株", "sector": "テクノロジー"},
    {"symbol": "MSFT", "name": "Microsoft", "name_en": "Microsoft Corp.", "market": "米国株", "sector": "テクノロジー"},
    {"symbol": "NVDA", "name": "NVIDIA", "name_en": "NVIDIA Corp.", "market": "米国株", "sector": "半導体"},
    {"symbol": "TSLA", "name": "Tesla", "name_en": "Tesla Inc.", "market": "米国株", "sector": "EV"},
    {"symbol": "AMZN", "name": "Amazon", "name_en": "Amazon.com Inc.", "market": "米国株", "sector": "EC/クラウド"},
    {"symbol": "META", "name": "Meta", "name_en": "Meta Platforms", "market": "米国株", "sector": "SNS"},
    {"symbol": "GOOGL", "name": "Google", "name_en": "Alphabet Inc.", "market": "米国株", "sector": "テクノロジー"},
    {"symbol": "AMD", "name": "AMD", "name_en": "Advanced Micro Devices", "market": "米国株", "sector": "半導体"},
    {"symbol": "PLTR", "name": "Palantir", "name_en": "Palantir Technologies", "market": "米国株", "sector": "AI/データ"},
    {"symbol": "NFLX", "name": "Netflix", "name_en": "Netflix Inc.", "market": "米国株", "sector": "動画配信"},
    {"symbol": "COIN", "name": "Coinbase", "name_en": "Coinbase Global", "market": "米国株", "sector": "暗号資産"},
    {"symbol": "SMCI", "name": "スーパーマイクロ", "name_en": "Super Micro Computer", "market": "米国株", "sector": "AI/サーバー"},
    {"symbol": "ARM", "name": "ARM Holdings", "name_en": "ARM Holdings", "market": "米国株", "sector": "半導体"},
    {"symbol": "MSTR", "name": "MicroStrategy", "name_en": "MicroStrategy Inc.", "market": "米国株", "sector": "ビットコイン"},
    {"symbol": "SHOP", "name": "Shopify", "name_en": "Shopify Inc.", "market": "米国株", "sector": "EC"},
    {"symbol": "CRM", "name": "Salesforce", "name_en": "Salesforce Inc.", "market": "米国株", "sector": "SaaS"},
    {"symbol": "UBER", "name": "Uber", "name_en": "Uber Technologies", "market": "米国株", "sector": "モビリティ"},
    {"symbol": "SPOT", "name": "Spotify", "name_en": "Spotify Technology", "market": "米国株", "sector": "音楽配信"},
]


def search_stocks(query: str) -> list[dict]:
    q = query.lower().strip()
    if not q:
        return []
    results = [
        s for s in STOCK_DB
        if q in s["symbol"].lower()
        or q in s["name"].lower()
        or q in s["name_en"].lower()
        or q in s["sector"].lower()
    ]
    return results[:10]
