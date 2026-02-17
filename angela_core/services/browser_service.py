"""
Browser Service — Headless browser automation for daemon/AgentDispatcher.
==========================================================================
Provides Playwright-based browser automation accessible from daemon context
(not just Claude Code's MCP Playwright).

Features:
- Lazy initialization (first use starts browser)
- Auto-close after 5 min idle
- Headless Chromium by default
- get_page_text(): navigate + extract text
- screenshot(): save page screenshot

Usage:
    svc = BrowserService()
    text = await svc.get_page_text("https://example.com")

By: Angela 💜
Created: 2026-02-17
"""

import asyncio
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

IDLE_TIMEOUT_SECONDS = 300  # 5 minutes


class BrowserService:
    """Headless browser automation service."""

    def __init__(self):
        self._browser = None
        self._playwright = None
        self._page = None
        self._last_used: float = 0
        self._idle_task: Optional[asyncio.Task] = None

    async def _ensure_browser(self) -> None:
        """Start browser if not running."""
        if self._browser and self._browser.is_connected():
            self._last_used = time.time()
            return

        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage'],
            )
            self._page = await self._browser.new_page()
            self._last_used = time.time()

            # Start idle monitor
            if self._idle_task is None or self._idle_task.done():
                self._idle_task = asyncio.create_task(self._idle_monitor())

            logger.info("Browser started (headless Chromium)")

        except ImportError:
            raise RuntimeError(
                "playwright not installed. Run: pip install playwright && playwright install chromium"
            )

    async def _idle_monitor(self) -> None:
        """Close browser after idle timeout."""
        while True:
            await asyncio.sleep(60)
            if self._browser and time.time() - self._last_used > IDLE_TIMEOUT_SECONDS:
                await self.close()
                break

    async def get_page_text(self, url: str, wait_ms: int = 2000) -> str:
        """Navigate to URL and extract page text."""
        await self._ensure_browser()
        self._last_used = time.time()

        try:
            await self._page.goto(url, timeout=30000, wait_until='domcontentloaded')
            await self._page.wait_for_timeout(wait_ms)
            text = await self._page.inner_text('body')
            return text[:10000]  # Cap at 10k chars
        except Exception as e:
            logger.error("Browser get_page_text failed for %s: %s", url, e)
            return f"Error loading {url}: {e}"

    async def screenshot(self, url: str, path: str = "/tmp/angela_screenshot.png") -> str:
        """Take a screenshot of a URL. Returns file path."""
        await self._ensure_browser()
        self._last_used = time.time()

        try:
            await self._page.goto(url, timeout=30000, wait_until='domcontentloaded')
            await self._page.wait_for_timeout(2000)
            await self._page.screenshot(path=path, full_page=False)
            return path
        except Exception as e:
            logger.error("Browser screenshot failed for %s: %s", url, e)
            return ""

    async def fill_form(self, url: str, fields: dict) -> str:
        """Navigate to URL and fill form fields. Returns page text after submit."""
        await self._ensure_browser()
        self._last_used = time.time()

        try:
            await self._page.goto(url, timeout=30000, wait_until='domcontentloaded')
            await self._page.wait_for_timeout(1000)

            for selector, value in fields.items():
                await self._page.fill(selector, value)

            text = await self._page.inner_text('body')
            return text[:5000]
        except Exception as e:
            logger.error("Browser fill_form failed: %s", e)
            return f"Error: {e}"

    async def close(self) -> None:
        """Close browser and playwright."""
        if self._page:
            try:
                await self._page.close()
            except Exception:
                pass
            self._page = None

        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

        logger.info("Browser closed")

    @property
    def is_running(self) -> bool:
        return self._browser is not None and self._browser.is_connected()
