"""
KTSTOCK - Alert Engine
Hệ thống cảnh báo tự động: theo dõi giá, chỉ báo kỹ thuật và thông báo.
"""
from datetime import datetime
from typing import Optional
from loguru import logger

from src.data.database.connection import get_db
from src.utils.constants import AlertCondition, NotificationType


class AlertEngine:
    """
    Engine quản lý và kích hoạt cảnh báo.
    """

    def __init__(self):
        self.db = get_db()

    def create_alert(
        self,
        user_id: int,
        symbol: str,
        condition: str,
        threshold: float,
        notification_type: str = "in_app",
    ) -> int:
        """Tạo cảnh báo mới. Returns alert_id."""
        symbol = symbol.upper().strip()
        
        # Đảm bảo symbol tồn tại trong bảng symbols (để không lỗi FK)
        existing = self.db.execute_one("SELECT symbol FROM symbols WHERE symbol = ?", (symbol,))
        if not existing:
            # Tạm thời insert với exchange unknown nếu chưa có
            self.db.execute_write(
                "INSERT OR IGNORE INTO symbols (symbol, exchange, asset_type) VALUES (?, ?, ?)",
                (symbol, "UNKNOWN", "stock")
            )

        return self.db.execute_insert(
            """INSERT INTO alerts (user_id, symbol, condition, threshold, notification_type)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, symbol, condition, threshold, notification_type)
        )

    def get_alerts(self, user_id: int, active_only: bool = True) -> list[dict]:
        """Lấy danh sách cảnh báo."""
        query = "SELECT * FROM alerts WHERE user_id = ?"
        if active_only:
            query += " AND is_active = 1"
        query += " ORDER BY created_at DESC"
        return self.db.execute(query, (user_id,))

    def toggle_alert(self, alert_id: int) -> None:
        """Bật/tắt cảnh báo."""
        self.db.execute_write(
            "UPDATE alerts SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?",
            (alert_id,)
        )

    def delete_alert(self, alert_id: int) -> None:
        """Xóa cảnh báo."""
        self.db.execute_write("DELETE FROM alerts WHERE id = ?", (alert_id,))

    def check_alerts(self, market_data: dict[str, dict]) -> list[dict]:
        """
        Kiểm tra tất cả cảnh báo active và kích hoạt nếu thỏa điều kiện.

        Args:
            market_data: {symbol: {"price": float, "rsi": float, "volume": int, ...}}

        Returns:
            Danh sách cảnh báo đã kích hoạt
        """
        active_alerts = self.db.execute(
            "SELECT * FROM alerts WHERE is_active = 1"
        )

        triggered = []
        for alert in active_alerts:
            symbol = alert["symbol"]
            data = market_data.get(symbol)
            if not data:
                continue

            is_triggered = self._evaluate_condition(
                alert["condition"],
                alert["threshold"],
                data,
            )

            if is_triggered:
                message = self._build_message(alert, data)
                self._record_trigger(alert["id"], data.get("price", 0), message)
                triggered.append({**alert, "message": message, "triggered_at": datetime.now()})

        if triggered:
            logger.info(f"🔔 {len(triggered)} alerts triggered")
        return triggered

    def _evaluate_condition(self, condition: str, threshold: float, data: dict) -> bool:
        """Đánh giá điều kiện cảnh báo."""
        price = data.get("price", 0)
        rsi = data.get("rsi", 50)
        volume = data.get("volume", 0)
        macd_hist = data.get("macd_hist", 0)

        conditions_map = {
            "price_above": price > threshold,
            "price_below": price < threshold,
            "rsi_overbought": rsi > threshold,
            "rsi_oversold": rsi < threshold,
            "volume_spike": volume > threshold,
            "macd_cross_up": macd_hist > 0,
            "macd_cross_down": macd_hist < 0,
        }

        return conditions_map.get(condition, False)

    def _build_message(self, alert: dict, data: dict) -> str:
        """Tạo thông báo cảnh báo."""
        symbol = alert["symbol"]
        condition = alert["condition"]
        threshold = alert["threshold"]
        price = data.get("price", 0)

        messages = {
            "price_above": f"🔔 {symbol}: Giá {price:,.0f} vượt ngưỡng {threshold:,.0f}",
            "price_below": f"🔔 {symbol}: Giá {price:,.0f} dưới ngưỡng {threshold:,.0f}",
            "rsi_overbought": f"🔔 {symbol}: RSI = {data.get('rsi', 0):.1f} (quá mua)",
            "rsi_oversold": f"🔔 {symbol}: RSI = {data.get('rsi', 0):.1f} (quá bán)",
            "volume_spike": f"🔔 {symbol}: Khối lượng đột biến ({data.get('volume', 0):,.0f})",
            "macd_cross_up": f"🔔 {symbol}: MACD cắt lên (tín hiệu mua)",
            "macd_cross_down": f"🔔 {symbol}: MACD cắt xuống (tín hiệu bán)",
        }

        return messages.get(condition, f"🔔 {symbol}: Cảnh báo {condition}")

    def _record_trigger(self, alert_id: int, value: float, message: str):
        """Ghi lại lịch sử kích hoạt."""
        self.db.execute_write(
            "INSERT INTO alert_history (alert_id, triggered_value, message) VALUES (?, ?, ?)",
            (alert_id, value, message)
        )
        self.db.execute_write(
            "UPDATE alerts SET last_triggered = ? WHERE id = ?",
            (datetime.now().isoformat(), alert_id)
        )

    def get_alert_history(self, user_id: int, limit: int = 50) -> list[dict]:
        """Lấy lịch sử cảnh báo."""
        return self.db.execute(
            """SELECT ah.*, a.symbol, a.condition, a.threshold
               FROM alert_history ah
               JOIN alerts a ON ah.alert_id = a.id
               WHERE a.user_id = ?
               ORDER BY ah.triggered_at DESC
               LIMIT ?""",
            (user_id, limit)
        )

    def mark_read(self, history_id: int):
        """Đánh dấu đã đọc."""
        self.db.execute_write(
            "UPDATE alert_history SET is_read = 1 WHERE id = ?",
            (history_id,)
        )

    def get_unread_count(self, user_id: int) -> int:
        """Đếm số cảnh báo chưa đọc."""
        result = self.db.execute_one(
            """SELECT COUNT(*) as count FROM alert_history ah
               JOIN alerts a ON ah.alert_id = a.id
               WHERE a.user_id = ? AND ah.is_read = 0""",
            (user_id,)
        )
        return result["count"] if result else 0
