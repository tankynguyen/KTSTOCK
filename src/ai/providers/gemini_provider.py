"""
KTSTOCK - Gemini AI Integration
Tích hợp Google Gemini AI cho phân tích thị trường.
"""
import time
from typing import Optional
from loguru import logger

from src.utils.config import get_settings
from src.utils.decorators import retry, timer
from src.services.cache_service import get_cache
from src.utils.helpers import generate_cache_key


class GeminiProvider:
    """
    Provider cho Google Gemini AI.
    Hỗ trợ: phân tích, tóm tắt, chat, generate insight.
    """

    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.ai.gemini_api_key
        self.model_name = "gemini-2.5-flash"
        self._model = None
        self._is_connected = False
        self.cache = get_cache()

    def connect(self) -> bool:
        """Khởi tạo kết nối Gemini."""
        if not self.api_key:
            logger.error("❌ Gemini API key not configured")
            return False

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(self.model_name)
            self._is_connected = True
            logger.info(f"✅ Gemini AI connected (model={self.model_name})")
            return True
        except ImportError:
            logger.error("❌ google-generativeai not installed. Run: pip install google-generativeai")
            return False
        except Exception as e:
            logger.error(f"❌ Gemini connection error: {e}")
            return False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @timer
    @retry(max_retries=2, delay=2.0)
    def generate(self, prompt: str, use_cache: bool = True) -> Optional[str]:
        """
        Gửi prompt đến Gemini và nhận response.

        Args:
            prompt: Nội dung prompt
            use_cache: Có cache kết quả không

        Returns:
            Text response
        """
        if not self._is_connected:
            self.connect()

        if not self._model:
            return None

        # Check cache
        if use_cache:
            cache_key = generate_cache_key("gemini", prompt[:200])
            cached = self.cache.get_file(cache_key)
            if cached is not None:
                logger.debug("📦 Gemini cache hit")
                return cached

        try:
            response = self._model.generate_content(prompt)
            result = response.text

            if use_cache and result:
                self.cache.set_file(cache_key, result, ttl=3600)

            return result
        except Exception as e:
            logger.error(f"❌ Gemini generate error: {e}")
            return None

    def analyze_stock(self, symbol: str, data: dict) -> Optional[str]:
        """
        Phân tích cổ phiếu bằng AI.

        Args:
            symbol: Mã cổ phiếu
            data: Dict chứa dữ liệu thị trường

        Returns:
            Phân tích chi tiết dạng text
        """
        prompt = f"""
Bạn là chuyên gia phân tích chứng khoán Việt Nam. Phân tích chi tiết mã cổ phiếu {symbol}:

📊 DỮ LIỆU THỊ TRƯỜNG:
- Giá hiện tại: {data.get('price', 'N/A')}
- Thay đổi: {data.get('change_pct', 'N/A')}%
- Khối lượng: {data.get('volume', 'N/A')}
- RSI (14): {data.get('rsi', 'N/A')}
- MACD: {data.get('macd', 'N/A')}
- P/E: {data.get('pe_ratio', 'N/A')}
- ROE: {data.get('roe', 'N/A')}%
- Xu hướng: {data.get('trend', 'N/A')}

YÊU CẦU PHÂN TÍCH:
1. 📈 Phân tích kỹ thuật (ngắn gọn)
2. 📋 Phân tích cơ bản (ngắn gọn)
3. 🎯 Khuyến nghị đầu tư (MUA/BÁN/GIỮ)
4. ⚠️ Rủi ro cần lưu ý
5. 🔮 Dự báo ngắn hạn (1-2 tuần)

Trả lời bằng tiếng Việt, ngắn gọn, chuyên nghiệp, có cấu trúc.
"""
        return self.generate(prompt)

    def analyze_crypto(self, symbol: str, data: dict) -> Optional[str]:
        """Phân tích crypto bằng AI."""
        prompt = f"""
Bạn là chuyên gia phân tích crypto. Phân tích cặp {symbol}:

📊 DỮ LIỆU:
- Giá: ${data.get('price', 'N/A')}
- Thay đổi 24h: {data.get('change_pct_24h', 'N/A')}%
- Volume 24h: ${data.get('volume_24h', 'N/A')}
- RSI: {data.get('rsi', 'N/A')}
- Xu hướng: {data.get('trend', 'N/A')}

YÊU CẦU:
1. Phân tích kỹ thuật ngắn gọn
2. Sentiment thị trường
3. Khuyến nghị (LONG/SHORT/ĐỨNG NGOÀI)
4. Mức hỗ trợ/kháng cự
5. Rủi ro

Trả lời bằng tiếng Việt, chuyên nghiệp.
"""
        return self.generate(prompt)

    def summarize_news(self, news_texts: list[str]) -> Optional[str]:
        """Tóm tắt tin tức bằng AI."""
        combined = "\n---\n".join(news_texts[:10])
        prompt = f"""
Tóm tắt các tin tức chứng khoán sau đây thành 5-7 điểm chính:

{combined}

YÊU CẦU:
1. Tóm tắt ngắn gọn, dạng bullet points
2. Đánh giá tác động đến thị trường (tích cực/tiêu cực/trung tính)
3. Highlights quan trọng nhất

Trả lời bằng tiếng Việt.
"""
        return self.generate(prompt)

    def generate_market_report(self, market_summary: dict) -> Optional[str]:
        """Tạo báo cáo thị trường hàng ngày bằng AI."""
        prompt = f"""
Bạn là chuyên gia phân tích thị trường chứng khoán Việt Nam.
Viết báo cáo thị trường ngắn gọn dựa trên dữ liệu sau:

📊 TỔNG QUAN THỊ TRƯỜNG:
- VN-Index: {market_summary.get('vnindex', 'N/A')}
- HNX-Index: {market_summary.get('hnx', 'N/A')}
- Khối lượng: {market_summary.get('total_volume', 'N/A')}
- Tăng/Giảm/Đứng: {market_summary.get('advances', 'N/A')}/{market_summary.get('declines', 'N/A')}/{market_summary.get('unchanged', 'N/A')}
- Top tăng: {market_summary.get('top_gainers', 'N/A')}
- Top giảm: {market_summary.get('top_losers', 'N/A')}
- Khối ngoại: {market_summary.get('foreign_flow', 'N/A')}

YÊU CẦU:
1. Nhận định tổng thể
2. Phân tích dòng tiền
3. Nhóm ngành nổi bật
4. Dự báo phiên tới
5. Khuyến nghị

Viết bằng tiếng Việt, chuyên nghiệp, cấu trúc rõ ràng.
"""
        return self.generate(prompt)

    def chat(self, message: str, context: str = "") -> Optional[str]:
        """Chat với AI về thị trường."""
        prompt = f"""
Bạn là trợ lý AI chuyên về đầu tư chứng khoán và crypto.
{f"Ngữ cảnh: {context}" if context else ""}

Câu hỏi: {message}

Trả lời ngắn gọn, chuyên nghiệp, bằng tiếng Việt.
"""
        return self.generate(prompt, use_cache=False)

    def health_check(self) -> dict:
        """Kiểm tra trạng thái Gemini."""
        start = time.time()
        if not self._is_connected:
            self.connect()

        if not self._model:
            return {"status": "error", "message": "Not connected", "latency_ms": 0}

        try:
            response = self._model.generate_content("Hello")
            latency = (time.time() - start) * 1000
            return {
                "status": "ok",
                "message": f"Gemini OK (model={self.model_name})",
                "latency_ms": round(latency, 1),
            }
        except Exception as e:
            return {"status": "error", "message": str(e), "latency_ms": 0}
