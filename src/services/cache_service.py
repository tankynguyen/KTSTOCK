"""
KTSTOCK - Cache Service
File-based caching + Streamlit cache integration.
Không cần Redis server.
"""
import json
import hashlib
import pickle
import time
from pathlib import Path
from typing import Any, Callable, Optional
from datetime import datetime, timedelta

import pandas as pd
from loguru import logger

from src.utils.config import get_settings, CACHE_DIR


class CacheService:
    """
    Service quản lý cache dựa trên file hệ thống.

    Hỗ trợ 3 loại cache:
    1. Memory cache (dict trong RAM - nhanh nhất)
    2. File cache (pickle/parquet - persistent)
    3. Streamlit cache (@st.cache_data - tự động)
    """

    _instance: Optional["CacheService"] = None

    def __new__(cls) -> "CacheService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        settings = get_settings()
        self.cache_dir = Path(settings.cache.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = settings.cache.cache_ttl_seconds
        self.max_size_mb = settings.cache.cache_max_size_mb

        # Memory cache (nhanh nhất)
        self._memory_cache: dict[str, dict] = {}
        self._initialized = True
        logger.info(f"✅ CacheService initialized | dir={self.cache_dir} | ttl={self.default_ttl}s")

    def _generate_key(self, *args, **kwargs) -> str:
        """Tạo cache key duy nhất."""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.md5(key_data.encode()).hexdigest()

    # =========================================
    # Memory Cache (Nhanh nhất - tạm thời)
    # =========================================
    def get_memory(self, key: str) -> Optional[Any]:
        """Lấy giá trị từ memory cache."""
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if time.time() < entry["expires_at"]:
                return entry["value"]
            else:
                del self._memory_cache[key]
        return None

    def set_memory(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Lưu giá trị vào memory cache."""
        ttl = ttl or self.default_ttl
        self._memory_cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl,
        }

    # =========================================
    # File Cache (Persistent)
    # =========================================
    def _get_file_path(self, key: str, extension: str = ".pkl") -> Path:
        """Lấy đường dẫn file cache."""
        return self.cache_dir / f"{key}{extension}"

    def get_file(self, key: str) -> Optional[Any]:
        """Lấy dữ liệu từ file cache."""
        meta_path = self._get_file_path(key, ".meta.json")
        data_path = self._get_file_path(key, ".pkl")

        if not meta_path.exists() or not data_path.exists():
            return None

        # Kiểm tra hết hạn
        try:
            meta = json.loads(meta_path.read_text())
            if time.time() > meta["expires_at"]:
                self.delete_file(key)
                return None
            return pickle.loads(data_path.read_bytes())
        except Exception as e:
            logger.warning(f"⚠️ Cache read error for {key}: {e}")
            return None

    def set_file(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Lưu dữ liệu vào file cache."""
        ttl = ttl or self.default_ttl
        data_path = self._get_file_path(key, ".pkl")
        meta_path = self._get_file_path(key, ".meta.json")

        try:
            # Lưu dữ liệu
            data_path.write_bytes(pickle.dumps(value))

            # Lưu metadata
            meta = {
                "key": key,
                "expires_at": time.time() + ttl,
                "size_bytes": data_path.stat().st_size,
                "created_at": datetime.now().isoformat(),
            }
            meta_path.write_text(json.dumps(meta))
        except Exception as e:
            logger.error(f"❌ Cache write error for {key}: {e}")

    def delete_file(self, key: str) -> None:
        """Xóa file cache."""
        for ext in [".pkl", ".meta.json", ".parquet"]:
            path = self._get_file_path(key, ext)
            if path.exists():
                path.unlink()

    # =========================================
    # DataFrame Cache (Parquet - tối ưu cho data)
    # =========================================
    def get_dataframe(self, key: str) -> Optional[pd.DataFrame]:
        """Lấy DataFrame từ parquet cache."""
        meta_path = self._get_file_path(key, ".meta.json")
        data_path = self._get_file_path(key, ".parquet")

        if not meta_path.exists() or not data_path.exists():
            return None

        try:
            meta = json.loads(meta_path.read_text())
            if time.time() > meta["expires_at"]:
                self.delete_file(key)
                return None
            return pd.read_parquet(data_path)
        except Exception as e:
            logger.warning(f"⚠️ DataFrame cache read error for {key}: {e}")
            return None

    def set_dataframe(self, key: str, df: pd.DataFrame, ttl: Optional[int] = None) -> None:
        """Lưu DataFrame vào parquet cache."""
        ttl = ttl or self.default_ttl
        data_path = self._get_file_path(key, ".parquet")
        meta_path = self._get_file_path(key, ".meta.json")

        try:
            df.to_parquet(data_path, index=False)
            meta = {
                "key": key,
                "type": "dataframe",
                "expires_at": time.time() + ttl,
                "rows": len(df),
                "columns": list(df.columns),
                "size_bytes": data_path.stat().st_size,
                "created_at": datetime.now().isoformat(),
            }
            meta_path.write_text(json.dumps(meta))
        except Exception as e:
            logger.error(f"❌ DataFrame cache write error for {key}: {e}")

    # =========================================
    # Tiện ích
    # =========================================
    def get_or_set(self, key: str, factory: Callable, ttl: Optional[int] = None) -> Any:
        """
        Lấy từ cache hoặc tạo mới nếu chưa có.

        Args:
            key: Cache key
            factory: Hàm tạo dữ liệu mới nếu cache miss
            ttl: Time to live (giây)
        """
        # Thử memory cache trước
        value = self.get_memory(key)
        if value is not None:
            return value

        # Thử file cache
        value = self.get_file(key)
        if value is not None:
            self.set_memory(key, value, ttl)  # Promote lên memory
            return value

        # Cache miss - tạo mới
        value = factory()
        self.set_memory(key, value, ttl)
        self.set_file(key, value, ttl)
        return value

    def clear_all(self) -> int:
        """Xóa toàn bộ cache. Trả về số file đã xóa."""
        count = 0
        self._memory_cache.clear()
        for f in self.cache_dir.iterdir():
            if f.is_file():
                f.unlink()
                count += 1
        logger.info(f"🗑️ Cleared {count} cache files")
        return count

    def clear_expired(self) -> int:
        """Xóa các cache đã hết hạn. Trả về số file đã xóa."""
        count = 0
        for meta_file in self.cache_dir.glob("*.meta.json"):
            try:
                meta = json.loads(meta_file.read_text())
                if time.time() > meta.get("expires_at", 0):
                    key = meta_file.stem.replace(".meta", "")
                    self.delete_file(key)
                    count += 1
            except Exception:
                pass

        # Clear expired memory cache
        expired_keys = [
            k for k, v in self._memory_cache.items()
            if time.time() >= v["expires_at"]
        ]
        for k in expired_keys:
            del self._memory_cache[k]

        if count > 0:
            logger.info(f"🗑️ Cleared {count} expired cache entries")
        return count

    def get_stats(self) -> dict:
        """Lấy thống kê cache."""
        total_size = sum(f.stat().st_size for f in self.cache_dir.iterdir() if f.is_file())
        return {
            "memory_entries": len(self._memory_cache),
            "file_entries": len(list(self.cache_dir.glob("*.meta.json"))),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_dir": str(self.cache_dir),
        }


def get_cache() -> CacheService:
    """Lấy CacheService singleton."""
    return CacheService()
