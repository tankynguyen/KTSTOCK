"""
KTSTOCK - vnstock_news Connector
Crawler tin tức từ 21 trang báo Việt Nam.
"""
from typing import Optional

import pandas as pd
from loguru import logger

from src.services.cache_service import get_cache
from src.utils.decorators import timer
from src.utils.helpers import generate_cache_key


# Danh sách 21 trang báo được hỗ trợ
SUPPORTED_SITES = [
    "vnexpress", "tuoitre", "cafef", "dantri", "thanhnien",
    "znews", "tienphong", "vietstock", "cafebiz", "baodautu",
    "vneconomy", "ktsg", "nld", "plo", "nhandan",
    "vietnamnet", "dddn", "petrotimes", "24h", "nguoiquansat",
    "thoibaotaichinhvietnam",
]


class VnstockNewsConnector:
    """
    Connector cho vnstock_news - 21 trang báo Việt Nam.

    Hỗ trợ:
    - RSS Feed: Tin mới nhất (nhanh, < 10 giây)
    - Sitemap: Lịch sử lâu dài (1-2 năm)
    - Batch Crawler: Lấy hàng loạt (đồng bộ)
    - AsyncBatch: Lấy hàng loạt (bất đồng bộ, nhanh 5-10x)
    """

    def __init__(self):
        self._available = False
        self.cache = get_cache()
        try:
            import vnstock_news
            self._vnstock_news = vnstock_news
            self._available = True
            logger.info("✅ vnstock_news connector initialized")
        except ImportError:
            logger.warning("⚠️ vnstock_news not installed. News features unavailable.")

    @property
    def is_available(self) -> bool:
        return self._available

    @property
    def supported_sites(self) -> list[str]:
        """Danh sách trang báo được hỗ trợ."""
        return SUPPORTED_SITES.copy()

    # ============================================================
    # CORE CRAWL METHODS
    # ============================================================

    @timer
    def get_latest_news(self, site_name: str = "vnexpress", limit: int = 20) -> Optional[pd.DataFrame]:
        """
        Lấy tin mới nhất từ RSS feed.

        Args:
            site_name: Tên trang báo (vnexpress, cafef, tuoitre, ...)
            limit: Số bài tối đa

        Returns:
            DataFrame với columns: url, title, short_description, content,
                                   publish_time, author, category, tags, source
        """
        if not self._available:
            return None

        cache_key = generate_cache_key("vnnews_latest", site_name, str(limit))
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock_news import Crawler
            crawler = Crawler(site_name=site_name)
            articles = crawler.get_articles_from_feed(limit_per_feed=limit)

            if articles:
                df = pd.DataFrame(articles) if isinstance(articles, list) else articles
                if not df.empty:
                    self.cache.set_dataframe(cache_key, df, ttl=1800)  # 30 min
                    logger.info(f"📰 Fetched {len(df)} latest articles from {site_name}")
                return df
        except Exception as e:
            logger.error(f"❌ Error fetching latest news from {site_name}: {e}")
        return None

    @timer
    def get_historical_news(self, site_name: str = "cafef", limit: int = 100) -> Optional[pd.DataFrame]:
        """
        Lấy tin tức lịch sử qua Sitemap/Batch.

        Args:
            site_name: Tên trang báo
            limit: Số bài tối đa
        """
        if not self._available:
            return None

        cache_key = generate_cache_key("vnnews_hist", site_name, str(limit))
        cached = self.cache.get_dataframe(cache_key)
        if cached is not None:
            return cached

        try:
            from vnstock_news import BatchCrawler
            crawler = BatchCrawler(site_name=site_name, request_delay=1.0)
            articles = crawler.fetch_articles(limit=limit)

            if articles is not None and len(articles) > 0:
                df = articles if isinstance(articles, pd.DataFrame) else pd.DataFrame(articles)
                self.cache.set_dataframe(cache_key, df, ttl=3600)
                logger.info(f"📰 Fetched {len(df)} historical articles from {site_name}")
                return df
        except Exception as e:
            logger.error(f"❌ Error fetching historical news from {site_name}: {e}")
        return None

    @timer
    def get_batch_news(self, site_name: str = "cafef", limit: int = 50) -> Optional[pd.DataFrame]:
        """
        Batch crawl tin tức (đồng bộ, ổn định).

        Args:
            site_name: Tên trang báo
            limit: Số bài tối đa
        """
        if not self._available:
            return None

        try:
            from vnstock_news import BatchCrawler
            crawler = BatchCrawler(site_name=site_name, request_delay=1.0)
            articles = crawler.fetch_articles(limit=limit)
            if articles is not None and len(articles) > 0:
                df = articles if isinstance(articles, pd.DataFrame) else pd.DataFrame(articles)
                logger.info(f"📰 Batch fetched {len(df)} articles from {site_name}")
                return df
        except Exception as e:
            logger.error(f"❌ Error batch fetching from {site_name}: {e}")
        return None

    @timer
    def search_news(self, keyword: str, site_name: str = "cafef", limit: int = 50) -> Optional[pd.DataFrame]:
        """
        Tìm kiếm tin tức theo từ khóa.

        Args:
            keyword: Từ khóa tìm kiếm (VD: "VCB", "lãi suất", "FED")
            site_name: Trang báo
            limit: Số bài tối đa
        """
        if not self._available:
            return None

        try:
            articles = self.get_latest_news(site_name=site_name, limit=limit)
            if articles is None or articles.empty:
                articles = self.get_batch_news(site_name=site_name, limit=limit)

            if articles is not None and not articles.empty:
                # Tìm trong title và short_description
                keyword_lower = keyword.lower()
                mask = articles.apply(
                    lambda row: any(
                        keyword_lower in str(val).lower()
                        for val in [row.get('title', ''), row.get('short_description', ''), row.get('content', '')]
                    ),
                    axis=1
                )
                filtered = articles[mask]
                logger.info(f"🔍 Found {len(filtered)} articles matching '{keyword}' from {site_name}")
                return filtered
        except Exception as e:
            logger.error(f"❌ Error searching news: {e}")
        return None

    # ============================================================
    # ANALYSIS METHODS
    # ============================================================

    @timer
    def get_trending_keywords(self, site_name: str = "vnexpress", limit: int = 30, top_n: int = 20) -> Optional[list]:
        """
        Trích xuất từ khóa trending từ tiêu đề tin.

        Args:
            site_name: Trang báo
            limit: Số bài để phân tích
            top_n: Số từ khóa top

        Returns:
            List of tuples: [(keyword, count), ...]
        """
        if not self._available:
            return None

        try:
            import re
            from collections import Counter

            articles = self.get_latest_news(site_name=site_name, limit=limit)
            if articles is None or articles.empty:
                return []

            all_words = []
            for _, row in articles.iterrows():
                title = str(row.get('title', ''))
                words = re.findall(r'\w+', title.lower())
                all_words.extend([w for w in words if len(w) >= 3])

            keywords = Counter(all_words).most_common(top_n)
            logger.info(f"📊 Extracted {len(keywords)} trending keywords from {site_name}")
            return keywords
        except Exception as e:
            logger.error(f"❌ Error analyzing trending: {e}")
            return None

    @timer
    def get_stock_news(self, symbol: str, sites: list[str] = None, limit: int = 20) -> Optional[pd.DataFrame]:
        """
        Lấy tin tức liên quan đến mã cổ phiếu.

        Args:
            symbol: Mã cổ phiếu (VD: "VCB")
            sites: Danh sách trang báo (default: cafef, vietstock)
            limit: Số bài mỗi trang
        """
        if not self._available:
            return None

        if sites is None:
            sites = ["cafef", "vietstock", "vnexpress"]

        all_articles = []
        for site in sites:
            try:
                articles = self.search_news(keyword=symbol.upper(), site_name=site, limit=limit)
                if articles is not None and not articles.empty:
                    articles = articles.copy()
                    articles['source_site'] = site
                    all_articles.append(articles)
            except Exception as e:
                logger.warning(f"⚠️ Could not fetch {symbol} news from {site}: {e}")

        if all_articles:
            result = pd.concat(all_articles, ignore_index=True)
            # Sort by publish_time
            if 'publish_time' in result.columns:
                result = result.sort_values('publish_time', ascending=False)
            logger.info(f"📰 Found {len(result)} articles about {symbol} from {len(sites)} sites")
            return result

        return None

    # ============================================================
    # MULTI-SITE METHODS
    # ============================================================

    @timer
    def get_news_from_multiple_sites(
        self, sites: list[str] = None, limit_per_site: int = 10
    ) -> Optional[pd.DataFrame]:
        """
        Lấy tin từ nhiều trang báo cùng lúc.

        Args:
            sites: Danh sách trang báo (default: top 5)
            limit_per_site: Số bài mỗi trang
        """
        if not self._available:
            return None

        if sites is None:
            sites = ["vnexpress", "cafef", "tuoitre", "dantri", "thanhnien"]

        all_articles = []
        for site in sites:
            try:
                articles = self.get_latest_news(site_name=site, limit=limit_per_site)
                if articles is not None and not articles.empty:
                    articles = articles.copy()
                    articles['source_site'] = site
                    all_articles.append(articles)
            except Exception as e:
                logger.warning(f"⚠️ Could not fetch from {site}: {e}")

        if all_articles:
            result = pd.concat(all_articles, ignore_index=True)
            if 'publish_time' in result.columns:
                result = result.sort_values('publish_time', ascending=False)
            return result

        return None
