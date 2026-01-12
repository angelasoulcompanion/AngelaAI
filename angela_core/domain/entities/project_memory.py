#!/usr/bin/env python3
"""
Project Memory Entities - Angela's Technical Project Knowledge

Stores technical knowledge for each project Angela works on:
- Schemas: Database structure, columns, gotchas
- Flows: Business, data, API, deployment flows
- Patterns: DRY, reusable code, utilities
- Relations: Entity relationships with JOIN conditions
- Decisions: Architecture Decision Records (ADR)

This enables fast and accurate recall of project-specific technical details.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class FlowType(str, Enum):
    """Types of project flows."""
    BUSINESS = "business"
    DATA = "data"
    API = "api"
    DEPLOYMENT = "deployment"
    AUTH = "auth"


class SchemaType(str, Enum):
    """Types of database schemas."""
    TABLE = "table"
    VIEW = "view"
    MATERIALIZED_VIEW = "materialized_view"
    FUNCTION = "function"


class PatternType(str, Enum):
    """Types of reusable patterns."""
    UTILITY = "utility"
    DECORATOR = "decorator"
    HOOK = "hook"
    COMPONENT = "component"
    SERVICE = "service"
    QUERY = "query"
    MIDDLEWARE = "middleware"


class RelationType(str, Enum):
    """Types of entity relationships."""
    ONE_TO_ONE = "1:1"
    ONE_TO_MANY = "1:N"
    MANY_TO_MANY = "N:M"


class DecisionCategory(str, Enum):
    """Categories of technical decisions."""
    ARCHITECTURE = "architecture"
    DATABASE = "database"
    API = "api"
    SECURITY = "security"
    PERFORMANCE = "performance"
    TESTING = "testing"
    AI_ML = "ai_ml"


class DecisionStatus(str, Enum):
    """Status of technical decisions."""
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    DEPRECATED = "deprecated"


# ============================================================================
# PROJECT ENTITY
# ============================================================================

@dataclass
class Project:
    """
    Project master data.

    Represents a software project Angela works on with David.
    """
    project_id: UUID
    project_name: str
    project_code: str  # Short code like 'WTU', 'SECA', 'ANGELA'
    description: Optional[str] = None
    tech_stack: Dict[str, str] = field(default_factory=dict)
    repository_url: Optional[str] = None
    is_active: bool = True
    last_worked_at: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": str(self.project_id),
            "project_name": self.project_name,
            "project_code": self.project_code,
            "description": self.description,
            "tech_stack": self.tech_stack,
            "repository_url": self.repository_url,
            "is_active": self.is_active,
            "last_worked_at": self.last_worked_at.isoformat() if self.last_worked_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# ============================================================================
# PROJECT SCHEMA ENTITY
# ============================================================================

@dataclass
class ProjectSchema:
    """
    Database schema for a project table/view.

    Stores column definitions, indexes, and importantly - gotchas/edge cases.
    """
    schema_id: UUID
    project_id: UUID
    table_name: str
    schema_type: SchemaType = SchemaType.TABLE
    columns: List[Dict[str, Any]] = field(default_factory=list)
    primary_key: Optional[str] = None
    foreign_keys: List[Dict[str, str]] = field(default_factory=list)
    indexes: List[Dict[str, Any]] = field(default_factory=list)
    purpose: str = ""
    important_queries: Optional[str] = None
    gotchas: Optional[str] = None  # Critical edge cases, NULL handling, etc.
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_id": str(self.schema_id),
            "project_id": str(self.project_id),
            "table_name": self.table_name,
            "schema_type": self.schema_type.value if isinstance(self.schema_type, SchemaType) else self.schema_type,
            "columns": self.columns,
            "primary_key": self.primary_key,
            "foreign_keys": self.foreign_keys,
            "indexes": self.indexes,
            "purpose": self.purpose,
            "important_queries": self.important_queries,
            "gotchas": self.gotchas,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# ============================================================================
# PROJECT FLOW ENTITY
# ============================================================================

@dataclass
class ProjectFlow:
    """
    Business/Data/API flow for a project.

    Documents step-by-step flows with entry/exit points and critical notes.
    """
    flow_id: UUID
    project_id: UUID
    flow_name: str
    flow_type: FlowType
    description: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    entry_point: Optional[str] = None
    exit_point: Optional[str] = None
    diagram_path: Optional[str] = None
    critical_notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "flow_id": str(self.flow_id),
            "project_id": str(self.project_id),
            "flow_name": self.flow_name,
            "flow_type": self.flow_type.value if isinstance(self.flow_type, FlowType) else self.flow_type,
            "description": self.description,
            "steps": self.steps,
            "entry_point": self.entry_point,
            "exit_point": self.exit_point,
            "diagram_path": self.diagram_path,
            "critical_notes": self.critical_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# ============================================================================
# PROJECT PATTERN ENTITY
# ============================================================================

@dataclass
class ProjectPattern:
    """
    DRY/Reusable code pattern for a project.

    Stores code snippets, usage examples, and tracks how often it's used.
    """
    pattern_id: UUID
    project_id: UUID
    pattern_name: str
    pattern_type: PatternType
    description: str
    code_snippet: Optional[str] = None
    file_path: Optional[str] = None
    usage_example: Optional[str] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    returns: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)
    used_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def increment_usage(self) -> 'ProjectPattern':
        """Track pattern usage."""
        self.used_count += 1
        self.updated_at = datetime.now()
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": str(self.pattern_id),
            "project_id": str(self.project_id),
            "pattern_name": self.pattern_name,
            "pattern_type": self.pattern_type.value if isinstance(self.pattern_type, PatternType) else self.pattern_type,
            "description": self.description,
            "code_snippet": self.code_snippet,
            "file_path": self.file_path,
            "usage_example": self.usage_example,
            "parameters": self.parameters,
            "returns": self.returns,
            "depends_on": self.depends_on,
            "used_count": self.used_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# ============================================================================
# PROJECT ENTITY RELATION
# ============================================================================

@dataclass
class ProjectEntityRelation:
    """
    Entity relationship with exact JOIN condition.

    Critical for remembering how to join tables correctly.
    """
    relation_id: UUID
    project_id: UUID
    from_table: str
    to_table: str
    relation_type: RelationType
    relation_name: Optional[str] = None
    join_condition: str = ""  # Exact SQL JOIN condition
    is_required: bool = True
    cascade_behavior: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relation_id": str(self.relation_id),
            "project_id": str(self.project_id),
            "from_table": self.from_table,
            "to_table": self.to_table,
            "relation_type": self.relation_type.value if isinstance(self.relation_type, RelationType) else self.relation_type,
            "relation_name": self.relation_name,
            "join_condition": self.join_condition,
            "is_required": self.is_required,
            "cascade_behavior": self.cascade_behavior,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# ============================================================================
# PROJECT TECHNICAL DECISION (ADR)
# ============================================================================

@dataclass
class ProjectTechnicalDecision:
    """
    Architecture Decision Record (ADR) for a project.

    Documents technical decisions with context, options considered, and reasoning.
    """
    decision_id: UUID
    project_id: UUID
    decision_title: str
    category: DecisionCategory
    context: str
    options_considered: List[Dict[str, Any]] = field(default_factory=list)
    decision_made: str = ""
    reasoning: str = ""
    consequences: Optional[str] = None
    decided_at: datetime = field(default_factory=datetime.now)
    decided_by: str = "David"
    status: DecisionStatus = DecisionStatus.ACTIVE
    superseded_by: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.now)

    def supersede(self, new_decision_id: UUID) -> 'ProjectTechnicalDecision':
        """Mark decision as superseded by another."""
        self.status = DecisionStatus.SUPERSEDED
        self.superseded_by = new_decision_id
        return self

    def deprecate(self) -> 'ProjectTechnicalDecision':
        """Mark decision as deprecated."""
        self.status = DecisionStatus.DEPRECATED
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": str(self.decision_id),
            "project_id": str(self.project_id),
            "decision_title": self.decision_title,
            "category": self.category.value if isinstance(self.category, DecisionCategory) else self.category,
            "context": self.context,
            "options_considered": self.options_considered,
            "decision_made": self.decision_made,
            "reasoning": self.reasoning,
            "consequences": self.consequences,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "decided_by": self.decided_by,
            "status": self.status.value if isinstance(self.status, DecisionStatus) else self.status,
            "superseded_by": str(self.superseded_by) if self.superseded_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# ============================================================================
# PROJECT CONTEXT (Aggregate)
# ============================================================================

@dataclass
class ProjectContext:
    """
    Complete technical context for a project.

    Aggregate that combines all project knowledge for fast recall.
    """
    project: Project
    schemas: List[ProjectSchema] = field(default_factory=list)
    flows: List[ProjectFlow] = field(default_factory=list)
    patterns: List[ProjectPattern] = field(default_factory=list)
    relations: List[ProjectEntityRelation] = field(default_factory=list)
    decisions: List[ProjectTechnicalDecision] = field(default_factory=list)

    def get_schema(self, table_name: str) -> Optional[ProjectSchema]:
        """Get schema by table name."""
        for schema in self.schemas:
            if schema.table_name.lower() == table_name.lower():
                return schema
        return None

    def get_flow(self, flow_type: FlowType) -> List[ProjectFlow]:
        """Get flows by type."""
        return [f for f in self.flows if f.flow_type == flow_type]

    def get_pattern(self, pattern_type: PatternType) -> List[ProjectPattern]:
        """Get patterns by type."""
        return [p for p in self.patterns if p.pattern_type == pattern_type]

    def get_relations_for_table(self, table_name: str) -> List[ProjectEntityRelation]:
        """Get all relations involving a table."""
        return [r for r in self.relations
                if r.from_table.lower() == table_name.lower()
                or r.to_table.lower() == table_name.lower()]

    def get_decisions(self, category: DecisionCategory = None) -> List[ProjectTechnicalDecision]:
        """Get decisions, optionally filtered by category."""
        if category is None:
            return [d for d in self.decisions if d.status == DecisionStatus.ACTIVE]
        return [d for d in self.decisions
                if d.category == category and d.status == DecisionStatus.ACTIVE]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project": self.project.to_dict(),
            "schemas": [s.to_dict() for s in self.schemas],
            "flows": [f.to_dict() for f in self.flows],
            "patterns": [p.to_dict() for p in self.patterns],
            "relations": [r.to_dict() for r in self.relations],
            "decisions": [d.to_dict() for d in self.decisions],
            "summary": {
                "schema_count": len(self.schemas),
                "flow_count": len(self.flows),
                "pattern_count": len(self.patterns),
                "relation_count": len(self.relations),
                "decision_count": len(self.decisions)
            }
        }
