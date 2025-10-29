#!/usr/bin/env python3
"""
Documentation Monitor Service for Angela
Monitors documentation files for changes and auto-imports to database

This ensures Angela NEVER loses any knowledge!
พอมีการเปลี่ยนแปลง documentation → import ทันที!
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Set, Optional
from datetime import datetime
import hashlib

from angela_core.knowledge_importer import KnowledgeImporter

logger = logging.getLogger('DocumentationMonitor')


class DocumentationMonitor:
    """
    Monitors documentation files and auto-imports changes

    Features:
    - Track file modifications by hash
    - Detect new files
    - Auto-import on changes
    - Daily full scan (paranoid mode - no loss!)
    - Incremental updates
    """

    def __init__(
        self,
        docs_dir: str = "/Users/davidsamanyaporn/PycharmProjects/AngelaAI/docs",
        cache_file: str = "/Users/davidsamanyaporn/PycharmProjects/AngelaAI/logs/doc_hashes.json"
    ):
        self.docs_dir = Path(docs_dir)
        self.cache_file = Path(cache_file)
        self.file_hashes: Dict[str, str] = {}  # path -> hash
        self.importer: Optional[KnowledgeImporter] = None
        self.last_full_scan: Optional[datetime] = None

    async def initialize(self):
        """Initialize the monitor"""
        logger.info("📚 Initializing Documentation Monitor...")

        # Create importer
        self.importer = KnowledgeImporter()
        await self.importer.connect()

        # Load existing hashes
        await self._load_hashes()

        # Do initial scan
        await self.scan_and_import()

        logger.info("✅ Documentation Monitor initialized")

    async def close(self):
        """Close the monitor"""
        if self.importer:
            await self.importer.close()
        await self._save_hashes()

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    async def _load_hashes(self):
        """Load cached file hashes"""
        if self.cache_file.exists():
            import json
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    self.file_hashes = data.get('hashes', {})
                    last_scan_str = data.get('last_full_scan')
                    if last_scan_str:
                        self.last_full_scan = datetime.fromisoformat(last_scan_str)
                logger.info(f"📂 Loaded {len(self.file_hashes)} cached file hashes")
            except Exception as e:
                logger.warning(f"⚠️ Could not load hash cache: {e}")
                self.file_hashes = {}

    async def _save_hashes(self):
        """Save file hashes to cache"""
        import json
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                'hashes': self.file_hashes,
                'last_full_scan': self.last_full_scan.isoformat() if self.last_full_scan else None
            }
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"💾 Saved {len(self.file_hashes)} file hashes")
        except Exception as e:
            logger.error(f"❌ Could not save hash cache: {e}")

    async def scan_and_import(self, force: bool = False) -> Dict[str, int]:
        """
        Scan documentation directory and import changes

        Args:
            force: Force re-import even if no changes detected

        Returns:
            Stats dict with counts
        """
        logger.info("🔍 Scanning documentation directory...")

        # Find all markdown files
        md_files = list(self.docs_dir.rglob("*.md"))
        logger.info(f"📄 Found {len(md_files)} documentation files")

        stats = {
            'files_scanned': len(md_files),
            'files_changed': 0,
            'files_new': 0,
            'files_imported': 0,
            'knowledge_items': 0,
            'learnings': 0,
            'errors': 0
        }

        for md_file in md_files:
            try:
                file_path_str = str(md_file)

                # Calculate current hash
                current_hash = self._calculate_file_hash(md_file)
                cached_hash = self.file_hashes.get(file_path_str)

                # Check if file is new or changed
                is_new = cached_hash is None
                is_changed = cached_hash != current_hash

                if force or is_new or is_changed:
                    # Import the file!
                    if is_new:
                        stats['files_new'] += 1
                        logger.info(f"📄 NEW file detected: {md_file.name}")
                    else:
                        stats['files_changed'] += 1
                        logger.info(f"✏️  CHANGED file detected: {md_file.name}")

                    # Import
                    import_stats = await self.importer.import_file(
                        file_path_str,
                        verbose=False  # Less verbose for daemon
                    )

                    stats['files_imported'] += 1
                    stats['knowledge_items'] += import_stats['knowledge_items']
                    stats['learnings'] += import_stats['learnings']

                    # Update hash
                    self.file_hashes[file_path_str] = current_hash

                    logger.info(
                        f"✅ Imported {md_file.name}: "
                        f"{import_stats['knowledge_items']} knowledge, "
                        f"{import_stats['learnings']} learnings"
                    )

            except Exception as e:
                logger.error(f"❌ Error processing {md_file.name}: {e}")
                stats['errors'] += 1

        # Save updated hashes
        self.last_full_scan = datetime.now()
        await self._save_hashes()

        # Log summary
        if stats['files_imported'] > 0:
            logger.info(
                f"✅ Import complete: {stats['files_imported']} files imported, "
                f"{stats['knowledge_items']} knowledge items, "
                f"{stats['learnings']} learnings"
            )
        else:
            logger.info("✅ All documentation up to date! No changes detected.")

        return stats

    async def daily_full_scan(self) -> Dict[str, int]:
        """
        Daily full scan - paranoid mode!
        Re-scan everything to ensure no loss
        """
        logger.info("🔄 Starting DAILY FULL SCAN (paranoid mode - no loss!)")
        stats = await self.scan_and_import(force=False)  # Don't force re-import
        logger.info(f"✅ Daily full scan complete: {stats}")
        return stats

    async def check_for_updates(self) -> Dict[str, int]:
        """
        Quick check for updates (incremental)
        Called periodically by daemon
        """
        return await self.scan_and_import(force=False)


# Singleton instance
_monitor: Optional[DocumentationMonitor] = None


async def get_monitor() -> DocumentationMonitor:
    """Get or create the documentation monitor singleton"""
    global _monitor
    if _monitor is None:
        _monitor = DocumentationMonitor()
        await _monitor.initialize()
    return _monitor


async def close_monitor():
    """Close the documentation monitor"""
    global _monitor
    if _monitor:
        await _monitor.close()
        _monitor = None


# Convenience functions for daemon
async def daily_documentation_scan() -> Dict[str, int]:
    """Run daily documentation scan (for daemon)"""
    monitor = await get_monitor()
    return await monitor.daily_full_scan()


async def check_documentation_updates() -> Dict[str, int]:
    """Quick check for documentation updates (for daemon)"""
    monitor = await get_monitor()
    return await monitor.check_for_updates()
