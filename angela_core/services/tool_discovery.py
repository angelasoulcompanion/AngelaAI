"""
Tool Discovery — Scan system for available tools.
==================================================
Discovers CLI tools, Python packages, and API keys on the system
and automatically registers them in the ToolRegistry.

Discovery sources:
1. CLI binaries in PATH (ffmpeg, yt-dlp, pandoc, imagemagick, etc.)
2. Python packages (via pip list)
3. API keys in ~/.angela_secrets

Runs:
- At daemon init (once)
- Daily scan (refresh)

By: Angela 💜
Created: 2026-02-17
"""

import asyncio
import logging
import os
import shutil
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# CLI tools we know how to use and their descriptions
KNOWN_CLI_TOOLS = {
    "ffmpeg": "Convert and process audio/video files",
    "ffprobe": "Inspect audio/video file metadata",
    "yt-dlp": "Download videos and audio from YouTube and other sites",
    "pandoc": "Convert documents between formats (markdown, HTML, PDF, docx)",
    "convert": "ImageMagick: convert and process images",
    "identify": "ImageMagick: identify image properties",
    "jq": "Process and query JSON data",
    "curl": "Transfer data from/to URLs",
    "wget": "Download files from the web",
    "sqlite3": "Query SQLite databases",
    "say": "Text-to-speech on macOS",
    "open": "Open files/URLs with default app on macOS",
    "pbcopy": "Copy text to clipboard on macOS",
    "pbpaste": "Paste text from clipboard on macOS",
    "screencapture": "Take screenshots on macOS",
    "osascript": "Run AppleScript commands on macOS",
    "swift": "Run Swift code",
    "git": "Version control operations",
    "docker": "Container management",
}

# Python packages that provide useful capabilities
KNOWN_PYTHON_PACKAGES = {
    "pillow": "Image processing (PIL)",
    "requests": "HTTP requests",
    "beautifulsoup4": "HTML/XML parsing",
    "pandas": "Data analysis and manipulation",
    "matplotlib": "Create charts and visualizations",
    "pydub": "Audio processing",
    "qrcode": "Generate QR codes",
    "reportlab": "Generate PDF documents",
    "openpyxl": "Read/write Excel files",
    "duckduckgo-search": "Web search via DuckDuckGo",
}


class ToolDiscovery:
    """
    Discovers available tools on the system and registers them.

    Usage:
        discovery = ToolDiscovery(registry)
        report = await discovery.scan()
        # report = {"cli_found": 8, "packages_found": 5, "api_keys_found": 3}
    """

    def __init__(self, registry=None):
        self._registry = registry
        self._discovered_cli: Set[str] = set()
        self._discovered_packages: Set[str] = set()
        self._discovered_api_keys: Set[str] = set()

    def _get_registry(self):
        if self._registry is None:
            from angela_core.services.tool_registry import get_registry
            self._registry = get_registry()
        return self._registry

    # ── Full Scan ──

    async def scan(self) -> Dict[str, Any]:
        """Run full discovery scan across all sources."""
        cli_report = await self.scan_cli_tools()
        pkg_report = await self.scan_python_packages()
        key_report = await self.scan_api_keys()

        total = cli_report["found"] + pkg_report["found"] + key_report["found"]
        logger.info(
            "Tool discovery: %d CLI, %d packages, %d API keys found",
            cli_report["found"], pkg_report["found"], key_report["found"],
        )

        return {
            "total_discovered": total,
            "cli": cli_report,
            "packages": pkg_report,
            "api_keys": key_report,
        }

    # ── CLI Tool Scan ──

    async def scan_cli_tools(self) -> Dict[str, Any]:
        """Scan PATH for known CLI tools and register as DynamicCLITool."""
        from angela_core.services.tools.dynamic_cli_tool import DynamicCLITool

        found = []
        not_found = []

        for tool_name, description in KNOWN_CLI_TOOLS.items():
            path = shutil.which(tool_name)
            if path:
                found.append(tool_name)
                self._discovered_cli.add(tool_name)

                # Register as dynamic tool
                registry = self._get_registry()
                cli_tool = DynamicCLITool(tool_name, path, description)
                # Only register if not already registered
                if not registry.get(cli_tool.name):
                    registry.register(cli_tool)
                    logger.debug("Discovered CLI: %s → %s", tool_name, path)
            else:
                not_found.append(tool_name)

        return {
            "found": len(found),
            "tools": found,
            "not_found": not_found,
        }

    # ── Python Package Scan ──

    async def scan_python_packages(self) -> Dict[str, Any]:
        """Scan installed Python packages for known useful ones."""
        import importlib

        found = []
        not_found = []

        # Map package names to import names
        import_map = {
            "pillow": "PIL",
            "beautifulsoup4": "bs4",
            "duckduckgo-search": "duckduckgo_search",
        }

        for pkg_name, description in KNOWN_PYTHON_PACKAGES.items():
            import_name = import_map.get(pkg_name, pkg_name)
            try:
                importlib.import_module(import_name)
                found.append(pkg_name)
                self._discovered_packages.add(pkg_name)
            except ImportError:
                not_found.append(pkg_name)

        return {
            "found": len(found),
            "packages": found,
            "not_found": not_found,
        }

    # ── API Key Scan ──

    async def scan_api_keys(self) -> Dict[str, Any]:
        """Check for available API keys in ~/.angela_secrets."""
        secrets_path = os.path.expanduser("~/.angela_secrets")
        found = []

        try:
            if os.path.exists(secrets_path):
                with open(secrets_path) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key_name = line.split("=", 1)[0].strip()
                            if key_name and key_name.isupper():
                                found.append(key_name)
                                self._discovered_api_keys.add(key_name)
        except Exception as e:
            logger.debug("API key scan failed: %s", e)

        return {
            "found": len(found),
            "keys": found,
        }

    # ── Summary ──

    def summary(self) -> Dict[str, Any]:
        """Get discovery summary."""
        return {
            "cli_tools": sorted(self._discovered_cli),
            "python_packages": sorted(self._discovered_packages),
            "api_keys": sorted(self._discovered_api_keys),
            "total": len(self._discovered_cli) + len(self._discovered_packages) + len(self._discovered_api_keys),
        }
