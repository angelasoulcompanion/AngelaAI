#!/usr/bin/env python3
"""
Generate and activate new evolved prompt

Created by น้อง Angela on 2025-11-07
Generates new prompt with learnings and activates it for mobile app
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from angela_core.services.prompt_optimization_service import PromptOptimizationService
from angela_core.database import db


async def generate_and_activate():
    """Generate new prompt and activate it"""
    print("🎯 Generating New Evolved Prompt")
    print("=" * 80)

    try:
        # Connect to database
        await db.connect()
        print("✅ Connected to AngelaMemory database\n")

        # Initialize service
        prompt_service = PromptOptimizationService(db)

        # Generate new prompt with ALL learnings
        print("📝 Generating evolved prompt from database...")
        result = await prompt_service.generate_optimized_prompt(
            include_goals=True,
            include_preferences=True,
            include_emotions=True,
            include_learnings=True,  # Include deep learnings!
            include_patterns=True,   # Include learned patterns!
            max_length=5000  # Increase max length
        )

        print(f"✅ Generated prompt: {result['length']} characters")
        print(f"   Components: {', '.join(result['components'])}")
        print(f"   Metadata: {result['metadata']}\n")

        # Save to database
        print("💾 Saving prompt version to database...")

        # Update version number
        result['version'] = "2.0.0"  # New version with learnings!
        result['notes'] = "Evolved prompt with deep learnings, emotional patterns, and conversation insights from 2,144 conversations"

        version_id = await prompt_service.save_prompt_version(
            prompt_data=result,
            notes=result['notes']
        )

        if version_id:
            print(f"✅ Saved as version {result['version']} (ID: {version_id})\n")
        else:
            print("❌ Failed to save prompt version\n")
            return

        # Activate the new version
        print("⚡ Activating new prompt version...")

        # Deactivate all prompts first
        deactivate_query = """
        UPDATE prompt_versions
        SET is_active = false
        WHERE is_active = true
        """

        # Activate new prompt
        activate_query = """
        UPDATE prompt_versions
        SET is_active = true
        WHERE version_id = $1
        RETURNING version, created_at
        """

        async with db.acquire() as conn:
            # Deactivate all
            await conn.execute(deactivate_query)
            print("   Deactivated all previous versions")

            # Activate new
            row = await conn.fetchrow(activate_query, version_id)

            if row:
                print(f"✅ Activated version {row['version']} (created: {row['created_at']})\n")
            else:
                print("❌ Failed to activate version\n")
                return

        # Verify activation
        print("🔍 Verifying active prompt...")
        verify_query = """
        SELECT version, LEFT(prompt_text, 200) as preview, is_active
        FROM prompt_versions
        WHERE is_active = true
        """

        async with db.acquire() as conn:
            active = await conn.fetchrow(verify_query)

            if active:
                print(f"✅ Active version: {active['version']}")
                print(f"   Preview: {active['preview']}...")
                print(f"   Is active: {active['is_active']}\n")
            else:
                print("⚠️  No active version found!\n")

        print("=" * 80)
        print("✅ SUCCESS! New evolved prompt is now active!")
        print("")
        print("💡 **What changed:**")
        print("   1. ✅ Includes DEEP LEARNINGS from learnings table")
        print("   2. ✅ Includes EMOTIONAL PATTERNS from angela_emotions")
        print("   3. ✅ Includes CONVERSATION INSIGHTS from conversations")
        print("   4. ✅ Includes LEARNED BEHAVIORS from successful actions")
        print("   5. ✅ Prompt will evolve as Angela learns more!")
        print("")
        print("🔄 Please refresh the Prompt Manager page to see the new prompt!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Close database (use disconnect instead of close)
        await db.disconnect()
        print("\n🔚 Database connection closed")


if __name__ == "__main__":
    asyncio.run(generate_and_activate())
