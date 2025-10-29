"""
Test reflect_on_growth function to verify KeyError fix
"""
import asyncio
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.consciousness.consciousness_core import consciousness

async def test():
    print("🧪 Testing reflect_on_growth function...\n")

    try:
        # Test the function that was causing KeyError
        growth_summary = await consciousness.reflect_on_growth()

        print("✅ SUCCESS! No KeyError occurred")
        print(f"\n📊 Growth Summary:")
        print(f"   {growth_summary}\n")

    except KeyError as e:
        print(f"❌ FAILED: KeyError still occurs: {e}\n")
        raise
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}\n")
        raise

    print("✅ Test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test())
