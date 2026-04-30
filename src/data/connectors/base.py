"""
KTSTOCK - Base Connector
Abstract base class cho tất cả data connectors.
"""
from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd


class BaseConnector(ABC):
    """Abstract base class cho data connectors."""

    def __init__(self, name: str = "base"):
        self.name = name
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @abstractmethod
    def connect(self) -> bool:
        """Thiết lập kết nối. Returns True nếu thành công."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Đóng kết nối."""
        pass

    @abstractmethod
    def health_check(self) -> dict:
        """
        Kiểm tra trạng thái kết nối.
        Returns: {"status": "ok"|"error", "message": str, "latency_ms": float}
        """
        pass

    def get_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1D",
    ) -> Optional[pd.DataFrame]:
        """Lấy dữ liệu lịch sử OHLCV."""
        raise NotImplementedError

    def get_quote(self, symbol: str) -> Optional[dict]:
        """Lấy báo giá real-time."""
        raise NotImplementedError

    def get_company_info(self, symbol: str) -> Optional[dict]:
        """Lấy thông tin công ty."""
        raise NotImplementedError

    def search_symbols(self, query: str) -> list[dict]:
        """Tìm kiếm mã."""
        raise NotImplementedError
