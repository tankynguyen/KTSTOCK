"""
KTSTOCK - Stock Repository
Repository pattern cho truy xuất dữ liệu cổ phiếu.
Tự động chọn connector phù hợp (ưu tiên Sponsored).
"""
from typing import Optional

import pandas as pd
from loguru import logger

from src.data.connectors.vnstock_connector import VnstockFreeConnector
from src.data.connectors.vnstock_pro_connector import VnstockSponsoredConnector
from src.data.database.connection import get_db
from src.services.cache_service import get_cache
from src.utils.config import get_settings
from src.utils.helpers import generate_cache_key


class StockRepository:
    """
    Repository pattern cho dữ liệu cổ phiếu.
    Tự động fallback: Sponsored → Free → Database cache.
    """

    def __init__(self):
        settings = get_settings()
        self.db = get_db()
        self.cache = get_cache()

        # Khởi tạo cả 2 connectors
        self.free_connector = VnstockFreeConnector(source=settings.vnstock.vnstock_default_source)
        self.pro_connector = VnstockSponsoredConnector(source=settings.vnstock.vnstock_default_source)

        # Thử kết nối (ưu tiên Sponsored)
        self._prefer_sponsored = settings.vnstock.vnstock_prefer_sponsored
        self._pro_available = self.pro_connector.connect()
        self._free_available = self.free_connector.connect()

        active = "Sponsored" if self._pro_available else ("Free" if self._free_available else "None")
        logger.info(f"📊 StockRepository initialized | Active: {active}")

    @property
    def active_connector(self):
        """Lấy connector đang hoạt động (ưu tiên Sponsored)."""
        if self._prefer_sponsored and self._pro_available:
            return self.pro_connector
        if self._free_available:
            return self.free_connector
        return None

    def get_history(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1D",
        use_sponsored: Optional[bool] = None,
    ) -> Optional[pd.DataFrame]:
        """
        Lấy dữ liệu lịch sử OHLCV.

        Args:
            symbol: Mã cổ phiếu
            start_date: Ngày bắt đầu
            end_date: Ngày kết thúc
            interval: Khung thời gian
            use_sponsored: Bắt buộc dùng connector cụ thể (None = tự động)
        """
        connector = self._select_connector(use_sponsored)
        if connector is None:
            logger.error("❌ No connector available")
            return None

        df = connector.get_historical_data(symbol, start_date, end_date, interval)

        # Fallback sang connector còn lại nếu thất bại
        if df is None and connector == self.pro_connector and self._free_available:
            logger.warning(f"⚠️ Sponsored failed, fallback to Free for {symbol}")
            df = self.free_connector.get_historical_data(symbol, start_date, end_date, interval)
        elif df is None and connector == self.free_connector and self._pro_available:
            logger.warning(f"⚠️ Free failed, fallback to Sponsored for {symbol}")
            df = self.pro_connector.get_historical_data(symbol, start_date, end_date, interval)

        # Lưu vào database nếu có dữ liệu
        if df is not None and not df.empty:
            self.ensure_symbol(symbol)
            self._save_to_db(symbol, df, interval)

        return df

    def get_listing(self, use_sponsored: Optional[bool] = None) -> Optional[pd.DataFrame]:
        """Lấy danh sách mã cổ phiếu."""
        connector = self._select_connector(use_sponsored)
        if connector:
            return connector.get_listing()
        return None

    def get_company(self, symbol: str, use_sponsored: Optional[bool] = None) -> Optional[dict]:
        """Lấy thông tin công ty."""
        connector = self._select_connector(use_sponsored)
        if connector:
            return connector.get_company_info(symbol)
        return None

    def get_financials(
        self,
        symbol: str,
        report_type: str = "ratio",
        period: str = "year",
        use_sponsored: Optional[bool] = None,
    ) -> Optional[pd.DataFrame]:
        """Lấy dữ liệu tài chính."""
        connector = self._select_connector(use_sponsored)
        if connector:
            return connector.get_financial_data(symbol, report_type, period)
        return None

    def search(self, query: str) -> list[dict]:
        """Tìm kiếm mã cổ phiếu."""
        connector = self.active_connector
        if connector:
            return connector.search_symbols(query)
        return []

    def get_from_db(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1D",
    ) -> Optional[pd.DataFrame]:
        """Lấy dữ liệu từ database (offline mode)."""
        rows = self.db.execute(
            """SELECT date, open, high, low, close, volume
               FROM price_history
               WHERE symbol = ? AND date >= ? AND date <= ? AND interval = ?
               ORDER BY date""",
            (symbol.upper(), start_date, end_date, interval)
        )
        if rows:
            return pd.DataFrame(rows)
        return None

    def _select_connector(self, use_sponsored: Optional[bool] = None):
        """Chọn connector phù hợp."""
        if use_sponsored is True and self._pro_available:
            return self.pro_connector
        elif use_sponsored is False and self._free_available:
            return self.free_connector
        return self.active_connector

    def ensure_symbol(self, symbol: str, exchange: str = "UNKNOWN"):
        """Đảm bảo symbol tồn tại trong database."""
        symbol = symbol.upper().strip()
        existing = self.db.execute_one("SELECT symbol FROM symbols WHERE symbol = ?", (symbol,))
        if not existing:
            self.db.execute_write(
                "INSERT OR IGNORE INTO symbols (symbol, exchange) VALUES (?, ?)",
                (symbol, exchange)
            )

    def _save_to_db(self, symbol: str, df: pd.DataFrame, interval: str = "1D"):
        """Lưu dữ liệu vào database cho offline access."""
        try:
            records = []
            for _, row in df.iterrows():
                records.append((
                    symbol.upper(),
                    str(row.get("date", "")),
                    float(row.get("open", 0)),
                    float(row.get("high", 0)),
                    float(row.get("low", 0)),
                    float(row.get("close", 0)),
                    int(row.get("volume", 0)),
                    interval,
                ))

            self.db.execute_many(
                """INSERT OR REPLACE INTO price_history
                   (symbol, date, open, high, low, close, volume, interval)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                records
            )
        except Exception as e:
            logger.warning(f"⚠️ Failed to save {symbol} to DB: {e}")

    def get_health_status(self) -> dict:
        """Trạng thái tổng quan các connectors."""
        return {
            "free": self.free_connector.health_check() if self._free_available else {"status": "unavailable"},
            "sponsored": self.pro_connector.health_check() if self._pro_available else {"status": "unavailable"},
            "prefer_sponsored": self._prefer_sponsored,
            "db_records": self.db.get_table_count("price_history"),
        }
