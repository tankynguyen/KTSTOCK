"""
KTSTOCK - Database Connection Manager
Singleton quản lý kết nối SQLite, khởi tạo schema, và cung cấp helper methods.
"""
import sqlite3
import threading
from pathlib import Path
from typing import Any, Optional
from contextlib import contextmanager

from loguru import logger

from src.utils.config import PROJECT_ROOT, get_settings


class DatabaseManager:
    """
    Singleton quản lý kết nối SQLite.
    Thread-safe với threading.Lock.
    """

    _instance: Optional["DatabaseManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "DatabaseManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        settings = get_settings()
        # Trích xuất path từ connection string
        db_url = settings.database.database_url
        if db_url.startswith("sqlite:///"):
            db_path = db_url.replace("sqlite:///", "")
        else:
            db_path = str(PROJECT_ROOT / "data" / "ktstock.db")

        self.db_path = Path(db_path)
        if not self.db_path.is_absolute():
            self.db_path = PROJECT_ROOT / self.db_path

        # Đảm bảo thư mục tồn tại
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._schema_path = Path(__file__).parent / "schema.sql"
        self._initialized = True

        # Khởi tạo database
        self._init_database()
        logger.info(f"✅ Database initialized: {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Tạo connection mới (mỗi thread cần connection riêng)."""
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        conn.row_factory = sqlite3.Row  # Trả về dict-like rows
        conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    @contextmanager
    def get_connection(self):
        """Context manager cho database connection."""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Database error: {e}")
            raise
        finally:
            conn.close()

    def _init_database(self):
        """Khởi tạo database schema từ file SQL."""
        if not self._schema_path.exists():
            logger.warning(f"⚠️ Schema file not found: {self._schema_path}")
            return

        schema_sql = self._schema_path.read_text(encoding="utf-8")
        with self.get_connection() as conn:
            conn.executescript(schema_sql)
            logger.info("✅ Database schema applied successfully")

    def execute(self, query: str, params: tuple = ()) -> list[dict]:
        """
        Thực thi query SELECT và trả về danh sách dict.

        Args:
            query: SQL query
            params: Parameters cho query

        Returns:
            List of dict results
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def execute_one(self, query: str, params: tuple = ()) -> Optional[dict]:
        """Thực thi query và trả về 1 kết quả."""
        results = self.execute(query, params)
        return results[0] if results else None

    def execute_write(self, query: str, params: tuple = ()) -> int:
        """
        Thực thi query INSERT/UPDATE/DELETE.

        Returns:
            Số rows bị ảnh hưởng
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.rowcount

    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """
        Thực thi INSERT và trả về ID mới.

        Returns:
            ID của row mới
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.lastrowid

    def execute_many(self, query: str, params_list: list[tuple]) -> int:
        """Thực thi batch INSERT/UPDATE."""
        with self.get_connection() as conn:
            cursor = conn.executemany(query, params_list)
            return cursor.rowcount

    def table_exists(self, table_name: str) -> bool:
        """Kiểm tra bảng có tồn tại không."""
        result = self.execute_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return result is not None

    def get_table_count(self, table_name: str) -> int:
        """Đếm số rows trong bảng."""
        result = self.execute_one(f"SELECT COUNT(*) as count FROM {table_name}")
        return result["count"] if result else 0

    def get_db_size_mb(self) -> float:
        """Lấy kích thước database (MB)."""
        if self.db_path.exists():
            return self.db_path.stat().st_size / (1024 * 1024)
        return 0.0


def get_db() -> DatabaseManager:
    """Lấy DatabaseManager singleton."""
    return DatabaseManager()
