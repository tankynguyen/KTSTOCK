"""
KTSTOCK - vnstock Free Connector
Kết nối dữ liệu chứng khoán VN qua thư viện vnstock (miễn phí).
Hỗ trợ đầy đủ: Listing, Quote, Company, Finance, Trading, Fund API.
"""
import time
from typing import Optional

import pandas as pd
from loguru import logger

from src.data.connectors.base import BaseConnector
from src.services.cache_service import get_cache
from src.utils.decorators import retry, timer
from src.utils.helpers import generate_cache_key


class VnstockFreeConnector(BaseConnector):
    """
    Connector sử dụng vnstock (free).
    Source: VCI hoặc KBS.
    """

    def __init__(self, source: str = "VCI"):
        super().__init__(name="vnstock_free")
        self.source = source
        self._vnstock = None
        self.cache = get_cache()

    def connect(self) -> bool:
        """Khởi tạo kết nối vnstock."""
        try:
            import vnstock
            self._vnstock = vnstock
            self._is_connected = True
            logger.info(f"✅ vnstock Free connected (source={self.source})")
            return True
        except ImportError:
            logger.error("❌ vnstock not installed. Run: pip install vnstock")
            self._is_connected = False
            return False

    def disconnect(self) -> None:
        self._vnstock = None
        self._is_connected = False

    def health_check(self) -> dict:
        """Kiểm tra vnstock hoạt động."""
        start = time.time()
        try:
            if not self._is_connected:
                self.connect()
            from vnstock import Listing
            listing = Listing(source=self.source)
            symbols = listing.all_symbols()
            latency = (time.time() - start) * 1000
            return {
                "status": "ok",
                "message": f"vnstock Free OK ({len(symbols)} symbols)",
                "latency_ms": round(latency, 1),
            }
        except Exception as e:
            return {"status": "error", "message": str(e), "latency_ms": 0}

    # ============================================================
    # QUOTE / PRICE API
    # ============================================================

    @timer
    @retry(max_retries=2, delay=1.0)
    def get_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1D",
    ) -> Optional[pd.DataFrame]:
        """
        Lấy dữ liệu lịch sử giá OHLCV.

        Args:
            symbol: Mã cổ phiếu (VD: "VCB")
            start_date: Ngày bắt đầu (YYYY-MM-DD)
            end_date: Ngày kết thúc (YYYY-MM-DD)
            interval: Khung thời gian ("1D", "1W", "1M")

        Returns:
            DataFrame với columns: time, open, high, low, close, volume
        """
        if not self._is_connected:
            self.connect()

        self.last_error = None
        
        # Check cache
        cache_key = generate_cache_key("vnfree_hist", symbol, start_date, end_date, interval)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            logger.debug(f"📦 Cache hit: {symbol} history")
            return cached

        sources_to_try = [self.source]
        fallback_sources = ["VCI", "KBS", "MSN"]
        for src in fallback_sources:
            if src.upper() != self.source.upper():
                sources_to_try.append(src.upper())

        errors = []
        for current_source in sources_to_try:
            try:
                from vnstock import Quote
                quote = Quote(source=current_source, symbol=symbol.upper())
                df = quote.history(start=start_date, end=end_date, interval=interval)

                if df is not None and not df.empty:
                    # Chuẩn hóa columns
                    df = self._normalize_columns(df)
                    # Cache kết quả (1 giờ)
                    self.cache.set_dataframe(cache_key, df, ttl=3600)
                    logger.info(f"📈 Fetched {len(df)} rows for {symbol} ({start_date} → {end_date}) via {current_source}")
                    return df
                else:
                    errors.append(f"{current_source}: returned empty")
            except Exception as e:
                errors.append(f"{current_source}: {str(e)}")

        self.last_error = f"All sources failed. Errors: {'; '.join(errors)}"
        logger.error(f"❌ Error fetching {symbol} history: {self.last_error}")
        return None

    # ============================================================
    # LISTING API
    # ============================================================

    @timer
    @retry(max_retries=2, delay=1.0)
    def get_listing(self) -> Optional[pd.DataFrame]:
        """Lấy danh sách tất cả mã cổ phiếu."""
        cache_key = generate_cache_key("vnfree_listing", self.source)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock import Listing
            listing = Listing(source=self.source)
            df = listing.all_symbols()
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)  # 24h
            return df
        except Exception as e:
            logger.error(f"❌ Error fetching listing: {e}")
            return None

    @timer
    def get_symbols_by_exchange(self, exchange: str = "HOSE") -> Optional[pd.DataFrame]:
        """
        Lấy danh sách mã theo sàn giao dịch.

        Args:
            exchange: "HOSE", "HNX", hoặc "UPCOM"
        """
        cache_key = generate_cache_key("vnfree_exchange", self.source, exchange)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock import Listing
            listing = Listing(source=self.source)
            df = listing.symbols_by_exchange(exchange=exchange)
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except Exception as e:
            logger.error(f"❌ Error fetching symbols by exchange {exchange}: {e}")
            return None

    @timer
    def get_symbols_by_industries(self, industry_name: str = None) -> Optional[pd.DataFrame]:
        """
        Lấy danh sách mã theo ngành.

        Args:
            industry_name: Tên ngành (VD: "Ngân hàng"). None = tất cả ngành.
        """
        cache_key = generate_cache_key("vnfree_industries", self.source, str(industry_name))
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock import Listing
            listing = Listing(source=self.source)
            if industry_name:
                df = listing.symbols_by_industries(industry_name=industry_name)
            else:
                df = listing.symbols_by_industries()
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except Exception as e:
            logger.error(f"❌ Error fetching symbols by industries: {e}")
            return None

    @timer
    def get_symbols_by_group(self, group_name: str = "VN30") -> Optional[pd.DataFrame]:
        """
        Lấy danh sách mã theo chỉ số (index group).

        Args:
            group_name: VN30, VN100, VNMID, VNSML, HNX30, VNALL, ...
        """
        cache_key = generate_cache_key("vnfree_group", self.source, group_name)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock import Listing
            listing = Listing(source=self.source)
            df = listing.symbols_by_group(group_name=group_name)
            if df is not None and not df.empty:
                if isinstance(df, pd.Series):
                    df = df.to_frame(name="symbol")
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except Exception as e:
            logger.error(f"❌ Error fetching symbols by group {group_name}: {e}")
            return None

    @timer
    def get_industries_icb(self) -> Optional[pd.DataFrame]:
        """Lấy danh sách phân loại ICB (VCI only)."""
        cache_key = generate_cache_key("vnfree_icb", self.source)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock import Listing
            listing = Listing(source=self.source)
            df = listing.industries_icb()
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except (NotImplementedError, Exception) as e:
            logger.warning(f"⚠️ ICB not available for {self.source}: {e}")
            return None

    @timer
    def get_all_future_indices(self) -> Optional[pd.DataFrame]:
        """Lấy danh sách hợp đồng tương lai."""
        cache_key = generate_cache_key("vnfree_futures", self.source)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock import Listing
            listing = Listing(source=self.source)
            result = listing.all_future_indices()
            if result is not None:
                df = result if isinstance(result, pd.DataFrame) else result.to_frame(name="symbol")
                self.cache.set_dataframe(cache_key, df, ttl=86400)
                return df
        except Exception as e:
            logger.error(f"❌ Error fetching futures: {e}")
        return None

    @timer
    def get_all_government_bonds(self) -> Optional[pd.DataFrame]:
        """Lấy danh sách trái phiếu chính phủ."""
        cache_key = generate_cache_key("vnfree_gov_bonds", self.source)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock import Listing
            listing = Listing(source=self.source)
            result = listing.all_government_bonds()
            if result is not None:
                df = result if isinstance(result, pd.DataFrame) else result.to_frame(name="symbol")
                self.cache.set_dataframe(cache_key, df, ttl=86400)
                return df
        except Exception as e:
            logger.error(f"❌ Error fetching government bonds: {e}")
        return None

    @timer
    def get_all_covered_warrant(self) -> Optional[pd.DataFrame]:
        """Lấy danh sách chứng quyền."""
        cache_key = generate_cache_key("vnfree_warrant", self.source)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock import Listing
            listing = Listing(source=self.source)
            result = listing.all_covered_warrant()
            if result is not None:
                df = result if isinstance(result, pd.DataFrame) else result.to_frame(name="symbol")
                self.cache.set_dataframe(cache_key, df, ttl=86400)
                return df
        except Exception as e:
            logger.error(f"❌ Error fetching covered warrants: {e}")
        return None

    @timer
    def get_all_bonds(self) -> Optional[pd.DataFrame]:
        """Lấy danh sách trái phiếu doanh nghiệp."""
        cache_key = generate_cache_key("vnfree_bonds", self.source)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock import Listing
            listing = Listing(source=self.source)
            result = listing.all_bonds()
            if result is not None:
                df = result if isinstance(result, pd.DataFrame) else result.to_frame(name="symbol")
                self.cache.set_dataframe(cache_key, df, ttl=86400)
                return df
        except Exception as e:
            logger.error(f"❌ Error fetching bonds: {e}")
        return None

    @timer
    def get_all_etf(self) -> Optional[pd.DataFrame]:
        """Lấy danh sách ETF (KBS only)."""
        cache_key = generate_cache_key("vnfree_etf", self.source)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock import Listing
            listing = Listing(source="KBS")
            result = listing.all_etf()
            if result is not None:
                df = result if isinstance(result, pd.DataFrame) else result.to_frame(name="symbol")
                self.cache.set_dataframe(cache_key, df, ttl=86400)
                return df
        except (NotImplementedError, AttributeError, Exception) as e:
            logger.warning(f"⚠️ ETF listing not available: {e}")
        return None

    @timer
    def get_all_indices(self) -> Optional[pd.DataFrame]:
        """Lấy danh sách tất cả chỉ số thị trường."""
        cache_key = generate_cache_key("vnfree_indices", self.source)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock import Listing
            listing = Listing(source=self.source)
            df = listing.all_indices()
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except Exception as e:
            logger.error(f"❌ Error fetching indices: {e}")
            return None

    @timer
    def get_indices_by_group(self, group: str = "HOSE") -> Optional[pd.DataFrame]:
        """
        Lấy danh sách chỉ số theo nhóm.

        Args:
            group: Tên nhóm (VD: "HOSE", "Sector Indices")
        """
        cache_key = generate_cache_key("vnfree_indices_grp", self.source, group)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock import Listing
            listing = Listing(source=self.source)
            df = listing.indices_by_group(group=group)
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except Exception as e:
            logger.error(f"❌ Error fetching indices by group {group}: {e}")
            return None

    # ============================================================
    # COMPANY API
    # ============================================================

    @timer
    def get_company_info(self, symbol: str) -> Optional[dict]:
        """Lấy thông tin tổng quan công ty."""
        cache_key = generate_cache_key("vnfree_company", symbol)
        cached = self.cache.get_file(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock import Company
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
            logger.error(f"❌ Error fetching company info {symbol}: {e}")
        return None

    @timer
    def get_shareholders(self, symbol: str) -> Optional[pd.DataFrame]:
        """Lấy danh sách cổ đông lớn."""
        cache_key = generate_cache_key("vnfree_shareholders", symbol, self.source)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock import Company
            company = Company(source=self.source, symbol=symbol.upper())
            df = company.shareholders()
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except Exception as e:
            logger.error(f"❌ Error fetching shareholders {symbol}: {e}")
            return None

    @timer
    def get_officers(self, symbol: str, filter_by: str = "all") -> Optional[pd.DataFrame]:
        """
        Lấy danh sách ban lãnh đạo.

        Args:
            symbol: Mã cổ phiếu
            filter_by: "all", "ceo", "boc"
        """
        cache_key = generate_cache_key("vnfree_officers", symbol, self.source, filter_by)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock import Company
            company = Company(source=self.source, symbol=symbol.upper())
            df = company.officers()
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except Exception as e:
            logger.error(f"❌ Error fetching officers {symbol}: {e}")
            return None

    @timer
    def get_subsidiaries(self, symbol: str) -> Optional[pd.DataFrame]:
        """Lấy danh sách công ty con."""
        cache_key = generate_cache_key("vnfree_subsidiaries", symbol, self.source)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock import Company
            company = Company(source=self.source, symbol=symbol.upper())
            df = company.subsidiaries()
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except Exception as e:
            logger.error(f"❌ Error fetching subsidiaries {symbol}: {e}")
            return None

    @timer
    def get_company_news(self, symbol: str) -> Optional[pd.DataFrame]:
        """Lấy tin tức công ty."""
        cache_key = generate_cache_key("vnfree_news", symbol, self.source)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock import Company
            company = Company(source=self.source, symbol=symbol.upper())
            df = company.news()
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=3600)  # 1h
            return df
        except Exception as e:
            logger.error(f"❌ Error fetching news {symbol}: {e}")
            return None

    @timer
    def get_company_events(self, symbol: str) -> Optional[pd.DataFrame]:
        """Lấy sự kiện công ty (cổ tức, phát hành cổ phiếu, ...)."""
        cache_key = generate_cache_key("vnfree_events", symbol, self.source)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock import Company
            company = Company(source=self.source, symbol=symbol.upper())
            df = company.events()
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except Exception as e:
            logger.error(f"❌ Error fetching events {symbol}: {e}")
            return None

    @timer
    def get_ownership(self, symbol: str) -> Optional[pd.DataFrame]:
        """Lấy cơ cấu cổ đông (KBS only)."""
        cache_key = generate_cache_key("vnfree_ownership", symbol)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock import Company
            company = Company(source="KBS", symbol=symbol.upper())
            df = company.ownership()
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except (AttributeError, NotImplementedError, Exception) as e:
            logger.warning(f"⚠️ Ownership not available for {symbol}: {e}")
            return None

    @timer
    def get_insider_trading(self, symbol: str) -> Optional[pd.DataFrame]:
        """Lấy giao dịch nội bộ (KBS only)."""
        cache_key = generate_cache_key("vnfree_insider", symbol)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock import Company
            company = Company(source="KBS", symbol=symbol.upper())
            df = company.insider_trading()
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except (AttributeError, NotImplementedError, Exception) as e:
            logger.warning(f"⚠️ Insider trading not available for {symbol}: {e}")
            return None

    # ============================================================
    # FINANCE API
    # ============================================================

    @timer
    def get_financial_data(
        self,
        symbol: str,
        report_type: str = "income",
        period: str = "year",
    ) -> Optional[pd.DataFrame]:
        """
        Lấy dữ liệu tài chính.

        Args:
            symbol: Mã cổ phiếu
            report_type: "income", "balance", "cashflow", "ratio"
            period: "year" hoặc "quarter"
        """
        cache_key = generate_cache_key("vnfree_financial", symbol, report_type, period)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock import Finance
            finance = Finance(source=self.source, symbol=symbol.upper())

            method_map = {
                "income": finance.income_statement,
                "balance": finance.balance_sheet,
                "cashflow": finance.cash_flow,
                "ratio": finance.ratio,
            }

            fetch_method = method_map.get(report_type)
            if not fetch_method:
                logger.warning(f"⚠️ Unknown report_type: {report_type}")
                return None

            df = fetch_method(period=period)
            if df is not None and not df.empty:
                # Deduplicate columns to avoid Parquet serialization errors
                if df.columns.duplicated().any():
                    cols = pd.Series(df.columns)
                    for dup in cols[cols.duplicated()].unique():
                        cols[cols[cols == dup].index.values.tolist()] = [f"{dup}_{i}" if i != 0 else str(dup) for i in range(sum(cols == dup))]
                    df.columns = cols
                    
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except Exception as e:
            logger.error(f"❌ Error fetching {report_type} for {symbol}: {e}")
            return None

    # ============================================================
    # TRADING API
    # ============================================================

    @timer
    def get_intraday(self, symbol: str) -> Optional[pd.DataFrame]:
        """Lấy dữ liệu intraday."""
        try:
            from vnstock import Trading
            trading = Trading(source=self.source, symbol=symbol.upper())
            return trading.price_depth()
        except Exception as e:
            logger.error(f"❌ Error fetching intraday {symbol}: {e}")
            return None

    @timer
    def get_price_board(self, symbols_list: list[str]) -> Optional[pd.DataFrame]:
        """
        Lấy bảng giá real-time.

        Args:
            symbols_list: Danh sách mã (VD: ["VCB", "ACB", "FPT"])
        """
        cache_key = generate_cache_key("vnfree_priceboard", "_".join(sorted(symbols_list)))
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock import Trading
            trading = Trading(source=self.source, symbol=symbols_list[0].upper())
            df = trading.price_board(symbols_list=[s.upper() for s in symbols_list])
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=60)  # 1 minute cache
            return df
        except Exception as e:
            logger.error(f"❌ Error fetching price board: {e}")
            return None

    # ============================================================
    # FUND API
    # ============================================================

    @timer
    def get_funds(self) -> Optional[pd.DataFrame]:
        """Lấy danh sách quỹ đầu tư mở (Fmarket)."""
        cache_key = generate_cache_key("vnfree_funds")
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock import Fund
            fund = Fund()
            df = fund.all_funds() if hasattr(fund, 'all_funds') else None
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except (ImportError, AttributeError, Exception) as e:
            logger.warning(f"⚠️ Fund data not available: {e}")
            return None

    # ============================================================
    # SEARCH & UTILITIES
    # ============================================================

    def search_symbols(self, query: str) -> list[dict]:
        """Tìm kiếm mã cổ phiếu."""
        listing = self.get_listing()
        if listing is None or listing.empty:
            return []

        query_upper = query.upper()
        # Tìm theo symbol hoặc tên
        mask = listing.apply(
            lambda row: any(query_upper in str(val).upper() for val in row), axis=1
        )
        results = listing[mask].head(20)
        return results.to_dict(orient="records")

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Chuẩn hóa tên columns cho thống nhất."""
        column_map = {
            "time": "date",
            "trading_date": "date",
            "TradingDate": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
        df = df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})
        return df
