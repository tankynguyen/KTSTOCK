"""
KTSTOCK - Dashboard Page
Trang tổng quan thị trường.
"""
import time
import streamlit as st
import pandas as pd
from datetime import datetime

from src.app.i18n import t
from src.app.components.shared import signal_badge, trend_badge, error_handler, debug_show_inline
from src.utils.debug_logger import get_debug_logger, LogCategory, LogLevel


@error_handler
def render_dashboard():
    """Render trang Dashboard."""
    lang = st.session_state.get("language", "vi")

    # === Market Indices ===
    st.markdown("### 📊 " + ("Chỉ số thị trường" if lang == "vi" else "Market Indices"))
    col1, col2, col3, col4 = st.columns(4)

    try:
        from src.data.connectors.vnstock_connector import VnstockFreeConnector
        connector = VnstockFreeConnector()
        connector.connect()

        # Thử fetch dữ liệu real
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = datetime.now().strftime("%Y-%m-%d")

        with col1:
            _render_index_metric(connector, "VNINDEX", "VN-Index")
        with col2:
            _render_index_metric(connector, "HNX", "HNX-Index")
        with col3:
            _render_index_metric(connector, "UPCOM", "UPCOM-Index")
        with col4:
            _render_crypto_metric()

    except Exception as e:
        col1.metric("VN-Index", "---", "Đang tải...")
        col2.metric("HNX-Index", "---", "Đang tải...")
        col3.metric("UPCOM-Index", "---", "Đang tải...")
        col4.metric("BTC/USDT", "---", "Đang tải...")
        # Log lỗi connector
        dlog = get_debug_logger()
        dlog.log_api_call(
            page="dashboard", component="render_dashboard",
            source="VnstockFreeConnector", method="connect",
            params={}, result_status="ERROR", error=e, symbol=""
        )

    st.divider()

    # === Quick Actions ===
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 🔥 " + ("Top giao dịch" if lang == "vi" else "Top Trading"))
        _render_top_stocks()
    with c2:
        st.markdown("### 📰 " + ("Tin mới nhất" if lang == "vi" else "Latest News"))
        st.info("📡 Tính năng tin tức sẽ hoàn thiện ở Phase 5+" if lang == "vi"
                else "📡 News feature coming soon")
    with c3:
        st.markdown("### 🤖 AI Insight")
        st.info("🤖 Kết nối Gemini AI để nhận insight" if lang == "vi"
                else "🤖 Connect Gemini AI for insights")

    st.divider()

    # === System Info ===
    with st.expander("📊 " + ("Thông tin hệ thống" if lang == "vi" else "System Info")):
        _render_system_info()


def _render_index_metric(connector, symbol: str, label: str):
    """Render metric cho 1 chỉ số."""
    dlog = get_debug_logger()
    t0 = time.perf_counter()
    try:
        from datetime import timedelta
        end = datetime.now()
        start = end - timedelta(days=7)
        params = {"symbol": symbol, "start": start.strftime("%Y-%m-%d"), "end": end.strftime("%Y-%m-%d")}
        df = connector.get_historical_data(symbol, params["start"], params["end"])
        duration = (time.perf_counter() - t0) * 1000

        if df is not None and len(df) >= 2:
            last = df.iloc[-1]["close"]
            prev = df.iloc[-2]["close"]
            change = last - prev
            pct = (change / prev) * 100
            st.metric(label, f"{last:,.2f}", f"{change:+,.2f} ({pct:+.2f}%)")
            dlog.log_api_call(
                page="dashboard", component="_render_index_metric",
                source="VnstockFreeConnector", method="get_historical_data",
                params=params, result_status="SUCCESS", duration_ms=duration, symbol=symbol
            )
            debug_show_inline("SUCCESS", "vnstock", duration)
        else:
            st.metric(label, "---")
            dlog.log_api_call(
                page="dashboard", component="_render_index_metric",
                source="VnstockFreeConnector", method="get_historical_data",
                params=params, result_status="EMPTY", duration_ms=duration, symbol=symbol
            )
            debug_show_inline("EMPTY", "vnstock", duration)
    except Exception as e:
        duration = (time.perf_counter() - t0) * 1000
        st.metric(label, "---")
        dlog.log_api_call(
            page="dashboard", component="_render_index_metric",
            source="VnstockFreeConnector", method="get_historical_data",
            params={"symbol": symbol}, result_status="ERROR", error=e, duration_ms=duration, symbol=symbol
        )
        debug_show_inline("ERROR", "vnstock", duration, str(e))


