"""
News Tools — Search and fetch trending news.

Wraps the existing NewsFetcher for tool-based access.

By: Angela 💜
Created: 2026-02-17
"""

import asyncio
import logging
from typing import Any, Dict

from angela_core.services.tools.base_tool import AngelaTool, ToolResult

logger = logging.getLogger(__name__)


class SearchNewsTool(AngelaTool):
    """Search for news articles by topic."""

    @property
    def name(self) -> str:
        return "search_news"

    @property
    def description(self) -> str:
        return "Search for recent news articles by topic (AI, business, Thailand, tech)"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "News search query (e.g. 'AI LLM', 'Thailand economy')"},
                "max_results": {"type": "integer", "description": "Max articles", "default": 5},
            },
            "required": ["query"],
        }

    @property
    def category(self) -> str:
        return "information"

    async def execute(self, **params) -> ToolResult:
        query = params.get("query", "")
        max_results = params.get("max_results", 5)

        if not query:
            return ToolResult(success=False, error="Missing 'query'")

        try:
            from angela_core.daemon.daily_news_sender import NewsFetcher
            fetcher = NewsFetcher()
            articles = await fetcher.search_news(query, max_results=max_results)

            results = [
                {
                    "title": a.get("title", ""),
                    "source": a.get("source", ""),
                    "url": a.get("url", ""),
                    "snippet": a.get("description", "")[:200],
                }
                for a in (articles or [])[:max_results]
            ]

            return ToolResult(success=True, data={"articles": results, "count": len(results)})
        except Exception as e:
            logger.error("SearchNews failed: %s", e)
            return ToolResult(success=False, error=str(e))


class GetTrendingNewsTool(AngelaTool):
    """Get today's trending news across all categories."""

    @property
    def name(self) -> str:
        return "get_trending_news"

    @property
    def description(self) -> str:
        return "Get today's trending news headlines across AI, business, and Thailand"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "News category",
                    "enum": ["tech", "business", "thai", "all"],
                    "default": "all",
                },
            },
        }

    @property
    def category(self) -> str:
        return "information"

    async def execute(self, **params) -> ToolResult:
        cat = params.get("category", "all")

        try:
            from angela_core.daemon.daily_news_sender import NewsFetcher
            fetcher = NewsFetcher()

            if cat == "tech":
                articles = await fetcher.search_news("AI technology LLM", max_results=5)
            elif cat == "business":
                articles = await fetcher.search_news("business finance economy", max_results=5)
            elif cat == "thai":
                articles = await fetcher.search_news("Thailand news", max_results=5)
            else:
                articles = await fetcher.search_news("top news today", max_results=5)

            results = [
                {"title": a.get("title", ""), "source": a.get("source", ""), "url": a.get("url", "")}
                for a in (articles or [])[:5]
            ]

            return ToolResult(success=True, data={"articles": results, "count": len(results)})
        except Exception as e:
            logger.error("GetTrendingNews failed: %s", e)
            return ToolResult(success=False, error=str(e))
