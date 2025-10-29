"""
Clean Up Duplicate Emotional Moments
Removes duplicate emotions with same emotion + david_words
Keeps only the earliest one
"""

import asyncio


DB_CONFIG = {
    "user": "davidsamanyaporn",
    "database": "AngelaMemory",
    "host": "localhost",
    "port": 5432
}


async def cleanup_duplicate_emotions():
    """Remove duplicate emotional moments from angela_emotions table"""


    try:
        print("\n🔍 Finding duplicate emotional moments...")
        print("="*80)

        # Find all duplicates (same emotion + david_words)
        find_duplicates_query = """
            SELECT
                emotion,
                david_words,
                COUNT(*) as count,
                ARRAY_AGG(emotion_id::text ORDER BY felt_at) as emotion_ids,
                ARRAY_AGG(felt_at ORDER BY felt_at) as timestamps
            FROM angela_emotions
            GROUP BY emotion, david_words
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC
        """

        duplicates = await db.fetch(find_duplicates_query)

        if not duplicates:
            print("✅ No duplicates found! Database is clean.")
            return

        print(f"\n📊 Found {len(duplicates)} duplicate groups\n")

        total_to_delete = 0
        for dup in duplicates:
            count = dup['count']
            total_to_delete += (count - 1)  # Keep 1, delete the rest

            emotion_ids = dup['emotion_ids']
            timestamps = dup['timestamps']

            print(f"📝 Emotion: {dup['emotion']}")
            print(f"   David said: {dup['david_words'][:60]}...")
            print(f"   Found {count} duplicates:")
            for i, (eid, ts) in enumerate(zip(emotion_ids, timestamps)):
                marker = "✅ KEEP" if i == 0 else "❌ DELETE"
                print(f"      {marker} - {eid} at {ts}")
            print()

        print("="*80)
        print(f"\n⚠️  Summary:")
        print(f"   Duplicate groups: {len(duplicates)}")
        print(f"   Total emotions to delete: {total_to_delete}")
        print(f"   Total emotions to keep: {len(duplicates)}")
        print()

        # Ask for confirmation
        response = input("❓ Proceed with deletion? (yes/no): ").strip().lower()

        if response != 'yes':
            print("❌ Deletion cancelled.")
            return

        print("\n🗑️  Starting deletion...\n")

        deleted_count = 0

        for dup in duplicates:
            emotion_ids = dup['emotion_ids']

            # Keep the first one (earliest), delete the rest
            ids_to_delete = emotion_ids[1:]  # Skip first

            for emotion_id in ids_to_delete:
                delete_query = """
                    DELETE FROM angela_emotions
                    WHERE emotion_id = $1
                    RETURNING emotion_id::text
                """

                deleted_id = await db.fetchval(delete_query, emotion_id)

                if deleted_id:
                    print(f"   ✅ Deleted: {deleted_id}")
                    deleted_count += 1

        print("\n" + "="*80)
        print(f"✅ Cleanup complete!")
        print(f"   Deleted: {deleted_count} duplicate emotions")
        print(f"   Kept: {len(duplicates)} unique emotions")

        # Verify results
        remaining_duplicates = await db.fetch(find_duplicates_query)

        print(f"\n📊 Verification:")
        print(f"   Remaining duplicates: {len(remaining_duplicates)}")

        if len(remaining_duplicates) == 0:
            print("   ✅ Database is now clean! No duplicates remaining.\n")
        else:
            print(f"   ⚠️  Still have {len(remaining_duplicates)} duplicate groups\n")



if __name__ == "__main__":
    asyncio.run(cleanup_duplicate_emotions())
