"""
KTSTOCK - Stock Screener
Bộ lọc cổ phiếu đa tiêu chí.
"""
from typing import Optional
import pandas as pd
import numpy as np
from loguru import logger

from src.utils.decorators import timer


class StockScreener:
    """
    Bộ lọc cổ phiếu theo nhiều tiêu chí.
    Hỗ trợ filter theo giá, khối lượng, chỉ số tài chính, kỹ thuật.
    """

    def __init__(self):
        self.filters: list[dict] = []

    def add_filter(
        self,
        column: str,
        operator: str,
        value: float,
        label: str = "",
    ) -> "StockScreener":
        """
        Thêm bộ lọc.

        Args:
            column: Tên cột để lọc
            operator: "gt", "gte", "lt", "lte", "eq", "between"
            value: Giá trị so sánh (hoặc tuple (min, max) cho between)
            label: Nhãn mô tả

        Returns:
            self (chaining)
        """
        self.filters.append({
            "column": column,
            "operator": operator,
            "value": value,
            "label": label or f"{column} {operator} {value}",
        })
        return self

    def clear_filters(self) -> "StockScreener":
        """Xóa tất cả bộ lọc."""
        self.filters = []
        return self

    @timer
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Áp dụng tất cả bộ lọc lên DataFrame.

        Args:
            df: DataFrame cần lọc

        Returns:
            DataFrame đã lọc
        """
        result = df.copy()
        initial_count = len(result)

        for f in self.filters:
            col = f["column"]
            op = f["operator"]
            val = f["value"]

            if col not in result.columns:
                logger.warning(f"⚠️ Column '{col}' not found, skipping filter")
                continue

            if op == "gt":
                result = result[result[col] > val]
            elif op == "gte":
                result = result[result[col] >= val]
            elif op == "lt":
                result = result[result[col] < val]
            elif op == "lte":
                result = result[result[col] <= val]
            elif op == "eq":
                result = result[result[col] == val]
            elif op == "between" and isinstance(val, (list, tuple)) and len(val) == 2:
                result = result[(result[col] >= val[0]) & (result[col] <= val[1])]

        logger.info(f"🔍 Screener: {initial_count} → {len(result)} ({len(self.filters)} filters)")
        return result

    def rank(
        self,
        df: pd.DataFrame,
        rank_by: str = "volume",
        ascending: bool = False,
        top_n: int = 20,
    ) -> pd.DataFrame:
        """
        Xếp hạng kết quả.

        Args:
            df: DataFrame
            rank_by: Cột để xếp hạng
            ascending: True = tăng dần
            top_n: Số kết quả trả về
        """
        if rank_by not in df.columns:
            return df.head(top_n)

        result = df.sort_values(rank_by, ascending=ascending).head(top_n)
        result = result.reset_index(drop=True)
        result.index = result.index + 1  # Rank từ 1
        result.index.name = "rank"
        return result

    # =========================================
    # Preset Filters (Bộ lọc có sẵn)
    # =========================================
    @classmethod
    def undervalued_stocks(cls) -> "StockScreener":
        """Preset: Cổ phiếu giá trị (undervalued)."""
        screener = cls()
        screener.add_filter("pe_ratio", "between", (0, 15), "P/E < 15")
        screener.add_filter("pb_ratio", "between", (0, 1.5), "P/B < 1.5")
        screener.add_filter("roe", "gt", 10, "ROE > 10%")
        return screener

    @classmethod
    def growth_stocks(cls) -> "StockScreener":
        """Preset: Cổ phiếu tăng trưởng."""
        screener = cls()
        screener.add_filter("revenue_growth", "gt", 15, "Tăng trưởng DT > 15%")
        screener.add_filter("earnings_growth", "gt", 20, "Tăng trưởng LN > 20%")
        screener.add_filter("roe", "gt", 15, "ROE > 15%")
        return screener

    @classmethod
    def high_dividend(cls) -> "StockScreener":
        """Preset: Cổ phiếu cổ tức cao."""
        screener = cls()
        screener.add_filter("dividend_yield", "gt", 5, "Cổ tức > 5%")
        screener.add_filter("payout_ratio", "between", (20, 80), "Payout 20-80%")
        return screener

    @classmethod
    def momentum_stocks(cls) -> "StockScreener":
        """Preset: Cổ phiếu momentum."""
        screener = cls()
        screener.add_filter("rsi", "between", (50, 70), "RSI 50-70")
        screener.add_filter("volume", "gt", 1000000, "Volume > 1M")
        return screener

    @classmethod
    def volume_breakout(cls) -> "StockScreener":
        """Preset: Đột biến khối lượng."""
        screener = cls()
        screener.add_filter("volume_ratio", "gt", 2.0, "Volume ratio > 2x")
        return screener
