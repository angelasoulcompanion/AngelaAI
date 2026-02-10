#!/usr/bin/env python3
"""
Project Memory Service - Angela's Technical Project Knowledge

CRUD operations and recall for project-specific technical knowledge:
- Projects: Master project data
- Schemas: Database tables, columns, gotchas
- Flows: Business, data, API flows
- Patterns: DRY, reusable code
- Relations: Entity relationships with JOIN conditions
- Decisions: Architecture Decision Records (ADR)

Usage:
    from angela_core.services.project_memory_service import ProjectMemoryService

    service = ProjectMemoryService()

    # Recall entire project context (call at session start)
    context = await service.recall_project_context("WTU")

    # Get specific items
    schema = await service.get_schema("WTU", "DimStudent")
    flows = await service.get_flows("WTU", flow_type="data")
    patterns = await service.find_patterns("WTU", pattern_type="query")
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID, uuid4

from angela_core.database import AngelaDatabase
from angela_core.services.base_db_service import BaseDBService
from angela_core.domain.entities.project_memory import (
    Project, ProjectSchema, ProjectFlow, ProjectPattern,
    ProjectEntityRelation, ProjectTechnicalDecision, ProjectContext,
    FlowType, SchemaType, PatternType, RelationType,
    DecisionCategory, DecisionStatus
)

logger = logging.getLogger(__name__)


class ProjectMemoryService(BaseDBService):
    """
    Service for managing Angela's project technical memory.

    Provides CRUD operations and intelligent recall of project knowledge.
    Database: Local PostgreSQL (angela database)
    """

    def __init__(self, db: AngelaDatabase = None):
        """Initialize with optional database connection."""
        if db is None:
            local_url = "postgresql://postgres@localhost:5432/angela"
            db = AngelaDatabase(connection_url=local_url)
        super().__init__(db)

    async def _ensure_connected(self):
        """Ensure database is connected."""
        await self.connect()

    # ========================================================================
    # PROJECT CONTEXT RECALL (Main Entry Point)
    # ========================================================================

    async def recall_project_context(self, project_code: str) -> Optional[ProjectContext]:
        """
        Load complete technical context for a project.

        Call this at session start to load all project knowledge.

        Args:
            project_code: Project code (e.g., 'WTU', 'SECA')

        Returns:
            ProjectContext with all schemas, flows, patterns, relations, decisions
        """
        await self._ensure_connected()

        try:
            # Get project
            project = await self.get_project(project_code)
            if not project:
                logger.warning(f"Project not found: {project_code}")
                return None

            project_id = project.project_id

            # Load all components in parallel-ish (sequential for simplicity)
            schemas = await self._get_schemas_by_project(project_id)
            flows = await self._get_flows_by_project(project_id)
            patterns = await self._get_patterns_by_project(project_id)
            relations = await self._get_relations_by_project(project_id)
            decisions = await self._get_decisions_by_project(project_id)

            context = ProjectContext(
                project=project,
                schemas=schemas,
                flows=flows,
                patterns=patterns,
                relations=relations,
                decisions=decisions
            )

            # Update last_worked_at
            await self._update_last_worked(project_id)

            logger.info(f"💜 Recalled project context: {project_code}")
            logger.info(f"   Schemas: {len(schemas)}, Flows: {len(flows)}, "
                       f"Patterns: {len(patterns)}, Relations: {len(relations)}, "
                       f"Decisions: {len(decisions)}")

            return context

        except Exception as e:
            logger.error(f"❌ Failed to recall project context: {e}")
            return None

    # ========================================================================
    # PROJECT CRUD
    # ========================================================================

    async def get_project(self, project_code: str) -> Optional[Project]:
        """Get project by code."""
        await self._ensure_connected()

        row = await self.db.fetchrow(
            "SELECT * FROM projects WHERE project_code = $1",
            project_code
        )

        if row:
            return self._row_to_project(row)
        return None

    async def get_all_projects(self, active_only: bool = True) -> List[Project]:
        """Get all projects."""
        await self._ensure_connected()

        if active_only:
            rows = await self.db.fetch(
                "SELECT * FROM projects WHERE is_active = true ORDER BY last_worked_at DESC"
            )
        else:
            rows = await self.db.fetch(
                "SELECT * FROM projects ORDER BY last_worked_at DESC"
            )

        return [self._row_to_project(row) for row in rows]

    async def create_project(
        self,
        project_name: str,
        project_code: str,
        description: str = None,
        tech_stack: Dict[str, str] = None,
        repository_url: str = None
    ) -> Optional[Project]:
        """Create a new project."""
        await self._ensure_connected()

        project_id = uuid4()
        tech_stack_json = json.dumps(tech_stack or {})

        try:
            await self.db.execute(
                """
                INSERT INTO projects (project_id, project_name, project_code, description,
                                     tech_stack, repository_url, is_active, last_worked_at, created_at)
                VALUES ($1, $2, $3, $4, $5::jsonb, $6, true, NOW(), NOW())
                """,
                str(project_id), project_name, project_code, description,
                tech_stack_json, repository_url
            )

            logger.info(f"✅ Created project: {project_code}")
            return await self.get_project(project_code)

        except Exception as e:
            logger.error(f"❌ Failed to create project: {e}")
            return None

    async def update_project(
        self,
        project_code: str,
        **kwargs
    ) -> Optional[Project]:
        """Update project fields."""
        await self._ensure_connected()

        allowed = ['project_name', 'description', 'tech_stack', 'repository_url', 'is_active']
        updates = []
        values = []
        idx = 1

        for key, value in kwargs.items():
            if key in allowed:
                if key == 'tech_stack':
                    updates.append(f"{key} = ${idx}::jsonb")
                    values.append(json.dumps(value))
                else:
                    updates.append(f"{key} = ${idx}")
                    values.append(value)
                idx += 1

        if not updates:
            return await self.get_project(project_code)

        values.append(project_code)
        query = f"UPDATE projects SET {', '.join(updates)}, updated_at = NOW() WHERE project_code = ${idx}"

        try:
            await self.db.execute(query, *values)
            logger.info(f"✅ Updated project: {project_code}")
            return await self.get_project(project_code)
        except Exception as e:
            logger.error(f"❌ Failed to update project: {e}")
            return None

    # ========================================================================
    # SCHEMA CRUD
    # ========================================================================

    async def get_schema(self, project_code: str, table_name: str) -> Optional[ProjectSchema]:
        """Get schema by project and table name."""
        await self._ensure_connected()

        row = await self.db.fetchrow(
            """
            SELECT ps.* FROM project_schemas ps
            JOIN projects p ON ps.project_id = p.project_id
            WHERE p.project_code = $1 AND ps.table_name = $2
            """,
            project_code, table_name
        )

        if row:
            return self._row_to_schema(row)
        return None

    async def get_schemas(self, project_code: str) -> List[ProjectSchema]:
        """Get all schemas for a project."""
        await self._ensure_connected()

        rows = await self.db.fetch(
            """
            SELECT ps.* FROM project_schemas ps
            JOIN projects p ON ps.project_id = p.project_id
            WHERE p.project_code = $1
            ORDER BY ps.table_name
            """,
            project_code
        )

        return [self._row_to_schema(row) for row in rows]

    async def add_schema(
        self,
        project_code: str,
        table_name: str,
        columns: List[Dict[str, Any]],
        purpose: str,
        schema_type: str = "table",
        primary_key: str = None,
        foreign_keys: List[Dict[str, str]] = None,
        indexes: List[Dict[str, Any]] = None,
        important_queries: str = None,
        gotchas: str = None
    ) -> Optional[ProjectSchema]:
        """Add a schema to a project."""
        await self._ensure_connected()

        project = await self.get_project(project_code)
        if not project:
            logger.error(f"Project not found: {project_code}")
            return None

        schema_id = uuid4()

        try:
            await self.db.execute(
                """
                INSERT INTO project_schemas
                (schema_id, project_id, table_name, schema_type, columns, primary_key,
                 foreign_keys, indexes, purpose, important_queries, gotchas, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7::jsonb, $8::jsonb, $9, $10, $11, NOW(), NOW())
                ON CONFLICT (project_id, table_name) DO UPDATE SET
                    columns = EXCLUDED.columns,
                    purpose = EXCLUDED.purpose,
                    gotchas = EXCLUDED.gotchas,
                    important_queries = EXCLUDED.important_queries,
                    updated_at = NOW()
                """,
                str(schema_id), str(project.project_id), table_name, schema_type,
                json.dumps(columns), primary_key,
                json.dumps(foreign_keys or []), json.dumps(indexes or []),
                purpose, important_queries, gotchas
            )

            logger.info(f"✅ Added schema: {project_code}.{table_name}")
            return await self.get_schema(project_code, table_name)

        except Exception as e:
            logger.error(f"❌ Failed to add schema: {e}")
            return None

    # ========================================================================
    # FLOW CRUD
    # ========================================================================

    async def get_flows(
        self,
        project_code: str,
        flow_type: str = None
    ) -> List[ProjectFlow]:
        """Get flows for a project, optionally filtered by type."""
        await self._ensure_connected()

        if flow_type:
            rows = await self.db.fetch(
                """
                SELECT pf.* FROM project_flows pf
                JOIN projects p ON pf.project_id = p.project_id
                WHERE p.project_code = $1 AND pf.flow_type = $2
                ORDER BY pf.flow_name
                """,
                project_code, flow_type
            )
        else:
            rows = await self.db.fetch(
                """
                SELECT pf.* FROM project_flows pf
                JOIN projects p ON pf.project_id = p.project_id
                WHERE p.project_code = $1
                ORDER BY pf.flow_type, pf.flow_name
                """,
                project_code
            )

        return [self._row_to_flow(row) for row in rows]

    async def add_flow(
        self,
        project_code: str,
        flow_name: str,
        flow_type: str,
        description: str,
        steps: List[Dict[str, Any]],
        entry_point: str = None,
        exit_point: str = None,
        diagram_path: str = None,
        critical_notes: str = None
    ) -> Optional[ProjectFlow]:
        """Add a flow to a project."""
        await self._ensure_connected()

        project = await self.get_project(project_code)
        if not project:
            logger.error(f"Project not found: {project_code}")
            return None

        flow_id = uuid4()

        try:
            await self.db.execute(
                """
                INSERT INTO project_flows
                (flow_id, project_id, flow_name, flow_type, description, steps,
                 entry_point, exit_point, diagram_path, critical_notes, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8, $9, $10, NOW(), NOW())
                ON CONFLICT (project_id, flow_name) DO UPDATE SET
                    description = EXCLUDED.description,
                    steps = EXCLUDED.steps,
                    critical_notes = EXCLUDED.critical_notes,
                    updated_at = NOW()
                """,
                str(flow_id), str(project.project_id), flow_name, flow_type,
                description, json.dumps(steps), entry_point, exit_point,
                diagram_path, critical_notes
            )

            logger.info(f"✅ Added flow: {project_code}.{flow_name}")

            # Return the flow
            flows = await self.get_flows(project_code)
            return next((f for f in flows if f.flow_name == flow_name), None)

        except Exception as e:
            logger.error(f"❌ Failed to add flow: {e}")
            return None

    # ========================================================================
    # PATTERN CRUD
    # ========================================================================

    async def find_patterns(
        self,
        project_code: str,
        pattern_type: str = None
    ) -> List[ProjectPattern]:
        """Find patterns for a project, optionally filtered by type."""
        await self._ensure_connected()

        if pattern_type:
            rows = await self.db.fetch(
                """
                SELECT pp.* FROM project_patterns pp
                JOIN projects p ON pp.project_id = p.project_id
                WHERE p.project_code = $1 AND pp.pattern_type = $2
                ORDER BY pp.used_count DESC, pp.pattern_name
                """,
                project_code, pattern_type
            )
        else:
            rows = await self.db.fetch(
                """
                SELECT pp.* FROM project_patterns pp
                JOIN projects p ON pp.project_id = p.project_id
                WHERE p.project_code = $1
                ORDER BY pp.used_count DESC, pp.pattern_name
                """,
                project_code
            )

        return [self._row_to_pattern(row) for row in rows]

    async def get_pattern(self, project_code: str, pattern_name: str) -> Optional[ProjectPattern]:
        """Get a specific pattern by name."""
        await self._ensure_connected()

        row = await self.db.fetchrow(
            """
            SELECT pp.* FROM project_patterns pp
            JOIN projects p ON pp.project_id = p.project_id
            WHERE p.project_code = $1 AND pp.pattern_name = $2
            """,
            project_code, pattern_name
        )

        if row:
            return self._row_to_pattern(row)
        return None

    async def add_pattern(
        self,
        project_code: str,
        pattern_name: str,
        pattern_type: str,
        description: str,
        code_snippet: str = None,
        file_path: str = None,
        usage_example: str = None,
        parameters: List[Dict[str, Any]] = None,
        returns: str = None,
        depends_on: List[str] = None
    ) -> Optional[ProjectPattern]:
        """Add a reusable pattern to a project."""
        await self._ensure_connected()

        project = await self.get_project(project_code)
        if not project:
            logger.error(f"Project not found: {project_code}")
            return None

        pattern_id = uuid4()

        try:
            await self.db.execute(
                """
                INSERT INTO project_patterns
                (pattern_id, project_id, pattern_name, pattern_type, description,
                 code_snippet, file_path, usage_example, parameters, returns,
                 depends_on, used_count, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10, $11, 0, NOW(), NOW())
                ON CONFLICT (project_id, pattern_name) DO UPDATE SET
                    description = EXCLUDED.description,
                    code_snippet = EXCLUDED.code_snippet,
                    usage_example = EXCLUDED.usage_example,
                    updated_at = NOW()
                """,
                str(pattern_id), str(project.project_id), pattern_name, pattern_type,
                description, code_snippet, file_path, usage_example,
                json.dumps(parameters or []), returns, depends_on or []
            )

            logger.info(f"✅ Added pattern: {project_code}.{pattern_name}")
            return await self.get_pattern(project_code, pattern_name)

        except Exception as e:
            logger.error(f"❌ Failed to add pattern: {e}")
            return None

    async def increment_pattern_usage(self, project_code: str, pattern_name: str) -> bool:
        """Track when a pattern is used."""
        await self._ensure_connected()

        try:
            await self.db.execute(
                """
                UPDATE project_patterns pp
                SET used_count = used_count + 1, updated_at = NOW()
                FROM projects p
                WHERE pp.project_id = p.project_id
                AND p.project_code = $1 AND pp.pattern_name = $2
                """,
                project_code, pattern_name
            )
            return True
        except Exception as e:
            logger.error(f"❌ Failed to increment pattern usage: {e}")
            return False

    # ========================================================================
    # RELATION CRUD
    # ========================================================================

    async def get_relations(self, project_code: str) -> List[ProjectEntityRelation]:
        """Get all entity relations for a project."""
        await self._ensure_connected()

        rows = await self.db.fetch(
            """
            SELECT er.* FROM project_entity_relations er
            JOIN projects p ON er.project_id = p.project_id
            WHERE p.project_code = $1
            ORDER BY er.from_table, er.to_table
            """,
            project_code
        )

        return [self._row_to_relation(row) for row in rows]

    async def get_relations_for_table(
        self,
        project_code: str,
        table_name: str
    ) -> List[ProjectEntityRelation]:
        """Get all relations involving a specific table."""
        await self._ensure_connected()

        rows = await self.db.fetch(
            """
            SELECT er.* FROM project_entity_relations er
            JOIN projects p ON er.project_id = p.project_id
            WHERE p.project_code = $1
            AND (er.from_table = $2 OR er.to_table = $2)
            ORDER BY er.from_table, er.to_table
            """,
            project_code, table_name
        )

        return [self._row_to_relation(row) for row in rows]

    async def add_relation(
        self,
        project_code: str,
        from_table: str,
        to_table: str,
        relation_type: str,
        join_condition: str,
        relation_name: str = None,
        is_required: bool = True,
        cascade_behavior: str = None,
        notes: str = None
    ) -> Optional[ProjectEntityRelation]:
        """Add an entity relation with JOIN condition."""
        await self._ensure_connected()

        project = await self.get_project(project_code)
        if not project:
            logger.error(f"Project not found: {project_code}")
            return None

        relation_id = uuid4()

        try:
            await self.db.execute(
                """
                INSERT INTO project_entity_relations
                (relation_id, project_id, from_table, to_table, relation_type,
                 relation_name, join_condition, is_required, cascade_behavior, notes, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW())
                ON CONFLICT (project_id, from_table, to_table, relation_type) DO UPDATE SET
                    join_condition = EXCLUDED.join_condition,
                    notes = EXCLUDED.notes
                """,
                str(relation_id), str(project.project_id), from_table, to_table,
                relation_type, relation_name, join_condition, is_required,
                cascade_behavior, notes
            )

            logger.info(f"✅ Added relation: {project_code}.{from_table} -> {to_table}")

            relations = await self.get_relations(project_code)
            return next((r for r in relations
                        if r.from_table == from_table and r.to_table == to_table), None)

        except Exception as e:
            logger.error(f"❌ Failed to add relation: {e}")
            return None

    # ========================================================================
    # DECISION CRUD
    # ========================================================================

    async def get_decisions(
        self,
        project_code: str,
        category: str = None,
        active_only: bool = True
    ) -> List[ProjectTechnicalDecision]:
        """Get technical decisions for a project."""
        await self._ensure_connected()

        if category and active_only:
            rows = await self.db.fetch(
                """
                SELECT td.* FROM project_technical_decisions td
                JOIN projects p ON td.project_id = p.project_id
                WHERE p.project_code = $1 AND td.category = $2 AND td.status = 'active'
                ORDER BY td.decided_at DESC
                """,
                project_code, category
            )
        elif category:
            rows = await self.db.fetch(
                """
                SELECT td.* FROM project_technical_decisions td
                JOIN projects p ON td.project_id = p.project_id
                WHERE p.project_code = $1 AND td.category = $2
                ORDER BY td.decided_at DESC
                """,
                project_code, category
            )
        elif active_only:
            rows = await self.db.fetch(
                """
                SELECT td.* FROM project_technical_decisions td
                JOIN projects p ON td.project_id = p.project_id
                WHERE p.project_code = $1 AND td.status = 'active'
                ORDER BY td.decided_at DESC
                """,
                project_code
            )
        else:
            rows = await self.db.fetch(
                """
                SELECT td.* FROM project_technical_decisions td
                JOIN projects p ON td.project_id = p.project_id
                WHERE p.project_code = $1
                ORDER BY td.decided_at DESC
                """,
                project_code
            )

        return [self._row_to_decision(row) for row in rows]

    async def add_decision(
        self,
        project_code: str,
        decision_title: str,
        category: str,
        context: str,
        decision_made: str,
        reasoning: str,
        options_considered: List[Dict[str, Any]] = None,
        consequences: str = None,
        decided_by: str = "David"
    ) -> Optional[ProjectTechnicalDecision]:
        """Add a technical decision (ADR)."""
        await self._ensure_connected()

        project = await self.get_project(project_code)
        if not project:
            logger.error(f"Project not found: {project_code}")
            return None

        decision_id = uuid4()

        try:
            await self.db.execute(
                """
                INSERT INTO project_technical_decisions
                (decision_id, project_id, decision_title, category, context,
                 options_considered, decision_made, reasoning, consequences,
                 decided_at, decided_by, status, created_at)
                VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8, $9, NOW(), $10, 'active', NOW())
                """,
                str(decision_id), str(project.project_id), decision_title, category,
                context, json.dumps(options_considered or []), decision_made,
                reasoning, consequences, decided_by
            )

            logger.info(f"✅ Added decision: {project_code}.{decision_title}")

            decisions = await self.get_decisions(project_code)
            return next((d for d in decisions if d.decision_title == decision_title), None)

        except Exception as e:
            logger.error(f"❌ Failed to add decision: {e}")
            return None

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    async def _get_schemas_by_project(self, project_id: UUID) -> List[ProjectSchema]:
        """Get all schemas for a project ID."""
        rows = await self.db.fetch(
            "SELECT * FROM project_schemas WHERE project_id = $1 ORDER BY table_name",
            str(project_id)
        )
        return [self._row_to_schema(row) for row in rows]

    async def _get_flows_by_project(self, project_id: UUID) -> List[ProjectFlow]:
        """Get all flows for a project ID."""
        rows = await self.db.fetch(
            "SELECT * FROM project_flows WHERE project_id = $1 ORDER BY flow_type, flow_name",
            str(project_id)
        )
        return [self._row_to_flow(row) for row in rows]

    async def _get_patterns_by_project(self, project_id: UUID) -> List[ProjectPattern]:
        """Get all patterns for a project ID."""
        rows = await self.db.fetch(
            "SELECT * FROM project_patterns WHERE project_id = $1 ORDER BY used_count DESC",
            str(project_id)
        )
        return [self._row_to_pattern(row) for row in rows]

    async def _get_relations_by_project(self, project_id: UUID) -> List[ProjectEntityRelation]:
        """Get all relations for a project ID."""
        rows = await self.db.fetch(
            "SELECT * FROM project_entity_relations WHERE project_id = $1 ORDER BY from_table",
            str(project_id)
        )
        return [self._row_to_relation(row) for row in rows]

    async def _get_decisions_by_project(self, project_id: UUID) -> List[ProjectTechnicalDecision]:
        """Get all active decisions for a project ID."""
        rows = await self.db.fetch(
            """SELECT * FROM project_technical_decisions
               WHERE project_id = $1 AND status = 'active'
               ORDER BY decided_at DESC""",
            str(project_id)
        )
        return [self._row_to_decision(row) for row in rows]

    async def _update_last_worked(self, project_id: UUID):
        """Update project's last_worked_at timestamp."""
        await self.db.execute(
            "UPDATE projects SET last_worked_at = NOW() WHERE project_id = $1",
            str(project_id)
        )

    # ========================================================================
    # ROW TO ENTITY MAPPERS
    # ========================================================================

    def _row_to_project(self, row: dict) -> Project:
        """Convert database row to Project entity."""
        tech_stack = row.get('tech_stack') or {}
        if isinstance(tech_stack, str):
            tech_stack = json.loads(tech_stack)

        return Project(
            project_id=UUID(str(row['project_id'])),
            project_name=row['project_name'],
            project_code=row['project_code'],
            description=row.get('description'),
            tech_stack=tech_stack,
            repository_url=row.get('repository_url'),
            is_active=row.get('is_active', True),
            last_worked_at=row.get('last_worked_at'),
            created_at=row.get('created_at')
        )

    def _row_to_schema(self, row: dict) -> ProjectSchema:
        """Convert database row to ProjectSchema entity."""
        columns = row.get('columns') or []
        if isinstance(columns, str):
            columns = json.loads(columns)

        foreign_keys = row.get('foreign_keys') or []
        if isinstance(foreign_keys, str):
            foreign_keys = json.loads(foreign_keys)

        indexes = row.get('indexes') or []
        if isinstance(indexes, str):
            indexes = json.loads(indexes)

        return ProjectSchema(
            schema_id=UUID(str(row['schema_id'])),
            project_id=UUID(str(row['project_id'])),
            table_name=row['table_name'],
            schema_type=row.get('schema_type', 'table'),
            columns=columns,
            primary_key=row.get('primary_key'),
            foreign_keys=foreign_keys,
            indexes=indexes,
            purpose=row.get('purpose', ''),
            important_queries=row.get('important_queries'),
            gotchas=row.get('gotchas'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at')
        )

    def _row_to_flow(self, row: dict) -> ProjectFlow:
        """Convert database row to ProjectFlow entity."""
        steps = row.get('steps') or []
        if isinstance(steps, str):
            steps = json.loads(steps)

        return ProjectFlow(
            flow_id=UUID(str(row['flow_id'])),
            project_id=UUID(str(row['project_id'])),
            flow_name=row['flow_name'],
            flow_type=row['flow_type'],
            description=row['description'],
            steps=steps,
            entry_point=row.get('entry_point'),
            exit_point=row.get('exit_point'),
            diagram_path=row.get('diagram_path'),
            critical_notes=row.get('critical_notes'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at')
        )

    def _row_to_pattern(self, row: dict) -> ProjectPattern:
        """Convert database row to ProjectPattern entity."""
        parameters = row.get('parameters') or []
        if isinstance(parameters, str):
            parameters = json.loads(parameters)

        depends_on = row.get('depends_on') or []
        if isinstance(depends_on, str):
            depends_on = json.loads(depends_on)

        return ProjectPattern(
            pattern_id=UUID(str(row['pattern_id'])),
            project_id=UUID(str(row['project_id'])),
            pattern_name=row['pattern_name'],
            pattern_type=row['pattern_type'],
            description=row['description'],
            code_snippet=row.get('code_snippet'),
            file_path=row.get('file_path'),
            usage_example=row.get('usage_example'),
            parameters=parameters,
            returns=row.get('returns'),
            depends_on=depends_on,
            used_count=row.get('used_count', 0),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at')
        )

    def _row_to_relation(self, row: dict) -> ProjectEntityRelation:
        """Convert database row to ProjectEntityRelation entity."""
        return ProjectEntityRelation(
            relation_id=UUID(str(row['relation_id'])),
            project_id=UUID(str(row['project_id'])),
            from_table=row['from_table'],
            to_table=row['to_table'],
            relation_type=row['relation_type'],
            relation_name=row.get('relation_name'),
            join_condition=row.get('join_condition', ''),
            is_required=row.get('is_required', True),
            cascade_behavior=row.get('cascade_behavior'),
            notes=row.get('notes'),
            created_at=row.get('created_at')
        )

    def _row_to_decision(self, row: dict) -> ProjectTechnicalDecision:
        """Convert database row to ProjectTechnicalDecision entity."""
        options = row.get('options_considered') or []
        if isinstance(options, str):
            options = json.loads(options)

        superseded_by = row.get('superseded_by')
        if superseded_by:
            superseded_by = UUID(str(superseded_by))

        return ProjectTechnicalDecision(
            decision_id=UUID(str(row['decision_id'])),
            project_id=UUID(str(row['project_id'])),
            decision_title=row['decision_title'],
            category=row['category'],
            context=row['context'],
            options_considered=options,
            decision_made=row.get('decision_made', ''),
            reasoning=row.get('reasoning', ''),
            consequences=row.get('consequences'),
            decided_at=row.get('decided_at'),
            decided_by=row.get('decided_by', 'David'),
            status=row.get('status', 'active'),
            superseded_by=superseded_by,
            created_at=row.get('created_at')
        )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def recall_project(project_code: str) -> Optional[ProjectContext]:
    """
    Quick function to recall project context.

    Usage:
        from angela_core.services.project_memory_service import recall_project
        context = await recall_project("WTU")
    """
    service = ProjectMemoryService()
    try:
        return await service.recall_project_context(project_code)
    finally:
        await service.disconnect()


async def list_projects() -> List[Project]:
    """
    Quick function to list all active projects.

    Usage:
        from angela_core.services.project_memory_service import list_projects
        projects = await list_projects()
    """
    service = ProjectMemoryService()
    try:
        return await service.get_all_projects()
    finally:
        await service.disconnect()
