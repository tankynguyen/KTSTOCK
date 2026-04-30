"""
KTSTOCK - AI Insights, News, Reports, Macro Pages
Các trang bổ sung cho hệ thống.
"""
import time
import streamlit as st
from src.app.components.shared import error_handler, symbol_selector, debug_show_inline
from src.utils.debug_logger import get_debug_logger


@error_handler
def render_ai_insights():
    """Trang AI Insights - Chat và phân tích."""
    dlog = get_debug_logger()
    st.markdown("### 💬 Chat với AI")
    if "ai_messages" not in st.session_state:
        st.session_state.ai_messages = []

    # Hiển thị lịch sử chat
    for msg in st.session_state.ai_messages:
        role = msg["role"]
        with st.chat_message(role):
            st.markdown(msg["content"])

    # Input
    user_input = st.chat_input("Hỏi AI về thị trường chứng khoán...")
    if user_input:
        st.session_state.ai_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("🤖 AI đang suy nghĩ..."):
                t0 = time.perf_counter()
                try:
                    from src.ai.services.analysis_service import AIAnalysisService
                    ai = AIAnalysisService()
                    response = ai.chat(user_input)
                    duration = (time.perf_counter() - t0) * 1000
                    st.markdown(response)
                    st.session_state.ai_messages.append({"role": "assistant", "content": response})
                    dlog.log_ai_request(
                        page="ai_insights", component="render_ai_insights",
                        provider="Gemini", prompt_preview=user_input,
                        result_status="SUCCESS", duration_ms=duration
                    )
                    debug_show_inline("SUCCESS", "Gemini AI", duration)
                except Exception as e:
                    duration = (time.perf_counter() - t0) * 1000
                    err = f"❌ Lỗi AI: {e}"
                    st.error(err)
                    st.session_state.ai_messages.append({"role": "assistant", "content": err})
                    dlog.log_ai_request(
                        page="ai_insights", component="render_ai_insights",
                        provider="Gemini", prompt_preview=user_input,
                        result_status="ERROR", error=e, duration_ms=duration
                    )
                    debug_show_inline("ERROR", "Gemini AI", duration, str(e))


@error_handler
def render_news():
    """Trang Tin tức & Sentiment."""
    st.markdown("### 📰 Tin tức thị trường")
    st.info("📡 Tính năng tin tức real-time sẽ được kết nối qua API trong bản cập nhật tiếp theo.")

    st.divider()
    st.markdown("### 🧠 Phân tích Sentiment")

    text = st.text_area("Nhập nội dung tin tức để phân tích", height=150,
                        placeholder="VCB công bố lợi nhuận tăng mạnh, vượt kỳ vọng...")

    if st.button("🔍 Phân tích Sentiment", type="primary") and text:
        from src.core.analysis.sentiment import SentimentAnalyzer
        sa = SentimentAnalyzer()
        result = sa.analyze_text(text)

        c1, c2, c3 = st.columns(3)
        sentiment_colors = {"positive": "🟢", "neutral": "🟡", "negative": "🔴"}
        c1.metric("Cảm xúc", f"{sentiment_colors.get(result['sentiment'], '⚪')} {result['sentiment'].upper()}")
        c2.metric("Điểm", f"{result['score']:+.3f}")
        c3.metric("Tích cực / Tiêu cực", f"{result['positive_count']} / {result['negative_count']}")

        if result.get("positive_keywords"):
            st.success(f"✅ Từ tích cực: {', '.join(result['positive_keywords'])}")
        if result.get("negative_keywords"):
            st.error(f"⚠️ Từ tiêu cực: {', '.join(result['negative_keywords'])}")


