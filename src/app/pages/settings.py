"""
KTSTOCK - Settings & Admin Pages
Trang cài đặt và quản trị hệ thống.
"""
import streamlit as st
from src.app.i18n import t
from src.app.components.shared import error_handler


@error_handler
def render_settings():
    """Render trang cài đặt."""
    lang = st.session_state.get("language", "vi")
    user = st.session_state.get("user", {})

    tab_ui, tab_ai, tab_data, tab_account = st.tabs([
        "🎨 Giao diện", "🤖 AI", "📊 Dữ liệu", "👤 Tài khoản"
    ])

    with tab_ui:
        st.subheader("🎨 " + t("settings.theme", lang))
        new_lang = st.selectbox(
            t("settings.language", lang),
            ["vi", "en"],
            format_func=lambda x: "🇻🇳 Tiếng Việt" if x == "vi" else "🇺🇸 English",
            index=0 if lang == "vi" else 1,
            key="settings_lang",
        )
        if new_lang != lang:
            st.session_state.language = new_lang
            st.rerun()

    with tab_ai:
        st.subheader("🤖 AI Configuration")
        from src.utils.config import get_settings
        settings = get_settings()

        st.text_input("Gemini API Key",
                      value=settings.ai.gemini_api_key[:10] + "..." if settings.ai.gemini_api_key else "",
                      disabled=True)
        st.caption("✅ Gemini configured" if settings.ai.gemini_api_key else "❌ Not configured")
        st.text_input("Grok API Key", value="Chưa cấu hình", disabled=True)
        st.text_input("DeepSeek API Key", value="Chưa cấu hình", disabled=True)

    with tab_data:
        st.subheader("📊 " + t("settings.data_source", lang))
        from src.services.cache_service import get_cache
        cache = get_cache()
        stats = cache.get_stats()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Cache Files", stats["file_entries"])
            st.metric("Cache Size", f"{stats['total_size_mb']:.2f} MB")
        with col2:
            st.metric("Memory Cache", stats["memory_entries"])

        if st.button("🗑️ " + t("settings.clear_cache", lang), type="primary"):
            count = cache.clear_all()
            st.success(f"✅ Đã xóa {count} cache files")

        if st.button("🧹 Xóa cache hết hạn"):
            count = cache.clear_expired()
            st.success(f"✅ Đã xóa {count} expired entries")

    with tab_account:
        st.subheader("👤 Tài khoản")
        if user:
            st.text_input("Username", value=user.get("username", ""), disabled=True)
            st.text_input("Email", value=user.get("email", ""), disabled=True)
            st.text_input("Role", value=user.get("role", ""), disabled=True)

            with st.expander("🔑 " + t("auth.change_password", lang)):
                old_pw = st.text_input(t("auth.old_password", lang), type="password", key="old_pw")
                new_pw = st.text_input(t("auth.new_password", lang), type="password", key="new_pw")
                confirm_pw = st.text_input(t("auth.confirm_password", lang), type="password", key="confirm_pw")

                if st.button(t("auth.change_password", lang)):
                    if new_pw != confirm_pw:
                        st.error("❌ Mật khẩu xác nhận không khớp")
                    elif len(new_pw) < 8:
                        st.error("❌ Mật khẩu phải ≥ 8 ký tự")
                    else:
                        from src.auth.auth_manager import AuthManager
                        auth = AuthManager()
                        result = auth.change_password(user["id"], old_pw, new_pw)
                        if result["success"]:
                            st.success(result["message"])
                        else:
                            st.error(result["message"])


@error_handler
def render_admin():
    """Render trang quản trị."""
    if st.session_state.get("user_role") != "admin":
        st.error("⛔ Bạn không có quyền truy cập!")
        return

    tab_users, tab_system, tab_db = st.tabs(["👥 Users", "⚙️ Hệ thống", "🗄️ Database"])

    with tab_users:
        _render_user_management()
    with tab_system:
        _render_system_status()
    with tab_db:
        _render_db_management()


def _render_user_management():
    """Quản lý users."""
    from src.auth.auth_manager import AuthManager
    import pandas as pd

    auth = AuthManager()
    users = auth.get_all_users()

    if users:
        df = pd.DataFrame(users)
        cols = [c for c in ["id", "username", "email", "role", "is_active", "last_login"] if c in df.columns]
        st.dataframe(df[cols], width='stretch')
    else:
        st.info("Chưa có user")


def _render_system_status():
    """Trạng thái hệ thống."""
    from src.data.database.connection import get_db
    from src.services.cache_service import get_cache

    db = get_db()
    cache = get_cache()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📁 DB Size", f"{db.get_db_size_mb():.2f} MB")
    col2.metric("📊 Users", db.get_table_count("users"))
    col3.metric("📈 Price Records", db.get_table_count("price_history"))
    col4.metric("🤖 AI Analyses", db.get_table_count("ai_analysis"))


def _render_db_management():
    """Quản lý database."""
    from src.data.database.connection import get_db
    db = get_db()

    tables = db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    if tables:
        for t_info in tables:
            name = t_info["name"]
            count = db.get_table_count(name)
            st.text(f"📋 {name}: {count} rows")
