"""
KTSTOCK - Pydantic Data Models: Stock
Định nghĩa cấu trúc dữ liệu cho cổ phiếu.
"""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field


class StockSymbol(BaseModel):
    """Thông tin cơ bản của mã cổ phiếu."""
    symbol: str = Field(..., description="Mã cổ phiếu (VD: VCB)")
    name: str = Field(default="", description="Tên công ty")
    exchange: str = Field(default="HOSE", description="Sàn giao dịch")
    asset_type: str = Field(default="stock")
    sector: Optional[str] = None
    industry: Optional[str] = None
    is_active: bool = True


class OHLCVData(BaseModel):
    """Dữ liệu giá OHLCV."""
    symbol: str
    date: str
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: int = 0
    interval: str = "1D"
    source: str = "VCI"


class StockQuote(BaseModel):
    """Báo giá real-time."""
    symbol: str
    price: float = 0.0
    change: float = 0.0
    change_pct: float = 0.0
    volume: int = 0
    high: float = 0.0
    low: float = 0.0
    open: float = 0.0
    prev_close: float = 0.0
    market_cap: Optional[float] = None
    timestamp: Optional[datetime] = None


class CompanyOverview(BaseModel):
    """Tổng quan công ty."""
    symbol: str
    name: str = ""
    short_name: str = ""
    exchange: str = ""
    industry: str = ""
    sector: str = ""
    market_cap: float = 0.0
    shares_outstanding: float = 0.0
    free_float: float = 0.0
    website: str = ""
    description: str = ""


class FinancialRatio(BaseModel):
    """Chỉ số tài chính."""
    symbol: str
    period: str = ""
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    eps: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    gross_margin: Optional[float] = None
    net_margin: Optional[float] = None
    dividend_yield: Optional[float] = None


class TechnicalSignal(BaseModel):
    """Tín hiệu kỹ thuật."""
    symbol: str
    signal: str = "hold"  # buy, sell, hold, strong_buy, strong_sell
    trend: str = "neutral"
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_lower: Optional[float] = None
    volume_sma: Optional[float] = None
    confidence: float = 0.0
    timestamp: Optional[datetime] = None
