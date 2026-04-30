"""
KTSTOCK - vnstock_pipeline Connector
Data pipeline cho lấy dữ liệu hàng loạt theo mô hình Fetcher → Validator → Transformer → Exporter.
"""
from typing import Optional

import pandas as pd
from loguru import logger

from src.utils.decorators import timer


class VnstockPipelineConnector:
    """
    Connector cho vnstock_pipeline - Data Pipeline.

    Hỗ trợ:
    - OHLCV Task: Lấy dữ liệu giá hàng loạt
    - Financial Task: Lấy BCTC hàng loạt
    - Intraday Task: Dữ liệu trong phiên
    - Price Board Task: Bảng giá real-time
    - Custom Pipeline: Tùy chỉnh Fetcher/Validator/Transformer/Exporter
    """

    def __init__(self):
        self._available = False
        try:
            import vnstock_pipeline
            self._vnstock_pipeline = vnstock_pipeline
            self._available = True
            logger.info("✅ vnstock_pipeline connector initialized")
        except ImportError:
            logger.warning("⚠️ vnstock_pipeline not installed. Pipeline features unavailable.")

    @property
    def is_available(self) -> bool:
        return self._available

    # ============================================================
    # BUILT-IN TASKS
    # ============================================================

    @timer
    def run_ohlcv_task(
        self,
        tickers: list[str],
        start: str = "2024-01-01",
        end: str = "2024-12-31",
        interval: str = "1D",
        output_dir: str = "data/ohlcv",
    ) -> dict:
        """
        Lấy dữ liệu OHLCV hàng loạt cho nhiều mã.

        Args:
            tickers: Danh sách mã (VD: ["VCB", "ACB", "HPG"])
            start: Ngày bắt đầu (YYYY-MM-DD)
            end: Ngày kết thúc (YYYY-MM-DD)
            interval: Khung thời gian (1D, 1W, 1M, 1h, 5m, 15m, 30m)
            output_dir: Thư mục lưu kết quả

        Returns:
            dict: {"success": int, "failed": int, "output_dir": str}
        """
        if not self._available:
            return {"success": 0, "failed": len(tickers), "error": "vnstock_pipeline not installed"}

        try:
            from vnstock_pipeline.tasks.ohlcv import run_task
            run_task(tickers, start=start, end=end, interval=interval)
            logger.info(f"✅ OHLCV task completed for {len(tickers)} tickers")
            return {
                "success": len(tickers),
                "failed": 0,
                "output_dir": output_dir,
            }
        except Exception as e:
            logger.error(f"❌ OHLCV task error: {e}")
            return {"success": 0, "failed": len(tickers), "error": str(e)}

    @timer
    def run_financial_task(
        self,
        tickers: list[str],
        reports: list[str] = None,
        period: str = "year",
        lang: str = "vi",
    ) -> dict:
        """
        Lấy BCTC hàng loạt.

        Args:
            tickers: Danh sách mã
            reports: Loại báo cáo ["balance_sheet", "income_statement", "cash_flow", "ratio"]
            period: "year" hoặc "quarter"
            lang: "vi" hoặc "en"

        Returns:
            dict: {"success": int, "failed": int}
        """
        if not self._available:
            return {"success": 0, "failed": len(tickers), "error": "vnstock_pipeline not installed"}

        try:
            from vnstock_pipeline.tasks.financial import run_financial_task

            kwargs = {
                "balance_sheet_period": period,
                "income_statement_year_period": period,
                "cash_flow_period": period,
                "ratio_period": period,
                "lang": lang,
            }

            run_financial_task(tickers, **kwargs)
            logger.info(f"✅ Financial task completed for {len(tickers)} tickers")
            return {"success": len(tickers), "failed": 0}
        except Exception as e:
            logger.error(f"❌ Financial task error: {e}")
            return {"success": 0, "failed": len(tickers), "error": str(e)}

    @timer
    def run_intraday_task(
        self,
        tickers: list[str],
        interval: str = "5m",
    ) -> dict:
        """
        Lấy dữ liệu intraday hàng loạt.

        Args:
            tickers: Danh sách mã
            interval: 1m, 5m, 15m, 30m, 1h
        """
        if not self._available:
            return {"success": 0, "failed": len(tickers), "error": "vnstock_pipeline not installed"}

        try:
            from vnstock_pipeline.tasks.ohlcv import run_task
            from datetime import date

            today = date.today().isoformat()
            run_task(tickers, start=today, end=today, interval=interval)
            logger.info(f"✅ Intraday task completed for {len(tickers)} tickers")
            return {"success": len(tickers), "failed": 0}
        except Exception as e:
            logger.error(f"❌ Intraday task error: {e}")
            return {"success": 0, "failed": len(tickers), "error": str(e)}

    @timer
    def run_price_board_task(self, tickers: list[str]) -> Optional[pd.DataFrame]:
        """
        Lấy bảng giá real-time cho nhiều mã.

        Args:
            tickers: Danh sách mã

        Returns:
            DataFrame bảng giá
        """
        if not self._available:
            return None

        try:
            from vnstock_pipeline.tasks.price_board import run_task as run_pb_task
            result = run_pb_task(tickers)
            if result is not None:
                logger.info(f"✅ Price board fetched for {len(tickers)} tickers")
            return result
        except (ImportError, AttributeError):
            # Fallback: dùng vnstock_data Trading
            try:
                from vnstock_data import Trading
                trading = Trading(source="VCI", symbol=tickers[0])
                df = trading.price_board(symbol_list=tickers)
                return df
            except Exception as e2:
                logger.error(f"❌ Price board fallback error: {e2}")
        except Exception as e:
            logger.error(f"❌ Price board task error: {e}")
        return None

    # ============================================================
    # CUSTOM PIPELINE BUILDER
    # ============================================================

    @timer
    def create_scheduler(
        self,
        fetcher=None,
        validator=None,
        transformer=None,
        exporter=None,
        max_workers: int = 5,
        retry_attempts: int = 3,
    ):
        """
        Tạo Scheduler tùy chỉnh.

        Args:
            fetcher: VNFetcher instance
            validator: VNValidator instance
            transformer: VNTransformer instance
            exporter: Exporter instance
            max_workers: Số workers song song
            retry_attempts: Số lần retry
        """
        if not self._available:
            return None

        try:
            from vnstock_pipeline.core.scheduler import Scheduler
            scheduler = Scheduler(
                fetcher=fetcher,
                validator=validator,
                transformer=transformer,
                exporter=exporter,
                max_workers=max_workers,
                retry_attempts=retry_attempts,
            )
            logger.info(f"✅ Custom scheduler created (workers={max_workers})")
            return scheduler
        except Exception as e:
            logger.error(f"❌ Error creating scheduler: {e}")
            return None

    @timer
    def run_custom_pipeline(
        self,
        scheduler,
        tickers: list[str],
        **kwargs,
    ) -> dict:
        """
        Chạy pipeline tùy chỉnh.

        Args:
            scheduler: Scheduler instance từ create_scheduler()
            tickers: Danh sách mã
            **kwargs: Tham số cho fetcher
        """
        if scheduler is None:
            return {"success": 0, "failed": len(tickers), "error": "Scheduler is None"}

        try:
            scheduler.run(tickers=tickers, fetcher_kwargs=kwargs)
            logger.info(f"✅ Custom pipeline completed for {len(tickers)} tickers")
            return {"success": len(tickers), "failed": 0}
        except Exception as e:
            logger.error(f"❌ Custom pipeline error: {e}")
            return {"success": 0, "failed": len(tickers), "error": str(e)}

    # ============================================================
    # BATCH UTILITIES
    # ============================================================

    @timer
    def batch_fetch_vn30(
        self, start: str = "2024-01-01", end: str = "2024-12-31"
    ) -> dict:
        """Lấy OHLCV cho tất cả VN30."""
        vn30 = [
            'ACB', 'BCM', 'BID', 'CTG', 'DGC', 'FPT', 'GAS', 'GVR', 'HDB', 'HPG',
            'LPB', 'MBB', 'MSN', 'MWG', 'PLX', 'SAB', 'SHB', 'SSB', 'SSI', 'STB',
            'TCB', 'TPB', 'VCB', 'VHM', 'VIB', 'VIC', 'VJC', 'VNM', 'VPB', 'VRE',
        ]
        return self.run_ohlcv_task(vn30, start=start, end=end)

    @timer
    def get_pipeline_status(self) -> dict:
        """Trạng thái pipeline."""
        return {
            "available": self._available,
            "version": self._get_version(),
        }

    def _get_version(self) -> str:
        """Lấy version vnstock_pipeline."""
        try:
            from importlib.metadata import version
            return version("vnstock_pipeline")
        except Exception:
            return "unknown"
