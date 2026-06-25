import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st
import pandas as pd

# Streamlit Cloud のシークレットをos.environに注入（ローカルではスキップ）
try:
    for _k, _v in st.secrets.items():
        os.environ.setdefault(_k, str(_v))
except Exception:
    pass
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from modules.stock_data import get_price_data, get_indicators, get_quote, get_stock_name, get_market_indices
from modules.news import get_news, get_market_news
from modules.ai_advisor import get_advice
from modules.recommender import get_recommendations
from modules.search import search_stocks

@st.cache_data(ttl=300)
def cached_price_data(symbol, interval, outputsize):
    return get_price_data(symbol, interval, outputsize)

@st.cache_data(ttl=300)
def cached_quote(symbol):
    time.sleep(1)
    return get_quote(symbol)

@st.cache_data(ttl=300)
def cached_indicators(symbol, interval):
    time.sleep(1)
    return get_indicators(symbol, interval)

@st.cache_data(ttl=600)
def cached_news(query, days, language):
    return get_news(query, days=days, language=language)

@st.cache_data(ttl=600)
def cached_market_news(days):
    return get_market_news(days=days)

@st.cache_data(ttl=3600)
def cached_stock_name(symbol):
    return get_stock_name(symbol)

@st.cache_data(ttl=60)
def cached_market_indices():
    return get_market_indices()

MARKET_HOURS = [
    ("🗽 NEW YORK", "America/New_York", (9, 30), (16, 0)),
    ("🇬🇧 LONDON", "Europe/London", (8, 0), (16, 30)),
    ("🗼 TOKYO", "Asia/Tokyo", (9, 0), (15, 30)),
    ("🇨🇳 SHANGHAI", "Asia/Shanghai", (9, 30), (15, 0)),
]

st.set_page_config(page_title="株トレードアシスタント", page_icon="📈", layout="wide")

# ---- ウォッチリスト初期化 ----
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["AAPL", "7203", "NVDA", "9984"]

# ---- サイドバー ----
with st.sidebar:
    st.title("📋 ウォッチリスト")

    with st.form("add_symbol"):
        new_symbol = st.text_input("銘柄追加（例: TSLA, 6758）").upper().strip()
        if st.form_submit_button("追加") and new_symbol:
            if new_symbol not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_symbol)

    for sym in st.session_state.watchlist:
        col1, col2 = st.columns([4, 1])
        name = cached_stock_name(sym)
        col1.write(f"**{sym}**  \n{name}")
        if col2.button("✕", key=f"del_{sym}"):
            st.session_state.watchlist.remove(sym)
            st.rerun()

    st.divider()
    options = st.session_state.watchlist
    labels = [f"{s} - {cached_stock_name(s)}" for s in options]
    selected_label = st.selectbox("分析する銘柄", labels)
    selected = options[labels.index(selected_label)]
    interval = st.selectbox("時間軸", ["1day", "4h", "1h", "30min", "15min"], index=0)
    outputsize = st.slider("表示本数", 30, 200, 90)

# ---- メインエリア ----
st.title("📈 株トレードアシスタント")

# ---- 市場時計 ----
clock_cols = st.columns(4)
for i, (name, tz, open_h, close_h) in enumerate(MARKET_HOURS):
    now = datetime.now(ZoneInfo(tz))
    mins = now.hour * 60 + now.minute
    is_open = now.weekday() < 5 and (open_h[0]*60+open_h[1]) <= mins < (close_h[0]*60+close_h[1])
    status = "🟢 OPEN" if is_open else "🔴 CLOSED"
    clock_cols[i].metric(name, now.strftime("%H:%M"), status)

# ---- 主要指数 ----
idx_cols = st.columns(2)
try:
    indices = cached_market_indices()
    for i, idx in enumerate(indices):
        arrow = "▲" if idx["change_pct"] >= 0 else "▼"
        color_label = f"{arrow} {idx['change_pct']:+.2f}%"
        idx_cols[i].metric(idx["name"], f"{idx['price']:,.2f}", color_label)
except Exception:
    pass

st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["チャート & テクニカル", "世界情勢ニュース", "AIアドバイス", "今日のおすすめ銘柄", "🔍 銘柄検索"])

