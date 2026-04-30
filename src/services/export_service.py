"""
KTSTOCK - Export Service
Xuất dữ liệu ra Excel và CSV.
"""
import io
from typing import Optional
from datetime import datetime

import pandas as pd
from loguru import logger


class ExportService:
    """Dịch vụ xuất dữ liệu ra các định dạng khác nhau."""

    @staticmethod
    def to_excel(df: pd.DataFrame, sheet_name: str = "Data") -> bytes:
        """
        Xuất DataFrame ra Excel (.xlsx).

        Returns:
            bytes content của file Excel
        """
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        output.seek(0)
        return output.getvalue()

    @staticmethod
    def to_csv(df: pd.DataFrame) -> str:
        """Xuất DataFrame ra CSV string."""
        return df.to_csv(index=False)

    @staticmethod
    def to_excel_multi(
        sheets: dict[str, pd.DataFrame],
        filename_prefix: str = "ktstock_report",
    ) -> bytes:
        """
        Xuất nhiều sheets ra 1 file Excel.

        Args:
            sheets: {"Sheet Name": DataFrame, ...}
        """
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            for name, df in sheets.items():
                df.to_excel(writer, sheet_name=name[:31], index=False)
        output.seek(0)
        return output.getvalue()

    @staticmethod
    def generate_filename(prefix: str = "ktstock", ext: str = "xlsx") -> str:
        """Tạo tên file với timestamp."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{ts}.{ext}"
