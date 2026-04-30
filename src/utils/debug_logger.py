"""
KTSTOCK - Debug Logger
Hệ thống ghi log chuyên nghiệp cho debug toàn bộ ứng dụng.
Ghi log dạng JSONL (1 JSON object/dòng) vào file theo ngày.
"""
import json
import uuid
import time
import sys
import platform
import traceback as tb_module
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Any

import streamlit as st
from loguru import logger

from src.utils.config import PROJECT_ROOT


# === Constants ===
DEBUG_LOG_DIR = PROJECT_ROOT / "logs" / "debug"
DEBUG_LOG_DIR.mkdir(parents=True, exist_ok=True)

# Timezone Vietnam
VN_TZ = timezone(timedelta(hours=7))

# Categories
class LogCategory:
    API_CALL = "API_CALL"
    AI_REQUEST = "AI_REQUEST"
    DB_QUERY = "DB_QUERY"
    AUTH_ACTION = "AUTH_ACTION"
    CACHE_OP = "CACHE_OP"
    UI_ERROR = "UI_ERROR"
    EXPORT = "EXPORT"
    SYSTEM = "SYSTEM"

# Levels
class LogLevel:
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    _ORDER = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}

    @classmethod
    def gte(cls, level: str, threshold: str) -> bool:
        """Check if level >= threshold."""
        return cls._ORDER.get(level, 0) >= cls._ORDER.get(threshold, 0)


