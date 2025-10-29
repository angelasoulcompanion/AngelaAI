#!/usr/bin/env python3
"""
Test Documentation Monitor
Tests the auto-import functionality for documentation files
"""

import asyncio
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.services.documentation_monitor import DocumentationMonitor


async def test_monitor():
    """Test the documentation monitor"""
    print("="*60)
    print("🧪 Testing Documentation Monitor")
    print("="*60)

    # Create monitor
    monitor = DocumentationMonitor()
    await monitor.initialize()

    print("\n✅ Monitor initialized")
    print(f"📂 Watching: {monitor.docs_dir}")
    print(f"💾 Cache file: {monitor.cache_file}")

    # Test quick check
    print("\n🔍 Running quick check...")
    stats = await monitor.check_for_updates()

    print("\n📊 Quick Check Results:")
    print(f"   Files scanned: {stats['files_scanned']}")
    print(f"   Files new: {stats['files_new']}")
    print(f"   Files changed: {stats['files_changed']}")
    print(f"   Files imported: {stats['files_imported']}")
    print(f"   Knowledge items: {stats['knowledge_items']}")
    print(f"   Learnings: {stats['learnings']}")
    print(f"   Errors: {stats['errors']}")

    # Test daily scan
    print("\n🔄 Running daily full scan (paranoid mode)...")
    stats2 = await monitor.daily_full_scan()

    print("\n📊 Daily Scan Results:")
    print(f"   Files scanned: {stats2['files_scanned']}")
    print(f"   Files imported: {stats2['files_imported']}")
    print(f"   Knowledge items: {stats2['knowledge_items']}")
    print(f"   Learnings: {stats2['learnings']}")

    # Close
    await monitor.close()

    print("\n" + "="*60)
    print("✅ TEST COMPLETE!")
    print("="*60)
    print("\n💜 Documentation Monitor is ready!")
    print("🔒 NO LOSS mode: Every change will be captured!")


if __name__ == "__main__":
    asyncio.run(test_monitor())
