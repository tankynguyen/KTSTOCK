"""
KTSTOCK - Unit Tests for DebugLogger
"""
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from src.utils.debug_logger import DebugLogger, LogCategory, LogLevel, DEBUG_LOG_DIR


@pytest.fixture
def fresh_logger(tmp_path):
    """Create a fresh logger with temp directory."""
    # Reset singleton
    DebugLogger._instance = None

    with patch("src.utils.debug_logger.DEBUG_LOG_DIR", tmp_path):
        with patch("src.utils.debug_logger.st") as mock_st:
            mock_st.session_state = {"debug_mode": True, "user": {"username": "test_user"}, "user_role": "admin", "session_token": "tok12345"}
            logger = DebugLogger()
            logger._initialized = False
            logger.__init__()
            yield logger, tmp_path

    # Reset singleton again
    DebugLogger._instance = None


class TestDebugLoggerWrite:
    """Test writing logs."""

    def test_log_creates_file(self, fresh_logger):
        logger, tmp_path = fresh_logger
        with patch("src.utils.debug_logger.DEBUG_LOG_DIR", tmp_path):
            with patch("src.utils.debug_logger.st") as mock_st:
                mock_st.session_state = {"debug_mode": True, "user": {"username": "test"}, "user_role": "admin", "session_token": "tok123"}
                logger.log(
                    level=LogLevel.ERROR,
                    category=LogCategory.API_CALL,
                    page="dashboard",
                    component="test_component",
                    action="test_action",
                    error_message="Test error",
                )

        # Check that a file was created
        files = list(tmp_path.glob("*.jsonl"))
        assert len(files) == 1

    def test_log_api_call_shortcut(self, fresh_logger):
        logger, tmp_path = fresh_logger
        with patch("src.utils.debug_logger.DEBUG_LOG_DIR", tmp_path):
            with patch("src.utils.debug_logger.st") as mock_st:
                mock_st.session_state = {"debug_mode": True, "user": {"username": "test"}, "user_role": "admin", "session_token": "tok123"}
                logger.log_api_call(
                    page="stock_analysis",
                    component="render_stock",
                    source="VnstockFreeConnector",
                    method="get_historical_data",
                    params={"symbol": "VCB"},
                    result_status="ERROR",
                    error=ValueError("test error"),
                    duration_ms=150.5,
                    symbol="VCB",
                )

        files = list(tmp_path.glob("*.jsonl"))
        assert len(files) == 1
        content = files[0].read_text(encoding="utf-8").strip()
        record = json.loads(content)
        assert record["category"] == "API_CALL"
        assert record["source"] == "VnstockFreeConnector"
        assert record["symbol"] == "VCB"
        assert record["error_type"] == "ValueError"

    def test_debug_off_skips_info(self, fresh_logger):
        logger, tmp_path = fresh_logger
        with patch("src.utils.debug_logger.DEBUG_LOG_DIR", tmp_path):
            with patch("src.utils.debug_logger.st") as mock_st:
                mock_st.session_state = {"debug_mode": False}
                logger.log(
                    level=LogLevel.INFO,
                    category=LogCategory.API_CALL,
                    page="dashboard",
                    component="test",
                    action="test",
                )

        files = list(tmp_path.glob("*.jsonl"))
        assert len(files) == 0

    def test_debug_off_still_logs_error(self, fresh_logger):
        logger, tmp_path = fresh_logger
        with patch("src.utils.debug_logger.DEBUG_LOG_DIR", tmp_path):
            with patch("src.utils.debug_logger.st") as mock_st:
                mock_st.session_state = {"debug_mode": False, "user": None, "user_role": "guest", "session_token": ""}
                logger.log(
                    level=LogLevel.ERROR,
                    category=LogCategory.UI_ERROR,
                    page="dashboard",
                    component="test",
                    action="test_error",
                    error_message="Critical failure",
                )

        files = list(tmp_path.glob("*.jsonl"))
        assert len(files) == 1


