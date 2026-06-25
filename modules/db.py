import os
from supabase import create_client


def _client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL / SUPABASE_KEY が未設定です")
    return create_client(url, key)


def load_watchlist() -> list[str]:
    try:
        res = _client().table("watchlist").select("symbol").order("added_at").execute()
        return [row["symbol"] for row in res.data]
    except Exception:
        return []


def add_symbol(symbol: str) -> None:
    try:
        _client().table("watchlist").upsert({"symbol": symbol}).execute()
    except Exception:
        pass


def remove_symbol(symbol: str) -> None:
    try:
        _client().table("watchlist").delete().eq("symbol", symbol).execute()
    except Exception:
        pass
