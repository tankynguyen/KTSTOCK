"""
KTSTOCK - Role-Based Access Control (RBAC)
Phân quyền truy cập theo vai trò người dùng.
"""
from typing import Optional
from src.utils.constants import UserRole


# ============================================================
# Định nghĩa quyền cho từng tính năng
# ============================================================
PERMISSIONS = {
    # Tính năng: [các role được phép]
    "view_dashboard":        [UserRole.GUEST, UserRole.USER, UserRole.ANALYST, UserRole.ADMIN],
    "view_stock_analysis":   [UserRole.USER, UserRole.ANALYST, UserRole.ADMIN],
    "view_crypto_analysis":  [UserRole.USER, UserRole.ANALYST, UserRole.ADMIN],
    "view_technical":        [UserRole.USER, UserRole.ANALYST, UserRole.ADMIN],
    "view_fundamental":      [UserRole.USER, UserRole.ANALYST, UserRole.ADMIN],
    "view_ai_insights":      [UserRole.ANALYST, UserRole.ADMIN],
    "view_screener":         [UserRole.USER, UserRole.ANALYST, UserRole.ADMIN],
    "view_portfolio":        [UserRole.USER, UserRole.ANALYST, UserRole.ADMIN],
    "view_alerts":           [UserRole.USER, UserRole.ANALYST, UserRole.ADMIN],
    "view_macro":            [UserRole.USER, UserRole.ANALYST, UserRole.ADMIN],
    "view_news":             [UserRole.USER, UserRole.ANALYST, UserRole.ADMIN],
    "view_reports":          [UserRole.ANALYST, UserRole.ADMIN],
    "manage_settings":       [UserRole.USER, UserRole.ANALYST, UserRole.ADMIN],
    "manage_users":          [UserRole.ADMIN],
    "manage_system":         [UserRole.ADMIN],
    "export_data":           [UserRole.ANALYST, UserRole.ADMIN],
    "create_alert":          [UserRole.USER, UserRole.ANALYST, UserRole.ADMIN],
    "manage_portfolio":      [UserRole.USER, UserRole.ANALYST, UserRole.ADMIN],
    "use_ai_analysis":       [UserRole.ANALYST, UserRole.ADMIN],
    "view_admin_panel":      [UserRole.ADMIN],
    "view_log_viewer":       [UserRole.ADMIN],
}


def has_permission(user_role: str, permission: str) -> bool:
    """
    Kiểm tra user có quyền thực hiện hành động không.

    Args:
        user_role: Role hiện tại của user (string)
        permission: Tên quyền cần kiểm tra

    Returns:
        True nếu có quyền
    """
    if permission not in PERMISSIONS:
        return False

    try:
        role = UserRole(user_role)
    except ValueError:
        return False

    return role in PERMISSIONS[permission]


def get_user_permissions(user_role: str) -> list[str]:
    """Lấy danh sách tất cả quyền của user."""
    try:
        role = UserRole(user_role)
    except ValueError:
        return []

    return [perm for perm, allowed_roles in PERMISSIONS.items() if role in allowed_roles]


def get_accessible_pages(user_role: str) -> list[dict]:
    """
    Lấy danh sách pages mà user có quyền truy cập.

    Returns:
        List of {"key": str, "label": str, "icon": str}
    """
    ALL_PAGES = [
        {"key": "dashboard",       "label": "Tổng quan",           "icon": "📊", "permission": "view_dashboard"},
        {"key": "stock_analysis",  "label": "Phân tích cổ phiếu",  "icon": "📈", "permission": "view_stock_analysis"},
        {"key": "crypto_analysis", "label": "Phân tích Crypto",     "icon": "₿",  "permission": "view_crypto_analysis"},
        {"key": "technical",       "label": "Phân tích kỹ thuật",  "icon": "📐", "permission": "view_technical"},
        {"key": "fundamental",     "label": "Phân tích cơ bản",    "icon": "📋", "permission": "view_fundamental"},
        {"key": "ai_insights",     "label": "AI Insights",          "icon": "🤖", "permission": "view_ai_insights"},
        {"key": "screener",        "label": "Bộ lọc cổ phiếu",    "icon": "🔍", "permission": "view_screener"},
        {"key": "portfolio",       "label": "Danh mục đầu tư",    "icon": "💼", "permission": "view_portfolio"},
        {"key": "alerts",          "label": "Cảnh báo",            "icon": "🔔", "permission": "view_alerts"},
        {"key": "macro",           "label": "Kinh tế vĩ mô",      "icon": "🌍", "permission": "view_macro"},
        {"key": "news",            "label": "Tin tức & Sentiment",  "icon": "📰", "permission": "view_news"},
        {"key": "reports",         "label": "Báo cáo",             "icon": "📑", "permission": "view_reports"},
        {"key": "settings",        "label": "Cài đặt",            "icon": "⚙️", "permission": "manage_settings"},
        {"key": "admin",           "label": "Quản trị",           "icon": "🛡️", "permission": "view_admin_panel"},
        {"key": "log_viewer",      "label": "Quản lý Log",        "icon": "📋", "permission": "view_log_viewer"},
        {"key": "connector_test",  "label": "Test Connectors",    "icon": "🧪", "permission": "view_admin_panel"},
    ]

    return [page for page in ALL_PAGES if has_permission(user_role, page["permission"])]


def get_role_display_name(role: str, language: str = "vi") -> str:
    """Lấy tên hiển thị của role."""
    names = {
        "vi": {
            "admin": "Quản trị viên",
            "analyst": "Nhà phân tích",
            "user": "Người dùng",
            "guest": "Khách",
        },
        "en": {
            "admin": "Administrator",
            "analyst": "Analyst",
            "user": "User",
            "guest": "Guest",
        }
    }
    return names.get(language, names["vi"]).get(role, role)
