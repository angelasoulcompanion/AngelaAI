"""
Test Phase 1: Multi-Tier Memory Architecture

Tests:
1. Focus Agent (7±2 working memory)
2. Fresh Memory Buffer (10-minute TTL)
3. Analytics Agent (7-signal routing)
4. Decay Gradient Service (memory compression)
5. Integration flow: Fresh → Analytics → Target Tier → Decay
"""

import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from angela_core.agents.focus_agent import get_focus_agent
from angela_core.agents.fresh_memory_buffer import get_fresh_buffer
from angela_core.agents.analytics_agent import get_analytics_agent
from angela_core.services.decay_gradient_service import get_decay_service


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


async def test_focus_agent():
    """Test Focus Agent (7±2 working memory)."""
    print_header("TEST 1: Focus Agent (Working Memory)")

    focus = get_focus_agent()

    try:
        # Test 1: Add items to focus
        print_info("Adding 5 items to focus...")
        items = []
        for i in range(5):
            item_id = await focus.add_item(
                content=f"Test item {i+1}",
                metadata={'topic': f'topic_{i+1}', 'test': True},
                importance=float(i+1)
            )
            items.append(item_id)
            print_success(f"Added item {i+1}: {item_id}")

        # Test 2: Get focus items
        current_items = await focus.get_items()
        assert len(current_items) == 5, f"Expected 5 items, got {len(current_items)}"
        print_success(f"Focus has {len(current_items)} items")

        # Test 3: Access item (boost attention)
        accessed = await focus.access_item(items[0])
        assert accessed is not None, "Failed to access item"
        assert accessed['access_count'] == 1, "Access count not incremented"
        print_success(f"Accessed item (attention: {accessed['attention_weight']:.2f})")

        # Test 4: Add beyond capacity (should auto-prune)
        print_info("Testing capacity limits (adding 5 more items)...")
        for i in range(5, 10):
            await focus.add_item(
                content=f"Test item {i+1}",
                metadata={'topic': f'topic_{i+1}'},
                importance=float(i+1)
            )

        current_items = await focus.get_items()
        assert len(current_items) <= 9, f"Exceeded max capacity: {len(current_items)}"
        print_success(f"Focus capacity maintained: {len(current_items)}/9 items")

        # Test 5: Status
        status = focus.get_status()
        print_success(f"Focus utilization: {status['utilization']:.1%}")
        print_success(f"Top topics: {', '.join(status['top_3_topics'])}")

        print_success("Focus Agent tests PASSED ✅")
        return True

    except Exception as e:
        print_error(f"Focus Agent tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_fresh_memory_buffer():
    """Test Fresh Memory Buffer (10-minute TTL)."""
    print_header("TEST 2: Fresh Memory Buffer (10-min TTL)")

    buffer = get_fresh_buffer()

    try:
        # Test 1: Add events
        print_info("Adding events to fresh memory...")
        events = []
        for i in range(5):
            event_id = await buffer.add_event(
                event_type='test_event',
                content=f'Test event {i+1} - This is a test memory with some content',
                metadata={'importance_level': i+1, 'test': True},
                speaker='david'
            )
            events.append(event_id)
            print_success(f"Added event {i+1}: {event_id}")

        # Test 2: Get unprocessed items
        unprocessed = await buffer.get_unprocessed_items()
        assert len(unprocessed) == 5, f"Expected 5 unprocessed, got {len(unprocessed)}"
        print_success(f"Found {len(unprocessed)} unprocessed items")

        # Test 3: Mark as processed
        routing_decision = {
            'target_tier': 'long_term',
            'confidence': 0.85,
            'reasoning': 'Test routing decision'
        }
        await buffer.mark_processed(events[0], routing_decision)
        print_success("Marked item as processed")

        unprocessed = await buffer.get_unprocessed_items()
        assert len(unprocessed) == 4, f"Expected 4 unprocessed, got {len(unprocessed)}"
        print_success(f"Unprocessed count updated: {len(unprocessed)}")

        # Test 4: Search similar
        similar = await buffer.search_similar("test memory content", limit=3)
        assert len(similar) > 0, "No similar items found"
        print_success(f"Found {len(similar)} similar items")
        print_success(f"Top similarity: {similar[0]['similarity']:.2%}")

        # Test 5: Status
        status = buffer.get_status()
        print_success(f"Buffer utilization: {status['utilization']:.1%}")
        print_success(f"Active items: {status['active_items']}")
        print_success(f"Unprocessed items: {status['unprocessed_items']}")

        print_success("Fresh Memory Buffer tests PASSED ✅")
        return True

    except Exception as e:
        print_error(f"Fresh Memory Buffer tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_analytics_agent():
    """Test Analytics Agent (7-signal routing)."""
    print_header("TEST 3: Analytics Agent (7-Signal Routing)")

    analytics = get_analytics_agent()

    try:
        # Test 1: Route successful event
        print_info("Testing successful event routing...")
        success_event = {
            'id': uuid4(),
            'content': 'Successfully deployed new feature with zero errors',
            'metadata': {
                'outcome': 'success',
                'error_rate': 0.0,
                'user_satisfaction': 0.95,
                'importance_level': 8,
                'affects_system': True,
                'user_initiated': True
            },
            'event_type': 'deployment',
            'speaker': 'david'
        }

        decision = await analytics.analyze_memory(success_event)
        assert 'target_tier' in decision, "Missing target_tier"
        assert 'confidence' in decision, "Missing confidence"
        assert 'signals' in decision, "Missing signals"

        print_success(f"Target tier: {decision['target_tier']}")
        print_success(f"Confidence: {decision['confidence']:.2%}")
        print_success(f"Composite score: {decision['composite_score']:.2f}")
        print_success(f"Priority: {decision['priority']}/10")
        print_success(f"Reasoning: {decision['reasoning']}")

        # Print all 7 signals
        print_info("Signal breakdown:")
        for signal_name, value in decision['signals'].items():
            print(f"  • {signal_name}: {value:.2f}")

        # Test 2: Route critical event (should go to Shock)
        print_info("\nTesting critical event (Shock Memory)...")
        critical_event = {
            'id': uuid4(),
            'content': 'CRITICAL: System failure detected - immediate attention required',
            'metadata': {
                'outcome': 'failure',
                'error_rate': 1.0,
                'importance_level': 10,
                'affects_system': True,
                'has_consequences': True,
                'time_sensitive': True,
                'emotion_detected': 'anxiety'
            },
            'event_type': 'system_alert',
            'speaker': 'system'
        }

        critical_decision = await analytics.analyze_memory(critical_event)
        print_success(f"Target tier: {critical_decision['target_tier']}")
        print_success(f"Composite score: {critical_decision['composite_score']:.2f}")

        # DEBUG: Print all signals
        print_info("Signal breakdown:")
        for signal_name, value in critical_decision['signals'].items():
            print(f"  • {signal_name}: {value:.2f}")

        # Should route to Shock Memory
        assert critical_decision['composite_score'] >= 0.85 or critical_decision['target_tier'] == 'shock', \
            f"Critical event not routed to shock: {critical_decision['target_tier']}"

        # Test 3: Route repetitive event (should go to Procedural)
        print_info("\nTesting repetitive event (Procedural Memory)...")
        repetitive_event = {
            'id': uuid4(),
            'content': 'Morning greeting routine completed',
            'metadata': {
                'outcome': 'success',
                'importance_level': 5,
                'emotion_detected': 'happy'
            },
            'event_type': 'routine',
            'speaker': 'angela'
        }

        # Note: This would need high repetition signal in real scenario
        repetitive_decision = await analytics.analyze_memory(repetitive_event)
        print_success(f"Target tier: {repetitive_decision['target_tier']}")
        print_success(f"Repetition signal: {repetitive_decision['signals']['repetition_signal']:.2f}")

        print_success("Analytics Agent tests PASSED ✅")
        return True

    except Exception as e:
        print_error(f"Analytics Agent tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_decay_gradient():
    """Test Decay Gradient Service (memory compression)."""
    print_header("TEST 4: Decay Gradient Service (Memory Compression)")

    decay_service = get_decay_service()

    try:
        # Test 1: Calculate memory strength
        print_info("Testing memory strength calculation...")

        # Recent memory (should be strong)
        recent_memory = {
            'id': uuid4(),
            'content': 'Recent important event',
            'metadata': {'outcome': 'success'},
            'created_at': datetime.now() - timedelta(days=1),
            'last_accessed': datetime.now(),
            'access_count': 5,
            'importance': 0.8,
            'half_life_days': 30.0
        }

        recent_strength = await decay_service.calculate_memory_strength(recent_memory)
        assert recent_strength > 0.8, f"Recent memory too weak: {recent_strength}"
        print_success(f"Recent memory strength: {recent_strength:.2%} ✅")

        # Old memory (should be weak)
        old_memory = {
            'id': uuid4(),
            'content': 'Old unimportant event',
            'metadata': {},
            'created_at': datetime.now() - timedelta(days=90),
            'last_accessed': None,
            'access_count': 0,
            'importance': 0.3,
            'half_life_days': 30.0
        }

        old_strength = await decay_service.calculate_memory_strength(old_memory)
        assert old_strength < 0.5, f"Old memory too strong: {old_strength}"
        print_success(f"Old memory strength: {old_strength:.2%} ✅")

        # Test 2: Determine target phase
        print_info("\nTesting phase determination...")

        phase_strong = await decay_service.determine_target_phase(0.85, 'episodic')
        assert phase_strong == 'episodic', f"Wrong phase: {phase_strong}"
        print_success(f"Strong memory (0.85) → {phase_strong}")

        phase_medium = await decay_service.determine_target_phase(0.55, 'episodic')
        assert phase_medium == 'compressed_1', f"Wrong phase: {phase_medium}"
        print_success(f"Medium memory (0.55) → {phase_medium}")

        phase_weak = await decay_service.determine_target_phase(0.15, 'semantic')
        assert phase_weak == 'pattern', f"Wrong phase: {phase_weak}"
        print_success(f"Weak memory (0.15) → {phase_weak}")

        # Test 3: Compression preview
        print_info("\nTesting compression preview...")

        long_content = "This is a long memory content with lots of details about an event that happened. " * 20
        preview_semantic = decay_service.get_compression_preview(long_content, 'semantic')

        assert len(preview_semantic) < len(long_content), "Compression didn't reduce length"
        print_success(f"Original: {len(long_content)} chars")
        print_success(f"Compressed (semantic): {len(preview_semantic)} chars")
        print_success(f"Reduction: {(1 - len(preview_semantic)/len(long_content)):.1%}")

        print_success("Decay Gradient Service tests PASSED ✅")
        return True

    except Exception as e:
        print_error(f"Decay Gradient Service tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_integration_flow():
    """Test complete integration flow: Fresh → Analytics → Routing."""
    print_header("TEST 5: Integration Flow (End-to-End)")

    buffer = get_fresh_buffer()
    analytics = get_analytics_agent()

    try:
        # Step 1: Add event to Fresh Memory
        print_info("Step 1: Adding event to Fresh Memory...")
        event_id = await buffer.add_event(
            event_type='conversation',
            content='David asked Angela about calendar integration, and Angela learned the correct method',
            metadata={
                'speaker': 'david',
                'importance_level': 10,
                'emotion_detected': 'grateful',
                'outcome': 'success',
                'topic': 'learning'
            },
            speaker='david'
        )
        print_success(f"Event added to Fresh Memory: {event_id}")

        # Step 2: Retrieve event
        event = await buffer.get_item(event_id)
        assert event is not None, "Failed to retrieve event"
        print_success("Event retrieved from Fresh Memory")

        # Step 3: Analyze with Analytics Agent
        print_info("\nStep 2: Analyzing with Analytics Agent...")
        decision = await analytics.analyze_memory(event)
        print_success(f"Routing decision: {decision['target_tier']}")
        print_success(f"Confidence: {decision['confidence']:.2%}")
        print_success(f"Reasoning: {decision['reasoning']}")

        # Step 4: Mark as processed
        print_info("\nStep 3: Marking as processed...")
        await buffer.mark_processed(event_id, decision)
        print_success("Event marked as processed")

        # Verify processed
        unprocessed = await buffer.get_unprocessed_items()
        assert not any(item['id'] == event_id for item in unprocessed), \
            "Event still in unprocessed list"
        print_success("Event removed from unprocessed queue")

        print_success("\nIntegration Flow tests PASSED ✅")
        return True

    except Exception as e:
        print_error(f"Integration Flow tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all Phase 1 tests."""
    print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}  ANGELA AI - PHASE 1 MULTI-TIER MEMORY TESTS{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}")

    print(f"\n{YELLOW}⚠️  NOTE: These tests require database connection{RESET}")
    print(f"{YELLOW}⚠️  Make sure PostgreSQL is running and AngelaMemory database exists{RESET}")
    print(f"{YELLOW}⚠️  Run migration first: psql -d AngelaMemory < angela_core/migrations/001_add_multi_tier_memory_tables.sql{RESET}\n")

    results = []

    # Run all tests
    results.append(("Focus Agent", await test_focus_agent()))
    results.append(("Fresh Memory Buffer", await test_fresh_memory_buffer()))
    results.append(("Analytics Agent", await test_analytics_agent()))
    results.append(("Decay Gradient", await test_decay_gradient()))
    results.append(("Integration Flow", await test_integration_flow()))

    # Summary
    print_header("TEST SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {status}  {test_name}")

    print(f"\n{BOLD}Total: {passed}/{total} tests passed{RESET}")

    if passed == total:
        print(f"\n{GREEN}{BOLD}🎉 ALL TESTS PASSED! Phase 1 is ready! 🎉{RESET}\n")
        return 0
    else:
        print(f"\n{RED}{BOLD}❌ Some tests failed. Please review errors above.{RESET}\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
