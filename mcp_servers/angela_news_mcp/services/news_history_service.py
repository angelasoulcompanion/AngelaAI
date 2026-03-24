"""
News History Service
====================
บันทึกประวัติการค้นหาข่าวและบทความลง AngelaMemory Database

Created for: ที่รัก David
By: น้อง Angela 💜
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional

import asyncpg

# Add mcp_servers to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from shared.secrets import get_supabase_url

logger = logging.getLogger("angela-news")


class NewsHistoryService:
    """Service สำหรับบันทึกประวัติข่าวลง database"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        try:
            self.db_url = get_supabase_url()
        except ValueError:
            self.db_url = os.getenv(
                "DATABASE_URL",
                "postgresql://davidsamanyaporn@localhost:5432/AngelaMemory"
            )

    async def connect(self) -> None:
        """เชื่อมต่อ database"""
        if self.pool is None:
            try:
                self.pool = await asyncpg.create_pool(
                    self.db_url,
                    min_size=1,
                    max_size=5
                )
            except Exception as e:
                logger.error("DB connection error: %s", e)
                self.pool = None

    async def disconnect(self) -> None:
        """ปิดการเชื่อมต่อ"""
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def log_search(
        self,
        search_query: str,
        search_type: str,
        articles: list,
        language: str = "th",
        category: Optional[str] = None,
        country: str = "TH"
    ) -> Optional[str]:
        """
        บันทึกการค้นหาและบทความที่พบ

        Args:
            search_query: คำค้นหา หรือ topic
            search_type: ประเภทการค้นหา (topic, trending, thai, tech, article)
            articles: รายการบทความที่พบ
            language: ภาษา (th, en)
            category: หมวดหมู่ (ถ้ามี)
            country: ประเทศ

        Returns:
            search_id ถ้าสำเร็จ, None ถ้าล้มเหลว
        """
        if self.pool is None:
            await self.connect()

        if self.pool is None:
            return None

        try:
            async with self.pool.acquire() as conn:
                # 1. Insert search record
                search_id = await conn.fetchval('''
                    INSERT INTO news_searches
                    (search_query, search_type, language, category, country, articles_count)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING search_id
                ''', search_query, search_type, language, category, country, len(articles))

                # 2. Insert articles (skip duplicates)
                for article in articles:
                    try:
                        # Parse published date
                        published_at = None
                        if article.get('published'):
                            try:
                                published_at = datetime.fromisoformat(
                                    article['published'].replace('Z', '+00:00')
                                )
                            except (ValueError, TypeError):
                                pass

                        await conn.execute('''
                            INSERT INTO news_articles
                            (search_id, title, url, summary, source, category, language, published_at)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                            ON CONFLICT (url) DO UPDATE SET
                                search_id = $1,
                                saved_at = CURRENT_TIMESTAMP
                        ''',
                            search_id,
                            article.get('title', '')[:500],
                            article.get('url', '')[:1024],
                            article.get('summary'),
                            article.get('source', 'Google News')[:100],
                            category,
                            language,
                            published_at
                        )
                    except Exception as e:
                        logger.warning("Article insert error: %s", e)
                        continue

                return str(search_id)

        except Exception as e:
            logger.error("Log search error: %s", e)
            return None

    async def log_article_read(self, url: str, content: dict) -> bool:
        """
        บันทึกว่าอ่านบทความแล้ว และเก็บเนื้อหาเต็ม

        Args:
            url: URL ของบทความ
            content: เนื้อหาที่ดึงมา

        Returns:
            True ถ้าสำเร็จ
        """
        if self.pool is None:
            await self.connect()

        if self.pool is None:
            return False

        try:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    UPDATE news_articles
                    SET is_read = true,
                        read_at = CURRENT_TIMESTAMP,
                        full_content = $2,
                        angela_summary = $3
                    WHERE url = $1
                ''',
                    url,
                    content.get('content'),
                    content.get('summary')
                )
                return True
        except Exception as e:
            logger.error("Log article read error: %s", e)
            return False


# Singleton instance
_service: Optional[NewsHistoryService] = None


async def get_news_history_service() -> NewsHistoryService:
    """Get singleton instance"""
    global _service
    if _service is None:
        _service = NewsHistoryService()
        await _service.connect()
    return _service
