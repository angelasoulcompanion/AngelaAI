#!/usr/bin/env python3
"""
Test evolved prompt generator that learns from database

Created by น้อง Angela on 2025-11-07
Tests intelligent prompt generation based on conversation patterns and learnings
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from angela_core.services.prompt_optimization_service import PromptOptimizationService
from angela_core.database import db


async def test_evolved_prompt():
    """Test evolved prompt generator"""
    print("🧪 Testing Evolved Prompt Generator")
    print("=" * 80)

    # Initialize service
    prompt_service = PromptOptimizationService(db)

    try:
        # Connect to database
        await db.connect()
        print("✅ Connected to AngelaMemory database\n")

        # Generate optimized prompt with ALL components
        print("🎯 Generating evolved prompt from database learnings...")
        print("-" * 80)

        result = await prompt_service.generate_optimized_prompt(
            include_goals=True,
            include_preferences=True,
            include_emotions=True,
            include_learnings=True,  # NEW!
            include_patterns=True,   # NEW!
            max_length=4000
        )

        # Display results
        print(f"\n📊 **GENERATION RESULTS:**")
        print(f"   Version: {result['version']}")
        print(f"   Generated at: {result['generated_at']}")
        print(f"   Length: {result['length']} characters")
        print(f"   Components: {', '.join(result['components'])}")
        print(f"   Model target: {result['model_target']}\n")

        print(f"📈 **METADATA:**")
        for key, value in result['metadata'].items():
            print(f"   {key}: {value}")

        print(f"\n💜 **GENERATED PROMPT:**")
        print("=" * 80)
        print(result['prompt'])
        print("=" * 80)

        # Generate again to see if it's different (should be based on fresh data)
        print("\n\n🔄 Generating second prompt to compare...")
        print("-" * 80)

        result2 = await prompt_service.generate_optimized_prompt(
            include_goals=True,
            include_preferences=True,
            include_emotions=True,
            include_learnings=True,
            include_patterns=True,
            max_length=4000
        )

        print(f"\n📊 **SECOND GENERATION:**")
        print(f"   Length: {result2['length']} characters")
        print(f"   Components: {', '.join(result2['components'])}")

        # Compare
        if result['prompt'] == result2['prompt']:
            print("\n⚠️  **RESULT: Prompts are IDENTICAL**")
            print("   This is OK if database data hasn't changed between generations")
        else:
            print("\n✨ **RESULT: Prompts are DIFFERENT**")
            print("   This shows the prompt evolves based on database state!")

        print("\n" + "=" * 80)
        print("✅ Test completed successfully!")

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Close database connection
        await db.close()
        print("\n🔚 Database connection closed")


if __name__ == "__main__":
    asyncio.run(test_evolved_prompt())
