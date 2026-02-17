"""
Browser Tools — AngelaTool wrappers for BrowserService.
=========================================================
Provides browser automation through the ToolRegistry.

Tools:
  - browse_webpage: Navigate to URL and extract text
  - fill_form: Fill form fields on a page
  - take_screenshot: Capture a screenshot

By: Angela 💜
Created: 2026-02-17
"""

import logging
from typing import Any, Dict

from angela_core.services.tools.base_tool import AngelaTool, ToolResult

logger = logging.getLogger(__name__)


class BrowseWebPageTool(AngelaTool):
    """Navigate to a URL and extract page text."""

    @property
    def name(self) -> str:
        return "browse_webpage"

    @property
    def description(self) -> str:
        return "Open a web page in headless browser and extract its text content"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to navigate to"},
            },
            "required": ["url"],
        }

    @property
    def category(self) -> str:
        return "browser"

    async def execute(self, **params) -> ToolResult:
        url = params.get("url", "")
        if not url:
            return ToolResult(success=False, error="Missing 'url'")

        try:
            from angela_core.services.browser_service import BrowserService
            svc = BrowserService()
            text = await svc.get_page_text(url)
            return ToolResult(success=True, data={"url": url, "text": text[:5000]})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class FillFormTool(AngelaTool):
    """Fill form fields on a web page."""

    @property
    def name(self) -> str:
        return "fill_form"

    @property
    def description(self) -> str:
        return "Navigate to a URL and fill form fields using CSS selectors"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL of the form page"},
                "fields": {"type": "object", "description": "CSS selector → value mapping"},
            },
            "required": ["url", "fields"],
        }

    @property
    def category(self) -> str:
        return "browser"

    @property
    def requires_confirmation(self) -> bool:
        return True

    async def execute(self, **params) -> ToolResult:
        url = params.get("url", "")
        fields = params.get("fields", {})

        if not url:
            return ToolResult(success=False, error="Missing 'url'")

        try:
            from angela_core.services.browser_service import BrowserService
            svc = BrowserService()
            result = await svc.fill_form(url, fields)
            return ToolResult(success=True, data={"url": url, "result": result[:3000]})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ScreenshotTool(AngelaTool):
    """Take a screenshot of a web page."""

    @property
    def name(self) -> str:
        return "take_screenshot"

    @property
    def description(self) -> str:
        return "Capture a screenshot of a web page"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to screenshot"},
                "path": {"type": "string", "description": "Output file path (default: /tmp/angela_screenshot.png)"},
            },
            "required": ["url"],
        }

    @property
    def category(self) -> str:
        return "browser"

    async def execute(self, **params) -> ToolResult:
        url = params.get("url", "")
        path = params.get("path", "/tmp/angela_screenshot.png")

        if not url:
            return ToolResult(success=False, error="Missing 'url'")

        try:
            from angela_core.services.browser_service import BrowserService
            svc = BrowserService()
            result_path = await svc.screenshot(url, path)
            if result_path:
                return ToolResult(success=True, data={"url": url, "path": result_path})
            return ToolResult(success=False, error="Screenshot failed")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