class TestDebugLoggerRead:
    """Test reading and filtering logs."""

    def _write_sample_logs(self, logger, tmp_path):
        """Write sample logs for testing."""
        with patch("src.utils.debug_logger.DEBUG_LOG_DIR", tmp_path):
            with patch("src.utils.debug_logger.st") as mock_st:
                mock_st.session_state = {"debug_mode": True, "user": {"username": "admin"}, "user_role": "admin", "session_token": "tok123"}
                
                logger.log(LogLevel.INFO, LogCategory.API_CALL, "dashboard", "comp1", "action1")
                logger.log(LogLevel.WARNING, LogCategory.API_CALL, "dashboard", "comp2", "action2", symbol="VCB")
                logger.log(LogLevel.ERROR, LogCategory.AI_REQUEST, "stock_analysis", "comp3", "action3", error_message="AI failed")
                logger.log(LogLevel.ERROR, LogCategory.API_CALL, "dashboard", "comp4", "action4", error_message="timeout")
                logger.log(LogLevel.CRITICAL, LogCategory.SYSTEM, "admin", "comp5", "action5")

    def test_get_logs_returns_all(self, fresh_logger):
        logger, tmp_path = fresh_logger
        self._write_sample_logs(logger, tmp_path)

        with patch("src.utils.debug_logger.DEBUG_LOG_DIR", tmp_path):
            logs = logger.get_logs()
        assert len(logs) == 5

    def test_get_logs_filter_level(self, fresh_logger):
        logger, tmp_path = fresh_logger
        self._write_sample_logs(logger, tmp_path)

        with patch("src.utils.debug_logger.DEBUG_LOG_DIR", tmp_path):
            logs = logger.get_logs(level="ERROR")
        assert len(logs) == 3  # ERROR + CRITICAL

    def test_get_logs_filter_category(self, fresh_logger):
        logger, tmp_path = fresh_logger
        self._write_sample_logs(logger, tmp_path)

        with patch("src.utils.debug_logger.DEBUG_LOG_DIR", tmp_path):
            logs = logger.get_logs(category="API_CALL")
        assert len(logs) == 3

    def test_get_logs_filter_page(self, fresh_logger):
        logger, tmp_path = fresh_logger
        self._write_sample_logs(logger, tmp_path)

        with patch("src.utils.debug_logger.DEBUG_LOG_DIR", tmp_path):
            logs = logger.get_logs(page="dashboard")
        assert len(logs) == 3

    def test_get_logs_keyword(self, fresh_logger):
        logger, tmp_path = fresh_logger
        self._write_sample_logs(logger, tmp_path)

        with patch("src.utils.debug_logger.DEBUG_LOG_DIR", tmp_path):
            logs = logger.get_logs(keyword="timeout")
        assert len(logs) == 1


class TestDebugLoggerSummary:
    """Test summary statistics."""

    def test_get_summary(self, fresh_logger):
        logger, tmp_path = fresh_logger
        with patch("src.utils.debug_logger.DEBUG_LOG_DIR", tmp_path):
            with patch("src.utils.debug_logger.st") as mock_st:
                mock_st.session_state = {"debug_mode": True, "user": {"username": "admin"}, "user_role": "admin", "session_token": "tok123"}
                logger.log(LogLevel.ERROR, LogCategory.API_CALL, "dashboard", "c", "a")
                logger.log(LogLevel.WARNING, LogCategory.API_CALL, "dashboard", "c", "a")
                logger.log(LogLevel.INFO, LogCategory.AI_REQUEST, "stock_analysis", "c", "a")

            summary = logger.get_summary()

        assert summary["total"] == 3
        assert summary["error_count"] == 1
        assert summary["by_level"]["ERROR"] == 1
        assert summary["by_category"]["API_CALL"] == 2

    def test_get_error_count_today(self, fresh_logger):
        logger, tmp_path = fresh_logger
        with patch("src.utils.debug_logger.DEBUG_LOG_DIR", tmp_path):
            with patch("src.utils.debug_logger.st") as mock_st:
                mock_st.session_state = {"debug_mode": True, "user": {"username": "admin"}, "user_role": "admin", "session_token": "tok123"}
                logger.log(LogLevel.ERROR, LogCategory.API_CALL, "d", "c", "a")
                logger.log(LogLevel.CRITICAL, LogCategory.SYSTEM, "d", "c", "a")
                logger.log(LogLevel.INFO, LogCategory.API_CALL, "d", "c", "a")

            count = logger.get_error_count_today()

        assert count == 2


class TestDebugLoggerManagement:
    """Test log management (clear, dates)."""

    def test_clear_logs(self, fresh_logger):
        logger, tmp_path = fresh_logger
        with patch("src.utils.debug_logger.DEBUG_LOG_DIR", tmp_path):
            with patch("src.utils.debug_logger.st") as mock_st:
                mock_st.session_state = {"debug_mode": True, "user": {"username": "admin"}, "user_role": "admin", "session_token": "tok123"}
                logger.log(LogLevel.ERROR, LogCategory.API_CALL, "d", "c", "a")

            from datetime import datetime, timezone, timedelta
            today = datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d")
            result = logger.clear_logs(today)

        assert result is True
        assert len(list(tmp_path.glob("*.jsonl"))) == 0

    def test_get_available_dates(self, fresh_logger):
        logger, tmp_path = fresh_logger
        # Create some fake log files
        (tmp_path / "2026-04-28.jsonl").write_text("{}\n")
        (tmp_path / "2026-04-29.jsonl").write_text("{}\n")
        (tmp_path / "2026-04-30.jsonl").write_text("{}\n")

        with patch("src.utils.debug_logger.DEBUG_LOG_DIR", tmp_path):
            dates = logger.get_available_dates()

        assert len(dates) == 3
        assert dates[0] == "2026-04-30"  # Newest first


class TestLogLevel:
    """Test LogLevel comparison."""

    def test_gte_same(self):
        assert LogLevel.gte("ERROR", "ERROR") is True

    def test_gte_higher(self):
        assert LogLevel.gte("CRITICAL", "ERROR") is True

    def test_gte_lower(self):
        assert LogLevel.gte("INFO", "ERROR") is False

    def test_gte_debug(self):
        assert LogLevel.gte("DEBUG", "DEBUG") is True
