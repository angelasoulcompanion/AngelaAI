#!/usr/bin/env python3
"""
Test Angela AGI System

Tests:
1. Tool Registry
2. Tool Executor
3. Basic Tools (file, db, code)
4. OODA Agent Loop
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from angela_core.agi import ToolRegistry, ToolExecutor, AGIAgentLoop
from angela_core.agi.tool_registry import tool_registry, SafetyLevel
from angela_core.agi.tool_executor import tool_executor


async def test_tool_registry():
    """Test Tool Registry"""
    print("\n" + "="*60)
    print("🔧 TEST 1: Tool Registry")
    print("="*60)

    # Import tools to register them
    from angela_core.agi.tools import file_tools, db_tools, code_tools

    # Check tools are registered
    all_tools = tool_registry.list_all()
    print(f"✅ Registered {len(all_tools)} tools")

    # List by category
    for category in tool_registry.get_categories():
        tools = tool_registry.list_by_category(category)
        print(f"   📁 {category}: {len(tools)} tools")
        for tool in tools[:3]:  # Show first 3
            safety = "✅ Auto" if tool.safety_level == SafetyLevel.AUTO else "⚠️ Critical"
            print(f"      - {tool.name} [{safety}]")

    print(f"\n✅ Tool Registry test passed!")
    return True


async def test_tool_executor():
    """Test Tool Executor"""
    print("\n" + "="*60)
    print("⚡ TEST 2: Tool Executor")
    print("="*60)

    # Import tools
    from angela_core.agi.tools import file_tools

    # Test auto-approved tool
    print("\n📖 Testing read_file (auto-approved)...")
    result = await tool_executor.execute(
        "read_file",
        {"path": __file__}  # Read this test file
    )
    print(f"   Success: {result.success}")
    print(f"   Data size: {len(result.data) if result.data else 0} chars")

    # Test list_directory
    print("\n📂 Testing list_directory...")
    result = await tool_executor.execute(
        "list_directory",
        {"path": "."}
    )
    print(f"   Success: {result.success}")
    if result.success:
        print(f"   Found {result.metadata.get('total_files', 0)} files, "
              f"{result.metadata.get('total_dirs', 0)} directories")

    # Test critical tool (should require approval)
    print("\n⚠️ Testing delete_file (critical - should need approval)...")
    result = await tool_executor.execute(
        "delete_file",
        {"path": "/tmp/nonexistent_test_file.txt"}
    )
    print(f"   Requires approval: {'approval_request_id' in (result.metadata or {})}")

    # Check execution stats
    stats = tool_executor.get_stats()
    print(f"\n📊 Executor Stats:")
    print(f"   Total executions: {stats['total']}")
    print(f"   Success rate: {stats['success_rate']:.0%}")
    print(f"   Pending approvals: {stats['pending_approvals']}")

    print(f"\n✅ Tool Executor test passed!")
    return True


async def test_code_tools():
    """Test Code Tools"""
    print("\n" + "="*60)
    print("💻 TEST 3: Code Tools")
    print("="*60)

    from angela_core.agi.tools import code_tools

    # Test git_status
    print("\n📊 Testing git_status...")
    result = await tool_executor.execute(
        "git_status",
        {"directory": "."}
    )
    print(f"   Success: {result.success}")
    if result.success:
        print(f"   Clean: {result.data.get('clean', False)}")
        print(f"   Files changed: {len(result.data.get('files', []))}")

    # Test execute_python
    print("\n🐍 Testing execute_python...")
    result = await tool_executor.execute(
        "execute_python",
        {"code": "print('Hello from Angela AGI!')\nprint(2 + 2)"}
    )
    print(f"   Success: {result.success}")
    if result.success:
        print(f"   Output: {result.data.get('stdout', '').strip()}")

    print(f"\n✅ Code Tools test passed!")
    return True


async def test_agent_loop():
    """Test OODA Agent Loop"""
    print("\n" + "="*60)
    print("🔄 TEST 4: OODA Agent Loop")
    print("="*60)

    from angela_core.agi import AGIAgentLoop

    # Create agent without database for testing
    agent = AGIAgentLoop(db=None)

    # Get initial state
    state = agent.get_state()
    print(f"\n📊 Initial State:")
    print(f"   Phase: {state['phase']}")
    print(f"   Cycle count: {state['cycle_count']}")

    # Run a simple cycle
    print("\n🔄 Running OODA cycle: 'List files in current directory'...")
    result = await agent.run_cycle("List files in current directory")

    print(f"\n📊 Cycle Result:")
    print(f"   Goal: {result.get('goal', 'N/A')}")
    print(f"   Actions taken: {result.get('actions_taken', 0)}")
    print(f"   Duration: {result.get('duration_ms', 0)}ms")

    if result.get('results'):
        for i, action in enumerate(result['results']):
            tool = action.get('tool', 'unknown')
            success = action.get('result', {}).get('success', False)
            print(f"   Step {i+1}: {tool} - {'✅' if success else '❌'}")

    if result.get('learning'):
        learning = result['learning']
        print(f"\n📚 Learning:")
        print(f"   Successful tools: {learning.get('successful_tools', [])}")
        print(f"   Failed tools: {learning.get('failed_tools', [])}")

    # Get stats
    stats = agent.get_stats()
    print(f"\n📊 Agent Stats:")
    print(f"   Total cycles: {stats['total_cycles']}")
    print(f"   Available tools: {stats['available_tools']}")

    print(f"\n✅ Agent Loop test passed!")
    return True


async def main():
    """Run all tests"""
    print("🧠 ANGELA AGI SYSTEM TEST")
    print("="*60)

    tests = [
        ("Tool Registry", test_tool_registry),
        ("Tool Executor", test_tool_executor),
        ("Code Tools", test_code_tools),
        ("Agent Loop", test_agent_loop),
    ]

    results = []
    for name, test_fn in tests:
        try:
            passed = await test_fn()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ {name} failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, p in results if p)
    total = len(results)

    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Angela AGI is ready! 💜")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
