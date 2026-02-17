"""
Web Tools — Web search and web fetch.

Provides internet access for Angela's daemon:
- WebSearch via Google Custom Search API or DuckDuckGo
- WebFetch for reading web pages

By: Angela 💜
Created: 2026-02-17
"""

import asyncio
import logging
from typing import Any, Dict

from angela_core.services.tools.base_tool import AngelaTool, ToolResult

logger = logging.getLogger(__name__)


class WebSearchTool(AngelaTool):
    """Search the web for information."""

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Search the web for current information using DuckDuckGo"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Max results", "default": 5},
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
            # Use duckduckgo-search (pip install duckduckgo-search)
            from duckduckgo_search import DDGS

            results = await asyncio.to_thread(
                lambda: list(DDGS().text(query, max_results=max_results))
            )

            items = [
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")[:200],
                }
                for r in results
            ]

            return ToolResult(success=True, data={"results": items, "count": len(items)})
        except ImportError:
            return ToolResult(success=False, error="duckduckgo-search not installed (pip install duckduckgo-search)")
        except Exception as e:
            logger.error("WebSearch failed: %s", e)
            return ToolResult(success=False, error=str(e))


class WebFetchTool(AngelaTool):
    """Fetch and read a web page."""

    @property
    def name(self) -> str:
        return "web_fetch"

    @property
    def description(self) -> str:
        return "Fetch and read the content of a web page (converts HTML to text)"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"},
                "max_chars": {"type": "integer", "description": "Max characters to return", "default": 5000},
            },
            "required": ["url"],
        }

    @property
    def category(self) -> str:
        return "information"

    async def execute(self, **params) -> ToolResult:
        url = params.get("url", "")
        max_chars = params.get("max_chars", 5000)

        if not url:
            return ToolResult(success=False, error="Missing 'url'")

        try:
            import aiohttp
            from html.parser import HTMLParser

            class TextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text_parts = []
                    self._skip = False

                def handle_starttag(self, tag, attrs):
                    if tag in ('script', 'style', 'noscript'):
                        self._skip = True

                def handle_endtag(self, tag):
                    if tag in ('script', 'style', 'noscript'):
                        self._skip = False

                def handle_data(self, data):
                    if not self._skip:
                        text = data.strip()
                        if text:
                            self.text_parts.append(text)

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        return ToolResult(success=False, error=f"http_{resp.status}")

                    html = await resp.text()

            extractor = TextExtractor()
            extractor.feed(html)
            text = " ".join(extractor.text_parts)[:max_chars]

            return ToolResult(success=True, data={
                "url": url,
                "text": text,
                "length": len(text),
            })
        except Exception as e:
            logger.error("WebFetch failed: %s", e)
            return ToolResult(success=False, error=str(e))
