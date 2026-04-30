"""
KTSTOCK - Authentication Manager
Quản lý đăng nhập, đăng ký, session và bảo mật.
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from loguru import logger

from src.data.database.connection import get_db
from src.utils.constants import UserRole


class AuthManager:
    """Quản lý xác thực người dùng."""

    SESSION_DURATION_HOURS = 24

    def __init__(self):
        self.db = get_db()

    def hash_password(self, password: str) -> str:
        """Hash mật khẩu bằng bcrypt."""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Kiểm tra mật khẩu."""
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"),
                password_hash.encode("utf-8")
            )
        except Exception:
            return False

    def register(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str = "",
        role: str = UserRole.USER.value,
    ) -> dict:
        """
        Đăng ký user mới.

        Returns:
            {"success": bool, "message": str, "user_id": int|None}
        """
        # Kiểm tra username đã tồn tại
        existing = self.db.execute_one(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (username, email)
        )
        if existing:
            return {"success": False, "message": "Username hoặc email đã tồn tại", "user_id": None}

        # Hash password và tạo user
        password_hash = self.hash_password(password)
        user_id = self.db.execute_insert(
            """INSERT INTO users (username, email, password_hash, full_name, role)
               VALUES (?, ?, ?, ?, ?)""",
            (username, email, password_hash, full_name, role)
        )

        # Tạo default settings
        self.db.execute_write(
            "INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)",
            (user_id,)
        )

        # Tạo default watchlist
        self.db.execute_write(
            "INSERT INTO watchlists (user_id, name) VALUES (?, ?)",
            (user_id, "Mặc định")
        )

        logger.info(f"✅ New user registered: {username} (role={role})")
        return {"success": True, "message": "Đăng ký thành công!", "user_id": user_id}

    def login(self, username: str, password: str) -> dict:
        """
        Đăng nhập.

        Returns:
            {"success": bool, "message": str, "user": dict|None, "token": str|None}
        """
        user = self.db.execute_one(
            "SELECT * FROM users WHERE (username = ? OR email = ?) AND is_active = 1",
            (username, username)
        )

        if not user:
            return {"success": False, "message": "Tài khoản không tồn tại hoặc đã bị khóa", "user": None, "token": None}

        if not self.verify_password(password, user["password_hash"]):
            return {"success": False, "message": "Mật khẩu không đúng", "user": None, "token": None}

        # Tạo session token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=self.SESSION_DURATION_HOURS)

        self.db.execute_write(
            "INSERT INTO sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)",
            (user["id"], token, expires_at.isoformat())
        )

        # Update last_login
        self.db.execute_write(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.now().isoformat(), user["id"])
        )

        user_data = {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "language": user["language"],
        }

        logger.info(f"✅ User logged in: {username}")
        return {"success": True, "message": "Đăng nhập thành công!", "user": user_data, "token": token}

    def validate_session(self, token: str) -> Optional[dict]:
        """
        Kiểm tra session token còn hợp lệ không.

        Returns:
            User dict nếu hợp lệ, None nếu hết hạn
        """
        result = self.db.execute_one(
            """SELECT u.id, u.username, u.email, u.full_name, u.role, u.language
               FROM sessions s
               JOIN users u ON s.user_id = u.id
               WHERE s.session_token = ? AND s.expires_at > ? AND u.is_active = 1""",
            (token, datetime.now().isoformat())
        )
        return dict(result) if result else None

    def logout(self, token: str) -> None:
        """Đăng xuất - xóa session."""
        self.db.execute_write(
            "DELETE FROM sessions WHERE session_token = ?",
            (token,)
        )
        logger.info("✅ User logged out")

    def change_password(self, user_id: int, old_password: str, new_password: str) -> dict:
        """Đổi mật khẩu."""
        user = self.db.execute_one("SELECT password_hash FROM users WHERE id = ?", (user_id,))
        if not user:
            return {"success": False, "message": "User không tồn tại"}

        if not self.verify_password(old_password, user["password_hash"]):
            return {"success": False, "message": "Mật khẩu cũ không đúng"}

        new_hash = self.hash_password(new_password)
        self.db.execute_write(
            "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
            (new_hash, datetime.now().isoformat(), user_id)
        )
        return {"success": True, "message": "Đổi mật khẩu thành công!"}

    def get_all_users(self) -> list[dict]:
        """Lấy danh sách tất cả users (dùng cho Admin)."""
        return self.db.execute(
            """SELECT id, username, email, full_name, role, is_active,
                      last_login, created_at
               FROM users ORDER BY created_at DESC"""
        )

    def update_user_role(self, user_id: int, new_role: str) -> bool:
        """Admin: cập nhật role của user."""
        valid_roles = [r.value for r in UserRole]
        if new_role not in valid_roles:
            return False
        self.db.execute_write(
            "UPDATE users SET role = ?, updated_at = ? WHERE id = ?",
            (new_role, datetime.now().isoformat(), user_id)
        )
        logger.info(f"✅ User {user_id} role updated to {new_role}")
        return True

    def toggle_user_active(self, user_id: int) -> bool:
        """Admin: kích hoạt/vô hiệu hóa user."""
        self.db.execute_write(
            "UPDATE users SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?",
            (user_id,)
        )
        return True

    def cleanup_expired_sessions(self) -> int:
        """Dọn dẹp session hết hạn."""
        count = self.db.execute_write(
            "DELETE FROM sessions WHERE expires_at < ?",
            (datetime.now().isoformat(),)
        )
        if count > 0:
            logger.info(f"🗑️ Cleaned up {count} expired sessions")
        return count
