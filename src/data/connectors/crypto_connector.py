"""
KTSTOCK - Binance Crypto Connector
Kết nối Binance API (REST + WebSocket) cho dữ liệu crypto real-time.
"""
import time
import asyncio
import json
from typing import Optional, Callable
from datetime import datetime

import pandas as pd
from loguru import logger

from src.data.connectors.base import BaseConnector
from src.services.cache_service import get_cache
from src.utils.config import get_settings
from src.utils.decorators import retry, timer
from src.utils.helpers import generate_cache_key


class BinanceConnector(BaseConnector):
    """
    Connector cho Binance.
    - REST API: Dữ liệu lịch sử, ticker
    - WebSocket: Real-time streaming (đồng bộ nhanh nhất)
    """

    BASE_URL = "https://api.binance.com/api/v3"
    WS_URL = "wss://stream.binance.com:9443/ws"

    # Mapping interval
    INTERVAL_MAP = {
        "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
        "1H": "1h", "4H": "4h", "1D": "1d", "1W": "1w", "1M": "1M",
        "1h": "1h", "4h": "4h", "1d": "1d", "1w": "1w",
    }

    def __init__(self):
        super().__init__(name="binance")
        settings = get_settings()
        self.api_key = settings.crypto.binance_api_key
        self.api_secret = settings.crypto.binance_api_secret
        self._http_client = None
        self._ws_connections: dict = {}
        self.cache = get_cache()

    def connect(self) -> bool:
        """Khởi tạo HTTP client."""
        try:
            import httpx
            self._http_client = httpx.Client(
                base_url=self.BASE_URL,
                timeout=15.0,
                headers={"X-MBX-APIKEY": self.api_key} if self.api_key else {},
            )
            self._is_connected = True
            logger.info("✅ Binance connector connected")
            return True
        except Exception as e:
            logger.error(f"❌ Binance connect failed: {e}")
            return False

    def disconnect(self) -> None:
        if self._http_client:
            self._http_client.close()
        self._is_connected = False

    def health_check(self) -> dict:
        start = time.time()
        try:
            if not self._is_connected:
                self.connect()
            resp = self._http_client.get("/ping")
            latency = (time.time() - start) * 1000
            if resp.status_code == 200:
                return {"status": "ok", "message": "Binance OK", "latency_ms": round(latency, 1)}
            return {"status": "error", "message": f"HTTP {resp.status_code}", "latency_ms": round(latency, 1)}
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
        limit: int = 1000,
    ) -> Optional[pd.DataFrame]:
        """
        Lấy dữ liệu lịch sử Klines (candlestick).

        Args:
            symbol: Cặp giao dịch (VD: "BTCUSDT")
            start_date: YYYY-MM-DD
            end_date: YYYY-MM-DD
            interval: "1m","5m","15m","1H","4H","1D","1W"
            limit: Số candles tối đa (max 1000)
        """
        if not self._is_connected:
            self.connect()

        cache_key = generate_cache_key("binance_klines", symbol, start_date, end_date, interval)
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            bi_interval = self.INTERVAL_MAP.get(interval, "1d")

            # Convert dates to milliseconds
            start_ms = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp() * 1000)
            end_ms = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp() * 1000)

            params = {
                "symbol": symbol.upper(),
                "interval": bi_interval,
                "startTime": start_ms,
                "endTime": end_ms,
                "limit": limit,
            }

            resp = self._http_client.get("/klines", params=params)
            resp.raise_for_status()
            data = resp.json()

            if not data:
                return None

            df = pd.DataFrame(data, columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "quote_volume", "trades", "taker_buy_volume",
                "taker_buy_quote_volume", "ignore"
            ])

            # Convert types
            for col in ["open", "high", "low", "close", "volume", "quote_volume"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            df["date"] = pd.to_datetime(df["open_time"], unit="ms").dt.strftime("%Y-%m-%d %H:%M")
            df["trades"] = df["trades"].astype(int)
            df = df[["date", "open", "high", "low", "close", "volume", "quote_volume", "trades"]]

            # Cache theo interval
            ttl = 300 if bi_interval in ("1m", "5m") else 3600
            self.cache.set_dataframe(cache_key, df, ttl=ttl)
            logger.info(f"₿ Fetched {len(df)} klines for {symbol} ({interval})")
            return df

        except Exception as e:
            logger.error(f"❌ Binance klines error for {symbol}: {e}")
            return None

    @timer
    @retry(max_retries=2, delay=0.5)
    def get_ticker_24h(self, symbol: str) -> Optional[dict]:
        """Lấy ticker 24h cho 1 cặp."""
        if not self._is_connected:
            self.connect()

        cache_key = generate_cache_key("binance_ticker", symbol)
        cached = self.cache.get_memory(cache_key)
        if cached is not None:
            return cached

        try:
            resp = self._http_client.get("/ticker/24hr", params={"symbol": symbol.upper()})
            resp.raise_for_status()
            data = resp.json()

            ticker = {
                "symbol": data["symbol"],
                "price": float(data["lastPrice"]),
                "change_24h": float(data["priceChange"]),
                "change_pct_24h": float(data["priceChangePercent"]),
                "high_24h": float(data["highPrice"]),
                "low_24h": float(data["lowPrice"]),
                "volume_24h": float(data["volume"]),
                "quote_volume_24h": float(data["quoteVolume"]),
            }

            self.cache.set_memory(cache_key, ticker, ttl=30)  # 30s cache
            return ticker
        except Exception as e:
            logger.error(f"❌ Binance ticker error for {symbol}: {e}")
            return None

    @timer
    def get_all_tickers(self) -> Optional[pd.DataFrame]:
        """Lấy giá tất cả các cặp."""
        if not self._is_connected:
            self.connect()

        cache_key = "binance_all_tickers"
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            resp = self._http_client.get("/ticker/price")
            resp.raise_for_status()
            data = resp.json()

            df = pd.DataFrame(data)
            df["price"] = pd.to_numeric(df["price"], errors="coerce")
            self.cache.set_dataframe(cache_key, df, ttl=60)
            return df
        except Exception as e:
            logger.error(f"❌ Binance all tickers error: {e}")
            return None

    @timer
    def get_order_book(self, symbol: str, limit: int = 20) -> Optional[dict]:
        """Lấy order book (bids/asks)."""
        if not self._is_connected:
            self.connect()

        try:
            resp = self._http_client.get("/depth", params={"symbol": symbol.upper(), "limit": limit})
            resp.raise_for_status()
            data = resp.json()

            return {
                "symbol": symbol.upper(),
                "bids": [[float(p), float(q)] for p, q in data.get("bids", [])],
                "asks": [[float(p), float(q)] for p, q in data.get("asks", [])],
            }
        except Exception as e:
            logger.error(f"❌ Binance order book error: {e}")
            return None

    def get_top_cryptos(self, quote: str = "USDT", limit: int = 20) -> Optional[pd.DataFrame]:
        """Lấy top crypto theo volume."""
        if not self._is_connected:
            self.connect()

        try:
            resp = self._http_client.get("/ticker/24hr")
            resp.raise_for_status()
            data = resp.json()

            df = pd.DataFrame(data)
            # Lọc theo quote asset
            df = df[df["symbol"].str.endswith(quote)]

            for col in ["lastPrice", "priceChangePercent", "volume", "quoteVolume"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            df = df.sort_values("quoteVolume", ascending=False).head(limit)
            df = df.rename(columns={
                "lastPrice": "price",
                "priceChangePercent": "change_pct",
                "quoteVolume": "quote_volume",
            })

            return df[["symbol", "price", "change_pct", "volume", "quote_volume"]].reset_index(drop=True)
        except Exception as e:
            logger.error(f"❌ Error fetching top cryptos: {e}")
            return None

    def search_symbols(self, query: str) -> list[dict]:
        """Tìm kiếm cặp giao dịch."""
        tickers = self.get_all_tickers()
        if tickers is None or tickers.empty:
            return []
        query_upper = query.upper()
        filtered = tickers[tickers["symbol"].str.contains(query_upper)]
        return filtered.head(20).to_dict(orient="records")

    # =========================================
    # WebSocket Real-time (Async)
    # =========================================
    async def stream_ticker(self, symbol: str, callback: Callable) -> None:
        """
        Stream real-time ticker qua WebSocket.
        Đồng bộ nhanh nhất có thể.

        Args:
            symbol: Cặp giao dịch (VD: "btcusdt")
            callback: Hàm xử lý mỗi khi nhận tick mới
        """
        import websockets

        ws_url = f"{self.WS_URL}/{symbol.lower()}@ticker"
        logger.info(f"🔌 WebSocket connecting: {ws_url}")

        try:
            async with websockets.connect(ws_url) as ws:
                self._ws_connections[symbol] = ws
                logger.info(f"✅ WebSocket connected: {symbol}")

                async for message in ws:
                    data = json.loads(message)
                    ticker = {
                        "symbol": data.get("s", symbol.upper()),
                        "price": float(data.get("c", 0)),
                        "change_24h": float(data.get("p", 0)),
                        "change_pct_24h": float(data.get("P", 0)),
                        "high_24h": float(data.get("h", 0)),
                        "low_24h": float(data.get("l", 0)),
                        "volume_24h": float(data.get("v", 0)),
                        "quote_volume_24h": float(data.get("q", 0)),
                        "timestamp": datetime.now(),
                    }
                    await callback(ticker)
        except Exception as e:
            logger.error(f"❌ WebSocket error {symbol}: {e}")
        finally:
            self._ws_connections.pop(symbol, None)

    async def stream_kline(self, symbol: str, interval: str, callback: Callable) -> None:
        """Stream real-time kline/candlestick qua WebSocket."""
        import websockets

        bi_interval = self.INTERVAL_MAP.get(interval, "1m")
        ws_url = f"{self.WS_URL}/{symbol.lower()}@kline_{bi_interval}"

        try:
            async with websockets.connect(ws_url) as ws:
                async for message in ws:
                    data = json.loads(message)
                    kline = data.get("k", {})
                    candle = {
                        "symbol": kline.get("s", symbol.upper()),
                        "interval": kline.get("i", interval),
                        "open": float(kline.get("o", 0)),
                        "high": float(kline.get("h", 0)),
                        "low": float(kline.get("l", 0)),
                        "close": float(kline.get("c", 0)),
                        "volume": float(kline.get("v", 0)),
                        "is_closed": kline.get("x", False),
                        "timestamp": datetime.now(),
                    }
                    await callback(candle)
        except Exception as e:
            logger.error(f"❌ WebSocket kline error {symbol}: {e}")
