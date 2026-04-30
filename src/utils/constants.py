"""
KTSTOCK - Constants & Enums
Các hằng số và enum dùng chung trong toàn bộ hệ thống.
"""
from enum import Enum, IntEnum


# ============================================================
# USER ROLES
# ============================================================
class UserRole(str, Enum):
    """Vai trò người dùng trong hệ thống."""
    ADMIN = "admin"           # Quản trị viên cao nhất
    ANALYST = "analyst"       # Nhà phân tích
    USER = "user"             # Người dùng thường
    GUEST = "guest"           # Khách (chỉ xem)

    @property
    def level(self) -> int:
        """Mức quyền (cao hơn = nhiều quyền hơn)."""
        return {
            UserRole.GUEST: 0,
            UserRole.USER: 1,
            UserRole.ANALYST: 2,
            UserRole.ADMIN: 3,
        }[self]


# ============================================================
# MARKET & EXCHANGE
# ============================================================
class Exchange(str, Enum):
    """Sàn giao dịch."""
    HOSE = "HOSE"        # Sàn TP.HCM
    HNX = "HNX"          # Sàn Hà Nội
    UPCOM = "UPCOM"      # Sàn UPCoM
    BINANCE = "BINANCE"  # Sàn Binance (Crypto)


class AssetType(str, Enum):
    """Loại tài sản."""
    STOCK = "stock"
    CRYPTO = "crypto"
    ETF = "etf"
    INDEX = "index"
    BOND = "bond"
    COMMODITY = "commodity"


class TimeInterval(str, Enum):
    """Khung thời gian."""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1H"
    H4 = "4H"
    D1 = "1D"
    W1 = "1W"
    MN = "1M"


# ============================================================
# ANALYSIS
# ============================================================
class TrendDirection(str, Enum):
    """Xu hướng."""
    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"


class SignalType(str, Enum):
    """Loại tín hiệu giao dịch."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"


class AnalysisType(str, Enum):
    """Loại phân tích."""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    AI = "ai"
    MACRO = "macro"


# ============================================================
# AI PROVIDERS
# ============================================================
class AIProvider(str, Enum):
    """Nhà cung cấp AI."""
    GEMINI = "gemini"
    GROK = "grok"
    DEEPSEEK = "deepseek"


# ============================================================
# ALERTS
# ============================================================
class AlertCondition(str, Enum):
    """Điều kiện cảnh báo."""
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    VOLUME_SPIKE = "volume_spike"
    RSI_OVERBOUGHT = "rsi_overbought"
    RSI_OVERSOLD = "rsi_oversold"
    MACD_CROSS_UP = "macd_cross_up"
    MACD_CROSS_DOWN = "macd_cross_down"
    CUSTOM = "custom"


class NotificationType(str, Enum):
    """Kênh thông báo."""
    TELEGRAM = "telegram"
    EMAIL = "email"
    ZALO = "zalo"
    IN_APP = "in_app"


# ============================================================
# VNSTOCK DATA SOURCES
# ============================================================
class VnstockSource(str, Enum):
    """Nguồn dữ liệu vnstock."""
    VCI = "VCI"
    KBS = "kbs"
    TCBS = "TCBS"  # Deprecated nhưng giữ lại cho tương thích


# ============================================================
# LANGUAGES
# ============================================================
class Language(str, Enum):
    """Ngôn ngữ hỗ trợ."""
    VI = "vi"
    EN = "en"


# ============================================================
# APP CONSTANTS
# ============================================================
APP_TITLE = "📊 KT Stock Analyzer"
APP_ICON = "📊"
APP_DESCRIPTION = "Nền tảng phân tích chứng khoán & crypto thông minh"

# Số lượng mặc định
DEFAULT_PAGE_SIZE = 20
MAX_SYMBOLS_PER_REQUEST = 50
MAX_CACHE_AGE_HOURS = 24

# Trading hours (Vietnam)
TRADING_START_HOUR = 9
TRADING_END_HOUR = 15
