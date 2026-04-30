"""
KTSTOCK - Configuration Manager
Quản lý tất cả cấu hình hệ thống từ .env, secrets.toml và database.
"""
import os
from pathlib import Path
from typing import Any, Optional
from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import Field


# === Đường dẫn gốc của dự án ===
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
DB_DIR = DATA_DIR


class AppSettings(BaseSettings):
    """Cấu hình chung của ứng dụng."""
    app_name: str = "KTSTOCK"
    app_version: str = "1.0.0"
    app_env: str = "development"
    app_debug: bool = True
    app_secret_key: str = "ktstock-secret-key-change-in-production"
    default_language: str = "vi"

    class Config:
        env_file = str(PROJECT_ROOT / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


class DatabaseSettings(BaseSettings):
    """Cấu hình database SQLite."""
    database_url: str = Field(
        default=f"sqlite:///{DB_DIR / 'ktstock.db'}",
        description="SQLite connection string"
    )

    class Config:
        env_file = str(PROJECT_ROOT / ".env")
        extra = "ignore"


class AISettings(BaseSettings):
    """Cấu hình AI Providers."""
    gemini_api_key: str = ""
    grok_api_key: str = ""
    deepseek_api_key: str = ""
    default_ai_provider: str = "gemini"

    class Config:
        env_file = str(PROJECT_ROOT / ".env")
        extra = "ignore"


class CryptoSettings(BaseSettings):
    """Cấu hình Binance."""
    binance_api_key: str = ""
    binance_api_secret: str = ""

    class Config:
        env_file = str(PROJECT_ROOT / ".env")
        extra = "ignore"


class NotificationSettings(BaseSettings):
    """Cấu hình thông báo."""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    email_smtp_host: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""

    class Config:
        env_file = str(PROJECT_ROOT / ".env")
        extra = "ignore"


class VnstockSettings(BaseSettings):
    """Cấu hình vnstock."""
    vnstock_data_api_key: str = ""
    vnstock_default_source: str = "VCI"
    vnstock_prefer_sponsored: bool = True

    class Config:
        env_file = str(PROJECT_ROOT / ".env")
        extra = "ignore"


class CacheSettings(BaseSettings):
    """Cấu hình cache."""
    cache_dir: str = str(CACHE_DIR)
    cache_ttl_seconds: int = 3600
    cache_max_size_mb: int = 500

    class Config:
        env_file = str(PROJECT_ROOT / ".env")
        extra = "ignore"


class Settings:
    """Singleton tổng hợp tất cả cấu hình."""

    _instance: Optional["Settings"] = None

    def __new__(cls) -> "Settings":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.app = AppSettings()
        self.database = DatabaseSettings()
        self.ai = AISettings()
        self.crypto = CryptoSettings()
        self.notification = NotificationSettings()
        self.vnstock = VnstockSettings()
        self.cache = CacheSettings()
        self._initialized = True

        # Đảm bảo các thư mục cần thiết tồn tại
        self._ensure_directories()

    def _ensure_directories(self):
        """Tạo các thư mục cần thiết nếu chưa có."""
        for dir_path in [DATA_DIR, CACHE_DIR, DATA_DIR / "raw", DATA_DIR / "processed"]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def reload(self):
        """Reload tất cả settings từ .env."""
        self._initialized = False
        self.__init__()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Lấy Settings singleton (cached)."""
    return Settings()
