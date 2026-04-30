"""
KTSTOCK - Portfolio Page
Trang quản lý danh mục đầu tư.
"""
import streamlit as st
import pandas as pd

from src.app.components.shared import error_handler


@error_handler
def render_portfolio():
    """Render trang danh mục đầu tư."""
    lang = st.session_state.get("language", "vi")
    user = st.session_state.get("user", {})
    user_id = user.get("id", 0)

    if not user_id:
        st.warning("⚠️ Vui lòng đăng nhập để sử dụng tính năng này")
        return

    from src.core.portfolio.manager import PortfolioManager
    pm = PortfolioManager(user_id)

    tab_overview, tab_create, tab_optimize = st.tabs([
        "📊 Tổng quan", "➕ Tạo mới", "📈 Tối ưu hóa"
    ])

    with tab_overview:
        _render_portfolio_overview(pm)
    with tab_create:
        _render_create_portfolio(pm)
    with tab_optimize:
        _render_optimizer()


def _render_portfolio_overview(pm):
    """Tab tổng quan portfolios."""
    portfolios = pm.get_portfolios()

    if not portfolios:
        st.info("📭 Chưa có danh mục nào. Tạo mới ở tab '➕ Tạo mới'")
        return

    for portfolio in portfolios:
        pid = portfolio["id"]
        with st.expander(f"💼 {portfolio['name']} (#{pid})", expanded=True):
            summary = pm.get_portfolio_summary(pid)

            # Metrics
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("💰 Tổng giá trị", f"{summary['total_value']:,.0f} VND")
            c2.metric("📊 Vốn đầu tư", f"{summary['total_cost']:,.0f} VND")

            pnl = summary["profit_loss"]
            pnl_color = "normal" if pnl >= 0 else "inverse"
            c3.metric("📈 Lãi/Lỗ", f"{pnl:+,.0f}", f"{summary['profit_loss_pct']:+.2f}%",
                      delta_color=pnl_color)
            c4.metric("📦 Vị thế", summary["num_positions"])

            # Positions table
            if summary.get("positions"):
                df = pd.DataFrame(summary["positions"])
                display_cols = [c for c in ["symbol", "quantity", "avg_price", "current_price",
                                            "market_value", "profit_loss", "profit_loss_pct", "weight"]
                                if c in df.columns]
                st.dataframe(df[display_cols], width='stretch', height=250)

                # Pie chart
                from src.charts.plotly_engine import portfolio_pie_chart
                fig = portfolio_pie_chart(summary["positions"], f"Phân bổ - {portfolio['name']}")
                st.plotly_chart(fig, width='stretch')

            # Add position form
            with st.form(f"add_pos_{pid}"):
                st.markdown("**➕ Thêm vị thế mới**")
                fc1, fc2, fc3 = st.columns(3)
                with fc1:
                    new_symbol = st.text_input("Mã CK", key=f"sym_{pid}").upper().strip()
                with fc2:
                    new_qty = st.number_input("Số lượng", min_value=0, step=100, key=f"qty_{pid}")
                with fc3:
                    new_price = st.number_input("Giá TB", min_value=0.0, step=0.1, key=f"price_{pid}")

                if st.form_submit_button("➕ Thêm", type="primary"):
                    if new_symbol and new_qty > 0 and new_price > 0:
                        pm.add_position(pid, new_symbol, new_qty, new_price)
                        st.success(f"✅ Đã thêm {new_qty} {new_symbol}")
                        st.rerun()
                    else:
                        st.error("❌ Vui lòng nhập đầy đủ thông tin")


def _render_create_portfolio(pm):
    """Tab tạo portfolio mới."""
    with st.form("create_portfolio"):
        name = st.text_input("📝 Tên danh mục", placeholder="Danh mục chính")
        description = st.text_area("📋 Mô tả", placeholder="Mô tả chiến lược...")
        capital = st.number_input("💰 Vốn ban đầu (VND)", min_value=0, step=1000000, value=100000000)

        if st.form_submit_button("✅ Tạo danh mục", type="primary"):
            if name:
                pid = pm.create_portfolio(name, description, capital)
                st.success(f"✅ Đã tạo danh mục '{name}' (ID: {pid})")
                st.rerun()
            else:
                st.error("❌ Vui lòng nhập tên danh mục")


def _render_optimizer():
    """Tab tối ưu hóa Markowitz."""
    st.markdown("### 📈 Tối ưu hóa danh mục (Markowitz)")
    st.info("📊 Nhập danh sách cổ phiếu để tìm phân bổ tối ưu")

    symbols_input = st.text_input("Nhập mã CK (phân cách bằng dấu phẩy)",
                                   value="VCB,FPT,HPG,MBB,VNM", key="opt_symbols")
    symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]

    if len(symbols) < 2:
        st.warning("⚠️ Cần ít nhất 2 mã cổ phiếu")
        return

    num_sim = st.slider("Số lần mô phỏng", 1000, 10000, 5000, step=1000, key="opt_sim")

    if st.button("🚀 Tối ưu hóa", type="primary", key="run_optimize"):
        with st.spinner("🔄 Đang mô phỏng Monte Carlo..."):
            try:
                from src.data.connectors.vnstock_connector import VnstockFreeConnector
                from src.core.portfolio.manager import PortfolioOptimizer
                from src.charts.plotly_engine import efficient_frontier_chart
                from datetime import datetime, timedelta
                import numpy as np

                connector = VnstockFreeConnector()
                connector.connect()

                end = datetime.now().strftime("%Y-%m-%d")
                start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

                # Fetch returns
                returns_dict = {}
                progress = st.progress(0)
                for i, sym in enumerate(symbols):
                    df = connector.get_historical_data(sym, start, end)
                    if df is not None and not df.empty:
                        returns_dict[sym] = df["close"].pct_change().dropna()
                    progress.progress((i + 1) / len(symbols))

                if len(returns_dict) < 2:
                    st.error("❌ Không đủ dữ liệu (cần ≥2 mã)")
                    return

                # Align returns
                returns_df = pd.DataFrame(returns_dict).dropna()

                result = PortfolioOptimizer.optimize(returns_df, num_portfolios=num_sim)

                # Display results
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("#### ⭐ Max Sharpe Ratio")
                    ms = result["max_sharpe"]
                    st.metric("Sharpe", f"{ms['sharpe']:.3f}")
                    st.metric("Return", f"{ms['return']:.2f}%")
                    st.metric("Risk", f"{ms['risk']:.2f}%")
                    for sym, w in ms["weights"].items():
                        st.caption(f"• {sym}: **{w:.1f}%**")

                with c2:
                    st.markdown("#### 🛡️ Min Volatility")
                    mv = result["min_volatility"]
                    st.metric("Sharpe", f"{mv['sharpe']:.3f}")
                    st.metric("Return", f"{mv['return']:.2f}%")
                    st.metric("Risk", f"{mv['risk']:.2f}%")
                    for sym, w in mv["weights"].items():
                        st.caption(f"• {sym}: **{w:.1f}%**")

                # Efficient Frontier chart
                fig = efficient_frontier_chart(result)
                st.plotly_chart(fig, width='stretch')

            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
