"""
KTSTOCK - vnstock Sponsored Connector (vnstock_data)
Kết nối dữ liệu chứng khoán VN qua vnstock_data (Sponsored - tốc độ nhanh hơn).
Hỗ trợ đầy đủ: Quote, Company, Finance, Trading, Market, Macro, Commodity, Fund API.
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

    # ============================================================
    # LISTING API
    # ============================================================

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

    # ============================================================
    # COMPANY API
    # ============================================================

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

    # ============================================================
    # FINANCE API
    # ============================================================

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

    # ============================================================
    # TRADING API
    # ============================================================

    @timer
    def get_price_board(self, symbols_list: list[str]) -> Optional[pd.DataFrame]:
        """Lấy bảng giá real-time (Sponsored)."""
        cache_key = generate_cache_key("vnpro_priceboard", "_".join(sorted(symbols_list)))
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock_data import Trading
            trading = Trading(source=self.source, symbol=symbols_list[0].upper())
            df = trading.price_board(symbol_list=[s.upper() for s in symbols_list])
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=60)
            return df
        except Exception as e:
            logger.error(f"❌ [Sponsored] Error fetching price board: {e}")
            return None

    @timer
    def get_foreign_trade(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Lấy dữ liệu giao dịch khối ngoại."""
        cache_key = generate_cache_key("vnpro_foreign", symbol, start_date, end_date)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock_data import Trading
            trading = Trading(source=self.source, symbol=symbol.upper())
            df = trading.foreign_trade(start=start_date, end=end_date)
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=3600)
            return df
        except Exception as e:
            logger.error(f"❌ [Sponsored] Error fetching foreign trade {symbol}: {e}")
            return None

    @timer
    def get_prop_trade(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Lấy dữ liệu tự doanh."""
        cache_key = generate_cache_key("vnpro_prop", symbol, start_date, end_date)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock_data import Trading
            trading = Trading(source=self.source, symbol=symbol.upper())
            df = trading.prop_trade(start=start_date, end=end_date)
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=3600)
            return df
        except Exception as e:
            logger.error(f"❌ [Sponsored] Error fetching prop trade {symbol}: {e}")
            return None

    @timer
    def get_insider_deal(self, symbol: str) -> Optional[pd.DataFrame]:
        """Lấy giao dịch nội bộ."""
        cache_key = generate_cache_key("vnpro_insider_deal", symbol)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock_data import Trading
            trading = Trading(source=self.source, symbol=symbol.upper())
            df = trading.insider_deal()
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except Exception as e:
            logger.error(f"❌ [Sponsored] Error fetching insider deal {symbol}: {e}")
            return None

    @timer
    def get_order_stats(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Lấy thống kê lệnh."""
        cache_key = generate_cache_key("vnpro_orderstats", symbol, start_date, end_date)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock_data import Trading
            trading = Trading(source=self.source, symbol=symbol.upper())
            df = trading.order_stats(start=start_date, end=end_date)
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=3600)
            return df
        except Exception as e:
            logger.error(f"❌ [Sponsored] Error fetching order stats {symbol}: {e}")
            return None

    # ============================================================
    # MARKET API
    # ============================================================

    @timer
    def get_market_pe(self) -> Optional[pd.DataFrame]:
        """Lấy P/E toàn thị trường."""
        cache_key = generate_cache_key("vnpro_market_pe")
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock_data import Market
            market = Market()
            df = market.pe()
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except Exception as e:
            logger.error(f"❌ [Sponsored] Error fetching market P/E: {e}")
            return None

    @timer
    def get_market_pb(self) -> Optional[pd.DataFrame]:
        """Lấy P/B toàn thị trường."""
        cache_key = generate_cache_key("vnpro_market_pb")
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock_data import Market
            market = Market()
            df = market.pb()
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except Exception as e:
            logger.error(f"❌ [Sponsored] Error fetching market P/B: {e}")
            return None

    @timer
    def get_market_evaluation(self) -> Optional[pd.DataFrame]:
        """Lấy định giá thị trường tổng hợp."""
        cache_key = generate_cache_key("vnpro_market_eval")
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock_data import Market
            market = Market()
            df = market.evaluation()
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except Exception as e:
            logger.error(f"❌ [Sponsored] Error fetching market evaluation: {e}")
            return None

    # ============================================================
    # MACRO API
    # ============================================================

    @timer
    def get_macro_data(self, indicator: str = "gdp") -> Optional[pd.DataFrame]:
        """
        Lấy dữ liệu kinh tế vĩ mô.

        Args:
            indicator: gdp, cpi, exchange_rate, fdi, money_supply,
                      interest_rate, industry_prod, import_export,
                      retail, population_labor
        """
        cache_key = generate_cache_key("vnpro_macro", indicator)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock_data import Macro
            macro = Macro()
            fetch_fn = getattr(macro, indicator, None)
            if fetch_fn is None:
                logger.warning(f"⚠️ Unknown macro indicator: {indicator}")
                return None
            df = fetch_fn()
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except Exception as e:
            logger.error(f"❌ [Sponsored] Error fetching macro {indicator}: {e}")
            return None

    @timer
    def get_gdp(self, start: str = None, end: str = None, period: str = "quarter") -> Optional[pd.DataFrame]:
        """Lấy GDP."""
        cache_key = generate_cache_key("vnpro_gdp", str(start), str(end), period)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached
        try:
            from vnstock_data import Macro
            macro = Macro()
            kwargs = {"period": period}
            if start:
                kwargs["start"] = start
            if end:
                kwargs["end"] = end
            df = macro.gdp(**kwargs)
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except Exception as e:
            logger.error(f"❌ [Sponsored] Error fetching GDP: {e}")
            return None

    @timer
    def get_cpi(self, start: str = None, end: str = None, period: str = "month") -> Optional[pd.DataFrame]:
        """Lấy CPI."""
        cache_key = generate_cache_key("vnpro_cpi", str(start), str(end), period)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached
        try:
            from vnstock_data import Macro
            macro = Macro()
            kwargs = {"period": period}
            if start:
                kwargs["start"] = start
            if end:
                kwargs["end"] = end
            df = macro.cpi(**kwargs)
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except Exception as e:
            logger.error(f"❌ [Sponsored] Error fetching CPI: {e}")
            return None

    @timer
    def get_exchange_rate(self, start: str = None, end: str = None, period: str = "day") -> Optional[pd.DataFrame]:
        """Lấy tỷ giá ngoại tệ."""
        cache_key = generate_cache_key("vnpro_exrate", str(start), str(end), period)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached
        try:
            from vnstock_data import Macro
            macro = Macro()
            kwargs = {"period": period}
            if start:
                kwargs["start"] = start
            if end:
                kwargs["end"] = end
            df = macro.exchange_rate(**kwargs)
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=3600)
            return df
        except Exception as e:
            logger.error(f"❌ [Sponsored] Error fetching exchange rate: {e}")
            return None

    @timer
    def get_fdi(self, start: str = None, end: str = None, period: str = "month") -> Optional[pd.DataFrame]:
        """Lấy FDI."""
        cache_key = generate_cache_key("vnpro_fdi", str(start), str(end), period)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached
        try:
            from vnstock_data import Macro
            macro = Macro()
            kwargs = {"period": period}
            if start:
                kwargs["start"] = start
            if end:
                kwargs["end"] = end
            df = macro.fdi(**kwargs)
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except Exception as e:
            logger.error(f"❌ [Sponsored] Error fetching FDI: {e}")
            return None

    @timer
    def get_interest_rate(self, length: str = "1Y", period: str = "day") -> Optional[pd.DataFrame]:
        """Lấy lãi suất liên ngân hàng."""
        cache_key = generate_cache_key("vnpro_interest", length, period)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached
        try:
            from vnstock_data import Macro
            macro = Macro()
            df = macro.interest_rate(length=length, period=period)
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except Exception as e:
            logger.error(f"❌ [Sponsored] Error fetching interest rate: {e}")
            return None

    # ============================================================
    # COMMODITY API
    # ============================================================

    @timer
    def get_gold_price(self) -> Optional[pd.DataFrame]:
        """Lấy giá vàng Việt Nam."""
        cache_key = generate_cache_key("vnpro_gold")
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached
        try:
            from vnstock_data import Commodity
            commodity = Commodity()
            df = commodity.gold_vn()
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=3600)
            return df
        except Exception as e:
            logger.error(f"❌ [Sponsored] Error fetching gold price: {e}")
            return None

    @timer
    def get_oil_price(self) -> Optional[pd.DataFrame]:
        """Lấy giá dầu thô."""
        cache_key = generate_cache_key("vnpro_oil")
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached
        try:
            from vnstock_data import Commodity
            commodity = Commodity()
            df = commodity.oil_crude()
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=3600)
            return df
        except Exception as e:
            logger.error(f"❌ [Sponsored] Error fetching oil price: {e}")
            return None

    @timer
    def get_steel_price(self) -> Optional[pd.DataFrame]:
        """Lấy giá thép HRC."""
        cache_key = generate_cache_key("vnpro_steel")
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached
        try:
            from vnstock_data import Commodity
            commodity = Commodity()
            df = commodity.steel_hrc()
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=3600)
            return df
        except Exception as e:
            logger.error(f"❌ [Sponsored] Error fetching steel price: {e}")
            return None

    @timer
    def get_pork_price(self) -> Optional[pd.DataFrame]:
        """Lấy giá heo hơi miền Bắc."""
        cache_key = generate_cache_key("vnpro_pork")
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached
        try:
            from vnstock_data import Commodity
            commodity = Commodity()
            df = commodity.pork_north_vn()
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=3600)
            return df
        except Exception as e:
            logger.error(f"❌ [Sponsored] Error fetching pork price: {e}")
            return None

    # ============================================================
    # FUND API
    # ============================================================

    @timer
    def get_etf_list(self) -> Optional[pd.DataFrame]:
        """Lấy danh sách quỹ ETF."""
        cache_key = generate_cache_key("vnpro_etf")
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached
        try:
            from vnstock_data import Fund
            fund = Fund()
            df = fund.etf_list() if hasattr(fund, 'etf_list') else None
            if df is not None and not df.empty:
                self.cache.set_dataframe(cache_key, df, ttl=86400)
            return df
        except Exception as e:
            logger.warning(f"⚠️ [Sponsored] ETF list not available: {e}")
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

    # ============================================================
    # SEARCH & UTILITIES
    # ============================================================

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