class DebugLogger:
    """
    Hệ thống ghi log debug chuyên nghiệp.
    
    - Ghi vào file JSONL theo ngày: logs/debug/YYYY-MM-DD.jsonl
    - Mỗi dòng là 1 JSON object hoàn chỉnh
    - Thread-safe qua file append mode
    - Tự động thu thập environment info
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._env_info = self._collect_environment()

    # ================================================================
    # PUBLIC API
    # ================================================================

    def log(
        self,
        level: str,
        category: str,
        page: str,
        component: str,
        action: str,
        *,
        action_detail: str = "",
        symbol: str = "",
        source: str = "",
        method: str = "",
        params: Optional[dict] = None,
        result_status: str = "",
        result_data: Optional[Any] = None,
        error_type: str = "",
        error_message: str = "",
        traceback_str: str = "",
        duration_ms: float = 0,
        extra: Optional[dict] = None,
    ) -> None:
        """
        Ghi 1 bản ghi log chi tiết.
        
        Khi debug_mode=OFF: chỉ ghi ERROR và CRITICAL.
        Khi debug_mode=ON: ghi tất cả levels.
        """
        debug_mode = self._is_debug_mode()
        
        # Khi debug OFF, chỉ ghi ERROR trở lên
        if not debug_mode and not LogLevel.gte(level, LogLevel.ERROR):
            return

        record = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.now(VN_TZ).isoformat(),
            "level": level,
            "category": category,
            "page": page,
            "page_title": self._get_page_title(page),
            "component": component,
            "action": action,
            "action_detail": action_detail,
            "symbol": symbol,
            "user": self._get_current_user(),
            "user_role": self._get_current_role(),
            "source": source,
            "method": method,
            "params": params or {},
            "result_status": result_status,
            "error_type": error_type,
            "error_message": error_message,
            "traceback": traceback_str,
            "duration_ms": round(duration_ms, 2),
            "environment": self._env_info,
            "session_id": self._get_session_id(),
        }

        if extra:
            record["extra"] = extra

        self._write_record(record)

    def log_api_call(
        self,
        page: str,
        component: str,
        source: str,
        method: str,
        params: dict,
        *,
        result_status: str = "SUCCESS",
        error: Optional[Exception] = None,
        duration_ms: float = 0,
        symbol: str = "",
        action_detail: str = "",
    ) -> None:
        """Shortcut: Ghi log cho 1 lần gọi API."""
        level = LogLevel.INFO if result_status == "SUCCESS" else (
            LogLevel.WARNING if result_status == "EMPTY" else LogLevel.ERROR
        )
        
        error_type = ""
        error_message = ""
        traceback_str = ""
        if error:
            error_type = type(error).__name__
            error_message = str(error)
            traceback_str = tb_module.format_exc()

        self.log(
            level=level,
            category=LogCategory.API_CALL,
            page=page,
            component=component,
            action=f"call_{method}",
            action_detail=action_detail or f"Gọi {source}.{method}({', '.join(f'{k}={v}' for k, v in params.items())})",
            symbol=symbol,
            source=source,
            method=method,
            params=params,
            result_status=result_status,
            error_type=error_type,
            error_message=error_message,
            traceback_str=traceback_str,
            duration_ms=duration_ms,
        )

    def log_ai_request(
        self,
        page: str,
        component: str,
        provider: str,
        prompt_preview: str,
        *,
        result_status: str = "SUCCESS",
        error: Optional[Exception] = None,
        duration_ms: float = 0,
    ) -> None:
        """Shortcut: Ghi log cho 1 lần gọi AI."""
        level = LogLevel.INFO if result_status == "SUCCESS" else LogLevel.ERROR

        error_type = ""
        error_message = ""
        traceback_str = ""
        if error:
            error_type = type(error).__name__
            error_message = str(error)
            traceback_str = tb_module.format_exc()

        self.log(
            level=level,
            category=LogCategory.AI_REQUEST,
            page=page,
            component=component,
            action="ai_request",
            action_detail=f"AI Provider: {provider} | Prompt: {prompt_preview[:100]}...",
            source=provider,
            method="generate",
            result_status=result_status,
            error_type=error_type,
            error_message=error_message,
            traceback_str=traceback_str,
            duration_ms=duration_ms,
        )

    def log_ui_error(
        self,
        page: str,
        component: str,
        error: Exception,
    ) -> None:
        """Shortcut: Ghi log lỗi UI rendering."""
        self.log(
            level=LogLevel.ERROR,
            category=LogCategory.UI_ERROR,
            page=page,
            component=component,
            action="render_error",
            action_detail=f"Lỗi khi render {component} trên trang {page}",
            error_type=type(error).__name__,
            error_message=str(error),
            traceback_str=tb_module.format_exc(),
        )

    # ================================================================
    # READ / QUERY API
    # ================================================================

    def get_logs(
        self,
        date: Optional[str] = None,
        level: Optional[str] = None,
        category: Optional[str] = None,
        page: Optional[str] = None,
        keyword: Optional[str] = None,
        limit: int = 200,
    ) -> list[dict]:
        """
        Đọc và lọc logs.
        
        Args:
            date: "YYYY-MM-DD" (mặc định: hôm nay)
            level: Lọc theo level tối thiểu
            category: Lọc theo category
            page: Lọc theo page
            keyword: Tìm kiếm text trong action/error
            limit: Số bản ghi tối đa
        """
        if date is None:
            date = datetime.now(VN_TZ).strftime("%Y-%m-%d")

        file_path = DEBUG_LOG_DIR / f"{date}.jsonl"
        if not file_path.exists():
            return []

        records = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    # Apply filters
                    if level and not LogLevel.gte(record.get("level", "DEBUG"), level):
                        continue
                    if category and record.get("category") != category:
                        continue
                    if page and record.get("page") != page:
                        continue
                    if keyword:
                        searchable = json.dumps(record, ensure_ascii=False).lower()
                        if keyword.lower() not in searchable:
                            continue

                    records.append(record)
        except Exception as e:
            logger.error(f"Error reading debug log {file_path}: {e}")

        # Return newest first, limited
        records.reverse()
        return records[:limit]

    def get_summary(self, date: Optional[str] = None) -> dict:
        """
        Tổng hợp thống kê log theo ngày.
        
        Returns:
            {
                "date": "2026-04-30",
                "total": 150,
                "by_level": {"DEBUG": 80, "INFO": 40, "WARNING": 15, "ERROR": 12, "CRITICAL": 3},
                "by_category": {"API_CALL": 90, ...},
                "by_page": {"dashboard": 30, ...},
                "error_count": 15,   # ERROR + CRITICAL
                "file_size_kb": 256,
            }
        """
        if date is None:
            date = datetime.now(VN_TZ).strftime("%Y-%m-%d")

        file_path = DEBUG_LOG_DIR / f"{date}.jsonl"
        result = {
            "date": date,
            "total": 0,
            "by_level": {},
            "by_category": {},
            "by_page": {},
            "error_count": 0,
            "file_size_kb": 0,
        }

        if not file_path.exists():
            return result

        result["file_size_kb"] = round(file_path.stat().st_size / 1024, 2)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    result["total"] += 1

                    lvl = record.get("level", "UNKNOWN")
                    result["by_level"][lvl] = result["by_level"].get(lvl, 0) + 1

                    cat = record.get("category", "UNKNOWN")
                    result["by_category"][cat] = result["by_category"].get(cat, 0) + 1

                    pg = record.get("page", "unknown")
                    result["by_page"][pg] = result["by_page"].get(pg, 0) + 1

                    if lvl in ("ERROR", "CRITICAL"):
                        result["error_count"] += 1
        except Exception as e:
            logger.error(f"Error reading debug log summary: {e}")

        return result

    def get_error_count_today(self) -> int:
        """Đếm nhanh số lỗi ERROR+CRITICAL hôm nay (cho badge sidebar)."""
        date = datetime.now(VN_TZ).strftime("%Y-%m-%d")
        file_path = DEBUG_LOG_DIR / f"{date}.jsonl"
        if not file_path.exists():
            return 0

        count = 0
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if '"ERROR"' in line or '"CRITICAL"' in line:
                        count += 1
        except Exception:
            pass
        return count

    def get_available_dates(self) -> list[str]:
        """Lấy danh sách ngày có file log."""
        dates = []
        for f in sorted(DEBUG_LOG_DIR.glob("*.jsonl"), reverse=True):
            dates.append(f.stem)
        return dates

    def clear_logs(self, date: str) -> bool:
        """Xóa log của 1 ngày."""
        file_path = DEBUG_LOG_DIR / f"{date}.jsonl"
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def clear_old_logs(self, keep_days: int = 30) -> int:
        """Xóa log cũ hơn keep_days ngày."""
        cutoff = datetime.now(VN_TZ) - timedelta(days=keep_days)
        cutoff_str = cutoff.strftime("%Y-%m-%d")
        count = 0
        for f in DEBUG_LOG_DIR.glob("*.jsonl"):
            if f.stem < cutoff_str:
                f.unlink()
                count += 1
        return count

    # ================================================================
    # PRIVATE HELPERS
    # ================================================================

    def _write_record(self, record: dict) -> None:
        """Ghi 1 record vào file JSONL của ngày hiện tại."""
        date = datetime.now(VN_TZ).strftime("%Y-%m-%d")
        file_path = DEBUG_LOG_DIR / f"{date}.jsonl"

        try:
            line = json.dumps(record, ensure_ascii=False, default=str)
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as e:
            logger.error(f"Failed to write debug log: {e}")

    def _is_debug_mode(self) -> bool:
        """Kiểm tra debug mode từ session state."""
        try:
            return st.session_state.get("debug_mode", False)
        except Exception:
            return False

    def _get_current_user(self) -> str:
        try:
            user = st.session_state.get("user")
            return user.get("username", "unknown") if user else "anonymous"
        except Exception:
            return "unknown"

    def _get_current_role(self) -> str:
        try:
            return st.session_state.get("user_role", "guest")
        except Exception:
            return "unknown"

    def _get_session_id(self) -> str:
        try:
            token = st.session_state.get("session_token", "")
            return token[:8] if token else "no-session"
        except Exception:
            return "unknown"

    def _get_page_title(self, page_key: str) -> str:
        titles = {
            "dashboard": "Tổng quan",
            "stock_analysis": "Phân tích cổ phiếu",
            "crypto_analysis": "Phân tích Crypto",
            "technical": "Phân tích kỹ thuật",
            "fundamental": "Phân tích cơ bản",
            "ai_insights": "AI Insights",
            "screener": "Bộ lọc cổ phiếu",
            "portfolio": "Danh mục đầu tư",
            "alerts": "Cảnh báo",
            "macro": "Kinh tế vĩ mô",
            "news": "Tin tức & Sentiment",
            "reports": "Báo cáo",
            "settings": "Cài đặt",
            "admin": "Quản trị hệ thống",
            "log_viewer": "Quản lý Log",
        }
        return titles.get(page_key, page_key)

    def _collect_environment(self) -> dict:
        """Thu thập thông tin môi trường 1 lần duy nhất."""
        try:
            import streamlit
            st_version = streamlit.__version__
        except Exception:
            st_version = "unknown"

        return {
            "platform": sys.platform,
            "python_version": platform.python_version(),
            "streamlit_version": st_version,
            "deploy_mode": "cloud" if self._detect_cloud() else "local",
        }

    def _detect_cloud(self) -> bool:
        """Detect Streamlit Cloud environment."""
        return Path("/mount/src").exists() or "STREAMLIT_SHARING_MODE" in __import__("os").environ


# ================================================================
# SINGLETON ACCESSOR
# ================================================================
def get_debug_logger() -> DebugLogger:
    """Lấy instance singleton của DebugLogger."""
    return DebugLogger()


# ================================================================
# CONTEXT MANAGER: Đo thời gian API call
# ================================================================
class ApiCallTimer:
    """
    Context manager để đo thời gian và tự động log API call.
    
    Usage:
        with ApiCallTimer("dashboard", "_render_index", "VnstockFreeConnector", "get_historical_data",
                          params={"symbol": "VCB"}, symbol="VCB"):
            df = connector.get_historical_data("VCB", start, end)
    """

    def __init__(
        self,
        page: str,
        component: str,
        source: str,
        method: str,
        *,
        params: Optional[dict] = None,
        symbol: str = "",
        action_detail: str = "",
    ):
        self.page = page
        self.component = component
        self.source = source
        self.method = method
        self.params = params or {}
        self.symbol = symbol
        self.action_detail = action_detail
        self._start = 0
        self.result_status = "SUCCESS"
        self.error: Optional[Exception] = None

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.perf_counter() - self._start) * 1000

        if exc_val:
            self.error = exc_val
            self.result_status = "ERROR"

        get_debug_logger().log_api_call(
            page=self.page,
            component=self.component,
            source=self.source,
            method=self.method,
            params=self.params,
            result_status=self.result_status,
            error=self.error,
            duration_ms=duration_ms,
            symbol=self.symbol,
            action_detail=self.action_detail,
        )

        # Don't suppress the exception
        return False
