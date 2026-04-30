"""
KTSTOCK - Helper Functions
Các hàm tiện ích dùng chung trong toàn bộ hệ thống.
"""
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Optional

import pandas as pd


def format_number(value: float, decimals: int = 2, suffix: str = "") -> str:
    """
    Format số theo chuẩn Việt Nam (dùng dấu chấm phân cách hàng nghìn).

    Args:
        value: Giá trị số
        decimals: Số chữ số thập phân
        suffix: Hậu tố (VD: "₫", "%")

    Returns:
        Chuỗi đã format. VD: "1.234.567,89₫"
    """
    if pd.isna(value):
        return "N/A"
    formatted = f"{value:,.{decimals}f}"
    return f"{formatted}{suffix}"


def format_currency_vnd(value: float) -> str:
    """Format tiền VNĐ. VD: 25,500 → '25,500 ₫'"""
    if pd.isna(value):
        return "N/A"
    return f"{value:,.0f} ₫"


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format phần trăm. VD: 0.0523 → '+5.23%'"""
    if pd.isna(value):
        return "N/A"
    sign = "+" if value > 0 else ""
    return f"{sign}{value * 100:.{decimals}f}%"


def format_volume(value: float) -> str:
    """Format khối lượng giao dịch. VD: 1500000 → '1.5M'"""
    if pd.isna(value):
        return "N/A"
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    elif abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    elif abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(int(value))


def format_market_cap(value: float) -> str:
    """Format vốn hóa thị trường (tỷ VNĐ)."""
    if pd.isna(value):
        return "N/A"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f} nghìn tỷ"
    return f"{value:.0f} tỷ"


def get_color_for_change(change: float) -> str:
    """Lấy màu CSS tương ứng với mức thay đổi giá."""
    if change > 0.065:
        return "#FF00FF"  # Tím - trần
    elif change > 0:
        return "#00C853"  # Xanh lá - tăng
    elif change < -0.065:
        return "#00BFFF"  # Xanh dương - sàn
    elif change < 0:
        return "#FF1744"  # Đỏ - giảm
    return "#FFD600"      # Vàng - tham chiếu


def generate_cache_key(*args: Any) -> str:
    """Tạo cache key duy nhất từ các tham số."""
    key_str = json.dumps(args, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def is_trading_hours() -> bool:
    """Kiểm tra có đang trong giờ giao dịch không (9h-15h, thứ 2-6)."""
    now = datetime.now()
    if now.weekday() >= 5:  # Thứ 7, CN
        return False
    return 9 <= now.hour < 15


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """Chia an toàn, trả về default nếu chia cho 0."""
    if b == 0 or pd.isna(b):
        return default
    return a / b


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Cắt ngắn text nếu quá dài."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def parse_date(date_str: str, fmt: str = "%Y-%m-%d") -> Optional[datetime]:
    """Parse chuỗi ngày tháng an toàn."""
    try:
        return datetime.strptime(date_str, fmt)
    except (ValueError, TypeError):
        return None


def get_date_range(days: int = 365) -> tuple[str, str]:
    """Lấy khoảng thời gian từ hôm nay trở về trước."""
    end = datetime.now()
    start = end - timedelta(days=days)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
