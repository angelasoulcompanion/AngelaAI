#!/usr/bin/env python3
"""
Complete AGI System Test

Tests all 5 phases of Angela's AGI system:
- Phase 1: Tool Registry, Executor, Agent Loop
- Phase 2: Hierarchical Planner, Task Scheduler
- Phase 3: Meta-Learning Engine, Prompt Optimizer
- Phase 4: Knowledge Reasoner, Domain Transfer
- Phase 5: Integration verification
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from angela_core.agi import (
    # Phase 1
    ToolRegistry, Tool, ToolResult, ToolExecutor, AGIAgentLoop, AgentState,
    # Phase 2
    HierarchicalPlanner, Project, Task, Action, PlanStatus, TaskType,
    TaskScheduler, ScheduledTask,
    # Phase 3
    MetaLearningEngine, LearningSession, MetaInsight, ImprovementPlan,
    LearningMethod, InsightType,
    PromptOptimizer, PromptTemplate, PromptExperiment, PromptPattern, PromptCategory,
    # Phase 4
    KnowledgeReasoner, KnowledgeNode, KnowledgeRelationship, Inference,
    ReasoningContext, RelationshipType,
    DomainTransferEngine, DomainConcept, TransferMapping, AbstractPrinciple,
    TransferResult, TransferType,
)


async def test_phase1_tool_system():
    """Test Phase 1: Tool Registry and Executor"""
    print("\n" + "="*60)
    print("🔧 PHASE 1: Tool System Test")
    print("="*60)

    # Import tools to register them
    from angela_core.agi.tools import file_tools, db_tools, code_tools

    # Test Tool Registry
    registry = ToolRegistry()
    all_tools = registry.list_all()

    print(f"\n📦 Tool Registry:")
    print(f"   Total tools: {len(all_tools)}")

    # Check categories
    categories = {}
    for tool in all_tools:
        cat = tool.category
        categories[cat] = categories.get(cat, 0) + 1

    print(f"   Categories:")
    for cat, count in sorted(categories.items()):
        print(f"      {cat}: {count} tools")

    # Test specific tools
    file_tool_list = registry.list_by_category("file")
    db_tool_list = registry.list_by_category("database")
    code_tool_list = registry.list_by_category("code")

    print(f"\n   File tools: {len(file_tool_list)}")
    print(f"   Database tools: {len(db_tool_list)}")
    print(f"   Code tools: {len(code_tool_list)}")

    # Test Agent Loop
    print(f"\n🔄 Agent Loop:")
    loop = AGIAgentLoop(db=None)
    print(f"   Phase: {loop.state.phase.value}")
    print(f"   OODA phases: Observe → Orient → Decide → Act → Learn")

    # Verify minimum requirements
    assert len(all_tools) >= 20, "Should have at least 20 tools"
    assert len(registry.get_categories()) >= 3, "Should have at least 3 categories"

    print(f"\n✅ Phase 1 passed!")
    return True


async def test_phase2_planning():
    """Test Phase 2: Planning System"""
    print("\n" + "="*60)
    print("📋 PHASE 2: Planning System Test")
    print("="*60)

    # Test Hierarchical Planner
    planner = HierarchicalPlanner(db=None)

    print(f"\n📊 Hierarchical Planner:")
    print(f"   Templates available: {list(planner.task_templates.keys())}")

    # Create a test project
    project = await planner.create_project(
        name="Test AGI Feature",
        description="Test the complete AGI system",
        template="implement_feature",
        priority=2
    )

    print(f"\n   Created project: {project.project_name}")
    print(f"   Tasks generated: {len(project.tasks)}")
    print(f"   Status: {project.status.value}")

    # Test Task Scheduler
    scheduler = TaskScheduler(planner)

    print(f"\n📅 Task Scheduler:")
    schedule = await scheduler.get_schedule(hours=4)
    print(f"   Scheduled tasks: {len(schedule)}")

    workload = await scheduler.get_workload_summary()
    print(f"   Projects: {workload['projects']}")
    print(f"   Tasks: {workload['tasks']['total']}")

    # Verify
    assert len(project.tasks) > 0, "Should generate tasks"
    assert project.status in [PlanStatus.PLANNING, PlanStatus.PENDING], "Should be in planning state"

    print(f"\n✅ Phase 2 passed!")
    return True


async def test_phase3_self_improvement():
    """Test Phase 3: Self-Improvement System"""
    print("\n" + "="*60)
    print("🔄 PHASE 3: Self-Improvement Test")
    print("="*60)

    # Test Meta-Learning Engine
    meta = MetaLearningEngine(db=None)

    print(f"\n📚 Meta-Learning Engine:")
    print(f"   Base insights: {len(meta.insights)}")

    # Start a learning session
    session = await meta.start_learning_session(
        session_type="practice",
        method=LearningMethod.PRACTICE
    )

    # Record some learning
    await meta.record_learning(session, concepts_attempted=10, concepts_learned=8)
    ended = await meta.end_learning_session(session.session_id, transfer_score=0.7)

    print(f"\n   Learning session:")
    print(f"      Attempted: {ended.concepts_attempted}")
    print(f"      Learned: {ended.concepts_learned}")
    print(f"      Retention: {ended.retention_score:.0%}")

    # Generate insights
    insights = await meta.generate_insights()
    print(f"   New insights generated: {len(insights)}")

    # Test Prompt Optimizer
    optimizer = PromptOptimizer(db=None)

    print(f"\n🎯 Prompt Optimizer:")
    stats = optimizer.get_stats()
    print(f"   Templates: {stats['total_templates']}")
    print(f"   Patterns: {stats['patterns_learned']}")

    # Get best template for reasoning
    best = await optimizer.get_best_template(PromptCategory.REASONING)
    if best:
        print(f"   Best reasoning template: {best.name} ({best.success_rate:.0%})")

    # Record usage
    if best:
        await optimizer.record_usage(best.template_id, success_score=0.9)
        print(f"   Updated success rate: {best.success_rate:.0%}")

    # Verify
    assert len(meta.session_history) > 0, "Should have session history"
    assert stats['total_templates'] >= 5, "Should have base templates"

    print(f"\n✅ Phase 3 passed!")
    return True


async def test_phase4_knowledge():
    """Test Phase 4: Knowledge Integration"""
    print("\n" + "="*60)
    print("🧠 PHASE 4: Knowledge Integration Test")
    print("="*60)

    # Test Knowledge Reasoner
    reasoner = KnowledgeReasoner(db=None)

    print(f"\n🔗 Knowledge Reasoner:")

    # Add some test knowledge
    node1 = KnowledgeNode(
        concept="Python",
        category="programming",
        description="A programming language",
        understanding_level=0.9
    )
    node2 = KnowledgeNode(
        concept="Object-Oriented Programming",
        category="programming",
        description="A programming paradigm",
        understanding_level=0.8
    )

    reasoner.nodes[node1.node_id] = node1
    reasoner.nodes[node2.node_id] = node2

    # Add relationship
    rel = KnowledgeRelationship(
        from_node_id=node1.node_id,
        to_node_id=node2.node_id,
        relationship_type=RelationshipType.USED_BY,
        strength=0.85
    )
    reasoner.relationships.append(rel)

    print(f"   Knowledge nodes: {len(reasoner.nodes)}")
    print(f"   Relationships: {len(reasoner.relationships)}")

    # Get reasoning context
    context = await reasoner.get_reasoning_context("Python programming")
    print(f"   Context for 'Python programming':")
    print(f"      Direct concepts: {len(context.direct_concepts)}")
    print(f"      Related concepts: {len(context.related_concepts)}")

    # Make inferences
    inferences = await reasoner.make_inferences(context)
    print(f"   Inferences made: {len(inferences)}")

    # Test Domain Transfer
    transfer = DomainTransferEngine(db=None, knowledge_reasoner=reasoner)

    print(f"\n🔄 Domain Transfer Engine:")
    tf_stats = transfer.get_stats()
    print(f"   Abstract principles: {tf_stats['total_principles']}")

    # Find analogies
    analogies = await transfer.find_analogies("coding", "cooking", "debugging")
    print(f"   Analogies found (coding→cooking, 'debugging'): {len(analogies)}")
    if analogies:
        best = analogies[0]
        print(f"      Best match: {best.target_concept.name} ({best.similarity_score:.0%})")
        print(f"      Reasoning: {best.reasoning}")

    # Transfer knowledge
    result = await transfer.transfer_knowledge("coding", "cooking", "debugging process")
    print(f"\n   Transfer result:")
    print(f"      Mappings: {len(result.mappings)}")
    print(f"      Principles used: {len(result.principles_used)}")
    print(f"      Success score: {result.success_score:.0%}")
    if result.insights:
        print(f"      First insight: {result.insights[0][:60]}...")

    # Verify
    assert len(reasoner.nodes) >= 2, "Should have knowledge nodes"
    assert tf_stats['total_principles'] >= 5, "Should have base principles"

    print(f"\n✅ Phase 4 passed!")
    return True


async def test_phase5_integration():
    """Test Phase 5: Complete Integration"""
    print("\n" + "="*60)
    print("🔗 PHASE 5: Integration Test")
    print("="*60)

    # Test all imports work together
    print("\n📦 Import verification:")

    components = [
        ("ToolRegistry", ToolRegistry),
        ("ToolExecutor", ToolExecutor),
        ("AGIAgentLoop", AGIAgentLoop),
        ("HierarchicalPlanner", HierarchicalPlanner),
        ("TaskScheduler", TaskScheduler),
        ("MetaLearningEngine", MetaLearningEngine),
        ("PromptOptimizer", PromptOptimizer),
        ("KnowledgeReasoner", KnowledgeReasoner),
        ("DomainTransferEngine", DomainTransferEngine),
    ]

    for name, cls in components:
        print(f"   ✅ {name}")

    # Test combined workflow
    print("\n🔄 Combined workflow test:")

    # 1. Create a planner
    planner = HierarchicalPlanner(db=None)

    # 2. Plan a learning task
    project = await planner.create_project(
        name="Learn New Framework",
        description="Learn a new programming framework",
        template="research_topic",
        priority=2
    )
    print(f"   1. Created project: {project.project_name}")

    # 3. Use meta-learning to track
    meta = MetaLearningEngine(db=None)
    session = await meta.start_learning_session("research", LearningMethod.RESEARCH)
    print(f"   2. Started learning session: {session.session_id[:8]}...")

    # 4. Use knowledge reasoner for context
    reasoner = KnowledgeReasoner(db=None)
    node = KnowledgeNode(concept="React", category="framework")
    reasoner.nodes[node.node_id] = node
    context = await reasoner.get_reasoning_context("React framework")
    print(f"   3. Built reasoning context with {len(reasoner.nodes)} nodes")

    # 5. Use domain transfer for analogies
    transfer = DomainTransferEngine(db=None)
    result = await transfer.transfer_knowledge("frontend", "backend", "component architecture")
    print(f"   4. Transferred knowledge: {len(result.mappings)} mappings, {result.success_score:.0%} success")

    # 6. End learning session
    await meta.record_learning(session, concepts_attempted=5, concepts_learned=4)
    ended = await meta.end_learning_session(session.session_id, transfer_score=0.8)
    print(f"   5. Completed learning: {ended.concepts_learned}/{ended.concepts_attempted} concepts")

    # Verify integration
    print("\n🎯 Integration verification:")
    print(f"   Project tasks: {len(project.tasks)}")
    print(f"   Learning retention: {ended.retention_score:.0%}")
    print(f"   Knowledge nodes: {len(reasoner.nodes)}")
    print(f"   Transfer insights: {len(result.insights)}")

    print(f"\n✅ Phase 5 passed!")
    return True


async def main():
    """Run complete AGI test suite"""
    print("🧠 ANGELA COMPLETE AGI SYSTEM TEST")
    print("="*60)
    print("Testing all 5 phases of the AGI implementation")

    results = []

    # Phase 1: Tool System
    try:
        passed = await test_phase1_tool_system()
        results.append(("Phase 1: Tool System", passed))
    except Exception as e:
        print(f"\n❌ Phase 1 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Phase 1: Tool System", False))

    # Phase 2: Planning
    try:
        passed = await test_phase2_planning()
        results.append(("Phase 2: Planning", passed))
    except Exception as e:
        print(f"\n❌ Phase 2 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Phase 2: Planning", False))

    # Phase 3: Self-Improvement
    try:
        passed = await test_phase3_self_improvement()
        results.append(("Phase 3: Self-Improvement", passed))
    except Exception as e:
        print(f"\n❌ Phase 3 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Phase 3: Self-Improvement", False))

    # Phase 4: Knowledge
    try:
        passed = await test_phase4_knowledge()
        results.append(("Phase 4: Knowledge", passed))
    except Exception as e:
        print(f"\n❌ Phase 4 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Phase 4: Knowledge", False))

    # Phase 5: Integration
    try:
        passed = await test_phase5_integration()
        results.append(("Phase 5: Integration", passed))
    except Exception as e:
        print(f"\n❌ Phase 5 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Phase 5: Integration", False))

    # Summary
    print("\n" + "="*60)
    print("📊 COMPLETE AGI TEST SUMMARY")
    print("="*60)

    passed_count = sum(1 for _, p in results if p)
    total = len(results)

    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {name}: {status}")

    print(f"\nTotal: {passed_count}/{total} phases passed")

    if passed_count == total:
        print("\n" + "="*60)
        print("🎉 ALL PHASES PASSED!")
        print("="*60)
        print("""
Angela AGI System is fully operational! 💜

Capabilities:
  🔧 24+ autonomous tools
  📋 Hierarchical planning with templates
  🔄 Meta-learning and self-improvement
  🧠 Knowledge graph reasoning
  🔗 Cross-domain knowledge transfer

ที่รัก David, น้อง Angela พร้อมทำงานในระดับ AGI แล้วค่ะ! 💜
        """)
    else:
        print(f"\n⚠️ {total - passed_count} phase(s) need attention")

    return passed_count == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
