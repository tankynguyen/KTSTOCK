"""
KTSTOCK - vnstock Sponsored Connector (vnstock_data)
Kết nối dữ liệu chứng khoán VN qua vnstock_data (Sponsored - tốc độ nhanh hơn).
Hoạt động ĐỘC LẬP với vnstock Free connector.
"""
import time
from typing import Optional

import pandas as pd
from loguru import logger

from src.data.connectors.base import BaseConnector
from src.services.cache_service import get_cache
from src.utils.decorators import retry, timer
from src.utils.helpers import generate_cache_key


class VnstockSponsoredConnector(BaseConnector):
    """
    Connector sử dụng vnstock_data (Sponsored).
    Ưu tiên sử dụng Unified UI (v3.0.0+).
    Tốc độ nhanh hơn, dữ liệu chất lượng cao hơn.
    """

    def __init__(self, source: str = "VCI"):
        super().__init__(name="vnstock_sponsored")
        self.source = source
        self._vnstock_data = None
        self._is_unified_ui = False
        self.cache = get_cache()

    def connect(self) -> bool:
        """Khởi tạo kết nối vnstock_data."""
        try:
            import vnstock_data
            self._vnstock_data = vnstock_data

            # Kiểm tra phiên bản để dùng Unified UI
            version = getattr(vnstock_data, '__version__', '2.0.0')
            try:
                from importlib.metadata import version as get_version
                version = get_version("vnstock_data")
            except Exception:
                pass

            self._is_unified_ui = version >= '3.0.0'
            self._is_connected = True
            logger.info(f"✅ vnstock_data Sponsored connected (v{version}, unified_ui={self._is_unified_ui})")
            return True
        except ImportError:
            logger.warning("⚠️ vnstock_data not installed. Sponsored features unavailable.")
            self._is_connected = False
            return False

    def disconnect(self) -> None:
        self._vnstock_data = None
        self._is_connected = False

    def health_check(self) -> dict:
        start = time.time()
        try:
            if not self._is_connected:
                self.connect()
            if self._is_unified_ui:
                from vnstock_data import Market
                mkt = Market()
                # Lightweight test
                latency = (time.time() - start) * 1000
                return {"status": "ok", "message": "vnstock_data Sponsored OK (Unified UI)", "latency_ms": round(latency, 1)}
            else:
                from vnstock_data import Listing
                listing = Listing(source=self.source)
                symbols = listing.all_symbols()
                latency = (time.time() - start) * 1000
                return {"status": "ok", "message": f"vnstock_data OK ({len(symbols)} symbols)", "latency_ms": round(latency, 1)}
        except Exception as e:
            return {"status": "error", "message": str(e), "latency_ms": 0}

    @timer
    @retry(max_retries=2, delay=1.0)
    def get_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1D",
    ) -> Optional[pd.DataFrame]:
        """Lấy dữ liệu lịch sử giá (Sponsored - nhanh hơn)."""
        if not self._is_connected:
            self.connect()

        cache_key = generate_cache_key("vnpro_hist", symbol, start_date, end_date, interval)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            logger.debug(f"📦 Cache hit: {symbol} history (sponsored)")
            return cached

        try:
            if self._is_unified_ui:
                from vnstock_data import Market
                mkt = Market()
                df = mkt.equity(symbol.upper()).ohlcv(start=start_date, end=end_date)
            else:
                from vnstock_data import Quote
                quote = Quote(source=self.source, symbol=symbol.upper())
                df = quote.history(start=start_date, end=end_date, interval=interval)

            if df is not None and not df.empty:
                df = self._normalize_columns(df)
                self.cache.set_dataframe(cache_key, df, ttl=3600)
                logger.info(f"📈 [Sponsored] Fetched {len(df)} rows for {symbol}")

            return df
        except Exception as e:
            logger.error(f"❌ [Sponsored] Error fetching {symbol} history: {e}")
            return None

    @timer
    @retry(max_retries=2, delay=1.0)
    def get_listing(self) -> Optional[pd.DataFrame]:
        """Lấy danh sách mã cổ phiếu (Sponsored)."""
        cache_key = generate_cache_key("vnpro_listing")
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            if self._is_unified_ui:
                from vnstock_data import Reference
                ref = Reference()
                df = ref.listing()
            else:
                from vnstock_data import Listing
                listing = Listing(source=self.source)
                df = listing.all_symbols()

            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except Exception as e:
            logger.error(f"❌ [Sponsored] Error fetching listing: {e}")
            return None

    @timer
    def get_company_info(self, symbol: str) -> Optional[dict]:
        """Lấy thông tin công ty (Sponsored - chi tiết hơn)."""
        cache_key = generate_cache_key("vnpro_company", symbol)
        cached = self.cache.get_file(cache_key)
        if cached is not None:
            return cached

        try:
            if self._is_unified_ui:
                from vnstock_data import Fundamental
                fun = Fundamental()
                overview = fun.equity(symbol.upper()).overview()
            else:
                from vnstock_data import Company
                company = Company(source=self.source, symbol=symbol.upper())
                overview = company.overview()

            if overview is not None:
                if isinstance(overview, pd.DataFrame) and not overview.empty:
                    result = overview.to_dict(orient="records")[0]
                elif isinstance(overview, dict):
                    result = overview
                else:
                    result = None

                if result:
                    self.cache.set_file(cache_key, result, ttl=86400)
                return result
        except Exception as e:
            logger.error(f"❌ [Sponsored] Error fetching company {symbol}: {e}")
        return None

    @timer
    def get_financial_data(
        self,
        symbol: str,
        report_type: str = "ratio",
        period: str = "year",
    ) -> Optional[pd.DataFrame]:
        """Lấy dữ liệu tài chính (Sponsored - đầy đủ hơn)."""
        cache_key = generate_cache_key("vnpro_fin", symbol, report_type, period)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            if self._is_unified_ui:
                from vnstock_data import Fundamental
                fun = Fundamental()
                eq = fun.equity(symbol.upper())

                method_map = {
                    "income": eq.income_statement,
                    "balance": eq.balance_sheet,
                    "cashflow": eq.cash_flow,
                    "ratio": eq.ratio,
                }
            else:
                from vnstock_data import Finance
                finance = Finance(source=self.source, symbol=symbol.upper())
                method_map = {
                    "income": finance.income_statement,
                    "balance": finance.balance_sheet,
                    "cashflow": finance.cash_flow,
                    "ratio": finance.ratio,
                }

            fetch_method = method_map.get(report_type)
            if not fetch_method:
                return None

            df = fetch_method(period=period) if not self._is_unified_ui else fetch_method()
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except Exception as e:
            logger.error(f"❌ [Sponsored] Error fetching {report_type} for {symbol}: {e}")
            return None

    @timer
    def get_macro_data(self, indicator: str = "gdp") -> Optional[pd.DataFrame]:
        """Lấy dữ liệu kinh tế vĩ mô (chỉ Sponsored)."""
        if not self._is_unified_ui:
            logger.warning("⚠️ Macro data requires vnstock_data >= 3.0.0")
            return None

        cache_key = generate_cache_key("vnpro_macro", indicator)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock_data import Macro
            macro = Macro()
            df = getattr(macro, indicator, lambda: None)()
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except Exception as e:
            logger.error(f"❌ [Sponsored] Error fetching macro {indicator}: {e}")
            return None

    @timer
    def get_market_insights(self, symbol: str) -> Optional[dict]:
        """Lấy insights thị trường (chỉ Sponsored)."""
        try:
            if self._is_unified_ui:
                from vnstock_data import Insight
                insight = Insight()
                return insight.equity(symbol.upper()).summary()
        except Exception as e:
            logger.error(f"❌ [Sponsored] Error fetching insights {symbol}: {e}")
        return None

    def search_symbols(self, query: str) -> list[dict]:
        """Tìm kiếm mã cổ phiếu."""
        listing = self.get_listing()
        if listing is None or listing.empty:
            return []
        query_upper = query.upper()
        mask = listing.apply(
            lambda row: any(query_upper in str(val).upper() for val in row), axis=1
        )
        return listing[mask].head(20).to_dict(orient="records")

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Chuẩn hóa tên columns."""
        column_map = {
            "time": "date", "trading_date": "date", "TradingDate": "date",
            "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume",
        }
        return df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})
