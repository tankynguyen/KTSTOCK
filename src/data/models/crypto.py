"""
KTSTOCK - Pydantic Data Models: Crypto
Định nghĩa cấu trúc dữ liệu cho crypto (Binance).
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CryptoSymbol(BaseModel):
    """Thông tin cặp giao dịch crypto."""
    symbol: str = Field(..., description="Cặp giao dịch (VD: BTCUSDT)")
    base_asset: str = Field(default="", description="Tài sản cơ sở (BTC)")
    quote_asset: str = Field(default="USDT", description="Tài sản báo giá")
    exchange: str = "BINANCE"
    asset_type: str = "crypto"
    is_active: bool = True


class CryptoOHLCV(BaseModel):
    """Dữ liệu giá OHLCV cho crypto."""
    symbol: str
    date: str
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0
    quote_volume: float = 0.0
    trades: int = 0
    interval: str = "1d"


class CryptoTicker(BaseModel):
    """Ticker real-time crypto."""
    symbol: str
    price: float = 0.0
    change_24h: float = 0.0
    change_pct_24h: float = 0.0
    high_24h: float = 0.0
    low_24h: float = 0.0
    volume_24h: float = 0.0
    quote_volume_24h: float = 0.0
    market_cap: Optional[float] = None
    timestamp: Optional[datetime] = None


class CryptoOrderBook(BaseModel):
    """Order book snapshot."""
    symbol: str
    bids: list[list[float]] = Field(default_factory=list, description="[[price, qty], ...]")
    asks: list[list[float]] = Field(default_factory=list, description="[[price, qty], ...]")
    timestamp: Optional[datetime] = None


class CryptoTrade(BaseModel):
    """Giao dịch realtime."""
    symbol: str
    price: float
    quantity: float
    side: str = "buy"  # buy or sell
    timestamp: Optional[datetime] = None
