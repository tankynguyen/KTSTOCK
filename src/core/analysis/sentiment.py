"""
KTSTOCK - Sentiment Analysis
Phân tích cảm xúc thị trường từ tin tức và bình luận.
"""
from typing import Optional
from loguru import logger

from src.utils.decorators import timer


class SentimentAnalyzer:
    """
    Phân tích cảm xúc (sentiment) từ text.
    Sử dụng phương pháp rule-based + keyword scoring.
    (AI-based sentiment sẽ được tích hợp ở Phase 4)
    """

    # Từ khóa tích cực (tiếng Việt + English)
    POSITIVE_KEYWORDS = {
        "vi": [
            "tăng", "tăng mạnh", "tăng trần", "bứt phá", "phục hồi", "khởi sắc",
            "lạc quan", "tích cực", "mua vào", "cổ tức", "lợi nhuận tăng",
            "doanh thu tăng", "vượt kỳ vọng", "đột phá", "hấp dẫn",
            "cơ hội", "tiềm năng", "an toàn", "ổn định", "phát triển",
        ],
        "en": [
            "bullish", "rally", "surge", "breakout", "recovery", "upgrade",
            "buy", "outperform", "strong", "growth", "profit", "dividend",
            "opportunity", "potential", "positive", "beat", "exceed",
        ],
    }

    # Từ khóa tiêu cực
    NEGATIVE_KEYWORDS = {
        "vi": [
            "giảm", "giảm mạnh", "giảm sàn", "bán tháo", "lao dốc", "sụt giảm",
            "bi quan", "tiêu cực", "bán ra", "thua lỗ", "nợ xấu",
            "rủi ro", "cảnh báo", "khủng hoảng", "phá sản", "điều tra",
            "vi phạm", "bong bóng", "suy thoái", "lạm phát",
        ],
        "en": [
            "bearish", "crash", "plunge", "selloff", "downgrade", "decline",
            "sell", "underperform", "weak", "loss", "debt", "risk",
            "warning", "crisis", "bankruptcy", "fraud", "bubble",
            "recession", "inflation",
        ],
    }

    @timer
    def analyze_text(self, text: str, language: str = "vi") -> dict:
        """
        Phân tích sentiment của text.

        Args:
            text: Nội dung cần phân tích
            language: "vi" hoặc "en"

        Returns:
            {"sentiment": str, "score": float (-1 to 1), "positive_count": int, "negative_count": int}
        """
        text_lower = text.lower()

        positive_words = self.POSITIVE_KEYWORDS.get(language, self.POSITIVE_KEYWORDS["vi"])
        negative_words = self.NEGATIVE_KEYWORDS.get(language, self.NEGATIVE_KEYWORDS["vi"])

        pos_count = sum(1 for kw in positive_words if kw in text_lower)
        neg_count = sum(1 for kw in negative_words if kw in text_lower)

        total = pos_count + neg_count
        if total == 0:
            score = 0.0
            sentiment = "neutral"
        else:
            score = (pos_count - neg_count) / total
            if score > 0.3:
                sentiment = "positive"
            elif score < -0.3:
                sentiment = "negative"
            else:
                sentiment = "neutral"

        return {
            "sentiment": sentiment,
            "score": round(score, 3),
            "positive_count": pos_count,
            "negative_count": neg_count,
            "positive_keywords": [kw for kw in positive_words if kw in text_lower],
            "negative_keywords": [kw for kw in negative_words if kw in text_lower],
        }

    def analyze_batch(self, texts: list[str], language: str = "vi") -> dict:
        """
        Phân tích sentiment cho nhiều texts (tin tức).

        Returns:
            {"overall_sentiment", "avg_score", "distribution", "results"}
        """
        results = [self.analyze_text(t, language) for t in texts]

        scores = [r["score"] for r in results]
        avg_score = sum(scores) / len(scores) if scores else 0

        distribution = {
            "positive": sum(1 for r in results if r["sentiment"] == "positive"),
            "neutral": sum(1 for r in results if r["sentiment"] == "neutral"),
            "negative": sum(1 for r in results if r["sentiment"] == "negative"),
        }

        if avg_score > 0.2:
            overall = "positive"
        elif avg_score < -0.2:
            overall = "negative"
        else:
            overall = "neutral"

        return {
            "overall_sentiment": overall,
            "avg_score": round(avg_score, 3),
            "total_texts": len(texts),
            "distribution": distribution,
            "results": results,
        }
