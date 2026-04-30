"""
KTSTOCK - Input Validators
Kiểm tra và validate dữ liệu đầu vào.
"""
import re
from datetime import datetime
from typing import Optional

from src.utils.constants import Exchange, TimeInterval


def validate_stock_symbol(symbol: str) -> bool:
    """
    Kiểm tra mã cổ phiếu Việt Nam hợp lệ.
    Quy tắc: 3 ký tự chữ cái in hoa (VD: VCB, FPT, VNM)
    """
    if not symbol:
        return False
    pattern = r'^[A-Z]{3}$'
    return bool(re.match(pattern, symbol.upper().strip()))


def validate_crypto_symbol(symbol: str) -> bool:
    """
    Kiểm tra mã crypto hợp lệ (VD: BTCUSDT, ETHUSDT).
    """
    if not symbol:
        return False
    pattern = r'^[A-Z]{2,10}(USDT|BTC|ETH|BNB|BUSD)$'
    return bool(re.match(pattern, symbol.upper().strip()))


def validate_date_range(start_date: str, end_date: str, fmt: str = "%Y-%m-%d") -> tuple[bool, str]:
    """
    Kiểm tra khoảng thời gian hợp lệ.

    Returns:
        (is_valid, error_message)
    """
    try:
        start = datetime.strptime(start_date, fmt)
        end = datetime.strptime(end_date, fmt)
    except ValueError:
        return False, f"Định dạng ngày không hợp lệ. Yêu cầu: {fmt}"

    if start > end:
        return False, "Ngày bắt đầu phải trước ngày kết thúc"

    if end > datetime.now():
        return False, "Ngày kết thúc không thể ở tương lai"

    return True, ""


def validate_email(email: str) -> bool:
    """Kiểm tra email hợp lệ."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple[bool, str]:
    """
    Kiểm tra mật khẩu đủ mạnh.

    Returns:
        (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Mật khẩu phải có ít nhất 8 ký tự"
    if not re.search(r'[A-Z]', password):
        return False, "Mật khẩu phải có ít nhất 1 chữ hoa"
    if not re.search(r'[a-z]', password):
        return False, "Mật khẩu phải có ít nhất 1 chữ thường"
    if not re.search(r'\d', password):
        return False, "Mật khẩu phải có ít nhất 1 chữ số"
    return True, ""


def validate_interval(interval: str) -> bool:
    """Kiểm tra khung thời gian hợp lệ."""
    valid_intervals = [ti.value for ti in TimeInterval]
    return interval in valid_intervals


def validate_exchange(exchange: str) -> bool:
    """Kiểm tra sàn giao dịch hợp lệ."""
    valid_exchanges = [ex.value for ex in Exchange]
    return exchange.upper() in valid_exchanges


def sanitize_input(text: str) -> str:
    """Làm sạch input để tránh injection."""
    # Loại bỏ ký tự nguy hiểm
    dangerous_chars = ['<', '>', '"', "'", ';', '--', '/*', '*/']
    result = text
    for char in dangerous_chars:
        result = result.replace(char, '')
    return result.strip()
