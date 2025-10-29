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
from angela_core.embedding_service import embedding
from angela_core.services.ollama_service import ollama

logger = logging.getLogger(__name__)


class KnowledgeExtractionService:
    """Service สำหรับดึงความรู้และสร้าง knowledge graph"""

    def __init__(self):
        self.ollama = ollama
        self.embedding = embedding
        logger.info("🧠 Knowledge Extraction Service initialized")

    async def extract_concepts_from_text(
        self,
        text: str,
        context: Optional[str] = None
    ) -> List[Dict]:
        """
        ดึง key concepts จาก text โดยใช้ LLM

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
                    "description": "Database system used by Angela"
                },
                ...
            ]
        """
        try:
            # Prompt สำหรับ LLM
            prompt = f"""วิเคราะห์ข้อความนี้และดึง key concepts ออกมา:

"{text}"

ให้ระบุ concepts ในรูปแบบ JSON array:
[
    {{
        "concept_name": "ชื่อ concept",
        "concept_category": "หมวดหมู่ (person/technology/emotion/concept/event/place)",
        "importance": "ความสำคัญ 1-10",
        "description": "คำอธิบายสั้นๆ"
    }}
]

กฎ:
- ดึงเฉพาะ concepts ที่สำคัญจริงๆ (ไม่เกิน 5-8 concepts)
- person: คน เช่น David, Angela
- technology: เทคโนโลยี เช่น PostgreSQL, Ollama, Python
- emotion: อารมณ์ เช่น happiness, loneliness, love
- concept: แนวคิด เช่น consciousness, memory, knowledge
- event: เหตุการณ์ เช่น Phase 4 completion, morning greeting
- place: สถานที่

ตอบเป็น JSON array เท่านั้น ไม่ต้องอธิบายเพิ่ม:"""

            # เรียก LLM
            response = await self.ollama.generate(
                model="qwen2.5:7b",
                prompt=prompt,
                temperature=0.3
            )

            # Parse JSON response
            response_text = response.strip()

            # ลองหา JSON array ในข้อความ
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']')

            if start_idx == -1 or end_idx == -1:
                logger.warning(f"⚠️ No JSON array found in response: {response_text[:100]}")
                return []

            json_str = response_text[start_idx:end_idx+1]
            concepts = json.loads(json_str)

            logger.info(f"✅ Extracted {len(concepts)} concepts from text")
            return concepts

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON: {e}")
            logger.error(f"Response was: {response_text[:200]}")
            return []
        except Exception as e:
            logger.error(f"❌ Failed to extract concepts: {e}")
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
