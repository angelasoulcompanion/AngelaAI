#!/usr/bin/env python3
"""
Quick API Health Check
Verifies all critical endpoints are working after refactoring fixes
"""

import asyncio
import httpx

BASE_URL = "http://localhost:50001"

async def test_endpoints():
    """Test all critical API endpoints"""

    endpoints = [
        ("/api/dashboard/stats", "Dashboard Stats"),
        ("/api/blog", "Blog Posts"),
        ("/api/conversations?limit=5", "Conversations"),
        ("/api/journal?limit=5", "Journal Entries"),
        ("/api/messages?limit=5", "Messages"),
        ("/api/documents", "Documents"),
        ("/emotions/current", "Current Emotions"),
        ("/api/knowledge-graph/stats", "Knowledge Graph Stats"),
    ]

    print("\n🧪 API Health Check - All Critical Endpoints\n")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=10.0) as client:
        results = []

        for endpoint, name in endpoints:
            url = f"{BASE_URL}{endpoint}"
            try:
                response = await client.get(url)
                status = "✅" if response.status_code == 200 else "❌"

                # Get response size
                data_size = len(response.content)

                results.append({
                    "name": name,
                    "status": response.status_code,
                    "size": data_size,
                    "ok": response.status_code == 200
                })

                print(f"{status} {name:30} → {response.status_code} ({data_size:,} bytes)")

            except Exception as e:
                print(f"❌ {name:30} → ERROR: {str(e)[:50]}")
                results.append({
                    "name": name,
                    "status": "error",
                    "size": 0,
                    "ok": False
                })

    print("=" * 60)

    # Summary
    success_count = sum(1 for r in results if r["ok"])
    total_count = len(results)

    print(f"\n📊 Summary: {success_count}/{total_count} endpoints healthy")

    if success_count == total_count:
        print("✅ All systems operational!")
    else:
        print(f"⚠️  {total_count - success_count} endpoints need attention")

    return success_count == total_count

if __name__ == "__main__":
    success = asyncio.run(test_endpoints())
    exit(0 if success else 1)
