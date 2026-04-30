"""
KTSTOCK - vnstock_ta Technical Analysis Connector
Wrapper cho vnstock_ta - 25+ chỉ báo kỹ thuật.
"""
from typing import Optional

import pandas as pd
from loguru import logger

from src.utils.decorators import timer


class VnstockTAConnector:
    """
    Connector cho vnstock_ta - 25+ Technical Indicators.

    Trend (8): SMA, EMA, VWAP, VWMA, ADX, AROON, PSAR, SUPERTREND
    Momentum (7): RSI, MACD, WILLR, CMO, STOCH, ROC, MOM
    Volatility (5): BBANDS, KC, ATR, STDEV, LINREG
    Volume (1): OBV
    """

    def __init__(self):
        self._available = False
        try:
            from vnstock_ta import Indicator
            self._Indicator = Indicator
            self._available = True
            logger.info("✅ vnstock_ta connector initialized")
        except ImportError:
            logger.warning("⚠️ vnstock_ta not installed. TA features unavailable.")

    @property
    def is_available(self) -> bool:
        return self._available

    def _get_indicator(self, df: pd.DataFrame):
        """Tạo Indicator object từ DataFrame OHLCV."""
        if not self._available:
            raise ImportError("vnstock_ta not installed")
        # Ensure DatetimeIndex
        work_df = df.copy()
        if 'time' in work_df.columns:
            work_df = work_df.set_index('time')
        elif 'date' in work_df.columns:
            work_df = work_df.set_index('date')
        if not isinstance(work_df.index, pd.DatetimeIndex):
            work_df.index = pd.to_datetime(work_df.index)
        return self._Indicator(data=work_df), work_df

    # ============================================================
    # TREND INDICATORS
    # ============================================================

    @timer
    def sma(self, df: pd.DataFrame, length: int = 20) -> Optional[pd.Series]:
        """Simple Moving Average."""
        try:
            indicator, _ = self._get_indicator(df)
            return indicator.sma(length=length)
        except Exception as e:
            logger.error(f"❌ SMA error: {e}")
            return None

    @timer
    def ema(self, df: pd.DataFrame, length: int = 20) -> Optional[pd.Series]:
        """Exponential Moving Average."""
        try:
            indicator, _ = self._get_indicator(df)
            return indicator.ema(length=length)
        except Exception as e:
            logger.error(f"❌ EMA error: {e}")
            return None

    @timer
    def vwap(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """Volume Weighted Average Price."""
        try:
            indicator, _ = self._get_indicator(df)
            return indicator.vwap()
        except Exception as e:
            logger.error(f"❌ VWAP error: {e}")
            return None

    @timer
    def vwma(self, df: pd.DataFrame, length: int = 20) -> Optional[pd.Series]:
        """Volume Weighted Moving Average."""
        try:
            indicator, _ = self._get_indicator(df)
            return indicator.vwma(length=length)
        except Exception as e:
            logger.error(f"❌ VWMA error: {e}")
            return None

    @timer
    def adx(self, df: pd.DataFrame, length: int = 14) -> Optional[pd.DataFrame]:
        """Average Directional Index. Returns: ADX, +DI, -DI."""
        try:
            indicator, _ = self._get_indicator(df)
            return indicator.adx(length=length)
        except Exception as e:
            logger.error(f"❌ ADX error: {e}")
            return None

    @timer
    def aroon(self, df: pd.DataFrame, length: int = 25) -> Optional[pd.DataFrame]:
        """Aroon Indicator. Returns: Aroon Up, Aroon Down, Aroon Osc."""
        try:
            indicator, _ = self._get_indicator(df)
            return indicator.aroon(length=length)
        except Exception as e:
            logger.error(f"❌ AROON error: {e}")
            return None

    @timer
    def psar(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Parabolic SAR."""
        try:
            indicator, _ = self._get_indicator(df)
            return indicator.psar()
        except Exception as e:
            logger.error(f"❌ PSAR error: {e}")
            return None

    @timer
    def supertrend(self, df: pd.DataFrame, length: int = 10, multiplier: float = 3.0) -> Optional[pd.DataFrame]:
        """SuperTrend Indicator."""
        try:
            indicator, _ = self._get_indicator(df)
            return indicator.supertrend(length=length, multiplier=multiplier)
        except Exception as e:
            logger.error(f"❌ SuperTrend error: {e}")
            return None

    # ============================================================
    # MOMENTUM INDICATORS
    # ============================================================

    @timer
    def rsi(self, df: pd.DataFrame, length: int = 14) -> Optional[pd.Series]:
        """Relative Strength Index."""
        try:
            indicator, _ = self._get_indicator(df)
            return indicator.rsi(length=length)
        except Exception as e:
            logger.error(f"❌ RSI error: {e}")
            return None

    @timer
    def macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Optional[pd.DataFrame]:
        """Moving Average Convergence Divergence."""
        try:
            indicator, _ = self._get_indicator(df)
            return indicator.macd(fast=fast, slow=slow, signal=signal)
        except Exception as e:
            logger.error(f"❌ MACD error: {e}")
            return None

    @timer
    def willr(self, df: pd.DataFrame, length: int = 14) -> Optional[pd.Series]:
        """Williams %R."""
        try:
            indicator, _ = self._get_indicator(df)
            return indicator.willr(length=length)
        except Exception as e:
            logger.error(f"❌ Williams %R error: {e}")
            return None

    @timer
    def cmo(self, df: pd.DataFrame, length: int = 14) -> Optional[pd.Series]:
        """Chande Momentum Oscillator."""
        try:
            indicator, _ = self._get_indicator(df)
            return indicator.cmo(length=length)
        except Exception as e:
            logger.error(f"❌ CMO error: {e}")
            return None

    @timer
    def stoch(self, df: pd.DataFrame, k: int = 14, d: int = 3) -> Optional[pd.DataFrame]:
        """Stochastic Oscillator."""
        try:
            indicator, _ = self._get_indicator(df)
            return indicator.stoch(k=k, d=d)
        except Exception as e:
            logger.error(f"❌ Stochastic error: {e}")
            return None

    @timer
    def roc(self, df: pd.DataFrame, length: int = 10) -> Optional[pd.Series]:
        """Rate of Change."""
        try:
            indicator, _ = self._get_indicator(df)
            return indicator.roc(length=length)
        except Exception as e:
            logger.error(f"❌ ROC error: {e}")
            return None

    @timer
    def mom(self, df: pd.DataFrame, length: int = 10) -> Optional[pd.Series]:
        """Momentum."""
        try:
            indicator, _ = self._get_indicator(df)
            return indicator.mom(length=length)
        except Exception as e:
            logger.error(f"❌ Momentum error: {e}")
            return None

    # ============================================================
    # VOLATILITY INDICATORS
    # ============================================================

    @timer
    def bbands(self, df: pd.DataFrame, length: int = 20, std: float = 2.0) -> Optional[pd.DataFrame]:
        """Bollinger Bands. Returns: BBL, BBM, BBU, BBB, BBP."""
        try:
            indicator, _ = self._get_indicator(df)
            return indicator.bbands(length=length, std=std)
        except Exception as e:
            logger.error(f"❌ Bollinger Bands error: {e}")
            return None

    @timer
    def kc(self, df: pd.DataFrame, length: int = 20, multiplier: float = 1.5) -> Optional[pd.DataFrame]:
        """Keltner Channel. Returns: KCL, KCM, KCU."""
        try:
            indicator, _ = self._get_indicator(df)
            return indicator.kc(length=length, multiplier=multiplier)
        except Exception as e:
            logger.error(f"❌ Keltner Channel error: {e}")
            return None

    @timer
    def atr(self, df: pd.DataFrame, length: int = 14) -> Optional[pd.Series]:
        """Average True Range."""
        try:
            indicator, _ = self._get_indicator(df)
            return indicator.atr(length=length)
        except Exception as e:
            logger.error(f"❌ ATR error: {e}")
            return None

    @timer
    def stdev(self, df: pd.DataFrame, length: int = 20) -> Optional[pd.Series]:
        """Standard Deviation."""
        try:
            indicator, _ = self._get_indicator(df)
            return indicator.stdev(length=length)
        except Exception as e:
            logger.error(f"❌ STDEV error: {e}")
            return None

    @timer
    def linreg(self, df: pd.DataFrame, length: int = 14) -> Optional[pd.Series]:
        """Linear Regression."""
        try:
            indicator, _ = self._get_indicator(df)
            return indicator.linreg(length=length)
        except Exception as e:
            logger.error(f"❌ Linear Regression error: {e}")
            return None

    # ============================================================
    # VOLUME INDICATORS
    # ============================================================

    @timer
    def obv(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """On-Balance Volume."""
        try:
            indicator, _ = self._get_indicator(df)
            return indicator.obv()
        except Exception as e:
            logger.error(f"❌ OBV error: {e}")
            return None

    # ============================================================
    # HELPER / COMPOSITE METHODS
    # ============================================================

    @timer
    def calculate_all(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Tính tất cả chỉ báo cùng lúc và merge vào DataFrame gốc.

        Returns:
            DataFrame gốc + tất cả cột chỉ báo
        """
        if not self._available:
            return df

        try:
            result = df.copy()
            indicator, work_df = self._get_indicator(df)

            # Trend
            result['SMA_20'] = indicator.sma(length=20).values if len(df) >= 20 else None
            result['EMA_20'] = indicator.ema(length=20).values if len(df) >= 20 else None

            # Momentum
            result['RSI_14'] = indicator.rsi(length=14).values if len(df) >= 14 else None

            macd_df = indicator.macd() if len(df) >= 26 else None
            if macd_df is not None:
                for col in macd_df.columns:
                    result[f'MACD_{col}'] = macd_df[col].values

            # Volatility
            bb_df = indicator.bbands(length=20, std=2) if len(df) >= 20 else None
            if bb_df is not None:
                for col in bb_df.columns:
                    result[f'BB_{col}'] = bb_df[col].values

            result['ATR_14'] = indicator.atr(length=14).values if len(df) >= 14 else None

            # Volume
            result['OBV'] = indicator.obv().values

            logger.info(f"📊 Calculated all indicators: {len(result.columns)} columns")
            return result
        except Exception as e:
            logger.error(f"❌ Error calculating all indicators: {e}")
            return df

    @timer
    def get_signals(self, df: pd.DataFrame) -> dict:
        """
        Phát sinh tín hiệu mua/bán từ các chỉ báo.

        Returns:
            dict với keys: rsi_signal, macd_signal, bb_signal, overall
        """
        signals = {
            "rsi_signal": "neutral",
            "macd_signal": "neutral",
            "bb_signal": "neutral",
            "supertrend_signal": "neutral",
            "overall": "neutral",
        }

        if not self._available or df is None or df.empty:
            return signals

        try:
            indicator, work_df = self._get_indicator(df)

            # RSI Signal
            rsi_val = indicator.rsi(length=14)
            if rsi_val is not None and len(rsi_val.dropna()) > 0:
                last_rsi = rsi_val.dropna().iloc[-1]
                if last_rsi > 70:
                    signals["rsi_signal"] = "overbought"
                elif last_rsi < 30:
                    signals["rsi_signal"] = "oversold"

            # MACD Signal
            if len(df) >= 26:
                macd_df = indicator.macd()
                if macd_df is not None and not macd_df.empty:
                    cols = macd_df.columns.tolist()
                    if len(cols) >= 2:
                        last_macd = macd_df[cols[0]].dropna().iloc[-1] if len(macd_df[cols[0]].dropna()) > 0 else 0
                        last_signal = macd_df[cols[1]].dropna().iloc[-1] if len(macd_df[cols[1]].dropna()) > 0 else 0
                        if last_macd > last_signal:
                            signals["macd_signal"] = "bullish"
                        else:
                            signals["macd_signal"] = "bearish"

            # Bollinger Bands Signal
            if len(df) >= 20:
                bb_df = indicator.bbands(length=20, std=2)
                if bb_df is not None and not bb_df.empty:
                    cols = bb_df.columns.tolist()
                    last_close = work_df['close'].iloc[-1] if 'close' in work_df.columns else None
                    if last_close and len(cols) >= 3:
                        bbl = bb_df[cols[0]].dropna().iloc[-1]
                        bbu = bb_df[cols[2]].dropna().iloc[-1]
                        if last_close < bbl:
                            signals["bb_signal"] = "oversold"
                        elif last_close > bbu:
                            signals["bb_signal"] = "overbought"

            # Overall
            buy_signals = sum(1 for v in signals.values() if v in ["oversold", "bullish"])
            sell_signals = sum(1 for v in signals.values() if v in ["overbought", "bearish"])

            if buy_signals >= 2:
                signals["overall"] = "buy"
            elif sell_signals >= 2:
                signals["overall"] = "sell"
            else:
                signals["overall"] = "hold"

        except Exception as e:
            logger.error(f"❌ Error generating signals: {e}")

        return signals
