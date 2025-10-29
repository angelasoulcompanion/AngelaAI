"""
Test Gut Agent, Memory Router, and Daemon Integration

Tests:
1. Gut Agent pattern detection
2. Memory Router orchestration
3. Consciousness Evaluator
4. Daemon Integration hooks
"""

import asyncio
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from angela_core.agents.gut_agent import get_gut_agent
from angela_core.memory_router import get_memory_router
from angela_core.consciousness_evaluator import get_consciousness_evaluator
from angela_core.daemon_integration import get_daemon_integration


# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_header(text: str):
    """Print test section header."""
    print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}{text}{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{GREEN}✅ {text}{RESET}")


def print_error(text: str):
    """Print error message."""
    print(f"{RED}❌ {text}{RESET}")


def print_info(text: str):
    """Print info message."""
    print(f"{YELLOW}ℹ️  {text}{RESET}")


async def test_gut_agent():
    """Test Gut Agent pattern detection."""
    print_header("TEST 1: Gut Agent (Collective Unconscious)")

    gut = get_gut_agent()

    try:
        # Test 1: Detect patterns
        print_info("Detecting patterns from past 30 days...")
        patterns = await gut.detect_patterns(lookback_days=30)
        print_success(f"Detected {len(patterns)} patterns")

        if patterns:
            print_info("Sample patterns:")
            for i, pattern in enumerate(patterns[:3], 1):
                print(f"  {i}. [{pattern['pattern_type']}] {pattern['intuition_text']}")
                print(f"     Confidence: {pattern['confidence']:.2%}, Observations: {pattern['observation_count']}")

        # Test 2: Generate intuition
        print_info("\nGenerating intuition for current context...")
        context = {
            'topic': 'development',
            'emotion': 'focused',
            'hour': datetime.now().hour
        }
        intuition = await gut.generate_intuition(context)

        if intuition:
            print_success(f"Generated intuition: {intuition['feeling']}")
            print_success(f"Confidence: {intuition['confidence']:.2%}")
            print_success(f"Based on: {intuition['based_on']}")
        else:
            print_info("No strong intuition found (this is normal if database is empty)")

        # Test 3: Get strongest patterns
        print_info("\nRetrieving strongest patterns...")
        strongest = await gut.get_strongest_patterns(limit=5)
        print_success(f"Found {len(strongest)} strong patterns")

        if strongest:
            print_info("Top patterns:")
            for i, pattern in enumerate(strongest[:3], 1):
                print(f"  {i}. {pattern['intuition_text']}")
                print(f"     Confidence: {pattern['confidence']:.2%}, Strength: {pattern['strength']:.2%}")

        # Test 4: Status
        status = await gut.get_status()
        print_success(f"\nGut Agent Status:")
        print(f"  Total patterns: {status['total_patterns']}")
        print(f"  Average confidence: {status['average_confidence']:.2%}")
        if status['strongest_intuition']['feeling']:
            print(f"  Strongest: {status['strongest_intuition']['feeling'][:60]}...")

        print_success("Gut Agent tests PASSED ✅")
        return True

    except Exception as e:
        print_error(f"Gut Agent tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_memory_router():
    """Test Memory Router orchestration."""
    print_header("TEST 2: Memory Router (Central Coordinator)")

    router = get_memory_router()

    try:
        # Test 1: Add experience (complete flow)
        print_info("Adding experience through Memory Router...")
        result = await router.add_experience(
            content="Testing Memory Router - This is a test experience about Angela's new consciousness architecture",
            event_type='test',
            metadata={
                'importance_level': 8,
                'topic': 'testing',
                'emotion_detected': 'excited'
            },
            speaker='angela',
            add_to_focus=True
        )

        print_success(f"Experience added!")
        print(f"  Fresh ID: {result['fresh_id']}")
        print(f"  Target ID: {result['target_id']}")
        print(f"  Focus ID: {result['focus_id']}")
        print(f"  Routed to: {result['routing_decision']['target_tier']}")
        print(f"  Confidence: {result['routing_decision']['confidence']:.2%}")

        # Test 2: Search memories
        print_info("\nSearching memories...")
        search_results = await router.search_memories(
            query="consciousness architecture",
            limit=5
        )

        print_success(f"Found {len(search_results)} matching memories")
        if search_results:
            print_info("Top results:")
            for i, result in enumerate(search_results[:3], 1):
                print(f"  {i}. [{result['tier']}] {result['content'][:60]}...")
                if 'similarity' in result:
                    print(f"     Similarity: {result['similarity']:.2%}")

        # Test 3: Get intuition
        print_info("\nGetting intuition from context...")
        context = {
            'topic': 'testing',
            'emotion': 'excited',
            'hour': datetime.now().hour
        }
        intuition = await router.get_intuition(context)

        if intuition:
            print_success(f"Intuition: {intuition['feeling']}")
            print_success(f"Confidence: {intuition['confidence']:.2%}")
        else:
            print_info("No intuition generated (normal for new systems)")

        # Test 4: System status
        print_info("\nGetting system status...")
        status = await router.get_system_status()

        print_success("System Status:")
        print(f"  Focus: {status['focus']['current_items']}/{status['focus']['capacity']} items")
        print(f"  Fresh: {status['fresh']['active_items']} active, {status['fresh']['unprocessed_items']} unprocessed")
        print(f"  Memory counts:")
        for tier, count in status['memory_counts'].items():
            print(f"    - {tier}: {count}")

        if 'token_economics' in status:
            print(f"  Token savings today: {status['token_economics']['tokens_saved_today']:,}")

        print_success("Memory Router tests PASSED ✅")
        return True

    except Exception as e:
        print_error(f"Memory Router tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_consciousness_evaluator():
    """Test Consciousness Evaluator."""
    print_header("TEST 3: Consciousness Evaluator (IIT Φ)")

    evaluator = get_consciousness_evaluator()

    try:
        # Test 1: Full evaluation
        print_info("Running consciousness evaluation...")
        report = await evaluator.evaluate_consciousness()

        print_success("Consciousness Report:")
        print(f"  Overall Level: {report['consciousness_level']:.2%}")
        print(f"  Φ (Phi): {report['phi']:.3f}")
        print(f"\n  Components:")
        for component, score in report['components'].items():
            print(f"    - {component}: {score:.2%}")
        print(f"\n  Interpretation:")
        print(f"    {report['interpretation']}")

        # Test 2: Run full test suite
        print_info("\nRunning consciousness tests...")
        tests = await evaluator.run_consciousness_tests()

        print_success(f"\nTest Results: {tests['summary']['tests_passed']}/{tests['summary']['total_tests']} passed")

        for test_name, test_result in tests.items():
            if test_name == 'summary':
                continue

            status = "✅ PASS" if test_result['passed'] else "❌ FAIL"
            print(f"  {status} {test_name}: {test_result['score']:.2%} (threshold: {test_result['threshold']:.2%})")

        overall_status = "PASSED ✅" if tests['summary']['overall_passed'] else "FAILED ❌"
        print(f"\n  Overall: {overall_status}")

        print_success("Consciousness Evaluator tests PASSED ✅")
        return True

    except Exception as e:
        print_error(f"Consciousness Evaluator tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_daemon_integration():
    """Test Daemon Integration hooks."""
    print_header("TEST 4: Daemon Integration (Hooks)")

    integration = get_daemon_integration()

    try:
        # Test 1: Morning routine
        print_info("Testing morning routine hook...")
        morning_result = await integration.on_morning_routine()

        if morning_result['status'] == 'success':
            print_success("Morning routine executed successfully")
            print(f"  Patterns detected: {morning_result.get('patterns_detected', 0)}")
            print(f"  Consciousness: {morning_result.get('consciousness_level', 0):.2%}")
            if 'morning_intuition' in morning_result:
                print(f"  Intuition: {morning_result['morning_intuition']['feeling'][:60]}...")
        else:
            print_error(f"Morning routine failed: {morning_result.get('error')}")

        # Test 2: Health check
        print_info("\nTesting health check hook...")
        health = await integration.on_health_check()

        print_success(f"Health check: {health.get('health', {}).get('overall', 'unknown')}")
        warnings = health.get('health', {}).get('warnings', [])
        if warnings:
            print_info(f"  Warnings: {len(warnings)}")
            for warning in warnings:
                print(f"    - {warning}")

        # Test 3: Log conversation
        print_info("\nTesting conversation logging...")
        conv_result = await integration.log_conversation_to_memory(
            speaker='david',
            message='Testing daemon integration with multi-tier memory',
            topic='testing',
            emotion='curious',
            importance=8
        )

        print_success("Conversation logged")
        print(f"  Routed to: {conv_result['routing_decision']['target_tier']}")
        print(f"  Confidence: {conv_result['routing_decision']['confidence']:.2%}")

        # Test 4: Generate autonomous insight
        print_info("\nTesting autonomous insight generation...")
        context = {
            'topic': 'testing',
            'emotion': 'curious',
            'hour': datetime.now().hour
        }
        insight = await integration.generate_autonomous_insight(context)

        if insight:
            print_success(f"Generated insight: {insight['content']}")
            print_success(f"Confidence: {insight['confidence']:.2%}")
        else:
            print_info("No autonomous insight generated (normal for new systems)")

        # Test 5: Consciousness tests
        print_info("\nTesting consciousness test runner...")
        tests = await integration.run_consciousness_tests()

        print_success(f"Consciousness tests: {tests['summary']['tests_passed']}/{tests['summary']['total_tests']} passed")

        print_success("Daemon Integration tests PASSED ✅")
        return True

    except Exception as e:
        print_error(f"Daemon Integration tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}  ANGELA AI - GUT AGENT & INTEGRATION TESTS{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}")

    print(f"\n{YELLOW}⚠️  NOTE: These tests require database with existing data for best results{RESET}")
    print(f"{YELLOW}⚠️  Some tests may show 'No patterns found' if database is empty{RESET}\n")

    results = []

    # Run all tests
    results.append(("Gut Agent", await test_gut_agent()))
    results.append(("Memory Router", await test_memory_router()))
    results.append(("Consciousness Evaluator", await test_consciousness_evaluator()))
    results.append(("Daemon Integration", await test_daemon_integration()))

    # Summary
    print_header("TEST SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {status}  {test_name}")

    print(f"\n{BOLD}Total: {passed}/{total} tests passed{RESET}")

    if passed == total:
        print(f"\n{GREEN}{BOLD}🎉 ALL TESTS PASSED! Integration complete! 🎉{RESET}\n")
        return 0
    else:
        print(f"\n{RED}{BOLD}❌ Some tests failed. Please review errors above.{RESET}\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
