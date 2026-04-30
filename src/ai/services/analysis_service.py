"""
KTSTOCK - AI Analysis Service
Service layer quản lý tất cả AI providers (Gemini, Grok, DeepSeek).
"""
from typing import Optional
from loguru import logger

from src.ai.providers.gemini_provider import GeminiProvider
from src.data.database.connection import get_db
from src.utils.config import get_settings
from src.utils.constants import AIProvider


class AIAnalysisService:
    """
    Service phân tích AI - tự động chọn provider phù hợp.
    Hỗ trợ fallback giữa các providers.
    """

    def __init__(self, preferred_provider: str = "gemini"):
        settings = get_settings()
        self.db = get_db()
        self.preferred = preferred_provider

        # Khởi tạo providers
        self._providers: dict[str, object] = {}
        self._init_providers(settings)

    def _init_providers(self, settings):
        """Khởi tạo các AI providers có API key."""
        # Gemini
        if settings.ai.gemini_api_key:
            provider = GeminiProvider(settings.ai.gemini_api_key)
            if provider.connect():
                self._providers["gemini"] = provider

        # Grok (placeholder cho tương lai)
        if settings.ai.grok_api_key:
            logger.info("📝 Grok API key found - sẽ tích hợp ở phiên bản sau")

        # DeepSeek (placeholder cho tương lai)
        if settings.ai.deepseek_api_key:
            logger.info("📝 DeepSeek API key found - sẽ tích hợp ở phiên bản sau")

        logger.info(f"🤖 AI Service: {len(self._providers)} providers available")

    @property
    def active_provider(self):
        """Lấy provider đang hoạt động (ưu tiên theo cấu hình)."""
        if self.preferred in self._providers:
            return self._providers[self.preferred]
        # Fallback: dùng provider đầu tiên có sẵn
        if self._providers:
            return next(iter(self._providers.values()))
        return None

    @property
    def is_available(self) -> bool:
        return self.active_provider is not None

    def analyze_stock(self, symbol: str, market_data: dict) -> dict:
        """
        Phân tích cổ phiếu bằng AI.

        Returns:
            {"success": bool, "analysis": str, "provider": str}
        """
        provider = self.active_provider
        if not provider:
            return {"success": False, "analysis": "Không có AI provider khả dụng", "provider": "none"}

        analysis = provider.analyze_stock(symbol, market_data)
        if analysis:
            # Lưu vào database
            self._save_analysis(symbol, self.preferred, "stock_analysis", analysis)
            return {"success": True, "analysis": analysis, "provider": self.preferred}

        return {"success": False, "analysis": "AI không thể phân tích", "provider": self.preferred}

    def analyze_crypto(self, symbol: str, market_data: dict) -> dict:
        """Phân tích crypto bằng AI."""
        provider = self.active_provider
        if not provider:
            return {"success": False, "analysis": "Không có AI provider", "provider": "none"}

        analysis = provider.analyze_crypto(symbol, market_data)
        if analysis:
            self._save_analysis(symbol, self.preferred, "crypto_analysis", analysis)
            return {"success": True, "analysis": analysis, "provider": self.preferred}

        return {"success": False, "analysis": "AI không thể phân tích", "provider": self.preferred}

    def summarize_news(self, news_texts: list[str]) -> dict:
        """Tóm tắt tin tức."""
        provider = self.active_provider
        if not provider:
            return {"success": False, "summary": "Không có AI provider"}

        summary = provider.summarize_news(news_texts)
        return {"success": bool(summary), "summary": summary or "Không thể tóm tắt"}

    def generate_report(self, market_summary: dict) -> dict:
        """Tạo báo cáo thị trường."""
        provider = self.active_provider
        if not provider:
            return {"success": False, "report": "Không có AI provider"}

        report = provider.generate_market_report(market_summary)
        return {"success": bool(report), "report": report or "Không thể tạo báo cáo"}

    def chat(self, message: str, context: str = "") -> str:
        """Chat với AI."""
        provider = self.active_provider
        if not provider:
            return "❌ Không có AI provider khả dụng. Vui lòng cấu hình API key."

        response = provider.chat(message, context)
        return response or "⚠️ AI không thể trả lời. Vui lòng thử lại."

    def get_analysis_history(self, symbol: str, limit: int = 10) -> list[dict]:
        """Lấy lịch sử phân tích AI cho symbol."""
        return self.db.execute(
            """SELECT * FROM ai_analysis WHERE symbol = ?
               ORDER BY created_at DESC LIMIT ?""",
            (symbol.upper(), limit)
        )

    def _save_analysis(self, symbol: str, provider: str, analysis_type: str, text: str):
        """Lưu kết quả phân tích vào database."""
        try:
            self.db.execute_insert(
                """INSERT INTO ai_analysis (symbol, provider, analysis_type, analysis_text)
                   VALUES (?, ?, ?, ?)""",
                (symbol.upper(), provider, analysis_type, text)
            )
        except Exception as e:
            logger.warning(f"⚠️ Failed to save AI analysis: {e}")

    def get_health_status(self) -> dict:
        """Trạng thái tất cả providers."""
        statuses = {}
        for name, provider in self._providers.items():
            try:
                statuses[name] = provider.health_check()
            except Exception as e:
                statuses[name] = {"status": "error", "message": str(e)}

        return {
            "providers": statuses,
            "preferred": self.preferred,
            "active": self.preferred if self.preferred in self._providers else None,
            "total_available": len(self._providers),
        }
