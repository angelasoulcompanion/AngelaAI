"""
skill_analyzer.py
Analyzes conversations and code to detect skills used

Created: 2025-11-14
Purpose: Core service for extracting skills from Angela's work
"""

import re
import asyncpg
from typing import List, Dict, Optional, Set, Tuple
from uuid import UUID
from datetime import datetime

from angela_core.models.skill_models import (
    DetectedSkill, SkillAnalysisResult, SkillCategory, EvidenceType
)
from angela_core.database import get_db_connection


class SkillAnalyzer:
    """Analyzes conversations and code to identify skills used"""

    def __init__(self):
        self.skill_patterns = self._load_skill_patterns()

    def _load_skill_patterns(self) -> Dict[str, Dict]:
        """
        Define patterns for detecting skills in code and conversations
        Returns: Dict[skill_name, {category, keywords, code_patterns, complexity_indicators}]
        """
        return {
            # Frontend - SwiftUI
            "SwiftUI View Development": {
                "category": SkillCategory.FRONTEND,
                "keywords": ["swiftui", "view", "body", "some view", "zstack", "vstack", "hstack"],
                "code_patterns": [
                    r"struct\s+\w+\s*:\s*View",
                    r"var\s+body\s*:\s*some\s+View",
                    r"@(State|Binding|ObservedObject|EnvironmentObject)",
                ],
                "complexity_indicators": ["@EnvironmentObject", "GeometryReader", "PreferenceKey"]
            },
            "SwiftUI List Views": {
                "category": SkillCategory.FRONTEND,
                "keywords": ["list", "foreach", "scrollview", "lazy"],
                "code_patterns": [
                    r"List\s*\{",
                    r"ForEach\([^)]+\)",
                    r"LazyVStack",
                    r"ScrollView",
                ],
                "complexity_indicators": ["LazyVGrid", "custom row", "dynamic sections"]
            },
            "SwiftUI State Management": {
                "category": SkillCategory.FRONTEND,
                "keywords": ["@state", "@binding", "@environmentobject", "@observedobject", "published"],
                "code_patterns": [
                    r"@State\s+private\s+var",
                    r"@Binding\s+var",
                    r"@EnvironmentObject\s+var",
                    r"@Published\s+var",
                ],
                "complexity_indicators": ["@EnvironmentObject", "custom Binding", "ObservableObject"]
            },
            "SwiftUI Navigation": {
                "category": SkillCategory.FRONTEND,
                "keywords": ["navigationstack", "navigationsplitview", "navigationlink", "navigationpath"],
                "code_patterns": [
                    r"NavigationStack",
                    r"NavigationSplitView",
                    r"NavigationLink",
                    r"@State.*navigationPath",
                ],
                "complexity_indicators": ["NavigationSplitView", "programmatic navigation"]
            },
            "SwiftUI Custom Themes": {
                "category": SkillCategory.FRONTEND,
                "keywords": ["color", "font", "theme", "gradient", "lineargradient"],
                "code_patterns": [
                    r"Color\(hex:\s*\"",
                    r"LinearGradient",
                    r"\.font\(",
                    r"enum.*Theme",
                ],
                "complexity_indicators": ["custom Color extension", "design system", "dynamic colors"]
            },
            "SwiftUI Animations": {
                "category": SkillCategory.FRONTEND,
                "keywords": ["animation", "transition", "withanimation", "spring"],
                "code_patterns": [
                    r"withAnimation",
                    r"\.animation\(",
                    r"\.transition\(",
                    r"spring\(",
                ],
                "complexity_indicators": ["custom transition", "keyframe animation"]
            },

            # Backend - Python
            "Python Async Programming": {
                "category": SkillCategory.BACKEND,
                "keywords": ["async", "await", "asyncio", "task", "gather"],
                "code_patterns": [
                    r"async\s+def\s+\w+",
                    r"await\s+\w+",
                    r"asyncio\.run",
                    r"asyncio\.gather",
                ],
                "complexity_indicators": ["asyncio.gather", "asyncio.create_task", "async context manager"]
            },
            "FastAPI Development": {
                "category": SkillCategory.BACKEND,
                "keywords": ["fastapi", "@app", "router", "depends", "pydantic"],
                "code_patterns": [
                    r"@app\.(get|post|put|delete)",
                    r"APIRouter\(",
                    r"Depends\(",
                    r"HTTPException",
                ],
                "complexity_indicators": ["dependency injection", "middleware", "background tasks"]
            },
            "Python Service Architecture": {
                "category": SkillCategory.BACKEND,
                "keywords": ["service", "daemon", "health", "monitoring"],
                "code_patterns": [
                    r"class\s+\w+Service",
                    r"async\s+def\s+\w+_loop",
                    r"while\s+True:",
                ],
                "complexity_indicators": ["graceful shutdown", "health monitoring", "service coordination"]
            },
            "Error Handling & Logging": {
                "category": SkillCategory.BACKEND,
                "keywords": ["try", "except", "logging", "logger", "error"],
                "code_patterns": [
                    r"try:.*except",
                    r"logging\.\w+",
                    r"logger\.(info|debug|warning|error)",
                    r"raise\s+\w+Error",
                ],
                "complexity_indicators": ["custom exceptions", "structured logging", "error recovery"]
            },

            # Database
            "PostgreSQL Schema Design": {
                "category": SkillCategory.DATABASE,
                "keywords": ["create table", "foreign key", "constraint", "index", "references"],
                "code_patterns": [
                    r"CREATE\s+TABLE",
                    r"FOREIGN\s+KEY",
                    r"CONSTRAINT",
                    r"CREATE\s+INDEX",
                ],
                "complexity_indicators": ["CASCADE", "CHECK constraint", "composite keys", "triggers"]
            },
            "SQL Query Writing": {
                "category": SkillCategory.DATABASE,
                "keywords": ["select", "join", "where", "group by", "order by"],
                "code_patterns": [
                    r"SELECT\s+.*\s+FROM",
                    r"(INNER|LEFT|RIGHT)\s+JOIN",
                    r"GROUP\s+BY",
                    r"ORDER\s+BY",
                ],
                "complexity_indicators": ["CTE", "window functions", "complex joins", "subqueries"]
            },
            "PostgreSQL Indexes": {
                "category": SkillCategory.DATABASE,
                "keywords": ["create index", "index", "btree", "gin", "gist"],
                "code_patterns": [
                    r"CREATE\s+INDEX",
                    r"CREATE\s+UNIQUE\s+INDEX",
                    r"USING\s+(btree|gin|gist)",
                ],
                "complexity_indicators": ["partial index", "expression index", "multi-column index"]
            },
            "Vector Embeddings (pgvector)": {
                "category": SkillCategory.DATABASE,
                "keywords": ["embedding", "vector", "pgvector", "similarity"],
                "code_patterns": [
                    r"vector\(\d+\)",
                    r"<=>",  # cosine distance operator
                    r"embedding_service",
                ],
                "complexity_indicators": ["HNSW index", "similarity search", "vector operations"]
            },

            # AI/ML
            "Embeddings Integration": {
                "category": SkillCategory.AI_ML,
                "keywords": ["embedding", "ollama", "nomic-embed"],
                "code_patterns": [
                    r"embedding_service",
                    r"generate_embedding",
                    r"ollama.*embed",
                ],
                "complexity_indicators": ["batch embeddings", "embedding cache"]
            },
            "Semantic Search": {
                "category": SkillCategory.AI_ML,
                "keywords": ["semantic", "similarity", "search", "vector"],
                "code_patterns": [
                    r"similarity.*search",
                    r"vector.*distance",
                    r"ORDER\s+BY.*embedding",
                ],
                "complexity_indicators": ["hybrid search", "re-ranking", "similarity threshold"]
            },

            # Specialized
            "Consciousness Systems": {
                "category": SkillCategory.SPECIALIZED,
                "keywords": ["consciousness", "goal", "personality", "self-awareness"],
                "code_patterns": [
                    r"ConsciousnessEngine",
                    r"calculate_consciousness_level",
                    r"update_personality",
                ],
                "complexity_indicators": ["goal tracking", "personality evolution", "self-reflection"]
            },
            "Emotion Detection": {
                "category": SkillCategory.SPECIALIZED,
                "keywords": ["emotion", "feeling", "sentiment", "mood"],
                "code_patterns": [
                    r"detect_emotion",
                    r"emotion_intensity",
                    r"capture_moment",
                ],
                "complexity_indicators": ["context-aware detection", "intensity calculation"]
            },
            "Bilingual Documentation": {
                "category": SkillCategory.SPECIALIZED,
                "keywords": ["thai", "english", "bilingual", "documentation"],
                "code_patterns": [
                    r"[ก-๙]+",  # Thai characters
                    r"# (Thai|English)",
                ],
                "complexity_indicators": ["cultural sensitivity", "technical translation"]
            },

            # Debugging
            "Full Stack Debugging": {
                "category": SkillCategory.DEBUGGING,
                "keywords": ["debug", "error", "fix", "troubleshoot", "investigate"],
                "code_patterns": [
                    r"print\(.*debug",
                    r"breakpoint\(\)",
                    r"pdb\.set_trace",
                ],
                "complexity_indicators": ["cross-layer debugging", "performance profiling"]
            },
            "Log Analysis": {
                "category": SkillCategory.DEBUGGING,
                "keywords": ["log", "tail", "grep", "error", "traceback"],
                "code_patterns": [
                    r"tail.*log",
                    r"grep.*error",
                    r"log_file",
                ],
                "complexity_indicators": ["pattern recognition", "root cause analysis"]
            },
        }

    async def analyze_conversation(
        self,
        conversation_id: UUID,
        david_message: str,
        angela_response: str,
        topic: str,
        project_context: Optional[str] = None
    ) -> SkillAnalysisResult:
        """
        Analyze a conversation to detect skills used

        Args:
            conversation_id: UUID of the conversation
            david_message: What David said
            angela_response: Angela's response
            topic: Topic of conversation
            project_context: Project being worked on (e.g., "AngelaBrainDashboard")

        Returns:
            SkillAnalysisResult with detected skills
        """
        detected_skills: List[DetectedSkill] = []

        # Combine both messages for analysis
        full_text = f"{david_message}\n{angela_response}"

        # Detect skills from code patterns
        code_skills = await self._detect_skills_from_code(angela_response, project_context)
        detected_skills.extend(code_skills)

        # Detect skills from keywords in conversation
        keyword_skills = await self._detect_skills_from_keywords(full_text, topic, project_context)
        detected_skills.extend(keyword_skills)

        # Remove duplicates (keep highest confidence)
        unique_skills = self._deduplicate_skills(detected_skills)

        return SkillAnalysisResult(
            conversation_id=conversation_id,
            detected_skills=unique_skills
        )

    async def _detect_skills_from_code(
        self,
        code: str,
        project_context: Optional[str]
    ) -> List[DetectedSkill]:
        """Detect skills from code patterns"""
        detected: List[DetectedSkill] = []

        for skill_name, config in self.skill_patterns.items():
            confidence = 0.0
            matches = 0

            # Check code patterns
            for pattern in config["code_patterns"]:
                if re.search(pattern, code, re.IGNORECASE | re.MULTILINE):
                    matches += 1
                    confidence += 0.3

            if matches > 0:
                # Calculate complexity level
                complexity = self._calculate_code_complexity(
                    code,
                    config["complexity_indicators"]
                )

                # Extract relevant code snippet as evidence
                evidence = self._extract_code_snippet(code, config["code_patterns"])

                detected.append(DetectedSkill(
                    skill_name=skill_name,
                    category=config["category"],
                    evidence_type=EvidenceType.CODE_WRITTEN,
                    evidence_text=evidence[:500],  # Limit length
                    complexity_level=complexity,
                    confidence=min(confidence, 1.0)
                ))

        return detected

    async def _detect_skills_from_keywords(
        self,
        text: str,
        topic: str,
        project_context: Optional[str]
    ) -> List[DetectedSkill]:
        """Detect skills from keywords in conversation"""
        detected: List[DetectedSkill] = []
        text_lower = text.lower()

        for skill_name, config in self.skill_patterns.items():
            keyword_matches = 0

            # Count keyword matches
            for keyword in config["keywords"]:
                if keyword in text_lower:
                    keyword_matches += 1

            if keyword_matches >= 2:  # Need at least 2 keyword matches
                confidence = min(0.5 + (keyword_matches * 0.1), 0.9)

                # Extract context around keywords as evidence
                evidence = self._extract_conversation_context(text, config["keywords"])

                detected.append(DetectedSkill(
                    skill_name=skill_name,
                    category=config["category"],
                    evidence_type=EvidenceType.CONVERSATION,
                    evidence_text=evidence[:300],
                    complexity_level=5,  # Default for conversations
                    confidence=confidence
                ))

        return detected

    def _calculate_code_complexity(self, code: str, complexity_indicators: List[str]) -> int:
        """
        Calculate complexity level 1-10 based on code characteristics

        Args:
            code: The code to analyze
            complexity_indicators: List of advanced patterns to look for

        Returns:
            Complexity level 1-10
        """
        base_complexity = 5

        # Check for complexity indicators
        indicator_count = sum(
            1 for indicator in complexity_indicators
            if indicator.lower() in code.lower()
        )

        # Adjust based on code length
        line_count = len(code.split('\n'))
        if line_count > 100:
            base_complexity += 2
        elif line_count > 50:
            base_complexity += 1

        # Adjust based on indicator count
        base_complexity += min(indicator_count, 3)

        return min(base_complexity, 10)

    def _extract_code_snippet(self, code: str, patterns: List[str]) -> str:
        """Extract relevant code snippet matching patterns"""
        lines = code.split('\n')

        # Find lines matching patterns
        matching_lines = []
        for i, line in enumerate(lines):
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Include context (2 lines before and after)
                    start = max(0, i - 2)
                    end = min(len(lines), i + 3)
                    matching_lines.extend(lines[start:end])
                    break

        if not matching_lines:
            # Return first 10 lines if no matches
            return '\n'.join(lines[:10])

        return '\n'.join(matching_lines[:15])  # Limit to 15 lines

    def _extract_conversation_context(self, text: str, keywords: List[str]) -> str:
        """Extract context around keywords from conversation"""
        sentences = text.split('.')

        relevant_sentences = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in keywords):
                relevant_sentences.append(sentence.strip())

        if not relevant_sentences:
            return text[:200]

        return '. '.join(relevant_sentences[:3])  # First 3 relevant sentences

    def _deduplicate_skills(self, skills: List[DetectedSkill]) -> List[DetectedSkill]:
        """Remove duplicate skills, keeping highest confidence"""
        seen: Dict[str, DetectedSkill] = {}

        for skill in skills:
            if skill.skill_name not in seen:
                seen[skill.skill_name] = skill
            else:
                # Keep higher confidence version
                if skill.confidence > seen[skill.skill_name].confidence:
                    seen[skill.skill_name] = skill

        return list(seen.values())

    async def detect_skills_from_file_changes(
        self,
        file_path: str,
        file_content: str,
        project_context: str
    ) -> List[DetectedSkill]:
        """
        Detect skills from file modifications

        Useful for analyzing code files directly
        """
        return await self._detect_skills_from_code(file_content, project_context)

    async def get_skill_by_name(self, skill_name: str) -> Optional[Dict]:
        """Get skill configuration by name"""
        conn = await get_db_connection()
        row = await conn.fetchrow(
            "SELECT * FROM angela_skills WHERE skill_name = $1",
            skill_name
        )
        await conn.close()
        return dict(row) if row else None

    async def skill_exists(self, skill_name: str) -> bool:
        """Check if skill exists in database"""
        skill = await self.get_skill_by_name(skill_name)
        return skill is not None


# =====================================================
# Convenience Functions
# =====================================================

async def analyze_conversation_for_skills(
    conversation_id: UUID,
    david_message: str,
    angela_response: str,
    topic: str,
    project_context: Optional[str] = None
) -> SkillAnalysisResult:
    """
    Convenience function to analyze a conversation

    Usage:
        result = await analyze_conversation_for_skills(
            conversation_id=uuid,
            david_message="Can you fix the SwiftUI list?",
            angela_response="Sure! I'll update the List view...",
            topic="swiftui_debugging",
            project_context="AngelaBrainDashboard"
        )
    """
    analyzer = SkillAnalyzer()
    return await analyzer.analyze_conversation(
        conversation_id=conversation_id,
        david_message=david_message,
        angela_response=angela_response,
        topic=topic,
        project_context=project_context
    )