# ===== Tab1: チャート =====
with tab1:
    df = quote = indicators = None
    if selected:
        with st.spinner(f"{selected} のデータ取得中..."):
            try:
                df = cached_price_data(selected, interval, outputsize)
                quote = cached_quote(selected)
                indicators = cached_indicators(selected, interval)
            except Exception as e:
                st.error(f"データ取得エラー: {e}")

    if df is not None and len(df) > 0 and quote is not None and indicators is not None:
        # 現在値サマリー
        price = float(quote.get("close", 0))
        change = float(quote.get("change", 0))
        change_pct = float(quote.get("percent_change", 0))
        color = "normal" if change >= 0 else "inverse"

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("現在値", f"{price:,.2f}", f"{change:+.2f} ({change_pct:+.2f}%)")

        rsi_val = indicators.get("rsi")
        if rsi_val:
            rsi = float(rsi_val["rsi"])
            rsi_label = "買われすぎ" if rsi > 70 else ("売られすぎ" if rsi < 30 else "中立")
            c2.metric("RSI(14)", f"{rsi:.1f}", rsi_label)

        ema20 = indicators.get("ema20")
        ema50 = indicators.get("ema50")
        if ema20 and ema50:
            e20 = float(ema20["ema"])
            e50 = float(ema50["ema"])
            trend = "上昇トレンド" if e20 > e50 else "下降トレンド"
            c3.metric("EMA20/50", f"{e20:,.2f} / {e50:,.2f}", trend)

        macd_val = indicators.get("macd")
        if macd_val:
            hist = float(macd_val["macd_hist"])
            c4.metric("MACDヒスト", f"{hist:.4f}", "強気" if hist > 0 else "弱気")

        # ローソク足チャート
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            row_heights=[0.6, 0.2, 0.2],
            vertical_spacing=0.03,
        )

        fig.add_trace(go.Candlestick(
            x=df["datetime"], open=df["open"], high=df["high"],
            low=df["low"], close=df["close"], name="価格",
            increasing_line_color="#26a69a", decreasing_line_color="#ef5350",
        ), row=1, col=1)

        if ema20 and ema50:
            # 簡易EMAライン（直近値のみ表示）
            pass

        bb_val = indicators.get("bbands")
        if bb_val:
            upper = float(bb_val["upper_band"])
            middle = float(bb_val["middle_band"])
            lower = float(bb_val["lower_band"])
            for band, name, color in [(upper, "BB上限", "rgba(100,149,237,0.5)"),
                                       (middle, "BB中央", "rgba(100,149,237,0.8)"),
                                       (lower, "BB下限", "rgba(100,149,237,0.5)")]:
                fig.add_hline(y=band, line_dash="dot", line_color=color,
                              annotation_text=name, row=1, col=1)

        # 出来高
        colors = ["#26a69a" if c >= o else "#ef5350"
                  for c, o in zip(df["close"], df["open"])]
        fig.add_trace(go.Bar(x=df["datetime"], y=df["volume"],
                             marker_color=colors, name="出来高"), row=2, col=1)

        # RSI
        if rsi_val:
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
            fig.add_hline(y=50, line_dash="dot", line_color="gray", row=3, col=1)
            fig.add_annotation(x=df["datetime"].iloc[-1], y=rsi,
                               text=f"RSI {rsi:.1f}", row=3, col=1,
                               showarrow=False, font=dict(size=11))

        fig.update_layout(
            title=f"{selected} チャート ({interval})",
            xaxis_rangeslider_visible=False,
            height=700,
            template="plotly_dark",
            legend=dict(orientation="h"),
        )
        fig.update_yaxes(title_text="価格", row=1, col=1)
        fig.update_yaxes(title_text="出来高", row=2, col=1)
        fig.update_yaxes(title_text="RSI", row=3, col=1, range=[0, 100])

        st.plotly_chart(fig, use_container_width=True)

# ===== Tab2: ニュース =====
with tab2:
    col_l, col_r = st.columns([1, 3])
    with col_l:
        news_query = st.text_input("キーワード検索", value=selected if selected else "")
        news_days = st.slider("過去N日", 1, 7, 3)
        search_btn = st.button("検索")
        market_btn = st.button("世界市場ニュース取得")

    with col_r:
        if search_btn and news_query:
            with st.spinner("ニュース取得中..."):
                articles = cached_news(news_query, news_days, "all")
            st.write(f"**{len(articles)}件** のニュースが見つかりました")
            for a in articles:
                with st.expander(f"[{a.get('publishedAt','')[:10]}] {a.get('title','')}"):
                    st.write(f"**ソース**: {a.get('source',{}).get('name','')}")
                    st.write(a.get("description", ""))
                    st.markdown(f"[記事を読む]({a.get('url','')})")

        elif market_btn:
            with st.spinner("世界市場ニュース取得中..."):
                articles = cached_market_news(news_days)
            st.write(f"**{len(articles)}件** の世界市場ニュース")
            for a in articles:
                with st.expander(f"[{a.get('publishedAt','')[:10]}] {a.get('title','')}"):
                    st.write(f"**ソース**: {a.get('source',{}).get('name','')}")
                    st.write(a.get("description", ""))
                    st.markdown(f"[記事を読む]({a.get('url','')})")
        else:
            st.info("キーワードを入力して検索するか、「世界市場ニュース取得」ボタンを押してください。")

