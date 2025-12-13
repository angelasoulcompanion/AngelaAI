"""
News History Service
บันทึกและดึงประวัติการค้นหาข่าวผ่าน Angela News MCP

Created: 2025-12-10
Author: Angela 💜
"""

import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from angela_core.database import AngelaDatabase


@dataclass
class NewsSearchRecord:
    """Record of a news search"""
    search_id: uuid.UUID
    search_query: str
    search_type: str
    language: str
    category: Optional[str]
    country: str
    articles_count: int
    searched_at: datetime


@dataclass
class NewsArticleRecord:
    """Record of a news article"""
    article_id: uuid.UUID
    search_id: Optional[uuid.UUID]
    title: str
    url: str
    summary: Optional[str]
    source: Optional[str]
    category: Optional[str]
    language: str
    published_at: Optional[datetime]
    saved_at: datetime
    is_read: bool
    read_at: Optional[datetime]


class NewsHistoryService:
    """
    Service for saving and retrieving news search history.

    Usage:
        service = NewsHistoryService()
        await service.initialize()

        # Save a search with articles
        search_id = await service.save_search(
            search_query="Fintech",
            search_type="topic",
            language="th",
            articles=[{"title": "...", "url": "...", ...}]
        )

        # Get recent searches
        searches = await service.get_recent_searches(limit=20)

        await service.cleanup()
    """

    def __init__(self, db: Optional[AngelaDatabase] = None):
        self._db = db
        self._owns_db = db is None

    async def initialize(self) -> None:
        """Initialize database connection if not provided"""
        if self._owns_db:
            self._db = AngelaDatabase()
            await self._db.connect()

    async def cleanup(self) -> None:
        """Cleanup database connection if owned"""
        if self._owns_db and self._db:
            await self._db.disconnect()

    async def save_search(
        self,
        search_query: str,
        search_type: str,
        articles: List[Dict[str, Any]],
        language: str = "th",
        category: Optional[str] = None,
        country: str = "TH"
    ) -> uuid.UUID:
        """
        Save a news search and its articles to database.

        Args:
            search_query: The search term (e.g., "Fintech", "เศรษฐกิจไทย")
            search_type: Type of search ("topic", "trending", "thai", "tech")
            articles: List of article dicts from MCP response
            language: Language code ("th", "en")
            category: Optional category filter
            country: Country code ("TH", "US")

        Returns:
            UUID of the created search record
        """
        # Insert search record
        search_sql = """
            INSERT INTO news_searches
            (search_query, search_type, language, category, country, articles_count)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING search_id
        """

        result = await self._db.fetchrow(
            search_sql,
            search_query,
            search_type,
            language,
            category,
            country,
            len(articles)
        )

        search_id = result['search_id']

        # Save articles
        await self._save_articles(search_id, articles, language)

        return search_id

    async def _save_articles(
        self,
        search_id: uuid.UUID,
        articles: List[Dict[str, Any]],
        default_language: str = "th"
    ) -> int:
        """
        Save articles to database, skipping duplicates.

        Returns:
            Number of articles successfully saved
        """
        saved_count = 0

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

                # Insert article (ON CONFLICT DO NOTHING for duplicates)
                article_sql = """
                    INSERT INTO news_articles
                    (search_id, title, url, summary, source, category, language, published_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (url) DO UPDATE SET
                        search_id = EXCLUDED.search_id,
                        saved_at = CURRENT_TIMESTAMP
                    RETURNING article_id
                """

                result = await self._db.fetchrow(
                    article_sql,
                    search_id,
                    article.get('title', 'Untitled')[:500],
                    article.get('url', '')[:1024],
                    article.get('summary', '')[:5000] if article.get('summary') else None,
                    article.get('source', '')[:100] if article.get('source') else None,
                    article.get('category'),
                    default_language,
                    published_at
                )

                if result:
                    saved_count += 1

            except Exception as e:
                # Log error but continue with other articles
                print(f"⚠️ Error saving article: {e}")
                continue

        return saved_count

    async def get_recent_searches(
        self,
        limit: int = 50
    ) -> List[NewsSearchRecord]:
        """
        Get recent news searches.

        Args:
            limit: Maximum number of searches to return

        Returns:
            List of NewsSearchRecord objects
        """
        sql = """
            SELECT search_id, search_query, search_type, language,
                   category, country, articles_count, searched_at
            FROM news_searches
            ORDER BY searched_at DESC
            LIMIT $1
        """

        rows = await self._db.fetch(sql, limit)

        return [
            NewsSearchRecord(
                search_id=row['search_id'],
                search_query=row['search_query'],
                search_type=row['search_type'],
                language=row['language'],
                category=row['category'],
                country=row['country'],
                articles_count=row['articles_count'],
                searched_at=row['searched_at']
            )
            for row in rows
        ]

    async def get_articles_by_search(
        self,
        search_id: uuid.UUID,
        limit: int = 100
    ) -> List[NewsArticleRecord]:
        """
        Get articles for a specific search.

        Args:
            search_id: UUID of the search
            limit: Maximum articles to return

        Returns:
            List of NewsArticleRecord objects
        """
        sql = """
            SELECT article_id, search_id, title, url, summary, source,
                   category, language, published_at, saved_at, is_read, read_at
            FROM news_articles
            WHERE search_id = $1
            ORDER BY published_at DESC NULLS LAST
            LIMIT $2
        """

        rows = await self._db.fetch(sql, search_id, limit)

        return [self._row_to_article(row) for row in rows]

    async def get_all_articles(
        self,
        limit: int = 100,
        unread_only: bool = False
    ) -> List[NewsArticleRecord]:
        """
        Get all articles (timeline view).

        Args:
            limit: Maximum articles to return
            unread_only: If True, only return unread articles

        Returns:
            List of NewsArticleRecord objects
        """
        where_clause = "WHERE is_read = FALSE" if unread_only else ""

        sql = f"""
            SELECT article_id, search_id, title, url, summary, source,
                   category, language, published_at, saved_at, is_read, read_at
            FROM news_articles
            {where_clause}
            ORDER BY saved_at DESC
            LIMIT $1
        """

        rows = await self._db.fetch(sql, limit)

        return [self._row_to_article(row) for row in rows]

    async def get_articles_by_category(
        self,
        category: str,
        limit: int = 50
    ) -> List[NewsArticleRecord]:
        """Get articles filtered by category"""
        sql = """
            SELECT article_id, search_id, title, url, summary, source,
                   category, language, published_at, saved_at, is_read, read_at
            FROM news_articles
            WHERE category = $1
            ORDER BY saved_at DESC
            LIMIT $2
        """

        rows = await self._db.fetch(sql, category, limit)

        return [self._row_to_article(row) for row in rows]

    async def mark_as_read(self, article_id: uuid.UUID) -> bool:
        """
        Mark an article as read.

        Returns:
            True if successful
        """
        sql = """
            UPDATE news_articles
            SET is_read = TRUE, read_at = CURRENT_TIMESTAMP
            WHERE article_id = $1
            RETURNING article_id
        """

        result = await self._db.fetchrow(sql, article_id)
        return result is not None

    async def get_search_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about news searches.

        Returns:
            Dict with total_searches, total_articles, by_type, by_language
        """
        stats_sql = """
            SELECT
                (SELECT COUNT(*) FROM news_searches) as total_searches,
                (SELECT COUNT(*) FROM news_articles) as total_articles,
                (SELECT COUNT(*) FROM news_articles WHERE is_read = TRUE) as read_articles
        """

        type_sql = """
            SELECT search_type, COUNT(*) as count
            FROM news_searches
            GROUP BY search_type
            ORDER BY count DESC
        """

        lang_sql = """
            SELECT language, COUNT(*) as count
            FROM news_articles
            GROUP BY language
            ORDER BY count DESC
        """

        stats = await self._db.fetchrow(stats_sql)
        types = await self._db.fetch(type_sql)
        langs = await self._db.fetch(lang_sql)

        return {
            'total_searches': stats['total_searches'],
            'total_articles': stats['total_articles'],
            'read_articles': stats['read_articles'],
            'by_type': {row['search_type']: row['count'] for row in types},
            'by_language': {row['language']: row['count'] for row in langs}
        }

    def _row_to_article(self, row) -> NewsArticleRecord:
        """Convert database row to NewsArticleRecord"""
        return NewsArticleRecord(
            article_id=row['article_id'],
            search_id=row['search_id'],
            title=row['title'],
            url=row['url'],
            summary=row['summary'],
            source=row['source'],
            category=row['category'],
            language=row['language'],
            published_at=row['published_at'],
            saved_at=row['saved_at'],
            is_read=row['is_read'],
            read_at=row['read_at']
        )


# Singleton instance for use in Claude Code
_service_instance: Optional[NewsHistoryService] = None


async def get_news_history_service() -> NewsHistoryService:
    """Get or create singleton instance of NewsHistoryService"""
    global _service_instance
    if _service_instance is None:
        _service_instance = NewsHistoryService()
        await _service_instance.initialize()
    return _service_instance


async def save_news_search(
    search_query: str,
    search_type: str,
    articles: List[Dict[str, Any]],
    language: str = "th",
    category: Optional[str] = None
) -> uuid.UUID:
    """
    Convenience function to save a news search.

    Usage in Claude Code:
        from angela_core.services.news_history_service import save_news_search

        await save_news_search(
            search_query="Fintech",
            search_type="topic",
            articles=mcp_result['articles'],
            language="th"
        )
    """
    service = await get_news_history_service()
    return await service.save_search(
        search_query=search_query,
        search_type=search_type,
        articles=articles,
        language=language,
        category=category
    )
