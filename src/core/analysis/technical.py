"""
KTSTOCK - Technical Analysis Engine
Tính toán các chỉ báo kỹ thuật: RSI, MACD, Bollinger, Ichimoku, SMA/EMA, Stochastic, ADX...
"""
from typing import Optional
import pandas as pd
import numpy as np
from loguru import logger

from src.utils.constants import TrendDirection, SignalType
from src.utils.decorators import timer


class TechnicalAnalysis:
    """
    Engine phân tích kỹ thuật.
    Nhận DataFrame OHLCV và tính toán tất cả indicators.
    """

    def __init__(self, df: pd.DataFrame):
        """
        Args:
            df: DataFrame với columns: date, open, high, low, close, volume
        """
        self.df = df.copy()
        self._ensure_columns()

    def _ensure_columns(self):
        """Đảm bảo columns cần thiết tồn tại."""
        required = ["close"]
        for col in required:
            if col not in self.df.columns:
                raise ValueError(f"Missing required column: {col}")
        # Convert to numeric
        for col in ["open", "high", "low", "close", "volume"]:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors="coerce")

    # =========================================
    # Moving Averages
    # =========================================
    def sma(self, period: int = 20, column: str = "close") -> pd.Series:
        """Simple Moving Average."""
        return self.df[column].rolling(window=period, min_periods=1).mean()

    def ema(self, period: int = 20, column: str = "close") -> pd.Series:
        """Exponential Moving Average."""
        return self.df[column].ewm(span=period, adjust=False).mean()

    def wma(self, period: int = 20, column: str = "close") -> pd.Series:
        """Weighted Moving Average."""
        weights = np.arange(1, period + 1)
        return self.df[column].rolling(window=period).apply(
            lambda x: np.dot(x, weights) / weights.sum(), raw=True
        )

    # =========================================
    # RSI (Relative Strength Index)
    # =========================================
    def rsi(self, period: int = 14) -> pd.Series:
        """RSI - Chỉ số sức mạnh tương đối."""
        delta = self.df["close"].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)

        avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
        avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))

    # =========================================
    # MACD
    # =========================================
    def macd(self, fast: int = 12, slow: int = 26, signal: int = 9) -> dict[str, pd.Series]:
        """
        MACD - Moving Average Convergence Divergence.

        Returns:
            {"macd": Series, "signal": Series, "histogram": Series}
        """
        ema_fast = self.ema(fast)
        ema_slow = self.ema(slow)
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return {"macd": macd_line, "signal": signal_line, "histogram": histogram}

    # =========================================
    # Bollinger Bands
    # =========================================
    def bollinger_bands(self, period: int = 20, std_dev: float = 2.0) -> dict[str, pd.Series]:
        """
        Bollinger Bands.

        Returns:
            {"upper": Series, "middle": Series, "lower": Series, "bandwidth": Series}
        """
        middle = self.sma(period)
        std = self.df["close"].rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        bandwidth = (upper - lower) / middle * 100

        return {"upper": upper, "middle": middle, "lower": lower, "bandwidth": bandwidth}

    # =========================================
    # Stochastic Oscillator
    # =========================================
    def stochastic(self, k_period: int = 14, d_period: int = 3) -> dict[str, pd.Series]:
        """
        Stochastic Oscillator (%K và %D).

        Returns:
            {"k": Series, "d": Series}
        """
        low_min = self.df["low"].rolling(window=k_period).min()
        high_max = self.df["high"].rolling(window=k_period).max()

        k = 100 * (self.df["close"] - low_min) / (high_max - low_min).replace(0, np.nan)
        d = k.rolling(window=d_period).mean()

        return {"k": k, "d": d}

    # =========================================
    # ADX (Average Directional Index)
    # =========================================
    def adx(self, period: int = 14) -> dict[str, pd.Series]:
        """
        ADX - Đo sức mạnh xu hướng.

        Returns:
            {"adx": Series, "di_plus": Series, "di_minus": Series}
        """
        high = self.df["high"]
        low = self.df["low"]
        close = self.df["close"]

        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)

        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs()
        ], axis=1).max(axis=1)

        atr = tr.ewm(span=period, adjust=False).mean()
        di_plus = 100 * plus_dm.ewm(span=period, adjust=False).mean() / atr.replace(0, np.nan)
        di_minus = 100 * minus_dm.ewm(span=period, adjust=False).mean() / atr.replace(0, np.nan)

        dx = 100 * (di_plus - di_minus).abs() / (di_plus + di_minus).replace(0, np.nan)
        adx_val = dx.ewm(span=period, adjust=False).mean()

        return {"adx": adx_val, "di_plus": di_plus, "di_minus": di_minus}

    # =========================================
    # ATR (Average True Range)
    # =========================================
    def atr(self, period: int = 14) -> pd.Series:
        """ATR - Đo biến động."""
        high = self.df["high"]
        low = self.df["low"]
        close = self.df["close"]

        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs()
        ], axis=1).max(axis=1)

        return tr.ewm(span=period, adjust=False).mean()

    # =========================================
    # Ichimoku Cloud
    # =========================================
    def ichimoku(
        self, tenkan: int = 9, kijun: int = 26, senkou_b: int = 52
    ) -> dict[str, pd.Series]:
        """
        Ichimoku Kinko Hyo.

        Returns:
            {"tenkan_sen", "kijun_sen", "senkou_a", "senkou_b", "chikou_span"}
        """
        high = self.df["high"]
        low = self.df["low"]

        tenkan_sen = (high.rolling(tenkan).max() + low.rolling(tenkan).min()) / 2
        kijun_sen = (high.rolling(kijun).max() + low.rolling(kijun).min()) / 2
        senkou_a = ((tenkan_sen + kijun_sen) / 2).shift(kijun)
        senkou_b_val = ((high.rolling(senkou_b).max() + low.rolling(senkou_b).min()) / 2).shift(kijun)
        chikou_span = self.df["close"].shift(-kijun)

        return {
            "tenkan_sen": tenkan_sen,
            "kijun_sen": kijun_sen,
            "senkou_a": senkou_a,
            "senkou_b": senkou_b_val,
            "chikou_span": chikou_span,
        }

    # =========================================
    # Volume Indicators
    # =========================================
    def obv(self) -> pd.Series:
        """On Balance Volume."""
        sign = np.sign(self.df["close"].diff()).fillna(0)
        return (sign * self.df["volume"]).cumsum()

    def vwap(self) -> pd.Series:
        """Volume Weighted Average Price."""
        typical_price = (self.df["high"] + self.df["low"] + self.df["close"]) / 3
        cumulative_tp_vol = (typical_price * self.df["volume"]).cumsum()
        cumulative_vol = self.df["volume"].cumsum()
        return cumulative_tp_vol / cumulative_vol.replace(0, np.nan)

    # =========================================
    # Tính tất cả indicators
    # =========================================
    @timer
    def calculate_all(self) -> pd.DataFrame:
        """Tính toàn bộ indicators và thêm vào DataFrame."""
        df = self.df.copy()

        # Moving Averages
        df["sma_20"] = self.sma(20)
        df["sma_50"] = self.sma(50)
        df["sma_200"] = self.sma(200)
        df["ema_12"] = self.ema(12)
        df["ema_26"] = self.ema(26)

        # RSI
        df["rsi"] = self.rsi(14)

        # MACD
        macd_data = self.macd()
        df["macd"] = macd_data["macd"]
        df["macd_signal"] = macd_data["signal"]
        df["macd_hist"] = macd_data["histogram"]

        # Bollinger
        bb = self.bollinger_bands()
        df["bb_upper"] = bb["upper"]
        df["bb_middle"] = bb["middle"]
        df["bb_lower"] = bb["lower"]

        # Stochastic
        stoch = self.stochastic()
        df["stoch_k"] = stoch["k"]
        df["stoch_d"] = stoch["d"]

        # ADX
        adx_data = self.adx()
        df["adx"] = adx_data["adx"]

        # ATR
        df["atr"] = self.atr()

        # Volume
        df["obv"] = self.obv()
        df["vwap"] = self.vwap()
        df["vol_sma_20"] = self.df["volume"].rolling(20).mean()

        return df

    # =========================================
    # Tín hiệu giao dịch
    # =========================================
    def generate_signals(self) -> dict:
        """
        Tạo tín hiệu giao dịch tổng hợp.

        Returns:
            {"signal": str, "trend": str, "confidence": float, "details": list}
        """
        df = self.calculate_all()
        last = df.iloc[-1]
        signals = []
        score = 0  # -5 to +5

        # RSI signals
        rsi_val = last.get("rsi", 50)
        if rsi_val < 30:
            signals.append(("RSI", "oversold", "buy"))
            score += 1
        elif rsi_val > 70:
            signals.append(("RSI", "overbought", "sell"))
            score -= 1

        # MACD signals
        if last.get("macd_hist", 0) > 0 and df["macd_hist"].iloc[-2] <= 0:
            signals.append(("MACD", "bullish crossover", "buy"))
            score += 1
        elif last.get("macd_hist", 0) < 0 and df["macd_hist"].iloc[-2] >= 0:
            signals.append(("MACD", "bearish crossover", "sell"))
            score -= 1

        # SMA signals
        close = last["close"]
        if close > last.get("sma_50", close) > last.get("sma_200", close):
            signals.append(("SMA", "golden cross area", "buy"))
            score += 1
        elif close < last.get("sma_50", close) < last.get("sma_200", close):
            signals.append(("SMA", "death cross area", "sell"))
            score -= 1

        # Bollinger signals
        if close <= last.get("bb_lower", close):
            signals.append(("Bollinger", "near lower band", "buy"))
            score += 1
        elif close >= last.get("bb_upper", close):
            signals.append(("Bollinger", "near upper band", "sell"))
            score -= 1

        # ADX trend strength
        adx_val = last.get("adx", 20)
        if adx_val > 25:
            signals.append(("ADX", f"strong trend ({adx_val:.0f})", "info"))

        # Determine overall signal
        if score >= 3:
            signal = SignalType.STRONG_BUY.value
            trend = TrendDirection.STRONG_BULLISH.value
        elif score >= 1:
            signal = SignalType.BUY.value
            trend = TrendDirection.BULLISH.value
        elif score <= -3:
            signal = SignalType.STRONG_SELL.value
            trend = TrendDirection.STRONG_BEARISH.value
        elif score <= -1:
            signal = SignalType.SELL.value
            trend = TrendDirection.BEARISH.value
        else:
            signal = SignalType.HOLD.value
            trend = TrendDirection.NEUTRAL.value

        confidence = min(abs(score) / 5.0, 1.0)

        return {
            "signal": signal,
            "trend": trend,
            "confidence": round(confidence, 2),
            "score": score,
            "details": signals,
            "rsi": round(rsi_val, 2) if not pd.isna(rsi_val) else None,
            "macd_hist": round(last.get("macd_hist", 0), 4),
            "adx": round(adx_val, 2) if not pd.isna(adx_val) else None,
        }
