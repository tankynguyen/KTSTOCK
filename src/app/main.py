"""
📊 KTSTOCK - Main Application Entry Point
Nền tảng phân tích chứng khoán & crypto thông minh.

Chạy ứng dụng:
    streamlit run src/app/main.py
"""
import sys
from pathlib import Path

# Thêm project root vào Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from src.utils.config import get_settings
from src.utils.logger import setup_logger, get_logger
from src.utils.constants import APP_TITLE, APP_ICON
from src.auth.auth_manager import AuthManager
from src.auth.rbac import get_accessible_pages, get_role_display_name, has_permission
from src.app.i18n import tt, t


# === Khởi tạo Logger ===
setup_logger(level="INFO")
log = get_logger("main")


# === Page Config ===
st.set_page_config(
    page_title="KT Stock Analyzer",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================
def inject_custom_css():
    """Inject CSS chuyên nghiệp cho toàn bộ ứng dụng."""
    st.markdown("""
    <style>
        /* === Import Google Font === */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* === Global === */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* === Sidebar === */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0E1117 0%, #1A1D23 100%);
            border-right: 1px solid rgba(255, 107, 53, 0.2);
        }

        [data-testid="stSidebar"] .stRadio > label {
            font-size: 0.9rem;
        }

        /* === Main Header Gradient === */
        .main-header {
            background: linear-gradient(135deg, #FF6B35 0%, #F7C948 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        /* === Metric Cards === */
        [data-testid="stMetric"] {
            background: linear-gradient(135deg, #1A1D23 0%, #252830 100%);
            border: 1px solid rgba(255, 107, 53, 0.15);
            border-radius: 12px;
            padding: 1rem;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        [data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(255, 107, 53, 0.15);
        }

        /* === Buttons === */
        .stButton > button {
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(255, 107, 53, 0.3);
        }

        /* === Data Tables === */
        [data-testid="stDataFrame"] {
            border-radius: 8px;
            overflow: hidden;
        }

        /* === Tabs === */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0;
        }

        /* === Expander === */
        .streamlit-expanderHeader {
            font-weight: 600;
        }

        /* === Status Badge === */
        .status-badge {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .status-online { background: rgba(0, 200, 83, 0.2); color: #00C853; }
        .status-offline { background: rgba(255, 23, 68, 0.2); color: #FF1744; }

        /* === Scrollbar === */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #0E1117; }
        ::-webkit-scrollbar-thumb { background: #FF6B35; border-radius: 3px; }

        /* === Hide Streamlit defaults === */
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        header { visibility: hidden; }
        [data-testid="stSidebarNav"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)


# ============================================================
# SESSION STATE INIT
# ============================================================
def init_session_state():
    """Khởi tạo session state mặc định."""
    defaults = {
        "authenticated": False,
        "user": None,
        "user_role": "guest",
        "session_token": None,
        "language": "vi",
        "current_page": "dashboard",
        "theme": "dark",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ============================================================
# LOGIN PAGE
# ============================================================
def render_login_page():
    """Hiển thị trang đăng nhập / đăng ký."""
    lang = st.session_state.get("language", "vi")

    # Center layout
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown('<h1 class="main-header">📊 KT Stock Analyzer</h1>', unsafe_allow_html=True)
        st.caption(t("app.description", lang))

        # Language selector
        lang_col1, lang_col2 = st.columns([3, 1])
        with lang_col2:
            new_lang = st.selectbox(
                "🌐",
                ["vi", "en"],
                format_func=lambda x: "🇻🇳 Tiếng Việt" if x == "vi" else "🇺🇸 English",
                index=0 if lang == "vi" else 1,
                key="login_lang",
                label_visibility="collapsed",
            )
            if new_lang != lang:
                st.session_state.language = new_lang
                st.rerun()

        st.divider()

        tab_login, tab_register = st.tabs([
            f"🔐 {t('auth.login', lang)}",
            f"📝 {t('auth.register', lang)}"
        ])

        auth = AuthManager()

        with tab_login:
            with st.form("login_form"):
                username = st.text_input(t("auth.username", lang), placeholder="admin")
                password = st.text_input(t("auth.password", lang), type="password", placeholder="Admin@123")
                submitted = st.form_submit_button(
                    t("auth.login", lang),
                    width='stretch',
                    type="primary"
                )

                if submitted:
                    if not username or not password:
                        st.error("⚠️ Vui lòng nhập đầy đủ thông tin!" if lang == "vi" else "⚠️ Please fill in all fields!")
                    else:
                        result = auth.login(username, password)
                        if result["success"]:
                            st.session_state.authenticated = True
                            st.session_state.user = result["user"]
                            st.session_state.user_role = result["user"]["role"]
                            st.session_state.session_token = result["token"]
                            st.session_state.language = result["user"].get("language", "vi")
                            st.success(t("auth.login_success", lang))
                            st.rerun()
                        else:
                            st.error(result["message"])

            st.caption("🔑 Tài khoản mặc định: **admin** / **Admin@123**" if lang == "vi"
                      else "🔑 Default account: **admin** / **Admin@123**")

        with tab_register:
            with st.form("register_form"):
                reg_fullname = st.text_input(t("auth.full_name", lang))
                reg_username = st.text_input(t("auth.username", lang), key="reg_user")
                reg_email = st.text_input(t("auth.email", lang))
                reg_password = st.text_input(t("auth.password", lang), type="password", key="reg_pass")
                reg_confirm = st.text_input(t("auth.confirm_password", lang), type="password")
                submitted = st.form_submit_button(
                    t("auth.register", lang),
                    width='stretch',
                    type="primary"
                )

                if submitted:
                    if not all([reg_username, reg_email, reg_password, reg_confirm]):
                        st.error("⚠️ Vui lòng nhập đầy đủ thông tin!")
                    elif reg_password != reg_confirm:
                        st.error("❌ Mật khẩu xác nhận không khớp!")
                    elif len(reg_password) < 8:
                        st.error("❌ Mật khẩu phải có ít nhất 8 ký tự!")
                    else:
                        result = auth.register(reg_username, reg_email, reg_password, reg_fullname)
                        if result["success"]:
                            st.success(t("auth.register_success", lang))
                            st.info("✅ Hãy đăng nhập với tài khoản vừa tạo!")
                        else:
                            st.error(result["message"])


# ============================================================
# MAIN DASHBOARD
# ============================================================
def render_sidebar():
    """Render sidebar với navigation và user info."""
    lang = st.session_state.language
    user = st.session_state.user

    with st.sidebar:
        # === Logo & Title ===
        st.markdown('<h2 class="main-header">📊 KTSTOCK</h2>', unsafe_allow_html=True)

        # === User Info ===
        if user:
            role_name = get_role_display_name(user["role"], lang)
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1E2028 0%, #2A2D35 100%);
                        border-radius: 10px; padding: 12px; margin-bottom: 1rem;
                        border: 1px solid rgba(255,107,53,0.2);">
                <div style="font-weight: 600; font-size: 0.95rem;">
                    👤 {user['full_name'] or user['username']}
                </div>
                <div style="font-size: 0.75rem; color: #888; margin-top: 2px;">
                    🏷️ {role_name} | 🌐 {'🇻🇳' if lang == 'vi' else '🇺🇸'}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # === Navigation ===
        pages = get_accessible_pages(st.session_state.user_role)
        page_labels = [f"{p['icon']} {t('nav.' + p['key'], lang)}" for p in pages]

        current_idx = 0
        for i, p in enumerate(pages):
            if p["key"] == st.session_state.current_page:
                current_idx = i
                break

        selected = st.radio(
            t("nav.dashboard", lang),
            page_labels,
            index=current_idx,
            label_visibility="collapsed",
        )

        # Map selection back to page key
        if selected:
            selected_idx = page_labels.index(selected)
            st.session_state.current_page = pages[selected_idx]["key"]

        st.divider()

        # === Quick Actions ===
        col1, col2 = st.columns(2)
        with col1:
            new_lang = st.selectbox(
                "🌐", ["vi", "en"],
                format_func=lambda x: "🇻🇳 VI" if x == "vi" else "🇺🇸 EN",
                index=0 if lang == "vi" else 1,
                label_visibility="collapsed",
                key="sidebar_lang",
            )
            if new_lang != lang:
                st.session_state.language = new_lang
                st.rerun()

        with col2:
            if st.button(f"🚪 {t('auth.logout', lang)}", width='stretch'):
                auth = AuthManager()
                auth.logout(st.session_state.session_token)
                for key in ["authenticated", "user", "user_role", "session_token"]:
                    st.session_state[key] = None
                st.session_state.authenticated = False
                st.rerun()

        # === System Status ===
        st.divider()
        st.session_state["debug_mode"] = st.checkbox("🛠️ Chế độ Debug (Lỗi API)", value=st.session_state.get("debug_mode", False))
        
        st.caption("📡 System Status")
        st.markdown("""
        <div style="font-size: 0.75rem; line-height: 1.8;">
            <span class="status-badge status-online">● Online</span> Database<br>
            <span class="status-badge status-online">● Online</span> Cache<br>
            <span class="status-badge status-online">● Ready</span> AI Engine
        </div>
        """, unsafe_allow_html=True)


def render_main_content():
    """Render nội dung chính theo page đã chọn."""
    page = st.session_state.current_page
    lang = st.session_state.language

    # Header
    page_titles = {
        "dashboard": ("📊", t("nav.dashboard", lang)),
        "stock_analysis": ("📈", t("nav.stock_analysis", lang)),
        "crypto_analysis": ("₿", t("nav.crypto_analysis", lang)),
        "technical": ("📐", t("nav.technical", lang)),
        "fundamental": ("📋", t("nav.fundamental", lang)),
        "ai_insights": ("🤖", t("nav.ai_insights", lang)),
        "screener": ("🔍", t("nav.screener", lang)),
        "portfolio": ("💼", t("nav.portfolio", lang)),
        "alerts": ("🔔", t("nav.alerts", lang)),
        "macro": ("🌍", t("nav.macro", lang)),
        "news": ("📰", t("nav.news", lang)),
        "reports": ("📑", t("nav.reports", lang)),
        "settings": ("⚙️", t("nav.settings", lang)),
        "admin": ("🛡️", t("nav.admin", lang)),
    }

    icon, title = page_titles.get(page, ("📊", "Dashboard"))
    st.markdown(f'<h1 class="main-header">{icon} {title}</h1>', unsafe_allow_html=True)

    # === Page Routing ===
    if page == "dashboard":
        from src.app.pages.dashboard import render_dashboard
        render_dashboard()
    elif page == "stock_analysis":
        from src.app.pages.stock_analysis import render_stock_analysis
        render_stock_analysis()
    elif page == "crypto_analysis":
        from src.app.pages.crypto_analysis import render_crypto_analysis
        render_crypto_analysis()
    elif page == "technical":
        from src.app.pages.stock_analysis import render_stock_analysis
        render_stock_analysis()
    elif page == "fundamental":
        from src.app.pages.extras import render_fundamental_page
        render_fundamental_page()
    elif page == "ai_insights":
        from src.app.pages.extras import render_ai_insights
        render_ai_insights()
    elif page == "screener":
        from src.app.pages.screener import render_screener
        render_screener()
    elif page == "portfolio":
        from src.app.pages.portfolio import render_portfolio
        render_portfolio()
    elif page == "alerts":
        from src.app.pages.alerts import render_alerts
        render_alerts()
    elif page == "macro":
        from src.app.pages.extras import render_macro
        render_macro()
    elif page == "news":
        from src.app.pages.extras import render_news
        render_news()
    elif page == "reports":
        from src.app.pages.extras import render_reports
        render_reports()
    elif page == "settings":
        from src.app.pages.settings import render_settings
        render_settings()
    elif page == "admin":
        from src.app.pages.settings import render_admin
        render_admin()


# ============================================================
# MAIN
# ============================================================
def main():
    """Main entry point."""
    inject_custom_css()
    init_session_state()

    if not st.session_state.authenticated:
        render_login_page()
    else:
        render_sidebar()
        render_main_content()


if __name__ == "__main__":
    main()