# ===== Tab4: おすすめ銘柄 =====
with tab4:
    st.subheader("🎯 今日のおすすめ銘柄")
    st.caption("日米約150銘柄の値動き・RSI・最新ニュースをAIが一括分析します")

    if st.button("今日のおすすめを分析する", type="primary"):
        with st.spinner("日米約150銘柄を一括分析中... (30〜60秒かかります)"):
            try:
                result = get_recommendations()
                col_buy, col_sell = st.columns(2)
                with col_buy:
                    st.markdown("### 📈 今日買うべき株")
                    st.markdown(result["buy"])
                with col_sell:
                    st.markdown("### 📉 今日売るべき株")
                    st.markdown(result["sell"])
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

# ===== Tab3: AIアドバイス =====
with tab3:
    st.subheader(f"🤖 {selected} のAIトレードアドバイス")
    st.caption("テクニカル指標 + 最新ニュースを元にClaudeが分析します")

    news_for_advice = st.text_input("ニュース検索キーワード（空白でも可）", value=selected)
    if st.button("アドバイスを生成", type="primary"):
        with st.spinner("分析中... (10〜20秒かかります)"):
            try:
                # データ取得
                quote = get_quote(selected)
                indicators = get_indicators(selected, interval="1day")
                articles = get_news(news_for_advice or selected, days=3, language="all") if news_for_advice else []

                advice = get_advice(selected, quote, indicators, articles)
                st.markdown(advice)
                st.divider()
                st.caption("⚠️ このアドバイスは参考情報です。投資判断は自己責任でお願いします。")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

# ===== Tab5: 銘柄検索 =====
with tab5:
    st.subheader("🔍 銘柄を探す")
    st.caption("銘柄名・コード・セクターで検索できます（例: トヨタ, NVIDIA, 半導体）")

    search_query = st.text_input("検索キーワード", placeholder="例: トヨタ, Apple, 9984, 半導体")
    results = search_stocks(search_query) if search_query else []

    if search_query and not results:
        st.info("該当する銘柄が見つかりませんでした")

    for r in results:
        with st.expander(f"**{r['symbol']}** {r['name']}　[{r['market']} / {r['sector']}]", expanded=False):
            col_chart, col_info = st.columns([3, 1])

            with col_chart:
                try:
                    preview_df = get_price_data(r["symbol"], "1day", 30)
                    if len(preview_df) > 0:
                        fig_preview = go.Figure(go.Scatter(
                            x=preview_df["datetime"], y=preview_df["close"],
                            mode="lines", line=dict(color="#26a69a", width=2),
                            fill="tozeroy", fillcolor="rgba(38,166,154,0.1)",
                        ))
                        fig_preview.update_layout(
                            height=180, margin=dict(l=0, r=0, t=0, b=0),
                            template="plotly_dark", showlegend=False,
                            xaxis=dict(showgrid=False), yaxis=dict(showgrid=False),
                        )
                        st.plotly_chart(fig_preview, use_container_width=True)
                except Exception:
                    st.write("チャート取得できませんでした")

                try:
                    news_list = get_news(r["name_en"], days=3, language="all")[:3]
                    for article in news_list:
                        st.markdown(f"- [{article.get('title','')}]({article.get('url','')})")
                except Exception:
                    pass

            with col_info:
                try:
                    q = get_quote(r["symbol"])
                    price = float(q.get("close", 0))
                    pct = float(q.get("percent_change", 0))
                    color = "🟢" if pct >= 0 else "🔴"
                    st.metric("現在値", f"{price:,.2f}", f"{pct:+.2f}%")
                except Exception:
                    pass

                already_in = r["symbol"] in st.session_state.watchlist
                if already_in:
                    st.success("ウォッチリスト済み")
                else:
                    if st.button("＋ ウォッチリストに追加", key=f"add_{r['symbol']}", type="primary"):
                        st.session_state.watchlist.append(r["symbol"])
                        st.rerun()
