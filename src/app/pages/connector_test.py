"""
KTSTOCK - Connector Test Page
Trang kiểm tra toàn bộ API connectors (Free, Sponsored, TA, News, Chart, Pipeline).
"""
import streamlit as st
import pandas as pd
from loguru import logger


def _status_badge(available: bool) -> str:
    return "🟢 Sẵn sàng" if available else "🔴 Chưa cài"


def _show_df(df, label=""):
    if df is not None and not df.empty:
        st.success(f"✅ {label}: {df.shape[0]} rows × {df.shape[1]} cols")
        st.dataframe(df.head(10), use_container_width=True)
    else:
        st.warning(f"⚠️ {label}: Không có dữ liệu")


def render_connector_test():
    """Render trang kiểm tra connectors."""
    st.markdown("### 🧪 Kiểm Tra Toàn Bộ Connectors")

    # ── Status Overview ──
    statuses = {}
    try:
        from src.data.connectors.vnstock_connector import VnstockFreeConnector
        free = VnstockFreeConnector()
        free.connect()
        statuses["vnstock Free"] = free.is_connected
    except Exception:
        statuses["vnstock Free"] = False

    try:
        from src.data.connectors.vnstock_pro_connector import VnstockSponsoredConnector
        pro = VnstockSponsoredConnector()
        pro.connect()
        statuses["vnstock Sponsored"] = pro.is_connected
    except Exception:
        statuses["vnstock Sponsored"] = False

    for name, mod in [("vnstock_ta", "vnstock_ta_connector"), ("vnstock_news", "vnstock_news_connector"),
                      ("vnstock_chart", "vnstock_chart_connector"), ("vnstock_pipeline", "vnstock_pipeline_connector")]:
        try:
            module = __import__(f"src.data.connectors.{mod}", fromlist=[mod])
            cls = list(vars(module).values())
            for v in vars(module).values():
                if isinstance(v, type) and v.__module__ == f"src.data.connectors.{mod}":
                    obj = v()
                    statuses[name] = getattr(obj, 'is_available', False) or getattr(obj, 'is_connected', False)
                    break
        except Exception:
            statuses[name] = False

    cols = st.columns(len(statuses))
    for i, (name, ok) in enumerate(statuses.items()):
        with cols[i]:
            st.metric(name, _status_badge(ok))

    st.divider()

    # ── Tab-based testing ──
    tabs = st.tabs(["📈 Free API", "⭐ Sponsored API", "📊 TA Indicators", "📰 News", "🎨 Chart", "🔄 Pipeline"])

    # ════════════════════════════════════════
    # TAB 1: FREE API
    # ════════════════════════════════════════
    with tabs[0]:
        st.markdown("#### vnstock Free Connector")
        try:
            from src.data.connectors.vnstock_connector import VnstockFreeConnector
            free = VnstockFreeConnector()
            free.connect()
        except Exception as e:
            st.error(f"Không thể khởi tạo: {e}")
            return

        test_group = st.selectbox("Chọn nhóm API:", ["Listing", "Company", "Trading", "Finance", "Quote"], key="free_grp")
        symbol = st.text_input("Mã cổ phiếu:", "VCB", key="free_sym")

        if test_group == "Listing":
            action = st.selectbox("Method:", [
                "all_symbols", "symbols_by_exchange", "symbols_by_industries",
                "symbols_by_group", "all_indices", "all_future_indices",
                "all_government_bonds", "all_covered_warrant", "all_bonds", "all_etf",
            ], key="free_list_act")
            if st.button("▶️ Chạy", key="free_list_run"):
                with st.spinner("Đang tải..."):
                    if action == "all_symbols":
                        _show_df(free.get_listing(), "all_symbols")
                    elif action == "symbols_by_exchange":
                        ex = st.session_state.get("free_exchange", "HOSE")
                        _show_df(free.get_symbols_by_exchange(ex), f"symbols_by_exchange({ex})")
                    elif action == "symbols_by_industries":
                        _show_df(free.get_symbols_by_industries(), "symbols_by_industries")
                    elif action == "symbols_by_group":
                        _show_df(free.get_symbols_by_group("VN30"), "symbols_by_group(VN30)")
                    elif action == "all_indices":
                        _show_df(free.get_all_indices(), "all_indices")
                    elif action == "all_future_indices":
                        _show_df(free.get_all_future_indices(), "all_future_indices")
                    elif action == "all_government_bonds":
                        _show_df(free.get_all_government_bonds(), "all_government_bonds")
                    elif action == "all_covered_warrant":
                        _show_df(free.get_all_covered_warrant(), "all_covered_warrant")
                    elif action == "all_bonds":
                        _show_df(free.get_all_bonds(), "all_bonds")
                    elif action == "all_etf":
                        _show_df(free.get_all_etf(), "all_etf")

        elif test_group == "Company":
            action = st.selectbox("Method:", [
                "overview", "shareholders", "officers", "subsidiaries",
                "news", "events", "ownership", "insider_trading",
            ], key="free_comp_act")
            if st.button("▶️ Chạy", key="free_comp_run"):
                with st.spinner("Đang tải..."):
                    if action == "overview":
                        result = free.get_company_info(symbol)
                        if result:
                            st.success(f"✅ overview: {len(result)} fields")
                            st.json(result)
                        else:
                            st.warning("Không có dữ liệu")
                    elif action == "shareholders":
                        _show_df(free.get_shareholders(symbol), "shareholders")
                    elif action == "officers":
                        _show_df(free.get_officers(symbol), "officers")
                    elif action == "subsidiaries":
                        _show_df(free.get_subsidiaries(symbol), "subsidiaries")
                    elif action == "news":
                        _show_df(free.get_company_news(symbol), "news")
                    elif action == "events":
                        _show_df(free.get_company_events(symbol), "events")
                    elif action == "ownership":
                        _show_df(free.get_ownership(symbol), "ownership (KBS)")
                    elif action == "insider_trading":
                        _show_df(free.get_insider_trading(symbol), "insider_trading (KBS)")

        elif test_group == "Trading":
            syms = st.text_input("Danh sách mã (phẩy):", "VCB,ACB,FPT", key="free_trade_syms")
            if st.button("▶️ Price Board", key="free_trade_run"):
                with st.spinner("Đang tải..."):
                    _show_df(free.get_price_board(syms.split(",")), "price_board")

        elif test_group == "Finance":
            rtype = st.selectbox("Report:", ["income", "balance", "cashflow", "ratio"], key="free_fin_type")
            period = st.selectbox("Period:", ["year", "quarter"], key="free_fin_period")
            if st.button("▶️ Chạy", key="free_fin_run"):
                with st.spinner("Đang tải..."):
                    _show_df(free.get_financial_data(symbol, rtype, period), f"{rtype} ({period})")

        elif test_group == "Quote":
            c1, c2 = st.columns(2)
            start = c1.date_input("Từ ngày:", value=pd.Timestamp("2024-01-01"), key="free_q_start")
            end = c2.date_input("Đến ngày:", value=pd.Timestamp.now(), key="free_q_end")
            if st.button("▶️ History", key="free_q_run"):
                with st.spinner("Đang tải..."):
                    _show_df(free.get_historical_data(symbol, str(start), str(end)), f"history({symbol})")

    # ════════════════════════════════════════
    # TAB 2: SPONSORED API
    # ════════════════════════════════════════
    with tabs[1]:
        st.markdown("#### vnstock Sponsored Connector")
        try:
            from src.data.connectors.vnstock_pro_connector import VnstockSponsoredConnector
            pro = VnstockSponsoredConnector()
            pro.connect()
        except Exception as e:
            st.error(f"Không thể khởi tạo: {e}")
            return

        test_grp2 = st.selectbox("Nhóm:", ["Market", "Macro", "Commodity", "Trading Pro"], key="pro_grp")
        if test_grp2 == "Market":
            action = st.selectbox("Method:", ["market_pe", "market_pb", "market_evaluation"], key="pro_mkt_act")
            if st.button("▶️ Chạy", key="pro_mkt_run"):
                with st.spinner("Đang tải..."):
                    fn = {"market_pe": pro.get_market_pe, "market_pb": pro.get_market_pb, "market_evaluation": pro.get_market_evaluation}
                    _show_df(fn[action](), action)

        elif test_grp2 == "Macro":
            action = st.selectbox("Method:", ["gdp", "cpi", "exchange_rate", "fdi", "interest_rate"], key="pro_mac_act")
            if st.button("▶️ Chạy", key="pro_mac_run"):
                with st.spinner("Đang tải..."):
                    fn_map = {"gdp": pro.get_gdp, "cpi": pro.get_cpi, "exchange_rate": pro.get_exchange_rate,
                              "fdi": pro.get_fdi, "interest_rate": lambda: pro.get_interest_rate("1Y", "day")}
                    _show_df(fn_map[action](), action)

        elif test_grp2 == "Commodity":
            action = st.selectbox("Method:", ["gold", "oil", "steel", "pork"], key="pro_cmd_act")
            if st.button("▶️ Chạy", key="pro_cmd_run"):
                with st.spinner("Đang tải..."):
                    fn = {"gold": pro.get_gold_price, "oil": pro.get_oil_price,
                          "steel": pro.get_steel_price, "pork": pro.get_pork_price}
                    _show_df(fn[action](), action)

        elif test_grp2 == "Trading Pro":
            sym2 = st.text_input("Mã:", "VCB", key="pro_trade_sym")
            action = st.selectbox("Method:", ["foreign_trade", "prop_trade", "insider_deal", "order_stats"], key="pro_trade_act")
            if st.button("▶️ Chạy", key="pro_trade_run"):
                with st.spinner("Đang tải..."):
                    if action == "foreign_trade":
                        _show_df(pro.get_foreign_trade(sym2, "2024-01-01", "2024-12-31"), action)
                    elif action == "prop_trade":
                        _show_df(pro.get_prop_trade(sym2, "2024-01-01", "2024-12-31"), action)
                    elif action == "insider_deal":
                        _show_df(pro.get_insider_deal(sym2), action)
                    elif action == "order_stats":
                        _show_df(pro.get_order_stats(sym2, "2024-01-01", "2024-12-31"), action)

    # ════════════════════════════════════════
    # TAB 3: TA INDICATORS
    # ════════════════════════════════════════
    with tabs[2]:
        st.markdown("#### vnstock_ta - Phân Tích Kỹ Thuật")
        try:
            from src.data.connectors.vnstock_ta_connector import VnstockTAConnector
            ta = VnstockTAConnector()
            if not ta.is_available:
                st.warning("⚠️ vnstock_ta chưa cài. Cài qua vnstock-installer.")
                return
        except Exception as e:
            st.error(str(e)); return

        sym_ta = st.text_input("Mã:", "VCB", key="ta_sym")
        category = st.selectbox("Nhóm:", ["Trend", "Momentum", "Volatility", "Volume", "Composite"], key="ta_cat")

        if st.button("▶️ Tính chỉ báo", key="ta_run"):
            with st.spinner("Đang tải dữ liệu & tính..."):
                from src.data.connectors.vnstock_connector import VnstockFreeConnector
                free = VnstockFreeConnector(); free.connect()
                df = free.get_historical_data(sym_ta, "2024-01-01", str(pd.Timestamp.now().date()))
                if df is None or df.empty:
                    st.error("Không lấy được dữ liệu giá"); return

                st.info(f"📊 Dữ liệu: {len(df)} rows")
                if category == "Trend":
                    for name, fn in [("SMA(20)", lambda: ta.sma(df, 20)), ("EMA(20)", lambda: ta.ema(df, 20)),
                                     ("ADX(14)", lambda: ta.adx(df, 14)), ("SuperTrend", lambda: ta.supertrend(df))]:
                        result = fn()
                        if result is not None:
                            st.success(f"✅ {name}")
                            st.dataframe(result.tail(5) if hasattr(result, 'tail') else result, use_container_width=True)
                elif category == "Momentum":
                    for name, fn in [("RSI(14)", lambda: ta.rsi(df, 14)), ("MACD", lambda: ta.macd(df)),
                                     ("Stochastic", lambda: ta.stoch(df))]:
                        result = fn()
                        if result is not None:
                            st.success(f"✅ {name}")
                            st.dataframe(result.tail(5) if hasattr(result, 'tail') else result, use_container_width=True)
                elif category == "Volatility":
                    for name, fn in [("Bollinger Bands", lambda: ta.bbands(df)), ("ATR(14)", lambda: ta.atr(df, 14)),
                                     ("Keltner Channel", lambda: ta.kc(df))]:
                        result = fn()
                        if result is not None:
                            st.success(f"✅ {name}")
                            st.dataframe(result.tail(5) if hasattr(result, 'tail') else result, use_container_width=True)
                elif category == "Volume":
                    result = ta.obv(df)
                    if result is not None:
                        st.success("✅ OBV"); st.dataframe(result.tail(10), use_container_width=True)
                elif category == "Composite":
                    signals = ta.get_signals(df)
                    st.json(signals)
                    enriched = ta.calculate_all(df)
                    if enriched is not None:
                        st.success(f"✅ calculate_all: {len(enriched.columns)} columns")
                        st.dataframe(enriched.tail(5), use_container_width=True)

    # ════════════════════════════════════════
    # TAB 4: NEWS
    # ════════════════════════════════════════
    with tabs[3]:
        st.markdown("#### vnstock_news - Tin Tức 21 Báo")
        try:
            from src.data.connectors.vnstock_news_connector import VnstockNewsConnector
            news = VnstockNewsConnector()
            if not news.is_available:
                st.warning("⚠️ vnstock_news chưa cài. Cài qua vnstock-installer.")
                return
        except Exception as e:
            st.error(str(e)); return

        st.info(f"📰 Hỗ trợ {len(news.supported_sites)} trang báo: {', '.join(news.supported_sites[:10])}...")
        site = st.selectbox("Trang báo:", news.supported_sites, key="news_site")
        action = st.selectbox("Method:", ["latest_news", "search_news", "stock_news", "trending_keywords", "multi_sites"], key="news_act")

        if action == "search_news":
            keyword = st.text_input("Từ khóa:", "lãi suất", key="news_kw")
        if action == "stock_news":
            stock_sym = st.text_input("Mã CK:", "VCB", key="news_stock_sym")

        if st.button("▶️ Chạy", key="news_run"):
            with st.spinner("Đang crawl..."):
                if action == "latest_news":
                    _show_df(news.get_latest_news(site, 20), f"latest from {site}")
                elif action == "search_news":
                    _show_df(news.search_news(keyword, site, 30), f"search '{keyword}'")
                elif action == "stock_news":
                    _show_df(news.get_stock_news(stock_sym), f"news about {stock_sym}")
                elif action == "trending_keywords":
                    kws = news.get_trending_keywords(site, 30, 15)
                    if kws:
                        st.dataframe(pd.DataFrame(kws, columns=["Keyword", "Count"]), use_container_width=True)
                elif action == "multi_sites":
                    _show_df(news.get_news_from_multiple_sites(limit_per_site=5), "multi-site news")

    # ════════════════════════════════════════
    # TAB 5: CHART
    # ════════════════════════════════════════
    with tabs[4]:
        st.markdown("#### vnstock_chart - Biểu Đồ Chuyên Nghiệp")
        try:
            from src.data.connectors.vnstock_chart_connector import VnstockChartConnector
            chart_conn = VnstockChartConnector()
            if not chart_conn.is_available:
                st.warning("⚠️ vnstock_chart chưa cài. Cài qua vnstock-installer.")
                return
        except Exception as e:
            st.error(str(e)); return

        sym_chart = st.text_input("Mã:", "VCB", key="chart_sym")
        chart_type = st.selectbox("Loại:", ["Candlestick", "Line", "Bar"], key="chart_type")
        if st.button("▶️ Tạo biểu đồ", key="chart_run"):
            with st.spinner("Đang tạo..."):
                from src.data.connectors.vnstock_connector import VnstockFreeConnector
                free = VnstockFreeConnector(); free.connect()
                df = free.get_historical_data(sym_chart, "2024-06-01", str(pd.Timestamp.now().date()))
                if df is None or df.empty:
                    st.error("Không có dữ liệu"); return
                if chart_type == "Candlestick":
                    html = chart_conn.create_candlestick(df, f"Nến {sym_chart}")
                elif chart_type == "Line":
                    html = chart_conn.create_line_chart(df['date'].astype(str).tolist(), df['close'].tolist(), f"Giá {sym_chart}")
                else:
                    html = chart_conn.create_bar_chart(df['date'].astype(str).tolist(), df['volume'].tolist(), f"KLGD {sym_chart}")
                if html:
                    chart_conn.embed_in_streamlit(html, height=500)
                else:
                    st.warning("Không tạo được biểu đồ")

    # ════════════════════════════════════════
    # TAB 6: PIPELINE
    # ════════════════════════════════════════
    with tabs[5]:
        st.markdown("#### vnstock_pipeline - Data Pipeline")
        try:
            from src.data.connectors.vnstock_pipeline_connector import VnstockPipelineConnector
            pipe = VnstockPipelineConnector()
            if not pipe.is_available:
                st.warning("⚠️ vnstock_pipeline chưa cài. Cài qua vnstock-installer.")
                return
        except Exception as e:
            st.error(str(e)); return

        status = pipe.get_pipeline_status()
        st.json(status)
        tickers_input = st.text_input("Tickers (phẩy):", "VCB,ACB,FPT", key="pipe_tickers")
        task = st.selectbox("Task:", ["OHLCV", "Financial", "VN30 Batch"], key="pipe_task")

        if st.button("▶️ Chạy Pipeline", key="pipe_run"):
            tickers = [t.strip() for t in tickers_input.split(",")]
            with st.spinner("Đang xử lý..."):
                if task == "OHLCV":
                    result = pipe.run_ohlcv_task(tickers, "2024-01-01", "2024-12-31")
                elif task == "Financial":
                    result = pipe.run_financial_task(tickers)
                elif task == "VN30 Batch":
                    result = pipe.batch_fetch_vn30("2024-06-01", "2024-12-31")
                st.json(result)
