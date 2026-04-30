"""
KTSTOCK - Unit Tests: Data Connectors
Test các connectors (vnstock Free, Sponsored, Binance).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd


# ============================================================
# Test VnstockFreeConnector
# ============================================================
class TestVnstockFreeConnector:
    """Test vnstock Free connector."""

    def test_connect_success(self):
        """Test kết nối thành công khi vnstock installed."""
        from src.data.connectors.vnstock_connector import VnstockFreeConnector
        connector = VnstockFreeConnector(source="VCI")
        # Chỉ test nếu vnstock installed
        result = connector.connect()
        if result:
            assert connector.is_connected is True
            assert connector.name == "vnstock_free"

    def test_normalize_columns(self):
        """Test chuẩn hóa tên columns."""
        from src.data.connectors.vnstock_connector import VnstockFreeConnector
        connector = VnstockFreeConnector()
        df = pd.DataFrame({
            "time": ["2024-01-01"],
            "Open": [25.0],
            "High": [26.0],
            "Low": [24.0],
            "Close": [25.5],
            "Volume": [1000000],
        })
        result = connector._normalize_columns(df)
        assert "date" in result.columns
        assert "open" in result.columns
        assert "close" in result.columns

    def test_search_symbols_empty(self):
        """Test tìm kiếm khi chưa có listing."""
        from src.data.connectors.vnstock_connector import VnstockFreeConnector
        connector = VnstockFreeConnector()
        # Không connect nên listing rỗng
        results = connector.search_symbols("VCB")
        assert isinstance(results, list)


# ============================================================
# Test VnstockSponsoredConnector
# ============================================================
class TestVnstockSponsoredConnector:
    """Test vnstock_data Sponsored connector."""

    def test_init(self):
        """Test khởi tạo connector."""
        from src.data.connectors.vnstock_pro_connector import VnstockSponsoredConnector
        connector = VnstockSponsoredConnector(source="VCI")
        assert connector.name == "vnstock_sponsored"
        assert connector.source == "VCI"

    def test_normalize_columns(self):
        """Test chuẩn hóa columns."""
        from src.data.connectors.vnstock_pro_connector import VnstockSponsoredConnector
        connector = VnstockSponsoredConnector()
        df = pd.DataFrame({
            "TradingDate": ["2024-01-01"],
            "Open": [100.0],
        })
        result = connector._normalize_columns(df)
        assert "date" in result.columns
        assert "open" in result.columns


# ============================================================
# Test BinanceConnector
# ============================================================
class TestBinanceConnector:
    """Test Binance connector."""

    def test_init(self):
        """Test khởi tạo."""
        from src.data.connectors.crypto_connector import BinanceConnector
        connector = BinanceConnector()
        assert connector.name == "binance"

    def test_interval_mapping(self):
        """Test interval mapping."""
        from src.data.connectors.crypto_connector import BinanceConnector
        connector = BinanceConnector()
        assert connector.INTERVAL_MAP["1D"] == "1d"
        assert connector.INTERVAL_MAP["1H"] == "1h"
        assert connector.INTERVAL_MAP["5m"] == "5m"

    def test_health_check_no_connection(self):
        """Test health check khi chưa connect."""
        from src.data.connectors.crypto_connector import BinanceConnector
        connector = BinanceConnector()
        # Không connect, sẽ tự thử connect
        result = connector.health_check()
        assert "status" in result
        assert "message" in result


# ============================================================
# Test Pydantic Models
# ============================================================
class TestModels:
    """Test data models."""

    def test_stock_symbol(self):
        from src.data.models.stock import StockSymbol
        s = StockSymbol(symbol="VCB", name="Vietcombank", exchange="HOSE")
        assert s.symbol == "VCB"
        assert s.asset_type == "stock"

    def test_ohlcv_data(self):
        from src.data.models.stock import OHLCVData
        o = OHLCVData(symbol="VCB", date="2024-01-01", open=85.0, close=86.0, volume=1000000)
        assert o.close == 86.0

    def test_crypto_symbol(self):
        from src.data.models.crypto import CryptoSymbol
        c = CryptoSymbol(symbol="BTCUSDT", base_asset="BTC")
        assert c.exchange == "BINANCE"
        assert c.asset_type == "crypto"

    def test_position_profit_loss(self):
        from src.data.models.portfolio import PositionModel
        p = PositionModel(
            portfolio_id=1, symbol="VCB",
            quantity=100, avg_price=85.0, current_price=90.0
        )
        assert p.profit_loss == 500.0  # (90-85)*100
        assert p.profit_loss_pct == pytest.approx(0.0588, abs=0.001)

    def test_alert_model(self):
        from src.data.models.portfolio import AlertModel
        a = AlertModel(user_id=1, symbol="VCB", condition="price_above", threshold=100.0)
        assert a.is_active is True


# ============================================================
# Test Async Loader
# ============================================================
class TestAsyncLoader:
    """Test parallel/async data loading."""

    def test_load_parallel(self):
        """Test parallel loading."""
        from src.services.async_loader import AsyncDataLoader
        loader = AsyncDataLoader(max_workers=2)

        def double(x):
            return x * 2

        results = loader.load_parallel(double, [1, 2, 3, 4])
        assert results[1] == 2
        assert results[4] == 8
        loader.shutdown()

    def test_load_parallel_with_errors(self):
        """Test parallel loading với errors."""
        from src.services.async_loader import AsyncDataLoader
        loader = AsyncDataLoader(max_workers=2)

        def maybe_fail(x):
            if x == 3:
                raise ValueError("Test error")
            return x * 2

        results = loader.load_parallel(maybe_fail, [1, 2, 3, 4])
        assert results[1] == 2
        assert results[3] is None  # Failed
        assert results[4] == 8
        loader.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
