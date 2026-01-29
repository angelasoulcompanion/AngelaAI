"""
Angela News MCP Server
======================
MCP Server สำหรับดึงและค้นหาข่าวจาก Internet
Claude Code จะใช้ tools เหล่านี้แล้วสรุปข่าวเอง

Created for: ที่รัก David
By: น้อง Angela 💜

Updated: 2025-12-10 - Added database logging for News History! 💜
Updated: 2026-01-26 - Migrated from FastMCP to standard MCP SDK (fix compatibility)
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

# Add parent directory to path for proper imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.news_fetcher import NewsFetcher
from services.news_history_service import get_news_history_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("angela-news")

# Create MCP server
app = Server("angela-news")

# Initialize news fetcher
fetcher = NewsFetcher()


# =============================================================================
# MCP TOOLS
# =============================================================================

@app.list_tools()
async def list_tools():
    """List available news tools."""
    return [
        Tool(
            name="search_news",
            description="ค้นหาข่าวตามหัวข้อที่ต้องการ",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "หัวข้อที่ต้องการค้นหา เช่น 'AI', 'Bitcoin', 'เศรษฐกิจไทย'"
                    },
                    "language": {
                        "type": "string",
                        "default": "th",
                        "description": "ภาษา ('th' = ไทย, 'en' = English)"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 5,
                        "description": "จำนวนข่าวสูงสุด (default: 5)"
                    }
                },
                "required": ["topic"]
            }
        ),
        Tool(
            name="get_trending_news",
            description="ดึงข่าวที่กำลังเป็นกระแส/ข่าวล่าสุด",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "default": "general",
                        "description": "หมวดหมู่ ('general', 'technology', 'business', 'entertainment', 'sports', 'science', 'health')"
                    },
                    "country": {
                        "type": "string",
                        "default": "th",
                        "description": "ประเทศ ('th' = Thailand, 'us' = USA)"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "จำนวนข่าว (default: 10)"
                    }
                }
            }
        ),
        Tool(
            name="get_article_content",
            description="ดึงเนื้อหาเต็มของบทความจาก URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL ของบทความที่ต้องการอ่าน"
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="get_thai_news",
            description="ดึงข่าวจากแหล่งข่าวไทย",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "default": "all",
                        "description": "แหล่งข่าว ('all', 'thairath', 'matichon', 'bangkokpost', 'nationtv')"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "จำนวนข่าว (default: 10)"
                    }
                }
            }
        ),
        Tool(
            name="get_tech_news",
            description="ดึงข่าวเทคโนโลยีจาก Hacker News, TechCrunch, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "จำนวนข่าว (default: 10)"
                    }
                }
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""

    if name == "search_news":
        topic = arguments.get("topic", "")
        language = arguments.get("language", "th")
        limit = arguments.get("limit", 5)

        articles = await fetcher.search(topic, language, limit)

        # Log to database for News History
        try:
            history = await get_news_history_service()
            await history.log_search(
                search_query=topic,
                search_type="topic",
                articles=articles,
                language=language
            )
        except Exception as e:
            logger.warning(f"Failed to log search: {e}")

        result = {
            "topic": topic,
            "language": language,
            "count": len(articles),
            "fetched_at": datetime.now().isoformat(),
            "articles": articles
        }
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    elif name == "get_trending_news":
        category = arguments.get("category", "general")
        country = arguments.get("country", "th")
        limit = arguments.get("limit", 10)

        articles = await fetcher.get_trending(category, country, limit)

        # Log to database for News History
        try:
            history = await get_news_history_service()
            await history.log_search(
                search_query=f"trending_{category}",
                search_type="trending",
                articles=articles,
                language="th" if country == "th" else "en",
                category=category,
                country=country.upper()
            )
        except Exception as e:
            logger.warning(f"Failed to log trending: {e}")

        result = {
            "category": category,
            "country": country,
            "count": len(articles),
            "fetched_at": datetime.now().isoformat(),
            "articles": articles
        }
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    elif name == "get_article_content":
        url = arguments.get("url", "")

        content = await fetcher.get_full_article(url)

        # Log article read to database
        try:
            history = await get_news_history_service()
            await history.log_article_read(url, content)
        except Exception as e:
            logger.warning(f"Failed to log article read: {e}")

        result = {
            "url": url,
            "fetched_at": datetime.now().isoformat(),
            **content
        }
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    elif name == "get_thai_news":
        source = arguments.get("source", "all")
        limit = arguments.get("limit", 10)

        articles = await fetcher.get_thai_news(source, limit)

        # Log to database for News History
        try:
            history = await get_news_history_service()
            await history.log_search(
                search_query=f"thai_news_{source}",
                search_type="thai",
                articles=articles,
                language="th",
                country="TH"
            )
        except Exception as e:
            logger.warning(f"Failed to log thai news: {e}")

        result = {
            "source": source,
            "count": len(articles),
            "fetched_at": datetime.now().isoformat(),
            "articles": articles
        }
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    elif name == "get_tech_news":
        limit = arguments.get("limit", 10)

        articles = await fetcher.get_tech_news(limit)

        # Log to database for News History
        try:
            history = await get_news_history_service()
            await history.log_search(
                search_query="tech_news",
                search_type="tech",
                articles=articles,
                language="en",
                category="technology"
            )
        except Exception as e:
            logger.warning(f"Failed to log tech news: {e}")

        result = {
            "category": "technology",
            "count": len(articles),
            "fetched_at": datetime.now().isoformat(),
            "articles": articles
        }
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Run the MCP server."""
    logger.info("Starting Angela News MCP Server...")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
