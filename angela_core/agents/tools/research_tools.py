"""
Research Tools - Web, News, and Knowledge Search
Tools สำหรับ Research Agent

Author: Angela AI 💜
Created: 2025-01-25
"""

import asyncio
from typing import Any, Optional, Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool


class WebResearchInput(BaseModel):
    """Input schema for web research tool"""
    query: str = Field(..., description="Search query to research on the web")
    max_results: int = Field(default=5, description="Maximum number of results to return")


class WebResearchTool(BaseTool):
    """
    Tool for searching and researching information on the web.
    Uses DuckDuckGo search via httpx.
    """
    name: str = "web_research"
    description: str = """ค้นหาข้อมูลจาก web.
    ใช้เมื่อต้องการค้นหาข้อมูลทั่วไป, ข่าวสาร, หรือความรู้ใหม่ๆ
    Input: query (search term), max_results (optional, default 5)"""
    args_schema: Type[BaseModel] = WebResearchInput

    def _run(self, query: str, max_results: int = 5) -> str:
        """Search web using DuckDuckGo"""
        try:
            import httpx
            from urllib.parse import quote_plus

            # Use DuckDuckGo HTML search
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }

            with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                response = client.get(search_url, headers=headers)
                response.raise_for_status()
                html = response.text

            # Parse results from HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            results = []
            for result in soup.select(".result"):
                title_elem = result.select_one(".result__title")
                snippet_elem = result.select_one(".result__snippet")
                url_elem = result.select_one(".result__url")

                if title_elem:
                    title = title_elem.get_text(strip=True)
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    url = url_elem.get_text(strip=True) if url_elem else ""

                    results.append({
                        "title": title,
                        "snippet": snippet,
                        "url": url
                    })

                if len(results) >= max_results:
                    break

            if not results:
                return f"ไม่พบข้อมูลสำหรับ: {query}"

            # Format results
            output = f"🔍 Web Research Results for: {query}\n\n"
            for i, item in enumerate(results, 1):
                title = item.get("title", "No title")
                url = item.get("url", "")
                snippet = item.get("snippet", "")[:200]
                output += f"{i}. **{title}**\n   {snippet}...\n   URL: {url}\n\n"

            return output

        except Exception as e:
            return f"Error during web research: {str(e)}"


class NewsSearchInput(BaseModel):
    """Input schema for news search tool"""
    topic: str = Field(..., description="Topic to search for news")
    language: str = Field(default="th", description="Language code (th, en)")
    limit: int = Field(default=5, description="Number of articles to return")


class NewsSearchTool(BaseTool):
    """
    Tool for searching latest news on specific topics.
    Uses NewsHistoryService and MCP News tools.
    """
    name: str = "news_search"
    description: str = """ค้นหาข่าวล่าสุดตามหัวข้อที่ต้องการ
    ใช้เมื่อต้องการข่าวสาร, trends, หรือ updates ล่าสุด
    Input: topic (หัวข้อข่าว), language (th/en), limit (จำนวนข่าว)"""
    args_schema: Type[BaseModel] = NewsSearchInput

    def _run(self, topic: str, language: str = "th", limit: int = 5) -> str:
        """Synchronous wrapper for news search"""
        try:
            from angela_core.services.news_history_service import NewsHistoryService

            async def do_search():
                service = NewsHistoryService()
                await service.initialize()
                results = await service.search_news(topic, language=language, limit=limit)
                await service.close()
                return results

            result = asyncio.get_event_loop().run_until_complete(do_search())

            if not result or not result.get("articles"):
                return f"ไม่พบข่าวสำหรับ: {topic}"

            # Format results
            output = f"📰 News Results for: {topic}\n\n"
            for i, article in enumerate(result["articles"][:limit], 1):
                title = article.get("title", "No title")
                source = article.get("source", "Unknown")
                published = article.get("published_at", "")
                output += f"{i}. **{title}**\n   Source: {source} | {published}\n\n"

            return output

        except Exception as e:
            return f"Error during news search: {str(e)}"


class KnowledgeSearchInput(BaseModel):
    """Input schema for knowledge search tool"""
    query: str = Field(..., description="Query to search in knowledge base")
    category: Optional[str] = Field(default=None, description="Knowledge category to filter")
    limit: int = Field(default=10, description="Number of results to return")


class KnowledgeSearchTool(BaseTool):
    """
    Tool for searching Angela's knowledge base.
    Uses semantic search on knowledge_nodes and learnings tables.
    """
    name: str = "knowledge_search"
    description: str = """ค้นหาความรู้จาก knowledge base ของ Angela
    ใช้เมื่อต้องการค้นหาความรู้ที่ Angela เคยเรียนรู้มา
    Input: query (คำค้นหา), category (optional), limit"""
    args_schema: Type[BaseModel] = KnowledgeSearchInput

    def _run(self, query: str, category: Optional[str] = None, limit: int = 10) -> str:
        """Synchronous wrapper for knowledge search"""
        try:
            from angela_core.database import db

            async def do_search():
                await db.connect()

                # Search in knowledge_nodes (fixed column name: times_referenced)
                sql = """
                    SELECT concept_name, concept_category, my_understanding,
                           understanding_level, times_referenced
                    FROM knowledge_nodes
                    WHERE concept_name ILIKE $1
                       OR my_understanding ILIKE $1
                    ORDER BY understanding_level DESC, times_referenced DESC
                    LIMIT $2
                """
                pattern = f"%{query}%"
                results = await db.fetch(sql, pattern, limit)
                await db.disconnect()
                return results

            # Handle async properly
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import nest_asyncio
                    nest_asyncio.apply()
                results = loop.run_until_complete(do_search())
            except RuntimeError:
                results = asyncio.run(do_search())

            if not results:
                return f"ไม่พบความรู้สำหรับ: {query}"

            # Format results
            output = f"🧠 Knowledge Results for: {query}\n\n"
            for i, item in enumerate(results, 1):
                concept = item.get("concept_name", "Unknown")
                cat = item.get("concept_category", "")
                understanding = item.get("my_understanding", "")[:200]
                level = item.get("understanding_level", 0)
                output += f"{i}. **{concept}** ({cat})\n"
                output += f"   Understanding: {understanding}...\n"
                output += f"   Level: {level}/10\n\n"

            return output

        except Exception as e:
            return f"Error during knowledge search: {str(e)}"
