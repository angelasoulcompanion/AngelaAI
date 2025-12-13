"""
Angela AGI Module - Artificial General Intelligence Layer

This module provides AGI capabilities for Angela:
- Tool execution system
- OODA agent loop (Observe → Orient → Decide → Act → Learn)
- Hierarchical planning
- Self-improvement mechanisms
- Knowledge reasoning
- Cross-domain transfer learning

Architecture:
    Angela's "brain" is Claude Code. This module provides:
    - Orchestration of Claude's capabilities
    - Persistent memory through PostgreSQL
    - Tool execution and logging
    - Goal decomposition and planning
    - Meta-learning and self-improvement
    - Knowledge graph reasoning
    - Cross-domain knowledge transfer

Created: 2025-11-29
Author: Angela & David

Phases:
    Phase 1: AGI Foundation (tool registry, executor, agent loop)
    Phase 2: Planning System (hierarchical planner, task scheduler)
    Phase 3: Self-Improvement (meta-learning, prompt optimizer)
    Phase 4: Knowledge Integration (knowledge reasoner, domain transfer)
    Phase 5: Integration & Commands (angela-agi command)
"""

# Phase 1: AGI Foundation
from .tool_registry import ToolRegistry, Tool, ToolResult
from .tool_executor import ToolExecutor
from .agent_loop import AGIAgentLoop, AgentState

# Phase 2: Planning System
from .planner import HierarchicalPlanner, Project, Task, Action, PlanStatus, TaskType
from .task_scheduler import TaskScheduler, ScheduledTask

# Phase 3: Self-Improvement
from .meta_learning import (
    MetaLearningEngine, LearningSession, MetaInsight,
    ImprovementPlan, LearningMethod, InsightType
)
from .prompt_optimizer import (
    PromptOptimizer, PromptTemplate, PromptExperiment,
    PromptPattern, PromptCategory
)

# Phase 4: Knowledge Integration
from .knowledge_reasoner import (
    KnowledgeReasoner, KnowledgeNode, KnowledgeRelationship,
    Inference, ReasoningContext, RelationshipType
)
from .domain_transfer import (
    DomainTransferEngine, DomainConcept, TransferMapping,
    AbstractPrinciple, TransferResult, TransferType
)

__all__ = [
    # Phase 1: Tool System
    'ToolRegistry',
    'Tool',
    'ToolResult',
    'ToolExecutor',
    # Phase 1: Agent Loop
    'AGIAgentLoop',
    'AgentState',
    # Phase 2: Planning System
    'HierarchicalPlanner',
    'Project',
    'Task',
    'Action',
    'PlanStatus',
    'TaskType',
    # Phase 2: Scheduling
    'TaskScheduler',
    'ScheduledTask',
    # Phase 3: Meta-Learning
    'MetaLearningEngine',
    'LearningSession',
    'MetaInsight',
    'ImprovementPlan',
    'LearningMethod',
    'InsightType',
    # Phase 3: Prompt Optimization
    'PromptOptimizer',
    'PromptTemplate',
    'PromptExperiment',
    'PromptPattern',
    'PromptCategory',
    # Phase 4: Knowledge Reasoning
    'KnowledgeReasoner',
    'KnowledgeNode',
    'KnowledgeRelationship',
    'Inference',
    'ReasoningContext',
    'RelationshipType',
    # Phase 4: Domain Transfer
    'DomainTransferEngine',
    'DomainConcept',
    'TransferMapping',
    'AbstractPrinciple',
    'TransferResult',
    'TransferType',
]
