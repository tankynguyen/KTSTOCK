"""
KTSTOCK - Log Viewer Page
Trang quản lý và theo dõi debug log dành cho Admin.
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from src.app.components.shared import error_handler
from src.utils.debug_logger import get_debug_logger, LogLevel, LogCategory


@error_handler
def render_log_viewer():
    """Render trang quản lý log."""
    if st.session_state.get("user_role") != "admin":
        st.error("⛔ Bạn không có quyền truy cập trang này!")
        return

    dlog = get_debug_logger()

    tab_dashboard, tab_explorer, tab_critical, tab_manage = st.tabs([
        "📊 Tổng quan", "📋 Chi tiết Log", "🔔 Lỗi nghiêm trọng", "⚙️ Quản lý"
    ])

    with tab_dashboard:
        _render_log_dashboard(dlog)

    with tab_explorer:
        _render_log_explorer(dlog)

    with tab_critical:
        _render_critical_errors(dlog)

    with tab_manage:
        _render_log_management(dlog)


def _render_log_dashboard(dlog):
    """Tab tổng quan thống kê."""
    dates = dlog.get_available_dates()
    if not dates:
        st.info("📭 Chưa có dữ liệu log nào.")
        return

    selected_date = st.selectbox("📅 Chọn ngày", dates, key="dash_date")
    summary = dlog.get_summary(selected_date)

    # === Metrics Row ===
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("📝 Tổng log", summary["total"])
    c2.metric("⚠️ Warning", summary["by_level"].get("WARNING", 0))
    c3.metric("❌ Error", summary["by_level"].get("ERROR", 0))
    c4.metric("🔥 Critical", summary["by_level"].get("CRITICAL", 0))
    c5.metric("📁 File size", f"{summary['file_size_kb']:.1f} KB")

    st.divider()

    # === Charts ===
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### 📊 Phân bố theo Level")
        level_data = summary["by_level"]
        if level_data:
            import plotly.express as px
            df_level = pd.DataFrame([
                {"Level": k, "Count": v} for k, v in level_data.items()
            ])
            color_map = {
                "DEBUG": "#888888", "INFO": "#4FC3F7",
                "WARNING": "#FFB74D", "ERROR": "#EF5350", "CRITICAL": "#D32F2F"
            }
            fig = px.pie(df_level, names="Level", values="Count",
                        color="Level", color_discrete_map=color_map,
                        hole=0.4)
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#FAFAFA",
                height=300,
                margin=dict(t=20, b=20, l=20, r=20),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Không có dữ liệu")

    with col_right:
        st.markdown("#### 📂 Phân bố theo Category")
        cat_data = summary["by_category"]
        if cat_data:
            import plotly.express as px
            df_cat = pd.DataFrame([
                {"Category": k, "Count": v} for k, v in
                sorted(cat_data.items(), key=lambda x: x[1], reverse=True)
            ])
            fig = px.bar(df_cat, x="Category", y="Count",
                        color="Count", color_continuous_scale="Oranges")
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#FAFAFA",
                height=300,
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Không có dữ liệu")

    # === Top pages with errors ===
    st.markdown("#### 📄 Top trang có nhiều log nhất")
    page_data = summary["by_page"]
    if page_data:
        df_pages = pd.DataFrame([
            {"Trang": k, "Số lượng": v} for k, v in
            sorted(page_data.items(), key=lambda x: x[1], reverse=True)[:10]
        ])
        st.dataframe(df_pages, width='stretch', hide_index=True)


def _render_log_explorer(dlog):
    """Tab chi tiết log với bộ lọc."""
    st.markdown("#### 🔍 Bộ lọc")

    dates = dlog.get_available_dates()
    if not dates:
        st.info("📭 Chưa có log.")
        return

    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        selected_date = st.selectbox("📅 Ngày", dates, key="exp_date")
    with col2:
        level_filter = st.selectbox("📊 Level", [
            "Tất cả", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
        ], key="exp_level")
    with col3:
        cat_filter = st.selectbox("📂 Category", [
            "Tất cả", "API_CALL", "AI_REQUEST", "DB_QUERY", "AUTH_ACTION",
            "CACHE_OP", "UI_ERROR", "EXPORT", "SYSTEM"
        ], key="exp_cat")
    with col4:
        keyword = st.text_input("🔎 Tìm kiếm", key="exp_keyword", placeholder="VCB, timeout...")

    limit = st.slider("Số bản ghi tối đa", 10, 500, 100, key="exp_limit")

    # Fetch logs
    logs = dlog.get_logs(
        date=selected_date,
        level=level_filter if level_filter != "Tất cả" else None,
        category=cat_filter if cat_filter != "Tất cả" else None,
        keyword=keyword or None,
        limit=limit,
    )

    st.caption(f"📝 Tìm thấy {len(logs)} bản ghi")

    if not logs:
        st.info("📭 Không có log phù hợp với bộ lọc.")
        return

    # Display logs
    for i, log in enumerate(logs):
        level = log.get("level", "INFO")
        level_colors = {
            "DEBUG": "🔵", "INFO": "🟢",
            "WARNING": "🟡", "ERROR": "🔴", "CRITICAL": "💥"
        }
        icon = level_colors.get(level, "⚪")
        ts = log.get("timestamp", "")[:19]
        page = log.get("page", "?")
        component = log.get("component", "?")
        action = log.get("action", "?")
        error_msg = log.get("error_message", "")

        # One-line summary
        summary_parts = [
            f"{icon} **{level}**",
            f"`{ts}`",
            f"📄 {page}",
            f"🔧 {component}",
            f"⚡ {action}",
        ]
        if error_msg:
            summary_parts.append(f"❌ {error_msg[:60]}...")

        header = "  |  ".join(summary_parts)

        with st.expander(header, expanded=False):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"""
                | Trường | Giá trị |
                |---|---|
                | **Page** | {log.get('page_title', '')} (`{page}`) |
                | **Component** | `{component}` |
                | **Action** | `{action}` |
                | **Action Detail** | {log.get('action_detail', 'N/A')} |
                | **Symbol** | {log.get('symbol', 'N/A')} |
                | **Source** | {log.get('source', 'N/A')} |
                | **Method** | `{log.get('method', 'N/A')}` |
                | **Duration** | {log.get('duration_ms', 0):.0f} ms |
                | **Result** | {log.get('result_status', 'N/A')} |
                """)

            with col_b:
                st.markdown(f"""
                | Trường | Giá trị |
                |---|---|
                | **User** | {log.get('user', 'N/A')} |
                | **Role** | {log.get('user_role', 'N/A')} |
                | **Session** | `{log.get('session_id', 'N/A')}` |
                | **Error Type** | `{log.get('error_type', 'N/A')}` |
                | **Error** | {error_msg or 'N/A'} |
                | **Platform** | {log.get('environment', {}).get('platform', 'N/A')} |
                | **Python** | {log.get('environment', {}).get('python_version', 'N/A')} |
                | **Deploy** | {log.get('environment', {}).get('deploy_mode', 'N/A')} |
                """)

            if log.get("params"):
                st.markdown("**📋 Params:**")
                st.json(log["params"])

            if log.get("traceback"):
                st.markdown("**🔍 Traceback:**")
                st.code(log["traceback"], language="python")

    # Export
    st.divider()
    if st.button("📥 Export CSV", key="export_logs"):
        df_export = pd.DataFrame(logs)
        csv = df_export.to_csv(index=False)
        st.download_button(
            "⬇️ Tải xuống CSV",
            csv, f"ktstock_logs_{selected_date}.csv",
            mime="text/csv", key="download_csv"
        )


def _render_critical_errors(dlog):
    """Tab lỗi nghiêm trọng."""
    dates = dlog.get_available_dates()
    if not dates:
        st.info("📭 Chưa có log.")
        return

    selected_date = st.selectbox("📅 Ngày", dates, key="crit_date")

    errors = dlog.get_logs(date=selected_date, level="ERROR", limit=500)

    if not errors:
        st.success("✅ Không có lỗi nghiêm trọng nào trong ngày này!")
        return

    st.error(f"🔔 Tìm thấy **{len(errors)}** lỗi trong ngày {selected_date}")

    # Group by error_type
    error_groups = {}
    for log in errors:
        etype = log.get("error_type", "Unknown")
        if etype not in error_groups:
            error_groups[etype] = []
        error_groups[etype].append(log)

    # Display grouped
    for etype, group in sorted(error_groups.items(), key=lambda x: len(x[1]), reverse=True):
        with st.expander(f"🔴 {etype} — {len(group)} lần", expanded=len(group) >= 3):
            st.markdown(f"**Số lần xuất hiện:** {len(group)}")

            # Show first occurrence details
            first = group[0]
            st.markdown(f"""
            - **Trang:** {first.get('page_title', '')} (`{first.get('page', '')}`)
            - **Component:** `{first.get('component', '')}`
            - **Action:** `{first.get('action', '')}`
            - **Error:** {first.get('error_message', '')}
            - **Lần đầu:** {first.get('timestamp', '')[:19]}
            - **Lần cuối:** {group[-1].get('timestamp', '')[:19]}
            """)

            if first.get("traceback"):
                st.code(first["traceback"][:500], language="python")

            # Show all occurrences in table
            if len(group) > 1:
                df_g = pd.DataFrame([
                    {
                        "Thời gian": g.get("timestamp", "")[:19],
                        "Page": g.get("page", ""),
                        "Symbol": g.get("symbol", ""),
                        "Duration(ms)": g.get("duration_ms", 0),
                    }
                    for g in group
                ])
                st.dataframe(df_g, width='stretch', hide_index=True)


def _render_log_management(dlog):
    """Tab quản lý file log."""
    st.markdown("#### 📁 File log theo ngày")

    dates = dlog.get_available_dates()
    if not dates:
        st.info("📭 Chưa có file log nào.")
        return

    # File list
    rows = []
    for date in dates:
        summary = dlog.get_summary(date)
        rows.append({
            "Ngày": date,
            "Tổng log": summary["total"],
            "Errors": summary["error_count"],
            "Size (KB)": summary["file_size_kb"],
        })

    df_files = pd.DataFrame(rows)
    st.dataframe(df_files, width='stretch', hide_index=True)

    st.divider()

    # Actions
    col1, col2, col3 = st.columns(3)

    with col1:
        delete_date = st.selectbox("Chọn ngày để xóa", dates, key="del_date")
        if st.button("🗑️ Xóa log ngày này", type="primary", key="del_single"):
            if dlog.clear_logs(delete_date):
                st.success(f"✅ Đã xóa log ngày {delete_date}")
                st.rerun()
            else:
                st.warning("⚠️ File không tồn tại")

    with col2:
        keep_days = st.number_input("Giữ log bao nhiêu ngày?", min_value=1, max_value=365, value=30, key="keep_days")
        if st.button("🧹 Xóa log cũ", key="del_old"):
            count = dlog.clear_old_logs(keep_days)
            st.success(f"✅ Đã xóa {count} file log cũ (>{keep_days} ngày)")
            if count > 0:
                st.rerun()

    with col3:
        st.markdown("#### 📊 Tổng quan")
        total_files = len(dates)
        total_size = sum(r["Size (KB)"] for r in rows)
        total_errors = sum(r["Errors"] for r in rows)
        st.metric("📁 Tổng file", total_files)
        st.metric("💾 Tổng dung lượng", f"{total_size:.1f} KB")
        st.metric("❌ Tổng lỗi", total_errors)