@error_handler
def render_reports():
    """Trang Báo cáo."""
    dlog = get_debug_logger()
    st.markdown("### 📑 Báo cáo thị trường")

    if st.button("🤖 Tạo báo cáo AI", type="primary"):
        with st.spinner("🤖 AI đang tạo báo cáo..."):
            t0 = time.perf_counter()
            try:
                from src.ai.services.analysis_service import AIAnalysisService
                ai = AIAnalysisService()
                result = ai.generate_report({
                    "vnindex": "Đang cập nhật",
                    "hnx": "Đang cập nhật",
                    "total_volume": "Đang cập nhật",
                })
                duration = (time.perf_counter() - t0) * 1000
                if result["success"]:
                    st.markdown(result["report"])
                    dlog.log_ai_request(
                        page="reports", component="render_reports",
                        provider="Gemini", prompt_preview="Generate market report",
                        result_status="SUCCESS", duration_ms=duration
                    )
                    debug_show_inline("SUCCESS", "Gemini AI", duration)
                else:
                    st.warning(result["report"])
                    dlog.log_ai_request(
                        page="reports", component="render_reports",
                        provider="Gemini", prompt_preview="Generate market report",
                        result_status="EMPTY", duration_ms=duration
                    )
            except Exception as e:
                duration = (time.perf_counter() - t0) * 1000
                st.error(f"❌ {e}")
                dlog.log_ai_request(
                    page="reports", component="render_reports",
                    provider="Gemini", prompt_preview="Generate market report",
                    result_status="ERROR", error=e, duration_ms=duration
                )
                debug_show_inline("ERROR", "Gemini AI", duration, str(e))

    st.divider()
    st.info("📊 Tính năng export PDF/Excel sẽ sẵn sàng trong bản cập nhật tiếp theo.")


@error_handler
def render_macro():
    """Trang Kinh tế vĩ mô."""
    st.markdown("### 🌍 Dữ liệu kinh tế vĩ mô")
    st.info("📡 Dữ liệu macro (GDP, CPI, lãi suất...) yêu cầu vnstock_data >= 3.0.0 (Sponsored)")

    st.divider()
    st.markdown("#### 📊 Chỉ số vĩ mô chính")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📈 GDP Growth", "5.05%", "+0.5%")
    c2.metric("📊 CPI", "3.2%", "-0.3%")
    c3.metric("🏦 Lãi suất", "4.5%", "0%")
    c4.metric("💱 USD/VND", "25,450", "+50")
    st.caption("⚠️ Dữ liệu mẫu. Kết nối live data qua vnstock_data Sponsored.")


@error_handler  
def render_fundamental_page():
    """Trang Phân tích cơ bản độc lập."""
    dlog = get_debug_logger()
    symbol = symbol_selector(key="fund_sym", exchange="stock")

    if st.button("📋 Phân tích", type="primary"):
        with st.spinner("📋 Đang phân tích..."):
            t0 = time.perf_counter()
            try:
                from src.data.connectors.vnstock_connector import VnstockFreeConnector
                connector = VnstockFreeConnector()
                connector.connect()

                # Company info
                company = connector.get_company_info(symbol)
                if company:
                    st.json(company)

                # Financial ratios
                ratios = connector.get_financial_data(symbol, "ratio")
                if ratios is not None and not ratios.empty:
                    st.dataframe(ratios, width='stretch')

                # Income statement
                income = connector.get_financial_data(symbol, "income")
                duration = (time.perf_counter() - t0) * 1000
                if income is not None and not income.empty:
                    st.markdown("#### 📊 Báo cáo thu nhập")
                    st.dataframe(income, width='stretch')
                
                dlog.log_api_call(
                    page="fundamental", component="render_fundamental_page",
                    source="VnstockFreeConnector", method="get_financial_data",
                    params={"symbol": symbol, "types": "ratio,income"},
                    result_status="SUCCESS", duration_ms=duration, symbol=symbol
                )
                debug_show_inline("SUCCESS", "vnstock", duration)
            except Exception as e:
                duration = (time.perf_counter() - t0) * 1000
                st.error(f"❌ {e}")
                dlog.log_api_call(
                    page="fundamental", component="render_fundamental_page",
                    source="VnstockFreeConnector", method="get_financial_data",
                    params={"symbol": symbol},
                    result_status="ERROR", error=e, duration_ms=duration, symbol=symbol
                )
                debug_show_inline("ERROR", "vnstock", duration, str(e))
