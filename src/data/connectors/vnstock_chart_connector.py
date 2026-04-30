"""
KTSTOCK - vnstock_chart Connector
Biểu đồ chuyên nghiệp dựa trên pyecharts cho Streamlit.
"""
from typing import Optional

import pandas as pd
from loguru import logger

from src.utils.decorators import timer


class VnstockChartConnector:
    """
    Connector cho vnstock_chart - Biểu đồ chuyên nghiệp.

    Chart Types:
    - CandlestickChart: Biểu đồ nến OHLC
    - LineChart: Biểu đồ đường
    - BarChart: Biểu đồ cột
    - Performance Dashboard
    - Risk Analysis
    """

    def __init__(self, theme: str = "dark"):
        self._available = False
        self.theme = theme
        try:
            import vnstock_chart
            self._vnstock_chart = vnstock_chart
            self._available = True
            logger.info("✅ vnstock_chart connector initialized")
        except ImportError:
            logger.warning("⚠️ vnstock_chart not installed. Chart features unavailable.")

    @property
    def is_available(self) -> bool:
        return self._available

    # ============================================================
    # BASIC CHARTS
    # ============================================================

    @timer
    def create_candlestick(
        self,
        df: pd.DataFrame,
        title: str = "Biểu Đồ Nến",
        size_preset: str = "large"
    ) -> Optional[str]:
        """
        Tạo biểu đồ nến OHLC.

        Args:
            df: DataFrame với columns: time/date, open, high, low, close, volume
            title: Tiêu đề biểu đồ
            size_preset: "mini", "small", "medium", "large", "wide", "tall"

        Returns:
            HTML string để embed vào Streamlit
        """
        if not self._available:
            return None

        try:
            from vnstock_chart import CandlestickChart
            chart = CandlestickChart(
                data=self._prepare_data(df),
                title=title,
                theme=self.theme,
                size_preset=size_preset,
            )
            return chart.embed()
        except Exception as e:
            logger.error(f"❌ Candlestick chart error: {e}")
            return None

    @timer
    def create_line_chart(
        self,
        x: list,
        y: list,
        title: str = "Biểu Đồ Đường",
        size_preset: str = "medium"
    ) -> Optional[str]:
        """
        Tạo biểu đồ đường.

        Args:
            x: Danh sách giá trị trục x
            y: Danh sách giá trị trục y
            title: Tiêu đề
            size_preset: Preset kích thước

        Returns:
            HTML string
        """
        if not self._available:
            return None

        try:
            from vnstock_chart import LineChart
            chart = LineChart(
                x=x, y=y,
                title=title,
                theme=self.theme,
                size_preset=size_preset,
            )
            return chart.embed()
        except Exception as e:
            logger.error(f"❌ Line chart error: {e}")
            return None

    @timer
    def create_bar_chart(
        self,
        x: list,
        y: list,
        title: str = "Biểu Đồ Cột",
        size_preset: str = "medium"
    ) -> Optional[str]:
        """
        Tạo biểu đồ cột.

        Args:
            x: Danh sách giá trị trục x
            y: Danh sách giá trị trục y
            title: Tiêu đề
            size_preset: Preset kích thước

        Returns:
            HTML string
        """
        if not self._available:
            return None

        try:
            from vnstock_chart import BarChart
            chart = BarChart(
                x=x, y=y,
                title=title,
                theme=self.theme,
                size_preset=size_preset,
            )
            return chart.embed()
        except Exception as e:
            logger.error(f"❌ Bar chart error: {e}")
            return None

    # ============================================================
    # ADVANCED CHARTS
    # ============================================================

    @timer
    def create_performance_dashboard(
        self,
        df: pd.DataFrame,
        title: str = "Performance Dashboard",
        size_preset: str = "large"
    ) -> Optional[str]:
        """
        Tạo dashboard phân tích hiệu suất.

        Args:
            df: DataFrame OHLCV
            title: Tiêu đề
        """
        if not self._available:
            return None

        try:
            from vnstock_chart import PerformanceDashboard
            dashboard = PerformanceDashboard(
                data=self._prepare_data(df),
                title=title,
                theme=self.theme,
                size_preset=size_preset,
            )
            return dashboard.embed()
        except (ImportError, AttributeError):
            logger.warning("⚠️ PerformanceDashboard not available in this vnstock_chart version")
            return None
        except Exception as e:
            logger.error(f"❌ Performance dashboard error: {e}")
            return None

    @timer
    def create_risk_analysis(
        self,
        df: pd.DataFrame,
        title: str = "Risk Analysis",
        size_preset: str = "large"
    ) -> Optional[str]:
        """
        Tạo biểu đồ phân tích rủi ro.

        Args:
            df: DataFrame OHLCV
            title: Tiêu đề
        """
        if not self._available:
            return None

        try:
            from vnstock_chart import RiskAnalysis
            analysis = RiskAnalysis(
                data=self._prepare_data(df),
                title=title,
                theme=self.theme,
                size_preset=size_preset,
            )
            return analysis.embed()
        except (ImportError, AttributeError):
            logger.warning("⚠️ RiskAnalysis not available in this vnstock_chart version")
            return None
        except Exception as e:
            logger.error(f"❌ Risk analysis error: {e}")
            return None

    # ============================================================
    # EXPORT METHODS
    # ============================================================

    @timer
    def save_chart_html(
        self,
        chart_html: str,
        filepath: str,
        auto_open: bool = False
    ) -> bool:
        """
        Lưu biểu đồ thành file HTML.

        Args:
            chart_html: HTML string từ các method create_*
            filepath: Đường dẫn file (VD: "charts/vcb_candle.html")
            auto_open: Tự động mở trên browser
        """
        try:
            import os
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(chart_html)
            logger.info(f"💾 Chart saved to {filepath}")
            if auto_open:
                import webbrowser
                webbrowser.open(filepath)
            return True
        except Exception as e:
            logger.error(f"❌ Error saving chart: {e}")
            return False

    # ============================================================
    # UTILITIES
    # ============================================================

    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Chuẩn bị dữ liệu cho vnstock_chart."""
        work_df = df.copy()
        # Ensure DatetimeIndex
        if 'time' in work_df.columns:
            work_df = work_df.set_index('time')
        elif 'date' in work_df.columns:
            work_df = work_df.set_index('date')
        if not isinstance(work_df.index, pd.DatetimeIndex):
            work_df.index = pd.to_datetime(work_df.index)
        return work_df

    @staticmethod
    def embed_in_streamlit(html_content: str, height: int = 600):
        """
        Embed biểu đồ HTML vào Streamlit app.

        Args:
            html_content: HTML string từ chart.embed()
            height: Chiều cao iframe
        """
        try:
            import streamlit.components.v1 as components
            components.html(html_content, height=height, scrolling=True)
        except Exception as e:
            logger.error(f"❌ Error embedding chart in Streamlit: {e}")
