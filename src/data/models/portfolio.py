"""
KTSTOCK - Pydantic Data Models: Portfolio & Alert
Định nghĩa cấu trúc dữ liệu cho danh mục đầu tư và cảnh báo.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PortfolioModel(BaseModel):
    """Danh mục đầu tư."""
    id: Optional[int] = None
    user_id: int
    name: str
    description: str = ""
    initial_capital: float = 0.0
    created_at: Optional[datetime] = None


class PositionModel(BaseModel):
    """Vị thế giao dịch trong portfolio."""
    id: Optional[int] = None
    portfolio_id: int
    symbol: str
    quantity: float = 0.0
    avg_price: float = 0.0
    current_price: Optional[float] = None
    notes: str = ""
    opened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    @property
    def market_value(self) -> float:
        if self.current_price:
            return self.quantity * self.current_price
        return self.quantity * self.avg_price

    @property
    def profit_loss(self) -> float:
        if self.current_price:
            return (self.current_price - self.avg_price) * self.quantity
        return 0.0

    @property
    def profit_loss_pct(self) -> float:
        if self.avg_price > 0 and self.current_price:
            return (self.current_price - self.avg_price) / self.avg_price
        return 0.0


class AlertModel(BaseModel):
    """Cảnh báo."""
    id: Optional[int] = None
    user_id: int
    symbol: str
    condition: str  # price_above, price_below, rsi_overbought, etc.
    threshold: float = 0.0
    notification_type: str = "in_app"
    is_active: bool = True
    last_triggered: Optional[datetime] = None
    created_at: Optional[datetime] = None


class AlertHistoryModel(BaseModel):
    """Lịch sử cảnh báo đã kích hoạt."""
    id: Optional[int] = None
    alert_id: int
    triggered_value: float = 0.0
    message: str = ""
    is_read: bool = False
    triggered_at: Optional[datetime] = None
