"""
KTSTOCK - Internationalization (i18n)
Hỗ trợ đa ngôn ngữ Tiếng Việt và English.
"""
import json
from pathlib import Path
from typing import Any, Optional
from functools import lru_cache

from src.utils.constants import Language


LOCALES_DIR = Path(__file__).parent / "locales"


@lru_cache(maxsize=4)
def _load_locale(language: str) -> dict:
    """Load file ngôn ngữ từ JSON."""
    locale_file = LOCALES_DIR / f"{language}.json"
    if not locale_file.exists():
        locale_file = LOCALES_DIR / "vi.json"  # Fallback to Vietnamese
    return json.loads(locale_file.read_text(encoding="utf-8"))


def t(key: str, language: str = "vi", **kwargs) -> str:
    """
    Dịch chuỗi theo key (dot notation).

    Args:
        key: Khóa dịch (VD: "auth.login", "common.loading")
        language: Ngôn ngữ ("vi" hoặc "en")
        **kwargs: Biến thay thế trong chuỗi

    Returns:
        Chuỗi đã dịch

    Examples:
        >>> t("auth.login", "vi")
        "Đăng nhập"
        >>> t("auth.welcome", "vi")
        "Xin chào"
    """
    locale = _load_locale(language)
    keys = key.split(".")
    value: Any = locale

    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return key  # Trả về key gốc nếu không tìm thấy

    if isinstance(value, str) and kwargs:
        try:
            value = value.format(**kwargs)
        except (KeyError, IndexError):
            pass

    return value if isinstance(value, str) else key


def get_current_language() -> str:
    """Lấy ngôn ngữ hiện tại từ session state."""
    try:
        import streamlit as st
        return st.session_state.get("language", "vi")
    except Exception:
        return "vi"


def tt(key: str, **kwargs) -> str:
    """
    Shortcut: Dịch theo ngôn ngữ hiện tại của session.

    Usage:
        st.title(tt("app.title"))
        st.button(tt("common.save"))
    """
    return t(key, get_current_language(), **kwargs)
