"""
Angela News MCP Server
======================
MCP Server สำหรับดึงและค้นหาข่าวจาก Internet
Claude Code จะใช้ tools เหล่านี้แล้วสรุปข่าวเอง

Created for: ที่รัก David
By: น้อง Angela 💜

Updated: 2025-12-10 - Added database logging for News History! 💜
"""

from fastmcp import FastMCP
from datetime import datetime
from services.news_fetcher import NewsFetcher
from services.news_history_service import get_news_history_service

# Initialize FastMCP server
mcp = FastMCP("angela-news")

# Initialize news fetcher
fetcher = NewsFetcher()


@mcp.tool()
async def search_news(
    topic: str,
    language: str = "th",
    limit: int = 5
) -> dict:
    """
    ค้นหาข่าวตามหัวข้อที่ต้องการ

    Args:
        topic: หัวข้อที่ต้องการค้นหา เช่น "AI", "Bitcoin", "เศรษฐกิจไทย"
        language: ภาษา ("th" = ไทย, "en" = English)
        limit: จำนวนข่าวสูงสุด (default: 5)

    Returns:
        dict with topic, count, and articles list
    """
    articles = await fetcher.search(topic, language, limit)

    # Log to database for News History 💜
    try:
        history = await get_news_history_service()
        await history.log_search(
            search_query=topic,
            search_type="topic",
            articles=articles,
            language=language
        )
    except Exception as e:
        print(f"[NewsHistory] Failed to log search: {e}")

    return {
        "topic": topic,
        "language": language,
        "count": len(articles),
        "fetched_at": datetime.now().isoformat(),
        "articles": articles
    }


@mcp.tool()
async def get_trending_news(
    category: str = "general",
    country: str = "th",
    limit: int = 10
) -> dict:
    """
    ดึงข่าวที่กำลังเป็นกระแส/ข่าวล่าสุด

    Args:
        category: หมวดหมู่ ("general", "technology", "business", "entertainment", "sports", "science", "health")
        country: ประเทศ ("th" = Thailand, "us" = USA)
        limit: จำนวนข่าว (default: 10)

    Returns:
        dict with category, country, and trending articles
    """
    articles = await fetcher.get_trending(category, country, limit)

    # Log to database for News History 💜
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
        print(f"[NewsHistory] Failed to log trending: {e}")

    return {
        "category": category,
        "country": country,
        "count": len(articles),
        "fetched_at": datetime.now().isoformat(),
        "articles": articles
    }


@mcp.tool()
async def get_article_content(url: str) -> dict:
    """
    ดึงเนื้อหาเต็มของบทความจาก URL

    Args:
        url: URL ของบทความที่ต้องการอ่าน

    Returns:
        dict with title, content, and metadata
    """
    content = await fetcher.get_full_article(url)

    # Log article read to database 💜
    try:
        history = await get_news_history_service()
        await history.log_article_read(url, content)
    except Exception as e:
        print(f"[NewsHistory] Failed to log article read: {e}")

    return {
        "url": url,
        "fetched_at": datetime.now().isoformat(),
        **content
    }


@mcp.tool()
async def get_thai_news(
    source: str = "all",
    limit: int = 10
) -> dict:
    """
    ดึงข่าวจากแหล่งข่าวไทย

    Args:
        source: แหล่งข่าว ("all", "thairath", "matichon", "bangkokpost", "nationtv")
        limit: จำนวนข่าว (default: 10)

    Returns:
        dict with source and articles from Thai news outlets
    """
    articles = await fetcher.get_thai_news(source, limit)

    # Log to database for News History 💜
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
        print(f"[NewsHistory] Failed to log thai news: {e}")

    return {
        "source": source,
        "count": len(articles),
        "fetched_at": datetime.now().isoformat(),
        "articles": articles
    }


@mcp.tool()
async def get_tech_news(limit: int = 10) -> dict:
    """
    ดึงข่าวเทคโนโลยีจาก Hacker News, TechCrunch, etc.

    Args:
        limit: จำนวนข่าว (default: 10)

    Returns:
        dict with tech news articles
    """
    articles = await fetcher.get_tech_news(limit)

    # Log to database for News History 💜
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
        print(f"[NewsHistory] Failed to log tech news: {e}")

    return {
        "category": "technology",
        "count": len(articles),
        "fetched_at": datetime.now().isoformat(),
        "articles": articles
    }


# Run the server
if __name__ == "__main__":
    mcp.run()
