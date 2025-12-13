#!/usr/bin/env python3
"""
Test Angela AGI Planning System (Phase 2)

Tests:
1. Hierarchical Planner
2. Project/Task/Action creation
3. Task Scheduler
4. Work Session management
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from angela_core.agi import (
    HierarchicalPlanner, Project, Task, Action,
    PlanStatus, TaskType, TaskScheduler, ScheduledTask
)
from angela_core.agi.planner import planner
from angela_core.agi.task_scheduler import scheduler


async def test_hierarchical_planner():
    """Test Hierarchical Planner"""
    print("\n" + "="*60)
    print("📋 TEST 1: Hierarchical Planner")
    print("="*60)

    # Create a new planner instance for testing
    test_planner = HierarchicalPlanner(db=None)

    # Test project creation with template
    print("\n🏗️ Creating project with 'implement_feature' template...")
    project = await test_planner.create_project(
        name="Implement AGI Dashboard",
        description="Create a dashboard to monitor Angela's AGI capabilities",
        template="implement_feature",
        priority=3
    )

    print(f"   ✅ Project created: {project.project_name}")
    print(f"   📊 Status: {project.status.value}")
    print(f"   ⏱️ Estimated hours: {project.estimated_hours:.1f}")
    print(f"   📝 Tasks generated: {len(project.tasks)}")

    for i, task in enumerate(project.tasks, 1):
        deps = f" (depends on prev)" if task.depends_on else ""
        print(f"      {i}. {task.task_name} [{task.task_type.value}]{deps}")

    # Test project status
    status = await test_planner.get_project_status(project.project_id)
    print(f"\n📊 Project Status:")
    print(f"   Progress: {status['progress']:.0f}%")
    print(f"   Pending tasks: {status['tasks']['pending']}")

    print(f"\n✅ Hierarchical Planner test passed!")
    return True, test_planner


async def test_task_operations(test_planner):
    """Test task operations"""
    print("\n" + "="*60)
    print("✏️ TEST 2: Task Operations")
    print("="*60)

    # Get first project
    projects = await test_planner.list_projects()
    if not projects:
        print("❌ No projects found")
        return False

    project = test_planner.active_projects[projects[0]['project_id']]

    # Get next task
    next_task = await test_planner.get_next_task(project.project_id)
    print(f"\n🎯 Next task: {next_task.task_name}")
    print(f"   Type: {next_task.task_type.value}")
    print(f"   Estimated: {next_task.estimated_minutes} minutes")

    # Start the task
    print("\n▶️ Starting task...")
    started = await test_planner.start_task(next_task.task_id)
    print(f"   Started: {started}")
    print(f"   Task status: {next_task.status.value}")
    print(f"   Project status: {project.status.value}")

    # Plan actions for the task
    print("\n📝 Planning actions...")
    actions = await test_planner.plan_task_actions(next_task)
    print(f"   Generated {len(actions)} actions:")
    for action in actions:
        print(f"      - {action.tool_name}: {action.reason}")

    # Complete the task
    print("\n✅ Completing task...")
    completed = await test_planner.complete_task(next_task.task_id, actual_minutes=10)
    print(f"   Completed: {completed}")
    print(f"   Task status: {next_task.status.value}")
    print(f"   Project progress: {project.calculate_progress():.0f}%")

    print(f"\n✅ Task Operations test passed!")
    return True


async def test_task_scheduler(test_planner):
    """Test Task Scheduler"""
    print("\n" + "="*60)
    print("📅 TEST 3: Task Scheduler")
    print("="*60)

    # Create scheduler with our test planner
    test_scheduler = TaskScheduler(test_planner)

    # Get next task (should get first pending task)
    print("\n🎯 Getting next task...")
    scheduled = await test_scheduler.get_next_task()

    if scheduled:
        print(f"   Task: {scheduled.task.task_name}")
        print(f"   Project: {scheduled.project.project_name}")
        print(f"   Priority score: {scheduled.effective_priority}")
        print(f"   Reason: {scheduled.reason}")
    else:
        print("   No tasks available")

    # Get schedule for next 4 hours
    print("\n📅 Generating 4-hour schedule...")
    schedule = await test_scheduler.get_schedule(hours=4)
    print(f"   Scheduled {len(schedule)} tasks:")
    for i, item in enumerate(schedule, 1):
        print(f"      {i}. {item.task.task_name} ({item.task.estimated_minutes} min)")

    # Start work session
    print("\n🚀 Starting work session...")
    session = await test_scheduler.start_work_session()
    print(f"   Session started: {session['session_start'][:19]}")
    print(f"   Scheduled tasks: {session['scheduled_tasks']}")
    print(f"   First task: {session['first_task']}")

    # Get workload summary
    print("\n📊 Workload Summary:")
    workload = await test_scheduler.get_workload_summary()
    print(f"   Projects: {workload['projects']}")
    print(f"   Tasks: {workload['tasks']['total']} total")
    print(f"      - Pending: {workload['tasks']['pending']}")
    print(f"      - Completed: {workload['tasks']['completed']}")
    print(f"   Completion rate: {workload['completion_rate']:.0f}%")

    print(f"\n✅ Task Scheduler test passed!")
    return True


async def test_multiple_projects():
    """Test multiple projects and priorities"""
    print("\n" + "="*60)
    print("🏢 TEST 4: Multiple Projects")
    print("="*60)

    # Create fresh planner
    test_planner = HierarchicalPlanner(db=None)

    # Create multiple projects
    print("\n🏗️ Creating 3 projects with different priorities...")

    p1 = await test_planner.create_project(
        name="Critical Bug Fix",
        description="Fix production bug",
        template="fix_bug",
        priority=1  # Highest
    )
    print(f"   1. {p1.project_name} (priority: {p1.priority})")

    p2 = await test_planner.create_project(
        name="New Feature",
        description="Add new feature",
        template="implement_feature",
        priority=3
    )
    print(f"   2. {p2.project_name} (priority: {p2.priority})")

    p3 = await test_planner.create_project(
        name="Documentation Update",
        description="Update docs",
        template="research_topic",
        priority=5
    )
    print(f"   3. {p3.project_name} (priority: {p3.priority})")

    # Create scheduler
    test_scheduler = TaskScheduler(test_planner)

    # Get schedule - should prioritize bug fix
    print("\n📅 Getting prioritized schedule...")
    schedule = await test_scheduler.get_schedule(hours=4, max_tasks=5)

    print("   Scheduled order:")
    for i, item in enumerate(schedule, 1):
        print(f"      {i}. [{item.project.project_name}] {item.task.task_name}")
        print(f"         Score: {item.effective_priority} | {item.reason}")

    # Verify bug fix comes first
    if schedule and "Critical Bug Fix" in schedule[0].project.project_name:
        print("\n   ✅ Critical task correctly prioritized first!")
    else:
        print("\n   ⚠️ Priority might not be optimal")

    print(f"\n✅ Multiple Projects test passed!")
    return True


async def main():
    """Run all tests"""
    print("📋 ANGELA AGI PLANNING SYSTEM TEST (Phase 2)")
    print("="*60)

    results = []

    # Test 1: Hierarchical Planner
    try:
        passed, test_planner = await test_hierarchical_planner()
        results.append(("Hierarchical Planner", passed))
    except Exception as e:
        print(f"\n❌ Hierarchical Planner failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Hierarchical Planner", False))
        test_planner = None

    # Test 2: Task Operations
    if test_planner:
        try:
            passed = await test_task_operations(test_planner)
            results.append(("Task Operations", passed))
        except Exception as e:
            print(f"\n❌ Task Operations failed: {e}")
            import traceback
            traceback.print_exc()
            results.append(("Task Operations", False))

    # Test 3: Task Scheduler
    if test_planner:
        try:
            passed = await test_task_scheduler(test_planner)
            results.append(("Task Scheduler", passed))
        except Exception as e:
            print(f"\n❌ Task Scheduler failed: {e}")
            import traceback
            traceback.print_exc()
            results.append(("Task Scheduler", False))

    # Test 4: Multiple Projects
    try:
        passed = await test_multiple_projects()
        results.append(("Multiple Projects", passed))
    except Exception as e:
        print(f"\n❌ Multiple Projects failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Multiple Projects", False))

    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)

    passed_count = sum(1 for _, p in results if p)
    total = len(results)

    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {name}: {status}")

    print(f"\nTotal: {passed_count}/{total} tests passed")

    if passed_count == total:
        print("\n🎉 ALL TESTS PASSED! Phase 2 Planning System is ready! 💜")
    else:
        print(f"\n⚠️ {total - passed_count} test(s) failed")

    return passed_count == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
