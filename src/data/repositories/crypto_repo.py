"""
KTSTOCK - Crypto Repository
Repository pattern cho dữ liệu crypto (Binance).
"""
from typing import Optional

import pandas as pd
from loguru import logger

from src.data.connectors.crypto_connector import BinanceConnector
from src.data.database.connection import get_db
from src.services.cache_service import get_cache


class CryptoRepository:
    """Repository pattern cho dữ liệu crypto."""

    def __init__(self):
        self.db = get_db()
        self.cache = get_cache()
        self.connector = BinanceConnector()
        self._available = self.connector.connect()
        logger.info(f"₿ CryptoRepository initialized | Available: {self._available}")

    def get_history(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1D",
    ) -> Optional[pd.DataFrame]:
        """Lấy dữ liệu lịch sử crypto."""
        if not self._available:
            return self.get_from_db(symbol, start_date, end_date, interval)

        df = self.connector.get_historical_data(symbol, start_date, end_date, interval)
        if df is not None and not df.empty:
            self._save_to_db(symbol, df, interval)
        return df

    def get_ticker(self, symbol: str) -> Optional[dict]:
        """Lấy ticker 24h."""
        if self._available:
            return self.connector.get_ticker_24h(symbol)
        return None

    def get_top_cryptos(self, limit: int = 20) -> Optional[pd.DataFrame]:
        """Lấy top crypto theo volume."""
        if self._available:
            return self.connector.get_top_cryptos(limit=limit)
        return None

    def get_order_book(self, symbol: str, limit: int = 20) -> Optional[dict]:
        """Lấy order book."""
        if self._available:
            return self.connector.get_order_book(symbol, limit)
        return None

    def search(self, query: str) -> list[dict]:
        """Tìm kiếm cặp crypto."""
        if self._available:
            return self.connector.search_symbols(query)
        return []

    def get_from_db(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1D",
    ) -> Optional[pd.DataFrame]:
        """Lấy từ database (offline)."""
        rows = self.db.execute(
            """SELECT date, open, high, low, close, volume
               FROM price_history
               WHERE symbol = ? AND date >= ? AND date <= ? AND interval = ?
               ORDER BY date""",
            (symbol.upper(), start_date, end_date, interval)
        )
        return pd.DataFrame(rows) if rows else None

    def _save_to_db(self, symbol: str, df: pd.DataFrame, interval: str = "1D"):
        """Lưu vào database."""
        try:
            records = []
            for _, row in df.iterrows():
                records.append((
                    symbol.upper(), str(row.get("date", "")),
                    float(row.get("open", 0)), float(row.get("high", 0)),
                    float(row.get("low", 0)), float(row.get("close", 0)),
                    int(row.get("volume", 0)), interval,
                ))
            self.db.execute_many(
                """INSERT OR REPLACE INTO price_history
                   (symbol, date, open, high, low, close, volume, interval)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                records
            )
        except Exception as e:
            logger.warning(f"⚠️ Failed to save crypto {symbol} to DB: {e}")

    def get_health_status(self) -> dict:
        """Trạng thái connector."""
        if self._available:
            return self.connector.health_check()
        return {"status": "unavailable", "message": "Binance not connected"}
