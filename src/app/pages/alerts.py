"""
KTSTOCK - Alerts Page
Trang quản lý cảnh báo giá.
"""
import streamlit as st
from src.app.components.shared import error_handler


@error_handler
def render_alerts():
    """Render trang cảnh báo."""
    user = st.session_state.get("user", {})
    user_id = user.get("id", 0)
    if not user_id:
        st.warning("⚠️ Vui lòng đăng nhập")
        return

    from src.core.alerts.engine import AlertEngine
    engine = AlertEngine()

    tab_active, tab_create, tab_history = st.tabs(["🔔 Đang hoạt động", "➕ Tạo mới", "📋 Lịch sử"])

    with tab_active:
        alerts = engine.get_alerts(user_id, active_only=True)
        unread = engine.get_unread_count(user_id)
        if unread > 0:
            st.warning(f"🔔 Bạn có **{unread}** cảnh báo chưa đọc!")
        if not alerts:
            st.info("📭 Chưa có cảnh báo. Tạo mới ở tab '➕ Tạo mới'")
        else:
            for a in alerts:
                c1, c2, c3 = st.columns([2, 4, 1])
                c1.markdown(f"**{a['symbol']}**")
                c2.caption(f"{a['condition']}: {a['threshold']:,.1f}")
                if c3.button("🗑️", key=f"del_{a['id']}"):
                    engine.delete_alert(a["id"])
                    st.rerun()

    with tab_create:
        with st.form("create_alert"):
            c1, c2 = st.columns(2)
            with c1:
                symbol = st.text_input("Mã CK", value="VCB").upper().strip()
                condition = st.selectbox("Điều kiện", [
                    "price_above", "price_below", "rsi_overbought",
                    "rsi_oversold", "volume_spike", "macd_cross_up", "macd_cross_down",
                ])
            with c2:
                threshold = st.number_input("Ngưỡng", value=100.0, step=0.5)
                notif = st.selectbox("Thông báo", ["in_app", "telegram", "email"])
            if st.form_submit_button("✅ Tạo cảnh báo", type="primary"):
                if symbol:
                    engine.create_alert(user_id, symbol, condition, threshold, notif)
                    st.success(f"✅ Đã tạo cảnh báo cho {symbol}")
                    st.rerun()

    with tab_history:
        history = engine.get_alert_history(user_id, limit=50)
        if not history:
            st.info("📭 Chưa có lịch sử")
        else:
            for item in history:
                st.caption(f"{'🟢' if not item.get('is_read') else '⚪'} {item.get('message', '')}")
