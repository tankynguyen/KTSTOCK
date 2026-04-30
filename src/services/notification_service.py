"""
KTSTOCK - Notification Service
Gửi thông báo qua Telegram, Email, và Zalo.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from loguru import logger

from src.utils.config import get_settings
from src.utils.decorators import retry


class TelegramNotifier:
    """Gửi thông báo qua Telegram Bot."""

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        settings = get_settings()
        self.bot_token = bot_token or settings.notification.telegram_bot_token
        self.chat_id = chat_id or settings.notification.telegram_chat_id

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    @retry(max_retries=2, delay=1.0)
    def send(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Gửi tin nhắn qua Telegram.

        Args:
            message: Nội dung tin nhắn
            parse_mode: "HTML" hoặc "Markdown"
        """
        if not self.is_configured:
            logger.warning("⚠️ Telegram not configured")
            return False

        try:
            import httpx
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode,
            }
            resp = httpx.post(url, json=data, timeout=10)
            resp.raise_for_status()
            logger.info("✅ Telegram message sent")
            return True
        except Exception as e:
            logger.error(f"❌ Telegram send error: {e}")
            return False


class EmailNotifier:
    """Gửi thông báo qua Email (SMTP)."""

    def __init__(self):
        settings = get_settings()
        self.smtp_host = settings.notification.email_smtp_host
        self.smtp_port = settings.notification.email_smtp_port
        self.username = settings.notification.email_username
        self.password = settings.notification.email_password

    @property
    def is_configured(self) -> bool:
        return bool(self.username and self.password)

    @retry(max_retries=2, delay=2.0)
    def send(self, to_email: str, subject: str, body: str, html: bool = False) -> bool:
        """Gửi email."""
        if not self.is_configured:
            logger.warning("⚠️ Email not configured")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.username
            msg["To"] = to_email
            msg["Subject"] = subject

            if html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info(f"✅ Email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"❌ Email send error: {e}")
            return False


class NotificationService:
    """Service thống nhất cho tất cả kênh thông báo."""

    def __init__(self):
        self.telegram = TelegramNotifier()
        self.email = EmailNotifier()

    def send_alert(self, message: str, channels: list[str] = None, email_to: str = "") -> dict:
        """
        Gửi cảnh báo qua nhiều kênh.

        Args:
            message: Nội dung
            channels: ["telegram", "email", "in_app"]
            email_to: Địa chỉ email nhận

        Returns:
            {"telegram": bool, "email": bool}
        """
        channels = channels or ["in_app"]
        results = {}

        if "telegram" in channels and self.telegram.is_configured:
            results["telegram"] = self.telegram.send(message)

        if "email" in channels and self.email.is_configured and email_to:
            results["email"] = self.email.send(
                email_to,
                "🔔 KT Stock Alert",
                message,
            )

        if "in_app" in channels:
            results["in_app"] = True  # Luôn lưu in-app

        return results

    def send_daily_report(self, report: str, email_to: str = "") -> dict:
        """Gửi báo cáo hàng ngày."""
        results = {}

        if self.telegram.is_configured:
            results["telegram"] = self.telegram.send(f"📊 <b>Báo cáo thị trường</b>\n\n{report}")

        if self.email.is_configured and email_to:
            html_report = f"<h2>📊 Báo cáo thị trường hàng ngày</h2><pre>{report}</pre>"
            results["email"] = self.email.send(
                email_to, "📊 KT Stock - Báo cáo thị trường", html_report, html=True
            )

        return results

    def get_status(self) -> dict:
        """Trạng thái các kênh thông báo."""
        return {
            "telegram": {"configured": self.telegram.is_configured},
            "email": {"configured": self.email.is_configured},
            "zalo": {"configured": False, "note": "Sẽ tích hợp ở phiên bản sau"},
        }
