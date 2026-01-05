"""
News Fetcher Service
====================
Service for fetching news from various sources (RSS, APIs, Web scraping)
"""

import aiohttp
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser as date_parser
from typing import Optional
import urllib.parse


class NewsFetcher:
    """Fetch news from various sources"""

    # Google News RSS
    GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl={lang}&gl={country}&ceid={country}:{lang}"

    # Thai News RSS Feeds
    THAI_NEWS_FEEDS = {
        "thairath": "https://www.thairath.co.th/rss/news.xml",
        "matichon": "https://www.matichon.co.th/feed",
        "bangkokpost": "https://www.bangkokpost.com/rss/data/headlines.xml",
        "nationtv": "https://www.nationtv.tv/rss/news.xml",
    }

    # Tech News RSS Feeds
    TECH_NEWS_FEEDS = {
        "hackernews": "https://hnrss.org/frontpage",
        "techcrunch": "https://techcrunch.com/feed/",
        "theverge": "https://www.theverge.com/rss/index.xml",
        "arstechnica": "https://feeds.arstechnica.com/arstechnica/technology-lab",
    }

    # News API categories
    CATEGORIES = ["general", "technology", "business", "entertainment", "sports", "science", "health"]

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                }
            )
        return self.session

    async def search(self, topic: str, language: str = "th", limit: int = 5) -> list:
        """
        Search news by topic using Google News RSS

        Args:
            topic: Search query
            language: Language code (th, en)
            limit: Max results

        Returns:
            List of article dicts
        """
        session = await self._get_session()

        # Build Google News RSS URL
        lang = "th" if language == "th" else "en"
        country = "TH" if language == "th" else "US"
        encoded_query = urllib.parse.quote(topic)

        url = self.GOOGLE_NEWS_RSS.format(
            query=encoded_query,
            lang=lang,
            country=country
        )

        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return []

                content = await resp.text()
                feed = feedparser.parse(content)

                articles = []
                for entry in feed.entries[:limit]:
                    articles.append(self._parse_rss_entry(entry, "Google News"))

                return articles

        except Exception as e:
            print(f"Error searching news: {e}")
            return []

    async def get_trending(self, category: str = "general", country: str = "th", limit: int = 10) -> list:
        """
        Get trending/top news

        Args:
            category: News category
            country: Country code
            limit: Max results

        Returns:
            List of trending articles
        """
        session = await self._get_session()

        # Use Google News top stories
        lang = "th" if country == "th" else "en"
        country_code = "TH" if country == "th" else "US"

        if category == "general":
            url = f"https://news.google.com/rss?hl={lang}&gl={country_code}&ceid={country_code}:{lang}"
        else:
            # Map category to Google News topic
            topic_map = {
                "technology": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB",
                "business": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB",
                "entertainment": "CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtVnVHZ0pWVXlnQVAB",
                "sports": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnVHZ0pWVXlnQVAB",
                "science": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y1RjU0FtVnVHZ0pWVXlnQVAB",
                "health": "CAAqIQgKIhtDQkFTRGdvSUwyMHZNR3QwTlRFU0FtVnVLQUFQAQ",
            }
            topic_id = topic_map.get(category, "")
            url = f"https://news.google.com/rss/topics/{topic_id}?hl={lang}&gl={country_code}&ceid={country_code}:{lang}"

        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return []

                content = await resp.text()
                feed = feedparser.parse(content)

                articles = []
                for entry in feed.entries[:limit]:
                    articles.append(self._parse_rss_entry(entry, "Google News"))

                return articles

        except Exception as e:
            print(f"Error fetching trending: {e}")
            return []

    async def get_thai_news(self, source: str = "all", limit: int = 10) -> list:
        """
        Get news from Thai news sources

        Args:
            source: Source name or "all"
            limit: Max results per source

        Returns:
            List of articles
        """
        session = await self._get_session()
        articles = []

        sources = self.THAI_NEWS_FEEDS if source == "all" else {source: self.THAI_NEWS_FEEDS.get(source)}

        for name, url in sources.items():
            if url is None:
                continue

            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        continue

                    content = await resp.text()
                    feed = feedparser.parse(content)

                    per_source_limit = limit if source != "all" else max(3, limit // len(sources))

                    for entry in feed.entries[:per_source_limit]:
                        articles.append(self._parse_rss_entry(entry, name.capitalize()))

            except Exception as e:
                print(f"Error fetching from {name}: {e}")
                continue

        return articles[:limit]

    async def get_tech_news(self, limit: int = 10) -> list:
        """
        Get tech news from various sources

        Args:
            limit: Max results

        Returns:
            List of tech articles
        """
        session = await self._get_session()
        articles = []

        for name, url in self.TECH_NEWS_FEEDS.items():
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        continue

                    content = await resp.text()
                    feed = feedparser.parse(content)

                    per_source_limit = max(3, limit // len(self.TECH_NEWS_FEEDS))

                    for entry in feed.entries[:per_source_limit]:
                        articles.append(self._parse_rss_entry(entry, name.capitalize()))

            except Exception as e:
                print(f"Error fetching from {name}: {e}")
                continue

        return articles[:limit]

    async def get_full_article(self, url: str) -> dict:
        """
        Fetch full article content from URL

        Args:
            url: Article URL

        Returns:
            Dict with title, content, etc.
        """
        session = await self._get_session()

        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return {"error": f"HTTP {resp.status}", "content": None}

                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")

                # Remove unwanted elements
                for tag in soup(["script", "style", "nav", "header", "footer", "aside", "iframe", "noscript"]):
                    tag.decompose()

                # Try to find article content
                article = soup.find("article") or soup.find("main") or soup.find(class_=["article", "post", "content", "entry"])

                if article:
                    content = article.get_text(separator="\n", strip=True)
                else:
                    # Fallback: get all paragraphs
                    paragraphs = soup.find_all("p")
                    content = "\n\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50)

                # Get title
                title = ""
                if soup.title:
                    title = soup.title.string or ""
                elif soup.h1:
                    title = soup.h1.get_text(strip=True)

                # Limit content length
                if len(content) > 5000:
                    content = content[:5000] + "..."

                return {
                    "title": title,
                    "content": content,
                    "content_length": len(content),
                    "success": True
                }

        except Exception as e:
            return {
                "error": str(e),
                "content": None,
                "success": False
            }

    def _parse_rss_entry(self, entry: dict, source: str) -> dict:
        """Parse RSS feed entry to article dict"""
        # Parse published date
        published = None
        if hasattr(entry, "published"):
            try:
                published = date_parser.parse(entry.published).isoformat()
            except:
                published = entry.published

        # Get summary/description
        summary = ""
        if hasattr(entry, "summary"):
            # Clean HTML from summary
            soup = BeautifulSoup(entry.summary, "html.parser")
            summary = soup.get_text(strip=True)[:500]

        return {
            "title": entry.get("title", "No title"),
            "url": entry.get("link", ""),
            "summary": summary,
            "published": published,
            "source": source
        }

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
