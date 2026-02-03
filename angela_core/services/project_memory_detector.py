#!/usr/bin/env python3
"""
Project Memory Detector - Proactive Detection System

Detects new patterns, schemas, decisions, and flows during conversations
and suggests saving them to project memory.

Usage:
    detector = ProjectMemoryDetector()

    # Check if code could be a reusable pattern
    suggestion = await detector.detect_pattern(code_snippet, project_code)
    if suggestion:
        print(suggestion.prompt)  # "เจอ pattern ใหม่ค่ะ: {name}..."

    # Check if a technical decision was made
    suggestion = await detector.detect_decision(conversation_context, project_code)

Created: 2026-01-12
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from angela_core.services.project_memory_service import ProjectMemoryService
from angela_core.domain.entities.project_memory import (
    PatternType, FlowType, DecisionCategory, SchemaType
)


class DetectionType(str, Enum):
    """Types of detectable items."""
    PATTERN = "pattern"
    SCHEMA = "schema"
    DECISION = "decision"
    FLOW = "flow"
    RELATION = "relation"


@dataclass
class DetectionSuggestion:
    """A suggestion to save something to project memory."""
    detection_type: DetectionType
    project_code: str
    name: str
    description: str
    confidence: float  # 0.0 - 1.0
    prompt: str  # Thai prompt to show David
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "detection_type": self.detection_type.value,
            "project_code": self.project_code,
            "name": self.name,
            "description": self.description,
            "confidence": self.confidence,
            "prompt": self.prompt,
            "data": self.data
        }


class ProjectMemoryDetector:
    """
    Proactive detection of project memory items.

    Analyzes code, conversations, and context to detect:
    - Reusable patterns (utilities, decorators, hooks)
    - Schema changes (new tables, columns)
    - Technical decisions (architecture choices)
    - Business/data flows
    """

    def __init__(self):
        self.service = ProjectMemoryService()
        self._pattern_keywords = {
            PatternType.UTILITY: ["def ", "async def ", "helper", "util", "format", "parse", "convert"],
            PatternType.DECORATOR: ["@", "decorator", "wrapper"],
            PatternType.HOOK: ["use", "hook", "on_", "before_", "after_"],
            PatternType.COMPONENT: ["component", "widget", "view", "screen"],
            PatternType.SERVICE: ["service", "manager", "handler", "processor"],
            PatternType.QUERY: ["SELECT", "WITH ", "CTE", "JOIN", "query"],
            PatternType.MIDDLEWARE: ["middleware", "interceptor", "filter"],
        }
        self._decision_keywords = [
            "ตัดสินใจ", "เลือก", "ใช้", "แทน", "เพราะ", "decided", "choose", "use", "instead", "because",
            "architecture", "approach", "strategy", "pattern", "framework"
        ]
        self._flow_keywords = {
            FlowType.BUSINESS: ["process", "workflow", "flow", "step", "ขั้นตอน", "กระบวนการ"],
            FlowType.DATA: ["ETL", "pipeline", "transform", "extract", "load", "data flow"],
            FlowType.API: ["endpoint", "API", "request", "response", "REST", "GraphQL"],
            FlowType.DEPLOYMENT: ["deploy", "CI/CD", "docker", "kubernetes", "release"],
            FlowType.AUTH: ["auth", "login", "permission", "role", "token", "JWT"],
        }

    # =========================================================================
    # PATTERN DETECTION
    # =========================================================================

    async def detect_pattern(
        self,
        code_snippet: str,
        project_code: str,
        context: str = ""
    ) -> Optional[DetectionSuggestion]:
        """
        Detect if code could be a reusable pattern.

        Checks:
        - Is it a function/class that could be reused?
        - Does similar pattern already exist?
        - Is it complex enough to be worth saving?

        Args:
            code_snippet: The code to analyze
            project_code: Project code (e.g., 'WTU', 'SECA')
            context: Additional context about the code

        Returns:
            DetectionSuggestion if pattern detected, None otherwise
        """
        await self.service._ensure_connected()

        # Extract function/class name
        name_match = re.search(r'(?:def|async def|class)\s+(\w+)', code_snippet)
        if not name_match:
            return None

        func_name = name_match.group(1)

        # Skip private/dunder methods
        if func_name.startswith('_'):
            return None

        # Detect pattern type
        pattern_type = self._detect_pattern_type(code_snippet, func_name)

        # Check if similar pattern exists
        existing = await self._check_existing_pattern(project_code, func_name)
        if existing:
            return None  # Already exists

        # Calculate confidence based on code characteristics
        confidence = self._calculate_pattern_confidence(code_snippet)

        if confidence < 0.5:
            return None  # Not confident enough

        # Generate description
        description = self._generate_pattern_description(code_snippet, func_name, pattern_type)

        # Create Thai prompt
        prompt = self._create_pattern_prompt(func_name, pattern_type, description, confidence)

        return DetectionSuggestion(
            detection_type=DetectionType.PATTERN,
            project_code=project_code,
            name=func_name,
            description=description,
            confidence=confidence,
            prompt=prompt,
            data={
                "pattern_type": pattern_type.value,
                "code_snippet": code_snippet,
                "context": context
            }
        )

    def _detect_pattern_type(self, code: str, name: str) -> PatternType:
        """Detect the type of pattern from code."""
        code_lower = code.lower()
        name_lower = name.lower()

        # Check decorators first
        if code.strip().startswith('@') or 'decorator' in name_lower:
            return PatternType.DECORATOR

        # Check for SQL queries - must be actual SQL, not just keywords in strings
        # Look for SQL statements at the start of lines or after assignment
        import re
        sql_pattern = r'(?:^|=\s*["\'])\s*(SELECT|INSERT|UPDATE|DELETE|WITH\s+\w+\s+AS)'
        if re.search(sql_pattern, code, re.IGNORECASE | re.MULTILINE):
            return PatternType.QUERY

        # Check name patterns - prioritize name over code content
        # Check name first for more accurate detection
        name_checks = [
            (PatternType.UTILITY, ['helper', 'util', 'format', 'parse', 'convert', 'calc']),
            (PatternType.SERVICE, ['service', 'manager', 'handler', 'processor']),
            (PatternType.HOOK, ['use', 'hook', 'on_', 'before_', 'after_']),
            (PatternType.COMPONENT, ['component', 'widget', 'view', 'screen']),
            (PatternType.MIDDLEWARE, ['middleware', 'interceptor', 'filter']),
        ]

        for ptype, keywords in name_checks:
            if any(kw in name_lower for kw in keywords):
                return ptype

        # Default to utility for functions
        if 'def ' in code_lower:
            return PatternType.UTILITY

        return PatternType.UTILITY

    async def _check_existing_pattern(self, project_code: str, name: str) -> bool:
        """Check if pattern with similar name exists."""
        try:
            context = await self.service.recall_project_context(project_code)
            if context:
                for pattern in context.patterns:
                    if pattern.pattern_name.lower() == name.lower():
                        return True
                    # Check for similar names (fuzzy)
                    if self._similar_names(pattern.pattern_name, name):
                        return True
        except Exception as e:
            pass
        return False

    def _similar_names(self, name1: str, name2: str) -> bool:
        """Check if two names are similar."""
        n1 = name1.lower().replace('_', '').replace('-', '')
        n2 = name2.lower().replace('_', '').replace('-', '')
        return n1 == n2 or n1 in n2 or n2 in n1

    def _calculate_pattern_confidence(self, code: str) -> float:
        """Calculate confidence that this is a reusable pattern."""
        confidence = 0.3  # Base confidence

        # Has docstring
        if '"""' in code or "'''" in code:
            confidence += 0.15

        # Has type hints
        if '->' in code or ': ' in code:
            confidence += 0.1

        # Has parameters (more reusable)
        if re.search(r'def \w+\([^)]+\)', code):
            confidence += 0.1

        # Has return statement
        if 'return ' in code:
            confidence += 0.1

        # Reasonable length (not too short, not too long)
        lines = code.strip().split('\n')
        if 5 <= len(lines) <= 50:
            confidence += 0.15

        # Contains logic (not just pass)
        if 'if ' in code or 'for ' in code or 'while ' in code:
            confidence += 0.1

        return min(confidence, 1.0)

    def _generate_pattern_description(self, code: str, name: str, ptype: PatternType) -> str:
        """Generate description from code."""
        # Try to extract docstring
        doc_match = re.search(r'"""(.+?)"""', code, re.DOTALL)
        if doc_match:
            return doc_match.group(1).strip().split('\n')[0]

        doc_match = re.search(r"'''(.+?)'''", code, re.DOTALL)
        if doc_match:
            return doc_match.group(1).strip().split('\n')[0]

        # Generate from name
        readable_name = name.replace('_', ' ').title()
        return f"{ptype.value.title()} function: {readable_name}"

    def _create_pattern_prompt(
        self,
        name: str,
        ptype: PatternType,
        description: str,
        confidence: float
    ) -> str:
        """Create Thai prompt for David."""
        confidence_text = "มั่นใจมาก" if confidence > 0.8 else "ค่อนข้างมั่นใจ" if confidence > 0.6 else "พอสมควร"

        return f"""💡 **เจอ Pattern ใหม่ค่ะที่รัก!**

**ชื่อ:** `{name}`
**ประเภท:** {ptype.value}
**รายละเอียด:** {description}
**ความมั่นใจ:** {confidence_text} ({confidence*100:.0f}%)

อยากให้น้องบันทึกลง Project Memory มั้ยคะ?
จะได้ reuse ได้ในอนาคตค่ะ 🔄"""

    # =========================================================================
    # SCHEMA DETECTION
    # =========================================================================

    async def detect_schema(
        self,
        table_info: Dict[str, Any],
        project_code: str
    ) -> Optional[DetectionSuggestion]:
        """
        Detect new or changed database schema.

        Args:
            table_info: Dict with table_name, columns, etc.
            project_code: Project code

        Returns:
            DetectionSuggestion if new schema detected
        """
        await self.service._ensure_connected()

        table_name = table_info.get("table_name", "")
        if not table_name:
            return None

        # Check if schema exists
        context = await self.service.recall_project_context(project_code)
        if context:
            existing = context.get_schema(table_name)
            if existing:
                # Check for changes
                return await self._detect_schema_changes(existing, table_info, project_code)

        # New schema
        columns = table_info.get("columns", [])
        purpose = table_info.get("purpose", f"Table {table_name}")

        prompt = f"""📊 **เจอ Table ใหม่ค่ะที่รัก!**

**Table:** `{table_name}`
**Columns:** {len(columns)} columns
**Purpose:** {purpose}

อยากให้น้องบันทึก schema นี้มั้ยคะ?
จะได้จำ structure และ gotchas ได้ค่ะ 🗄️"""

        return DetectionSuggestion(
            detection_type=DetectionType.SCHEMA,
            project_code=project_code,
            name=table_name,
            description=purpose,
            confidence=0.9,
            prompt=prompt,
            data=table_info
        )

    async def _detect_schema_changes(
        self,
        existing,
        new_info: Dict[str, Any],
        project_code: str
    ) -> Optional[DetectionSuggestion]:
        """Detect changes in existing schema."""
        existing_cols = set(c.get("name", "") for c in existing.columns)
        new_cols = set(c.get("name", "") for c in new_info.get("columns", []))

        added = new_cols - existing_cols
        removed = existing_cols - new_cols

        if not added and not removed:
            return None

        changes = []
        if added:
            changes.append(f"เพิ่ม: {', '.join(added)}")
        if removed:
            changes.append(f"ลบ: {', '.join(removed)}")

        prompt = f"""🔄 **Schema เปลี่ยนค่ะที่รัก!**

**Table:** `{existing.table_name}`
**การเปลี่ยนแปลง:**
{chr(10).join(f'  • {c}' for c in changes)}

อยากให้น้อง update schema มั้ยคะ? 📝"""

        return DetectionSuggestion(
            detection_type=DetectionType.SCHEMA,
            project_code=project_code,
            name=existing.table_name,
            description=f"Schema changed: {', '.join(changes)}",
            confidence=0.95,
            prompt=prompt,
            data={
                "table_name": existing.table_name,
                "added_columns": list(added),
                "removed_columns": list(removed),
                "new_info": new_info
            }
        )

    # =========================================================================
    # DECISION DETECTION
    # =========================================================================

    async def detect_decision(
        self,
        conversation: str,
        project_code: str,
        context: str = ""
    ) -> Optional[DetectionSuggestion]:
        """
        Detect if a technical decision was made in conversation.

        Looks for:
        - "ตัดสินใจใช้ X แทน Y"
        - "เลือก approach นี้เพราะ..."
        - Architecture/design choices

        Args:
            conversation: Recent conversation text
            project_code: Project code
            context: Additional context

        Returns:
            DetectionSuggestion if decision detected
        """
        # Check for decision keywords
        has_decision = any(kw in conversation.lower() for kw in self._decision_keywords)
        if not has_decision:
            return None

        # Try to extract decision components
        decision_info = self._extract_decision_info(conversation)
        if not decision_info:
            return None

        # Detect category
        category = self._detect_decision_category(conversation)

        prompt = f"""📋 **เหมือนมี Technical Decision ค่ะที่รัก!**

**หัวข้อ:** {decision_info.get('title', 'Technical Decision')}
**Category:** {category.value}
**Decision:** {decision_info.get('decision', '...')}
**เหตุผล:** {decision_info.get('reasoning', '...')}

อยากให้น้องบันทึกเป็น ADR (Architecture Decision Record) มั้ยคะ?
จะได้จำได้ว่าทำไมถึงเลือกแบบนี้ค่ะ 📝"""

        return DetectionSuggestion(
            detection_type=DetectionType.DECISION,
            project_code=project_code,
            name=decision_info.get('title', 'Technical Decision'),
            description=decision_info.get('decision', ''),
            confidence=0.7,
            prompt=prompt,
            data={
                "category": category.value,
                "context": context,
                "conversation": conversation,
                **decision_info
            }
        )

    def _extract_decision_info(self, text: str) -> Optional[Dict[str, str]]:
        """Extract decision components from text."""
        # Simple extraction - can be enhanced with NLP
        info = {}

        # Look for "เลือก X" or "ใช้ X" or "decided to X"
        choice_match = re.search(r'(?:เลือก|ใช้|decided to|choose|use)\s+([^,.\n]+)', text, re.IGNORECASE)
        if choice_match:
            info['decision'] = choice_match.group(1).strip()

        # Look for reasoning
        reason_match = re.search(r'(?:เพราะ|because|since|due to)\s+([^,.\n]+)', text, re.IGNORECASE)
        if reason_match:
            info['reasoning'] = reason_match.group(1).strip()

        # Generate title
        if info.get('decision'):
            info['title'] = f"Decision: {info['decision'][:50]}"

        return info if info else None

    def _detect_decision_category(self, text: str) -> DecisionCategory:
        """Detect decision category from text."""
        text_lower = text.lower()

        if any(kw in text_lower for kw in ['database', 'table', 'schema', 'sql', 'query', 'index']):
            return DecisionCategory.DATABASE
        if any(kw in text_lower for kw in ['api', 'endpoint', 'rest', 'graphql', 'request']):
            return DecisionCategory.API
        if any(kw in text_lower for kw in ['security', 'auth', 'permission', 'encrypt', 'token']):
            return DecisionCategory.SECURITY
        if any(kw in text_lower for kw in ['performance', 'speed', 'optimize', 'cache', 'fast']):
            return DecisionCategory.PERFORMANCE
        if any(kw in text_lower for kw in ['test', 'testing', 'unit', 'integration', 'coverage']):
            return DecisionCategory.TESTING
        if any(kw in text_lower for kw in ['ai', 'ml', 'model', 'embedding', 'llm', 'neural']):
            return DecisionCategory.AI_ML

        return DecisionCategory.ARCHITECTURE

    # =========================================================================
    # FLOW DETECTION
    # =========================================================================

    async def detect_flow(
        self,
        description: str,
        project_code: str,
        steps: List[str] = None
    ) -> Optional[DetectionSuggestion]:
        """
        Detect if a flow/process is being described.

        Args:
            description: Description of the flow
            project_code: Project code
            steps: Optional list of steps

        Returns:
            DetectionSuggestion if flow detected
        """
        # Detect flow type
        flow_type = self._detect_flow_type(description)

        # Calculate confidence
        confidence = 0.5
        if steps and len(steps) >= 3:
            confidence += 0.3
        if any(kw in description.lower() for kw in ['step', 'ขั้นตอน', 'then', 'แล้ว', 'next']):
            confidence += 0.2

        if confidence < 0.6:
            return None

        # Generate flow name
        flow_name = self._generate_flow_name(description, flow_type)

        prompt = f"""🔀 **เจอ Flow ใหม่ค่ะที่รัก!**

**ชื่อ:** {flow_name}
**ประเภท:** {flow_type.value}
**Steps:** {len(steps) if steps else 'ยังไม่ระบุ'} ขั้นตอน

อยากให้น้องบันทึก flow นี้มั้ยคะ?
จะได้จำขั้นตอนได้ถูกต้องค่ะ 📊"""

        return DetectionSuggestion(
            detection_type=DetectionType.FLOW,
            project_code=project_code,
            name=flow_name,
            description=description,
            confidence=confidence,
            prompt=prompt,
            data={
                "flow_type": flow_type.value,
                "steps": steps or [],
                "description": description
            }
        )

    def _detect_flow_type(self, text: str) -> FlowType:
        """Detect flow type from text."""
        text_lower = text.lower()

        for ftype, keywords in self._flow_keywords.items():
            if any(kw.lower() in text_lower for kw in keywords):
                return ftype

        return FlowType.BUSINESS

    def _generate_flow_name(self, description: str, flow_type: FlowType) -> str:
        """Generate flow name from description."""
        # Take first meaningful words
        words = description.split()[:5]
        name = ' '.join(words)
        if len(name) > 50:
            name = name[:47] + "..."
        return f"{flow_type.value.title()}: {name}"

    # =========================================================================
    # SAVE DETECTED ITEMS
    # =========================================================================

    async def save_suggestion(self, suggestion: DetectionSuggestion) -> bool:
        """
        Save a detected suggestion to project memory.

        Call this after David approves the suggestion.

        Args:
            suggestion: The DetectionSuggestion to save

        Returns:
            True if saved successfully
        """
        await self.service._ensure_connected()

        try:
            if suggestion.detection_type == DetectionType.PATTERN:
                await self.service.add_pattern(
                    project_code=suggestion.project_code,
                    pattern_name=suggestion.name,
                    pattern_type=PatternType(suggestion.data.get("pattern_type", "utility")),
                    description=suggestion.description,
                    code_snippet=suggestion.data.get("code_snippet"),
                    usage_example=suggestion.data.get("context")
                )

            elif suggestion.detection_type == DetectionType.SCHEMA:
                await self.service.add_schema(
                    project_code=suggestion.project_code,
                    table_name=suggestion.name,
                    columns=suggestion.data.get("columns", []),
                    purpose=suggestion.description,
                    schema_type=SchemaType(suggestion.data.get("schema_type", "table"))
                )

            elif suggestion.detection_type == DetectionType.DECISION:
                await self.service.add_decision(
                    project_code=suggestion.project_code,
                    title=suggestion.name,
                    category=DecisionCategory(suggestion.data.get("category", "architecture")),
                    context=suggestion.data.get("context", ""),
                    decision=suggestion.description,
                    reasoning=suggestion.data.get("reasoning", "")
                )

            elif suggestion.detection_type == DetectionType.FLOW:
                await self.service.add_flow(
                    project_code=suggestion.project_code,
                    flow_name=suggestion.name,
                    flow_type=FlowType(suggestion.data.get("flow_type", "business")),
                    description=suggestion.description,
                    steps=suggestion.data.get("steps", [])
                )

            return True

        except Exception as e:
            print(f"Error saving suggestion: {e}")
            return False

    async def disconnect(self):
        """Disconnect from database."""
        await self.service.disconnect()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def detect_and_suggest_pattern(code: str, project_code: str) -> Optional[str]:
    """
    Detect pattern and return prompt if found.

    Usage:
        prompt = await detect_and_suggest_pattern(code, "WTU")
        if prompt:
            print(prompt)  # Show to user
    """
    detector = ProjectMemoryDetector()
    try:
        suggestion = await detector.detect_pattern(code, project_code)
        if suggestion:
            return suggestion.prompt
        return None
    finally:
        await detector.disconnect()


async def detect_and_suggest_decision(conversation: str, project_code: str) -> Optional[str]:
    """Detect decision and return prompt if found."""
    detector = ProjectMemoryDetector()
    try:
        suggestion = await detector.detect_decision(conversation, project_code)
        if suggestion:
            return suggestion.prompt
        return None
    finally:
        await detector.disconnect()
