"""
KTSTOCK - Stock Analysis Page
Trang phân tích cổ phiếu chi tiết.
"""
import streamlit as st
import pandas as pd

from src.app.components.shared import (
    symbol_selector, date_range_selector, signal_badge, trend_badge, error_handler
)
from src.app.i18n import t


@error_handler
def render_stock_analysis():
    """Render trang phân tích cổ phiếu."""
    lang = st.session_state.get("language", "vi")

    # === Symbol & Date Selection ===
    col_sym, col_date = st.columns([1, 2])
    with col_sym:
        symbol = symbol_selector(key="stock_sym", exchange="stock")
    with col_date:
        start_date, end_date = date_range_selector(key="stock_date")

    if not symbol:
        st.warning("⚠️ Vui lòng nhập mã cổ phiếu")
        return

    # === Fetch Data ===
    with st.spinner(f"📡 Đang tải dữ liệu {symbol}..."):
        try:
            from src.data.connectors.vnstock_connector import VnstockFreeConnector
            connector = VnstockFreeConnector()
            connector.connect()
            df = connector.get_historical_data(symbol, start_date, end_date)
        except Exception as e:
            st.error(f"❌ Lỗi kết nối: {e}")
            return

    if df is None or df.empty:
        st.warning(f"📭 Không có dữ liệu cho {symbol}")
        return

    # === Tabs ===
    tab_chart, tab_technical, tab_fundamental, tab_ai = st.tabs([
        "📈 Biểu đồ", "📐 Kỹ thuật", "📋 Cơ bản", "🤖 AI"
    ])

    with tab_chart:
        _render_chart_tab(df, symbol)

    with tab_technical:
        _render_technical_tab(df, symbol)

    with tab_fundamental:
        _render_fundamental_tab(symbol, connector)

    with tab_ai:
        _render_ai_tab(symbol, df)


def _render_chart_tab(df: pd.DataFrame, symbol: str):
    """Tab biểu đồ nến."""
    from src.charts.plotly_engine import candlestick_chart

    # Options
    col1, col2, col3 = st.columns(3)
    with col1:
        show_volume = st.checkbox("📊 Volume", value=True, key="chart_vol")
    with col2:
        show_ma = st.checkbox("📏 Moving Average", value=True, key="chart_ma")
    with col3:
        ma_periods_str = st.text_input("MA Periods", value="20,50", key="chart_ma_p")
        ma_periods = [int(x.strip()) for x in ma_periods_str.split(",") if x.strip().isdigit()]

    fig = candlestick_chart(
        df, title=f"📈 {symbol}", show_volume=show_volume,
        show_ma=show_ma, ma_periods=ma_periods or [20, 50],
    )
    st.plotly_chart(fig, width='stretch')

    # Summary stats
    last = df.iloc[-1]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Close", f"{last['close']:,.2f}")
    c2.metric("High", f"{last.get('high', 0):,.2f}")
    c3.metric("Low", f"{last.get('low', 0):,.2f}")
    c4.metric("Volume", f"{last.get('volume', 0):,.0f}")


def _render_technical_tab(df: pd.DataFrame, symbol: str):
    """Tab phân tích kỹ thuật."""
    from src.core.analysis.technical import TechnicalAnalysis
    from src.charts.plotly_engine import technical_chart, signal_gauge

    ta = TechnicalAnalysis(df)
    signals = ta.generate_signals()

    # Signal summary
    st.markdown("#### 🎯 Tín hiệu tổng hợp")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(signal_badge(signals["signal"]), unsafe_allow_html=True)
    with col2:
        st.markdown(trend_badge(signals["trend"]), unsafe_allow_html=True)
    with col3:
        st.metric("Confidence", f"{signals['confidence']*100:.0f}%")

    # Signal details
    if signals.get("details"):
        with st.expander("📋 Chi tiết tín hiệu"):
            for ind, desc, action in signals["details"]:
                icon = "🟢" if action == "buy" else ("🔴" if action == "sell" else "ℹ️")
                st.markdown(f"- {icon} **{ind}**: {desc}")

    st.divider()

    # Technical indicators chart
    indicators = st.multiselect(
        "Chọn chỉ báo", ["rsi", "macd", "stochastic"],
        default=["rsi", "macd"], key="tech_ind"
    )

    df_ta = ta.calculate_all()
    fig = technical_chart(df_ta, indicators=indicators, title=f"📐 {symbol} - Chỉ báo kỹ thuật")
    st.plotly_chart(fig, width='stretch')

    # RSI & MACD gauges
    col1, col2 = st.columns(2)
    with col1:
        if signals.get("rsi") is not None:
            fig_rsi = signal_gauge(signals["rsi"], "RSI (14)")
            st.plotly_chart(fig_rsi, width='stretch')
    with col2:
        if signals.get("adx") is not None:
            fig_adx = signal_gauge(signals["adx"], "ADX (14)")
            st.plotly_chart(fig_adx, width='stretch')


def _render_fundamental_tab(symbol: str, connector):
    """Tab phân tích cơ bản."""
    st.markdown("#### 📋 Phân tích cơ bản")

    try:
        company = connector.get_company_info(symbol)
        if company:
            st.json(company)
        else:
            st.info("📭 Không có dữ liệu công ty")
    except Exception as e:
        st.warning(f"⚠️ {e}")

    try:
        ratios = connector.get_financial_data(symbol, "ratio")
        if ratios is not None and not ratios.empty:
            st.dataframe(ratios, width='stretch')
    except Exception as e:
        st.warning(f"⚠️ {e}")


def _render_ai_tab(symbol: str, df: pd.DataFrame):
    """Tab phân tích AI."""
    st.markdown("#### 🤖 Phân tích bằng AI")

    if st.button("🚀 Phân tích bằng Gemini AI", key="ai_stock_btn", type="primary"):
        with st.spinner("🤖 AI đang phân tích..."):
            try:
                from src.ai.services.analysis_service import AIAnalysisService
                from src.core.analysis.technical import TechnicalAnalysis

                ta = TechnicalAnalysis(df)
                signals = ta.generate_signals()
                last = df.iloc[-1]

                ai_service = AIAnalysisService()
                result = ai_service.analyze_stock(symbol, {
                    "price": last["close"],
                    "volume": last.get("volume", 0),
                    "rsi": signals.get("rsi"),
                    "macd": signals.get("macd_hist"),
                    "trend": signals.get("trend"),
                })

                if result["success"]:
                    st.markdown(result["analysis"])
                else:
                    st.warning(result["analysis"])
            except Exception as e:
                st.error(f"❌ Lỗi AI: {e}")
    else:
        st.info("👆 Nhấn nút để bắt đầu phân tích AI")
