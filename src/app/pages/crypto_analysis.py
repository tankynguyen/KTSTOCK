"""
KTSTOCK - Crypto Analysis Page
Trang phân tích Crypto (Binance).
"""
import streamlit as st
import pandas as pd

from src.app.components.shared import symbol_selector, date_range_selector, error_handler


@error_handler
def render_crypto_analysis():
    """Render trang phân tích crypto."""
    lang = st.session_state.get("language", "vi")

    col_sym, col_date = st.columns([1, 2])
    with col_sym:
        symbol = symbol_selector(key="crypto_sym", exchange="crypto")
    with col_date:
        start_date, end_date = date_range_selector(key="crypto_date")

    tab_chart, tab_tech, tab_market, tab_ai = st.tabs([
        "📈 Biểu đồ", "📐 Kỹ thuật", "📊 Thị trường", "🤖 AI"
    ])

    with tab_chart:
        _render_crypto_chart(symbol, start_date, end_date)

    with tab_tech:
        _render_crypto_technical(symbol, start_date, end_date)

    with tab_market:
        _render_market_overview()

    with tab_ai:
        _render_crypto_ai(symbol)


def _render_crypto_chart(symbol: str, start_date: str, end_date: str):
    """Tab biểu đồ crypto."""
    with st.spinner(f"₿ Đang tải {symbol}..."):
        try:
            from src.data.connectors.crypto_connector import BinanceConnector
            from src.charts.plotly_engine import candlestick_chart

            binance = BinanceConnector()
            binance.connect()

            # Ticker 24h
            ticker = binance.get_ticker_24h(symbol)
            if ticker:
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Giá", f"${ticker['price']:,.2f}")
                c2.metric("24h", f"{ticker['change_pct_24h']:+.2f}%",
                          delta_color="normal" if ticker["change_pct_24h"] >= 0 else "inverse")
                c3.metric("High 24h", f"${ticker['high_24h']:,.2f}")
                c4.metric("Low 24h", f"${ticker['low_24h']:,.2f}")

            # Candlestick
            interval = st.selectbox("⏱️ Interval", ["1D", "4H", "1H", "15m"], key="crypto_interval")
            df = binance.get_historical_data(symbol, start_date, end_date, interval)
            if df is not None and not df.empty:
                fig = candlestick_chart(df, title=f"₿ {symbol}", show_volume=True)
                st.plotly_chart(fig, width='stretch')
            else:
                st.warning("📭 Không có dữ liệu")
        except Exception as e:
            st.error(f"❌ {e}")


def _render_crypto_technical(symbol: str, start_date: str, end_date: str):
    """Tab kỹ thuật crypto."""
    try:
        from src.data.connectors.crypto_connector import BinanceConnector
        from src.core.analysis.technical import TechnicalAnalysis
        from src.app.components.shared import signal_badge, trend_badge

        binance = BinanceConnector()
        binance.connect()
        df = binance.get_historical_data(symbol, start_date, end_date, "1D")

        if df is not None and len(df) >= 20:
            ta = TechnicalAnalysis(df)
            signals = ta.generate_signals()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(signal_badge(signals["signal"]), unsafe_allow_html=True)
            with col2:
                st.markdown(trend_badge(signals["trend"]), unsafe_allow_html=True)
            with col3:
                st.metric("Confidence", f"{signals['confidence']*100:.0f}%")

            from src.charts.plotly_engine import technical_chart
            df_ta = ta.calculate_all()
            fig = technical_chart(df_ta, indicators=["rsi", "macd"], title=f"₿ {symbol} Technical")
            st.plotly_chart(fig, width='stretch')
        else:
            st.warning("📭 Cần ít nhất 20 candles")
    except Exception as e:
        st.error(f"❌ {e}")


def _render_market_overview():
    """Tab tổng quan thị trường crypto."""
    try:
        from src.data.connectors.crypto_connector import BinanceConnector
        binance = BinanceConnector()
        binance.connect()

        st.markdown("#### 🏆 Top 20 Crypto theo Volume")
        top = binance.get_top_cryptos(limit=20)
        if top is not None and not top.empty:
            st.dataframe(top, width='stretch', height=500)
        else:
            st.info("📭 Không thể tải dữ liệu")
    except Exception as e:
        st.error(f"❌ {e}")


def _render_crypto_ai(symbol: str):
    """Tab AI cho crypto."""
    if st.button("🤖 Phân tích AI", key="ai_crypto_btn", type="primary"):
        with st.spinner("🤖 AI đang phân tích..."):
            try:
                from src.ai.services.analysis_service import AIAnalysisService
                from src.data.connectors.crypto_connector import BinanceConnector

                binance = BinanceConnector()
                binance.connect()
                ticker = binance.get_ticker_24h(symbol)

                ai = AIAnalysisService()
                result = ai.analyze_crypto(symbol, ticker or {})
                if result["success"]:
                    st.markdown(result["analysis"])
                else:
                    st.warning(result["analysis"])
            except Exception as e:
                st.error(f"❌ {e}")
    else:
        st.info("👆 Nhấn nút để phân tích AI")
