"""
KTSTOCK - Stock Screener Page
Trang bộ lọc cổ phiếu đa tiêu chí.
"""
import streamlit as st
import pandas as pd

from src.app.components.shared import error_handler, render_dataframe


@error_handler
def render_screener():
    """Render trang bộ lọc cổ phiếu."""
    lang = st.session_state.get("language", "vi")

    # === Preset Buttons ===
    st.markdown("### 🎯 " + ("Bộ lọc nhanh" if lang == "vi" else "Quick Presets"))
    preset_cols = st.columns(5)

    from src.core.screener.filters import StockScreener
    screener = StockScreener()

    with preset_cols[0]:
        if st.button("💎 Cổ phiếu giá trị", width='stretch', key="preset_value"):
            screener = StockScreener.undervalued_stocks()
            st.session_state.screener_preset = "undervalued"
    with preset_cols[1]:
        if st.button("🚀 Tăng trưởng", width='stretch', key="preset_growth"):
            screener = StockScreener.growth_stocks()
            st.session_state.screener_preset = "growth"
    with preset_cols[2]:
        if st.button("💰 Cổ tức cao", width='stretch', key="preset_div"):
            screener = StockScreener.high_dividend()
            st.session_state.screener_preset = "dividend"
    with preset_cols[3]:
        if st.button("📈 Momentum", width='stretch', key="preset_momentum"):
            screener = StockScreener.momentum_stocks()
            st.session_state.screener_preset = "momentum"
    with preset_cols[4]:
        if st.button("🔥 Vol Breakout", width='stretch', key="preset_vol"):
            screener = StockScreener.volume_breakout()
            st.session_state.screener_preset = "volume"

    st.divider()

    # === Custom Filters ===
    st.markdown("### ⚙️ " + ("Bộ lọc tùy chỉnh" if lang == "vi" else "Custom Filters"))
    with st.expander("🔧 Thêm bộ lọc", expanded=True):
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

        with col1:
            filter_col = st.selectbox("Chỉ số", [
                "pe_ratio", "pb_ratio", "roe", "roa", "eps",
                "debt_to_equity", "dividend_yield", "volume",
                "rsi", "market_cap", "net_margin",
            ], key="filter_col")
        with col2:
            filter_op = st.selectbox("Điều kiện", [
                ("gt", ">"), ("gte", "≥"), ("lt", "<"), ("lte", "≤"), ("eq", "="),
            ], format_func=lambda x: x[1], key="filter_op")
        with col3:
            filter_val = st.number_input("Giá trị", value=0.0, key="filter_val")
        with col4:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Thêm", key="add_filter"):
                if "custom_filters" not in st.session_state:
                    st.session_state.custom_filters = []
                st.session_state.custom_filters.append({
                    "column": filter_col,
                    "operator": filter_op[0],
                    "value": filter_val,
                })

    # Hiển thị filters đã chọn
    if st.session_state.get("custom_filters"):
        st.markdown("**Bộ lọc đang áp dụng:**")
        for i, f in enumerate(st.session_state.custom_filters):
            op_display = {"gt": ">", "gte": "≥", "lt": "<", "lte": "≤", "eq": "="}
            col_f, col_x = st.columns([5, 1])
            col_f.caption(f"📌 {f['column']} {op_display.get(f['operator'], '?')} {f['value']}")
            if col_x.button("❌", key=f"del_f_{i}"):
                st.session_state.custom_filters.pop(i)
                st.rerun()

    st.divider()

    # === Results ===
    st.markdown("### 📊 " + ("Kết quả" if lang == "vi" else "Results"))

    if st.button("🔍 Chạy bộ lọc", type="primary", key="run_screener"):
        with st.spinner("🔍 Đang lọc..."):
            try:
                from src.data.connectors.vnstock_connector import VnstockFreeConnector
                connector = VnstockFreeConnector()
                connector.connect()
                listing = connector.get_listing()

                if listing is not None and not listing.empty:
                    # Apply custom filters
                    for f in st.session_state.get("custom_filters", []):
                        screener.add_filter(f["column"], f["operator"], f["value"])

                    result = screener.apply(listing)
                    result = screener.rank(result, rank_by="volume" if "volume" in result.columns else result.columns[0])

                    st.success(f"✅ Tìm thấy {len(result)} cổ phiếu phù hợp")
                    render_dataframe(result, height=500)
                else:
                    st.warning("📭 Không thể tải danh sách cổ phiếu")
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
    else:
        st.info("👆 Chọn preset hoặc thêm bộ lọc tùy chỉnh, sau đó nhấn 'Chạy bộ lọc'")
