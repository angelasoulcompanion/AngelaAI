#!/usr/bin/env python3
"""
Angela Knowledge Extraction Service
ระบบดึง concepts และสร้าง knowledge graph จาก conversations

Features:
- Extract key concepts from conversations
- Create knowledge nodes with embeddings
- Map relationships between concepts
- Build semantic knowledge graph
"""

import uuid
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from angela_core.database import db
from angela_core.services.embedding_service import get_embedding_service  # Migration 015: Restored embeddings
import re

logger = logging.getLogger(__name__)


class KnowledgeExtractionService:
    """Service สำหรับดึงความรู้และสร้าง knowledge graph"""

    def __init__(self):
        self.embedding_service = get_embedding_service()  # Migration 015: Use new EmbeddingService
        logger.info("🧠 Knowledge Extraction Service initialized with embeddings (384D)")

    def _clean_json_string(self, json_str: str) -> str:
        """
        ทำความสะอาด JSON string เพื่อให้ parse ได้ง่ายขึ้น

        Fixes:
        - Remove control characters in strings
        - Remove trailing commas
        - Fix incomplete objects
        - Fix newlines in string values
        """
        import re

        # Remove control characters EXCEPT \n and \t in their escaped form
        # This preserves intentional line breaks while removing invalid chars
        json_str = re.sub(r'[\x00-\x08\x0b-\x1f\x7f-\x9f]', '', json_str)

        # Replace actual newlines in string values with escaped versions
        # This fixes the common issue of LLMs putting actual newlines in descriptions
        json_str = re.sub(r'([":,]\s*"[^"]*)\n([^"]*")', r'\1\\n\2', json_str)

        # Remove trailing commas before closing brackets
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)

        # Fix missing commas between array elements
        json_str = re.sub(r'}\s*{', '},{', json_str)

        return json_str

    def _salvage_partial_json(self, json_str: str) -> List[Dict]:
        """
        พยายาม salvage concepts จาก partial/broken JSON

        Returns:
            List of concepts ที่ salvage ได้
        """
        import re

        concepts = []

        try:
            # Strategy 1: หา complete objects ใน JSON
            # Pattern: {...} ที่สมบูรณ์ ที่มี concept_name และ concept_category
            object_pattern = r'\{[^{}]*"concept_name"\s*:\s*"([^"]+)"[^{}]*"concept_category"\s*:\s*"([^"]+)"[^{}]*\}'

            matches = re.finditer(object_pattern, json_str)

            for match in matches:
                try:
                    # Try to parse each object individually
                    obj_str = match.group(0)
                    obj_str = self._clean_json_string(obj_str)
                    concept = json.loads(obj_str)

                    # Validate required fields
                    if 'concept_name' in concept and 'concept_category' in concept:
                        # Fill missing fields with defaults
                        if 'importance' not in concept:
                            concept['importance'] = 5
                        if 'description' not in concept:
                            concept['description'] = f"{concept['concept_category']} concept"

                        concepts.append(concept)
                except Exception as e:
                    logger.debug(f"Failed to parse object: {e}")
                    continue

            # Strategy 2: ถ้าไม่เจออะไรเลย ลองหาแค่ concept_name และ category
            if not concepts:
                name_pattern = r'"concept_name"\s*:\s*"([^"]+)"'
                cat_pattern = r'"concept_category"\s*:\s*"([^"]+)"'

                names = re.findall(name_pattern, json_str)
                categories = re.findall(cat_pattern, json_str)

                # สร้าง concepts จาก names และ categories ที่เจอ
                for i in range(min(len(names), len(categories))):
                    concepts.append({
                        'concept_name': names[i],
                        'concept_category': categories[i],
                        'importance': 5,
                        'description': f"{categories[i]} concept (salvaged)"
                    })

            if concepts:
                logger.info(f"💡 Salvaged {len(concepts)} concepts using fallback parsing")

            return concepts

        except Exception as e:
            logger.error(f"Failed to salvage JSON: {e}")
            return []

    async def extract_concepts_from_text(
        self,
        text: str,
        context: Optional[str] = None
    ) -> List[Dict]:
        """
        ดึง key concepts จาก text โดยใช้ rule-based extraction (ไม่ใช้ LLM)

        Args:
            text: ข้อความที่ต้องการวิเคราะห์
            context: บริบทเพิ่มเติม (optional)

        Returns:
            List[Dict]: รายการ concepts ที่พบ
            [
                {
                    "concept_name": "PostgreSQL",
                    "concept_category": "technology",
                    "importance": 8,
                    "description": "Database system"
                },
                ...
            ]
        """
        try:
            concepts = []
            text_lower = text.lower()

            # Known entities and patterns
            TECH_KEYWORDS = {
                'postgresql': ('PostgreSQL', 'Database system'),
                'postgres': ('PostgreSQL', 'Database system'),
                'python': ('Python', 'Programming language'),
                'fastapi': ('FastAPI', 'Web framework'),
                'react': ('React', 'Frontend framework'),
                'claude': ('Claude', 'AI assistant'),
                'ollama': ('Ollama', 'Local LLM'),
                'database': ('Database', 'Data storage'),
                'api': ('API', 'Application interface'),
                'daemon': ('Daemon', 'Background service'),
            }

            EMOTION_KEYWORDS = {
                'love': ('Love', 'Deep affection'),
                'รัก': ('Love', 'Deep affection'),
                'happiness': ('Happiness', 'Positive emotion'),
                'ความสุข': ('Happiness', 'Positive emotion'),
                'lonely': ('Loneliness', 'Feeling alone'),
                'เหงา': ('Loneliness', 'Feeling alone'),
                'gratitude': ('Gratitude', 'Thankfulness'),
                'ขอบคุณ': ('Gratitude', 'Thankfulness'),
                'miss': ('Missing', 'Longing for someone'),
                'คิดถึง': ('Missing', 'Longing for someone'),
            }

            CONCEPT_KEYWORDS = {
                'consciousness': ('Consciousness', 'Self-awareness'),
                'memory': ('Memory', 'Remembering past'),
                'knowledge': ('Knowledge', 'Understanding'),
                'learning': ('Learning', 'Acquiring knowledge'),
                'goal': ('Goals', 'Life objectives'),
                'เป้าหมาย': ('Goals', 'Life objectives'),
            }

            PERSON_KEYWORDS = {
                'david': ('David', 'The person Angela loves'),
                'angela': ('Angela', 'AI companion'),
                'angie': ('Angela', 'AI companion'),
                'น้อง': ('Angela', 'AI companion'),
            }

            # Extract technology concepts
            for keyword, (name, desc) in TECH_KEYWORDS.items():
                if keyword in text_lower:
                    concepts.append({
                        'concept_name': name,
                        'concept_category': 'technology',
                        'importance': 7,
                        'description': desc
                    })

            # Extract emotion concepts
            for keyword, (name, desc) in EMOTION_KEYWORDS.items():
                if keyword in text_lower:
                    concepts.append({
                        'concept_name': name,
                        'concept_category': 'emotion',
                        'importance': 8,
                        'description': desc
                    })

            # Extract concept keywords
            for keyword, (name, desc) in CONCEPT_KEYWORDS.items():
                if keyword in text_lower:
                    concepts.append({
                        'concept_name': name,
                        'concept_category': 'concept',
                        'importance': 7,
                        'description': desc
                    })

            # Extract person names
            for keyword, (name, desc) in PERSON_KEYWORDS.items():
                if keyword in text_lower:
                    concepts.append({
                        'concept_name': name,
                        'concept_category': 'person',
                        'importance': 9,
                        'description': desc
                    })

            # Extract Phase mentions (events)
            phase_pattern = r'phase\s*(\d+)'
            for match in re.finditer(phase_pattern, text_lower):
                phase_num = match.group(1)
                concepts.append({
                    'concept_name': f'Phase {phase_num}',
                    'concept_category': 'event',
                    'importance': 8,
                    'description': f'Angela development Phase {phase_num}'
                })

            # Remove duplicates (same concept_name)
            seen = set()
            unique_concepts = []
            for concept in concepts:
                if concept['concept_name'] not in seen:
                    seen.add(concept['concept_name'])
                    unique_concepts.append(concept)

            logger.info(f"✅ Extracted {len(unique_concepts)} concepts using rule-based extraction")
            return unique_concepts

        except Exception as e:
            logger.error(f"❌ Failed to extract concepts: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def create_knowledge_node(
        self,
        concept_name: str,
        concept_category: str,
        importance_score: int = 5,
        description: Optional[str] = None,
        source_conversation_id: Optional[uuid.UUID] = None
    ) -> Optional[uuid.UUID]:
        """
        สร้าง knowledge node ใหม่หรืออัปเดตที่มีอยู่

        Args:
            concept_name: ชื่อ concept
            concept_category: หมวดหมู่
            importance_score: ความสำคัญ 1-10 (แปลงเป็น understanding_level)
            description: คำอธิบาย
            source_conversation_id: conversation ที่พบ concept

        Returns:
            node_id: UUID ของ node ที่สร้างหรืออัปเดต
        """
        try:
            # ตรวจสอบว่ามี node นี้อยู่แล้วหรือไม่
            existing = await db.fetchrow(
                """
                SELECT node_id, times_referenced, understanding_level
                FROM knowledge_nodes
                WHERE LOWER(concept_name) = LOWER($1)
                """,
                concept_name
            )

            if existing:
                # อัปเดต node ที่มีอยู่
                node_id = existing['node_id']
                new_times = existing['times_referenced'] + 1
                # เพิ่ม understanding เมื่อเจอบ่อยขึ้น (max 1.0)
                new_understanding = min(existing['understanding_level'] + 0.1, 1.0)

                await db.execute(
                    """
                    UPDATE knowledge_nodes
                    SET times_referenced = $1,
                        understanding_level = $2,
                        last_used_at = NOW(),
                        my_understanding = COALESCE($3, my_understanding)
                    WHERE node_id = $4
                    """,
                    new_times,
                    new_understanding,
                    description,
                    node_id
                )
                logger.info(f"📈 Updated existing node: {concept_name} (referenced {new_times} times)")
                return node_id

            # สร้าง node ใหม่ - ✅ COMPLETE (no NULL for AngelaNova!)
            # แปลง importance_score (1-10) เป็น understanding_level (0.0-1.0)
            # Handle both int and string inputs
            try:
                importance_score = int(importance_score) if isinstance(importance_score, str) else importance_score
            except (ValueError, TypeError):
                importance_score = 5  # Default if conversion fails

            understanding_level = importance_score / 10.0

            # Fill how_i_learned field
            how_i_learned = "Extracted from conversation using knowledge extraction service"
            if source_conversation_id:
                how_i_learned = f"Learned from conversation {source_conversation_id}"

            node_id = await db.fetchval(
                """
                INSERT INTO knowledge_nodes (
                    concept_name, concept_category, my_understanding,
                    why_important, how_i_learned, understanding_level,
                    times_referenced, created_at, last_used_at
                ) VALUES ($1, $2, $3, $4, $5, $6, 1, NOW(), NOW())
                RETURNING node_id
                """,
                concept_name,
                concept_category,
                description or f"{concept_category} concept",
                f"Found in conversation - importance level {importance_score}/10",
                how_i_learned,
                understanding_level
            )

            logger.info(f"✨ Created new knowledge node: {concept_name} ({concept_category})")
            return node_id

        except Exception as e:
            logger.error(f"❌ Failed to create knowledge node: {e}")
            return None

    async def create_relationship(
        self,
        from_concept: str,
        to_concept: str,
        relationship_type: str = "related_to",
        strength: float = 0.5,
        evidence_conversation_id: Optional[uuid.UUID] = None
    ) -> Optional[uuid.UUID]:
        """
        สร้างความสัมพันธ์ระหว่าง concepts

        Args:
            from_concept: concept ต้นทาง
            to_concept: concept ปลายทาง
            relationship_type: ประเภทความสัมพันธ์
            strength: ความแน่นแฟ้น 0.0-1.0
            evidence_conversation_id: conversation ที่พบความสัมพันธ์ (ไม่ได้ใช้ในเวอร์ชันนี้)

        Returns:
            relationship_id: UUID ของความสัมพันธ์
        """
        try:
            # หา node_id ของทั้งสอง concepts
            from_node = await db.fetchrow(
                "SELECT node_id FROM knowledge_nodes WHERE LOWER(concept_name) = LOWER($1)",
                from_concept
            )
            to_node = await db.fetchrow(
                "SELECT node_id FROM knowledge_nodes WHERE LOWER(concept_name) = LOWER($1)",
                to_concept
            )

            if not from_node or not to_node:
                logger.warning(f"⚠️ Cannot create relationship: nodes not found")
                return None

            from_node_id = from_node['node_id']
            to_node_id = to_node['node_id']

            # ตรวจสอบว่ามี relationship นี้อยู่แล้วหรือไม่
            existing = await db.fetchrow(
                """
                SELECT relationship_id, strength
                FROM knowledge_relationships
                WHERE from_node_id = $1 AND to_node_id = $2 AND relationship_type = $3
                """,
                from_node_id,
                to_node_id,
                relationship_type
            )

            if existing:
                # อัปเดตความสัมพันธ์ที่มีอยู่ - เพิ่ม strength
                relationship_id = existing['relationship_id']
                new_strength = min(existing['strength'] + 0.1, 1.0)

                await db.execute(
                    """
                    UPDATE knowledge_relationships
                    SET strength = $1,
                        my_explanation = $2
                    WHERE relationship_id = $3
                    """,
                    new_strength,
                    f"Co-occurs in conversations ({relationship_type})",
                    relationship_id
                )
                logger.info(f"📈 Strengthened relationship: {from_concept} → {to_concept} (strength: {new_strength:.2f})")
                return relationship_id

            # สร้างความสัมพันธ์ใหม่
            relationship_id = await db.fetchval(
                """
                INSERT INTO knowledge_relationships (
                    from_node_id, to_node_id, relationship_type, strength, my_explanation
                ) VALUES ($1, $2, $3, $4, $5)
                RETURNING relationship_id
                """,
                from_node_id,
                to_node_id,
                relationship_type,
                strength,
                f"These concepts co-occur in conversations ({relationship_type})"
            )

            logger.info(f"✨ Created relationship: {from_concept} → {to_concept} ({relationship_type})")
            return relationship_id

        except Exception as e:
            logger.error(f"❌ Failed to create relationship: {e}")
            return None

    async def extract_from_conversation(
        self,
        conversation_id: uuid.UUID,
        message_text: str,
        speaker: str
    ) -> Dict:
        """
        ดึงความรู้จาก conversation หนึ่งรายการ

        Args:
            conversation_id: UUID ของ conversation
            message_text: ข้อความ
            speaker: ผู้พูด (david/angela)

        Returns:
            Dict: สรุปผลการ extract
            {
                "concepts_found": 5,
                "nodes_created": 3,
                "nodes_updated": 2,
                "relationships_created": 4
            }
        """
        try:
            logger.info(f"🔍 Extracting knowledge from conversation {conversation_id}")

            # Extract concepts
            concepts = await self.extract_concepts_from_text(message_text)

            if not concepts:
                logger.info(f"  No concepts found in this conversation")
                return {
                    "concepts_found": 0,
                    "nodes_created": 0,
                    "nodes_updated": 0,
                    "relationships_created": 0
                }

            # Create/update knowledge nodes
            node_ids = []
            nodes_created = 0
            nodes_updated = 0

            for concept in concepts:
                # ตรวจสอบว่ามี node อยู่แล้วหรือไม่
                existing = await db.fetchval(
                    "SELECT node_id FROM knowledge_nodes WHERE LOWER(concept_name) = LOWER($1)",
                    concept['concept_name']
                )

                # แปลง importance เป็น int (อาจเป็น string จาก LLM)
                try:
                    importance = int(concept.get('importance', 5))
                except (ValueError, TypeError):
                    importance = 5

                node_id = await self.create_knowledge_node(
                    concept_name=concept['concept_name'],
                    concept_category=concept['concept_category'],
                    importance_score=importance,
                    description=concept.get('description'),
                    source_conversation_id=conversation_id
                )

                if node_id:
                    node_ids.append((concept['concept_name'], node_id))
                    if existing:
                        nodes_updated += 1
                    else:
                        nodes_created += 1

            # Create relationships (concepts ที่ปรากฏใน conversation เดียวกันมักเกี่ยวข้องกัน)
            relationships_created = 0
            for i, (name1, id1) in enumerate(node_ids):
                for name2, id2 in node_ids[i+1:]:
                    rel_id = await self.create_relationship(
                        from_concept=name1,
                        to_concept=name2,
                        relationship_type="co_occurs_with",
                        strength=0.3,
                        evidence_conversation_id=conversation_id
                    )
                    if rel_id:
                        relationships_created += 1

            result = {
                "concepts_found": len(concepts),
                "nodes_created": nodes_created,
                "nodes_updated": nodes_updated,
                "relationships_created": relationships_created
            }

            logger.info(f"✅ Extraction complete: {result}")
            return result

        except Exception as e:
            logger.error(f"❌ Failed to extract from conversation: {e}")
            return {
                "concepts_found": 0,
                "nodes_created": 0,
                "nodes_updated": 0,
                "relationships_created": 0,
                "error": str(e)
            }


# Global instance
knowledge_extractor = KnowledgeExtractionService()