def _render_crypto_metric():
    """Render BTC metric."""
    dlog = get_debug_logger()
    t0 = time.perf_counter()
    try:
        from src.data.connectors.crypto_connector import BinanceConnector
        binance = BinanceConnector()
        if binance.connect():
            ticker = binance.get_ticker_24h("BTCUSDT")
            duration = (time.perf_counter() - t0) * 1000
            if ticker:
                st.metric("BTC/USDT",
                          f"${ticker['price']:,.0f}",
                          f"{ticker['change_pct_24h']:+.2f}%")
                dlog.log_api_call(
                    page="dashboard", component="_render_crypto_metric",
                    source="BinanceConnector", method="get_ticker_24h",
                    params={"symbol": "BTCUSDT"}, result_status="SUCCESS",
                    duration_ms=duration, symbol="BTCUSDT"
                )
                debug_show_inline("SUCCESS", "Binance", duration)
                return
            else:
                dlog.log_api_call(
                    page="dashboard", component="_render_crypto_metric",
                    source="BinanceConnector", method="get_ticker_24h",
                    params={"symbol": "BTCUSDT"}, result_status="EMPTY",
                    duration_ms=duration, symbol="BTCUSDT"
                )
    except Exception as e:
        duration = (time.perf_counter() - t0) * 1000
        dlog.log_api_call(
            page="dashboard", component="_render_crypto_metric",
            source="BinanceConnector", method="get_ticker_24h",
            params={"symbol": "BTCUSDT"}, result_status="ERROR", error=e,
            duration_ms=duration, symbol="BTCUSDT"
        )
        debug_show_inline("ERROR", "Binance", duration, str(e))
    st.metric("BTC/USDT", "---")


def _render_top_stocks():
    """Top stocks placeholder."""
    stocks = [
        {"symbol": "VCB", "price": "86.50", "change": "+2.3%"},
        {"symbol": "FPT", "price": "128.30", "change": "+1.8%"},
        {"symbol": "HPG", "price": "28.15", "change": "-0.5%"},
        {"symbol": "MBB", "price": "24.60", "change": "+1.2%"},
        {"symbol": "TCB", "price": "35.40", "change": "+0.8%"},
    ]
    for s in stocks:
        color = "#00C853" if "+" in s["change"] else "#FF1744"
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;padding:4px 0;">'
            f'<span style="font-weight:600;">{s["symbol"]}</span>'
            f'<span>{s["price"]}</span>'
            f'<span style="color:{color};font-weight:500;">{s["change"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


def _render_system_info():
    """Hiển thị thông tin hệ thống."""
    dlog = get_debug_logger()
    try:
        from src.data.database.connection import get_db
        from src.services.cache_service import get_cache

        col1, col2, col3 = st.columns(3)

        db = get_db()
        cache = get_cache()
        cache_stats = cache.get_stats()

        with col1:
            st.metric("📁 Database Size", f"{db.get_db_size_mb():.2f} MB")
        with col2:
            st.metric("📦 Cache Files", cache_stats.get("file_entries", 0))
        with col3:
            st.metric("🧠 Memory Cache", cache_stats.get("memory_entries", 0))
    except Exception as e:
        st.warning(f"⚠️ Không thể tải thông tin hệ thống")
        dlog.log(
            level=LogLevel.ERROR, category=LogCategory.DB_QUERY,
            page="dashboard", component="_render_system_info",
            action="load_system_info", error_type=type(e).__name__,
            error_message=str(e),
        )
