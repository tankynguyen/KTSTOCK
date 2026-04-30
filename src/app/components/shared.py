"""
KTSTOCK - Shared UI Components
Components dùng chung cho các trang Streamlit.
"""
import streamlit as st
import pandas as pd
from typing import Optional
from src.app.i18n import t


def metric_card(label: str, value: str, delta: str = "", delta_color: str = "normal"):
    """Metric card đẹp."""
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color)


def signal_badge(signal: str, lang: str = "vi") -> str:
    """Trả về HTML badge cho tín hiệu giao dịch."""
    badge_map = {
        "strong_buy": ("🟢 MUA MẠNH" if lang == "vi" else "🟢 STRONG BUY", "#00C853"),
        "buy": ("🟢 MUA" if lang == "vi" else "🟢 BUY", "#00C853"),
        "hold": ("🟡 GIỮ" if lang == "vi" else "🟡 HOLD", "#FFC107"),
        "sell": ("🔴 BÁN" if lang == "vi" else "🔴 SELL", "#FF1744"),
        "strong_sell": ("🔴 BÁN MẠNH" if lang == "vi" else "🔴 STRONG SELL", "#FF1744"),
    }
    text, color = badge_map.get(signal, ("⚪ N/A", "#888"))
    return f'<span style="background:{color}20;color:{color};padding:4px 12px;border-radius:8px;font-weight:600;font-size:0.9rem;">{text}</span>'


def trend_badge(trend: str, lang: str = "vi") -> str:
    """Trả về HTML badge cho xu hướng."""
    trend_map = {
        "strong_bullish": ("📈 Tăng mạnh" if lang == "vi" else "📈 Strong Bullish", "#00C853"),
        "bullish": ("📈 Tăng" if lang == "vi" else "📈 Bullish", "#4CAF50"),
        "neutral": ("➡️ Trung tính" if lang == "vi" else "➡️ Neutral", "#FFC107"),
        "bearish": ("📉 Giảm" if lang == "vi" else "📉 Bearish", "#FF5722"),
        "strong_bearish": ("📉 Giảm mạnh" if lang == "vi" else "📉 Strong Bearish", "#FF1744"),
    }
    text, color = trend_map.get(trend, ("⚪ N/A", "#888"))
    return f'<span style="color:{color};font-weight:600;">{text}</span>'


def symbol_selector(
    key: str = "symbol",
    label: str = "Mã cổ phiếu",
    default: str = "VCB",
    exchange: str = "stock",
) -> str:
    """Widget chọn mã cổ phiếu/crypto."""
    if exchange == "crypto":
        popular = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
                    "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT"]
        default = "BTCUSDT"
        label = "Cặp crypto"
    else:
        popular = ["VCB", "FPT", "VNM", "HPG", "MBB", "TCB", "VHM", "VIC",
                    "MSN", "VRE", "SSI", "HDB", "TPB", "ACB", "STB"]

    col1, col2 = st.columns([3, 1])
    with col1:
        symbol = st.text_input(label, value=default, key=key).upper().strip()
    with col2:
        st.caption("Phổ biến:")
        quick = st.selectbox("Quick", popular, label_visibility="collapsed", key=f"{key}_quick")
        if quick and quick != symbol:
            symbol = quick

    return symbol


def date_range_selector(key: str = "daterange") -> tuple[str, str]:
    """Widget chọn khoảng thời gian."""
    from datetime import datetime, timedelta

    presets = {
        "1 tháng": 30, "3 tháng": 90, "6 tháng": 180,
        "1 năm": 365, "2 năm": 730, "5 năm": 1825,
    }

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        preset = st.selectbox("Khoảng thời gian", list(presets.keys()),
                              index=3, key=f"{key}_preset")
    days = presets[preset]
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    with col2:
        start = st.date_input("Từ", value=start_date, key=f"{key}_start")
    with col3:
        end = st.date_input("Đến", value=end_date, key=f"{key}_end")

    return str(start), str(end)


def render_dataframe(df: pd.DataFrame, title: str = "", height: int = 400):
    """Hiển thị DataFrame đẹp."""
    if title:
        st.subheader(title)
    if df is not None and not df.empty:
        st.dataframe(df, width='stretch', height=height)
    else:
        st.info("📭 Không có dữ liệu")


def error_handler(func):
    """Decorator bắt lỗi cho page rendering."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.error(f"❌ Lỗi: {e}")
            st.caption("Vui lòng thử lại hoặc kiểm tra kết nối.")
    return wrapper
