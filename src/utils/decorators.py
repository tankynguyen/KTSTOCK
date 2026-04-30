"""
KTSTOCK - Custom Decorators
Các decorator tái sử dụng cho caching, retry, timing, auth.
"""
import time
import functools
from typing import Any, Callable, Optional

from loguru import logger


def timer(func: Callable) -> Callable:
    """
    Đo thời gian thực thi của hàm.

    Usage:
        @timer
        def my_function():
            ...
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.debug(f"⏱️ {func.__qualname__} executed in {elapsed:.3f}s")
        return result
    return wrapper


def retry(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """
    Decorator retry với exponential backoff.

    Args:
        max_retries: Số lần thử tối đa
        delay: Thời gian chờ ban đầu (giây)
        backoff: Hệ số nhân delay
        exceptions: Các exception cần retry

    Usage:
        @retry(max_retries=3, delay=1.0)
        def call_api():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"🔄 {func.__qualname__} attempt {attempt}/{max_retries} failed: {e}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"❌ {func.__qualname__} failed after {max_retries} attempts: {e}")
            raise last_exception
        return wrapper
    return decorator


def require_role(min_role: str):
    """
    Decorator kiểm tra quyền user trước khi thực thi.

    Args:
        min_role: Role tối thiểu cần có (guest, user, analyst, admin)

    Usage:
        @require_role("analyst")
        def sensitive_operation(user):
            ...
    """
    from src.utils.constants import UserRole

    role_levels = {r.value: r.level for r in UserRole}

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import streamlit as st
            user_role = st.session_state.get("user_role", "guest")
            user_level = role_levels.get(user_role, 0)
            required_level = role_levels.get(min_role, 0)

            if user_level < required_level:
                logger.warning(f"🚫 Access denied: {func.__qualname__} requires {min_role}, user has {user_role}")
                st.error(f"⛔ Bạn cần quyền **{min_role}** để sử dụng tính năng này.")
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_symbol(func: Callable) -> Callable:
    """Decorator kiểm tra symbol hợp lệ trước khi thực thi."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        symbol = kwargs.get("symbol") or (args[1] if len(args) > 1 else None)
        if not symbol or not isinstance(symbol, str) or len(symbol) < 1:
            logger.error(f"❌ Invalid symbol: {symbol}")
            raise ValueError(f"Symbol không hợp lệ: {symbol}")
        # Chuẩn hóa symbol
        if "symbol" in kwargs:
            kwargs["symbol"] = symbol.upper().strip()
        return func(*args, **kwargs)
    return wrapper
