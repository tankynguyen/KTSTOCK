"""
KTSTOCK - Logging Setup
Sử dụng Loguru để ghi log chuyên nghiệp với rotation và formatting.
"""
import sys
from pathlib import Path
from loguru import logger

from src.utils.config import PROJECT_ROOT


# === Thư mục log ===
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)


def setup_logger(
    level: str = "INFO",
    rotation: str = "10 MB",
    retention: str = "30 days",
    enable_console: bool = True,
) -> None:
    """
    Thiết lập logger cho toàn bộ ứng dụng.

    Args:
        level: Mức log tối thiểu (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        rotation: Kích thước file trước khi rotate
        retention: Thời gian giữ log cũ
        enable_console: Có hiển thị log ra console không
    """
    # Xóa handler mặc định
    logger.remove()

    # === Console handler ===
    if enable_console:
        logger.add(
            sys.stderr,
            level=level,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            ),
            colorize=True,
        )

    # === File handler - General log ===
    logger.add(
        LOG_DIR / "ktstock_{time:YYYY-MM-DD}.log",
        level=level,
        rotation=rotation,
        retention=retention,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
        encoding="utf-8",
        enqueue=True,  # Thread-safe
    )

    # === File handler - Error log (chỉ ghi lỗi) ===
    logger.add(
        LOG_DIR / "errors_{time:YYYY-MM-DD}.log",
        level="ERROR",
        rotation=rotation,
        retention=retention,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}\n{exception}",
        encoding="utf-8",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    logger.info(f"Logger initialized | level={level} | log_dir={LOG_DIR}")


def get_logger(name: str = "ktstock"):
    """Lấy logger instance với context name."""
    return logger.bind(name=name)
