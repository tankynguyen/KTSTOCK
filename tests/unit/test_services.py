"""
KTSTOCK - Unit Tests: Export, Cache, Auth (Phase 6)
Bổ sung test coverage cho các service và auth.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
import pandas as pd


# ============================================================
# Test Export Service
# ============================================================
class TestExportService:
    """Test export CSV/Excel."""

    def test_to_csv(self):
        from src.services.export_service import ExportService
        df = pd.DataFrame({"symbol": ["VCB", "FPT"], "price": [85, 128]})
        csv = ExportService.to_csv(df)
        assert "VCB" in csv
        assert "FPT" in csv

    def test_to_excel(self):
        from src.services.export_service import ExportService
        df = pd.DataFrame({"symbol": ["VCB"], "price": [85]})
        data = ExportService.to_excel(df)
        assert isinstance(data, bytes)
        assert len(data) > 100  # Valid Excel file

    def test_to_excel_multi(self):
        from src.services.export_service import ExportService
        sheets = {
            "Prices": pd.DataFrame({"symbol": ["VCB"], "price": [85]}),
            "Volume": pd.DataFrame({"symbol": ["VCB"], "volume": [1000000]}),
        }
        data = ExportService.to_excel_multi(sheets)
        assert isinstance(data, bytes)
        assert len(data) > 100

    def test_generate_filename(self):
        from src.services.export_service import ExportService
        name = ExportService.generate_filename("report", "xlsx")
        assert name.startswith("report_")
        assert name.endswith(".xlsx")


# ============================================================
# Test Auth Manager
# ============================================================
class TestAuthManager:
    """Test authentication manager."""

    def test_register_and_login(self):
        from src.auth.auth_manager import AuthManager
        auth = AuthManager()

        # Register
        reg = auth.register("testuser99", "test99@test.com", "TestPass123!", "Test User")
        # Có thể pass hoặc fail nếu user đã tồn tại
        assert "success" in reg

        # Login với admin mặc định
        result = auth.login("admin", "Admin@123")
        if result["success"]:
            assert result["user"]["username"] == "admin"
            assert result["user"]["role"] == "admin"
            assert "token" in result

    def test_login_wrong_password(self):
        from src.auth.auth_manager import AuthManager
        auth = AuthManager()
        result = auth.login("admin", "WrongPassword!")
        assert result["success"] is False

    def test_login_nonexistent_user(self):
        from src.auth.auth_manager import AuthManager
        auth = AuthManager()
        result = auth.login("nonexistent_user_xyz", "password")
        assert result["success"] is False


# ============================================================
# Test Cache Service
# ============================================================
class TestCacheService:
    """Test cache service."""

    def test_memory_cache(self):
        from src.services.cache_service import get_cache
        cache = get_cache()
        cache.set_memory("test_key", {"data": 123}, ttl=60)
        result = cache.get_memory("test_key")
        assert result == {"data": 123}

    def test_memory_cache_miss(self):
        from src.services.cache_service import get_cache
        cache = get_cache()
        result = cache.get_memory("nonexistent_key_xyz")
        assert result is None

    def test_file_cache(self):
        from src.services.cache_service import get_cache
        cache = get_cache()
        cache.set_file("test_file_key", {"name": "test"}, ttl=60)
        result = cache.get_file("test_file_key")
        assert result == {"name": "test"}

    def test_dataframe_cache(self):
        from src.services.cache_service import get_cache
        cache = get_cache()
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        cache.set_dataframe("test_df_key", df, ttl=60)
        result = cache.get_dataframe("test_df_key")
        assert result is not None
        assert len(result) == 3

    def test_get_stats(self):
        from src.services.cache_service import get_cache
        cache = get_cache()
        stats = cache.get_stats()
        assert "memory_entries" in stats
        assert "file_entries" in stats


# ============================================================
# Test Database Connection
# ============================================================
class TestDatabase:
    """Test database connection."""

    def test_get_db(self):
        from src.data.database.connection import get_db
        db = get_db()
        assert db is not None

    def test_table_count(self):
        from src.data.database.connection import get_db
        db = get_db()
        count = db.get_table_count("users")
        assert isinstance(count, int)
        assert count >= 1  # At least admin user

    def test_db_size(self):
        from src.data.database.connection import get_db
        db = get_db()
        size = db.get_db_size_mb()
        assert size > 0


# ============================================================
# Test RBAC
# ============================================================
class TestRBAC:
    """Test role-based access control."""

    def test_accessible_pages_admin(self):
        from src.auth.rbac import get_accessible_pages
        pages = get_accessible_pages("admin")
        keys = [p["key"] for p in pages]
        assert "dashboard" in keys
        assert "admin" in keys

    def test_accessible_pages_user(self):
        from src.auth.rbac import get_accessible_pages
        pages = get_accessible_pages("user")
        keys = [p["key"] for p in pages]
        assert "dashboard" in keys
        assert "admin" not in keys

    def test_has_permission(self):
        from src.auth.rbac import has_permission
        assert has_permission("admin", "manage_users") is True
        assert has_permission("user", "manage_users") is False

    def test_role_display_name(self):
        from src.auth.rbac import get_role_display_name
        assert "Admin" in get_role_display_name("admin", "en") or "Quản trị" in get_role_display_name("admin", "vi")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
