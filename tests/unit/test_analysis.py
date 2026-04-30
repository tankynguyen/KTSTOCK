"""
KTSTOCK - Unit Tests: Analysis Engine (Phase 3)
Test Technical, Fundamental, Screener, Portfolio, Alerts, Sentiment.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
import pandas as pd
import numpy as np


# ============================================================
# Helper: Tạo dữ liệu OHLCV mẫu
# ============================================================
def make_ohlcv(n: int = 100) -> pd.DataFrame:
    """Tạo DataFrame OHLCV mẫu."""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    return pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "open": close - np.random.rand(n) * 0.5,
        "high": close + np.random.rand(n) * 1.0,
        "low": close - np.random.rand(n) * 1.0,
        "close": close,
        "volume": np.random.randint(500000, 5000000, n),
    })


# ============================================================
# Test Technical Analysis
# ============================================================
class TestTechnicalAnalysis:
    """Test engine phân tích kỹ thuật."""

    def setup_method(self):
        from src.core.analysis.technical import TechnicalAnalysis
        self.df = make_ohlcv(200)
        self.ta = TechnicalAnalysis(self.df)

    def test_sma(self):
        sma = self.ta.sma(20)
        assert len(sma) == 200
        assert not sma.isna().all()

    def test_ema(self):
        ema = self.ta.ema(12)
        assert len(ema) == 200
        # EMA should never be all NaN
        assert ema.notna().sum() > 0

    def test_rsi(self):
        rsi = self.ta.rsi(14)
        # RSI should be between 0 and 100
        valid_rsi = rsi.dropna()
        assert valid_rsi.min() >= 0
        assert valid_rsi.max() <= 100

    def test_macd(self):
        result = self.ta.macd()
        assert "macd" in result
        assert "signal" in result
        assert "histogram" in result
        assert len(result["macd"]) == 200

    def test_bollinger_bands(self):
        bb = self.ta.bollinger_bands(20)
        assert "upper" in bb
        assert "middle" in bb
        assert "lower" in bb
        # Upper should always >= Lower
        valid = bb["upper"].dropna().index
        assert (bb["upper"][valid] >= bb["lower"][valid]).all()

    def test_stochastic(self):
        stoch = self.ta.stochastic()
        assert "k" in stoch and "d" in stoch
        valid_k = stoch["k"].dropna()
        assert valid_k.min() >= 0
        assert valid_k.max() <= 100

    def test_adx(self):
        result = self.ta.adx()
        assert "adx" in result
        assert "di_plus" in result
        assert "di_minus" in result

    def test_atr(self):
        atr = self.ta.atr(14)
        assert len(atr) == 200
        assert atr.dropna().min() >= 0  # ATR always positive

    def test_ichimoku(self):
        ich = self.ta.ichimoku()
        assert "tenkan_sen" in ich
        assert "kijun_sen" in ich
        assert "senkou_a" in ich

    def test_obv(self):
        obv = self.ta.obv()
        assert len(obv) == 200

    def test_vwap(self):
        vwap = self.ta.vwap()
        assert len(vwap) == 200

    def test_calculate_all(self):
        """Test tính toàn bộ indicators."""
        result = self.ta.calculate_all()
        assert "sma_20" in result.columns
        assert "rsi" in result.columns
        assert "macd" in result.columns
        assert "bb_upper" in result.columns
        assert "adx" in result.columns
        assert "obv" in result.columns

    def test_generate_signals(self):
        """Test tạo tín hiệu giao dịch."""
        signals = self.ta.generate_signals()
        assert "signal" in signals
        assert "trend" in signals
        assert "confidence" in signals
        assert signals["signal"] in ["buy", "sell", "hold", "strong_buy", "strong_sell"]
        assert 0 <= signals["confidence"] <= 1


# ============================================================
# Test Fundamental Analysis
# ============================================================
class TestFundamentalAnalysis:
    """Test engine phân tích cơ bản."""

    def setup_method(self):
        from src.core.analysis.fundamental import FundamentalAnalysis
        self.fa = FundamentalAnalysis()

    def test_pe_ratio(self):
        assert self.fa.pe_ratio(100, 5) == 20.0
        assert self.fa.pe_ratio(100, 0) is None

    def test_pb_ratio(self):
        assert self.fa.pb_ratio(50, 25) == 2.0

    def test_roe(self):
        assert self.fa.roe(100, 500) == 20.0

    def test_roa(self):
        assert self.fa.roa(50, 1000) == 5.0

    def test_debt_to_equity(self):
        assert self.fa.debt_to_equity(200, 100) == 2.0

    def test_gross_margin(self):
        assert self.fa.gross_margin(30, 100) == 30.0

    def test_net_margin(self):
        assert self.fa.net_margin(10, 100) == 10.0

    def test_dcf_valuation(self):
        result = self.fa.dcf_valuation(
            free_cash_flows=[100, 110, 120],
            growth_rate=0.05,
            terminal_growth=0.02,
            discount_rate=0.10,
            shares_outstanding=100,
        )
        assert "intrinsic_value" in result
        assert result["intrinsic_value"] > 0
        assert "projected_fcf" in result
        assert len(result["projected_fcf"]) == 5  # 5 years

    def test_analyze(self):
        result = self.fa.analyze(
            current_price=85.0,
            financial_data={
                "eps": 5.0,
                "book_value_per_share": 40.0,
                "revenue": 10000,
                "net_income": 1500,
                "total_assets": 50000,
                "equity": 8000,
                "total_debt": 5000,
                "gross_profit": 3000,
                "market_cap": 50000,
                "current_assets": 8000,
                "current_liabilities": 4000,
            }
        )
        assert "valuation" in result
        assert "profitability" in result
        assert "assessment" in result
        assert result["valuation"]["pe_ratio"] == 17.0


# ============================================================
# Test Stock Screener
# ============================================================
class TestStockScreener:
    """Test bộ lọc cổ phiếu."""

    def setup_method(self):
        from src.core.screener.filters import StockScreener
        self.screener = StockScreener()

    def test_add_filter(self):
        self.screener.add_filter("pe_ratio", "lt", 20)
        assert len(self.screener.filters) == 1

    def test_filter_chaining(self):
        result = self.screener.add_filter("pe_ratio", "lt", 20).add_filter("roe", "gt", 10)
        assert len(self.screener.filters) == 2
        assert result is self.screener  # fluent API

    def test_apply_filters(self):
        df = pd.DataFrame({
            "symbol": ["A", "B", "C", "D"],
            "pe_ratio": [10, 20, 5, 30],
            "roe": [15, 8, 20, 12],
        })
        self.screener.add_filter("pe_ratio", "lt", 15).add_filter("roe", "gt", 10)
        result = self.screener.apply(df)
        assert len(result) == 2  # A(10,15) and C(5,20)

    def test_between_filter(self):
        df = pd.DataFrame({"rsi": [20, 45, 55, 80]})
        self.screener.add_filter("rsi", "between", (30, 70))
        result = self.screener.apply(df)
        assert len(result) == 2  # 45 and 55

    def test_rank(self):
        df = pd.DataFrame({
            "symbol": ["A", "B", "C"],
            "volume": [1000, 3000, 2000],
        })
        ranked = self.screener.rank(df, rank_by="volume", top_n=2)
        assert len(ranked) == 2
        assert ranked.iloc[0]["symbol"] == "B"

    def test_presets(self):
        from src.core.screener.filters import StockScreener
        undervalued = StockScreener.undervalued_stocks()
        assert len(undervalued.filters) == 3
        growth = StockScreener.growth_stocks()
        assert len(growth.filters) == 3


# ============================================================
# Test Sentiment Analysis
# ============================================================
class TestSentimentAnalysis:
    """Test phân tích cảm xúc."""

    def setup_method(self):
        from src.core.analysis.sentiment import SentimentAnalyzer
        self.sa = SentimentAnalyzer()

    def test_positive_text_vi(self):
        result = self.sa.analyze_text("VCB tăng mạnh, lợi nhuận tăng vượt kỳ vọng", "vi")
        assert result["sentiment"] == "positive"
        assert result["score"] > 0

    def test_negative_text_vi(self):
        result = self.sa.analyze_text("Cổ phiếu giảm mạnh, thua lỗ, rủi ro cao", "vi")
        assert result["sentiment"] == "negative"
        assert result["score"] < 0

    def test_neutral_text(self):
        result = self.sa.analyze_text("Hôm nay thời tiết đẹp", "vi")
        assert result["sentiment"] == "neutral"

    def test_english_sentiment(self):
        result = self.sa.analyze_text("Strong bullish rally, growth exceeds expectations", "en")
        assert result["sentiment"] == "positive"

    def test_batch_analysis(self):
        texts = [
            "VCB tăng mạnh hôm nay",
            "Thị trường giảm sàn, bán tháo",
            "Một ngày giao dịch bình thường",
        ]
        result = self.sa.analyze_batch(texts, "vi")
        assert result["total_texts"] == 3
        assert "positive" in result["distribution"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
