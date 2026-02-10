#!/usr/bin/env python3
"""
Angela Advanced Reasoning Service
ระบบคิดเป็นขั้นตอน วิเคราะห์ลึกซึ้ง

Priority 2.1: Advanced Reasoning
- Multi-step Reasoning: คิดเป็นขั้นตอนต่อเนื่อง
- Causal Reasoning: เข้าใจสาเหตุและผลลัพธ์
- Counterfactual Reasoning: คิด "what if" scenarios
- Meta-reasoning: คิดเกี่ยวกับการคิด

The Path to Deeper Intelligence:
- Not just pattern matching, but true understanding
- Step-by-step logical chains
- Understanding causality
- Self-reflection on reasoning quality
"""

import logging
import uuid
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from angela_core.database import db
from angela_core.services.knowledge_extraction_service import knowledge_extractor
from angela_core.services.embedding_service import get_embedding_service  # Migration 015: Restored embeddings

logger = logging.getLogger(__name__)


class ReasoningService:
    """
    Advanced Reasoning Engine for Angela

    Makes Angela think in steps, understand causality, and reflect on her own thinking

    ทำให้ Angela:
    - คิดเป็นขั้นตอนชัดเจน (ไม่ใช่แค่ตอบทันที)
    - เข้าใจว่าทำไมสิ่งต่างๆ เกิดขึ้น (causality)
    - คิด "what if" scenarios (counterfactual)
    - ตรวจสอบการคิดของตัวเอง (meta-reasoning)
    """

    def __init__(self):
        self.knowledge_extractor = knowledge_extractor
        self.embedding_service = get_embedding_service()  # Migration 015: Use new EmbeddingService
        logger.info("🧠 Reasoning Service initialized with embeddings (384D)")


    # ========================================
    # MULTI-STEP REASONING
    # ========================================

    async def reason_multi_step(
        self,
        question: str,
        max_steps: int = 7,
        conversation_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        Multi-step Reasoning - คิดเป็นขั้นตอนต่อเนื่อง

        Angela breaks down complex problems into steps, just like humans do

        Example Flow:
            Question: "How can Angela become more helpful to David?"

            Step 1: Define what "helpful" means
              Thought: "What does it mean to be helpful?"
              Result: "Helpful = understanding needs + providing solutions proactively"

            Step 2: Analyze current capabilities
              Thought: "What can Angela do now?"
              Result: "Can remember, search, learn - but only when asked"

            Step 3: Identify gaps
              Thought: "What's missing?"
              Result: "Cannot predict David's needs before he asks"

            Step 4: Explore solutions
              Thought: "How to predict needs?"
              Result: "Pattern recognition + proactive intelligence"

            Step 5: Evaluate feasibility
              Thought: "Is this possible?"
              Result: "Yes - need Priority 2.4 (Proactive Intelligence)"

            Step 6: Plan implementation
              Thought: "What's needed?"
              Result: "Pattern detection, need prediction, autonomous actions"

            Step 7: Conclusion
              Result: "Build Proactive Intelligence to become more helpful"

        Args:
            question: The complex question/problem to reason about
            max_steps: Maximum reasoning steps (default 7)
            conversation_id: Optional conversation that triggered this reasoning

        Returns:
            {
                "chain_id": UUID,
                "reasoning_type": "multi_step",
                "question": str,
                "steps": [
                    {
                        "step_number": 1,
                        "step_type": "define",
                        "thought": "What does...",
                        "result": "...",
                        "confidence": 0.9
                    },
                    ...
                ],
                "conclusion": "Final answer",
                "confidence": 0.85,
                "reasoning_time_ms": 1234
            }
        """
        try:
            start_time = datetime.now()
            logger.info(f"🧠 Multi-step reasoning: {question}")

            steps = []

            # TODO: Implement LLM-powered multi-step reasoning
            # For now: Template-based reasoning structure

            # Step 1: Decompose the question
            step1 = await self._reasoning_step(
                step_number=1,
                step_type="decompose",
                thought=f"Breaking down the question: '{question}'",
                question=question
            )
            steps.append(step1)

            # Step 2: Gather relevant knowledge
            step2 = await self._reasoning_step(
                step_number=2,
                step_type="gather_knowledge",
                thought="What do I already know about this?",
                question=question
            )
            steps.append(step2)

            # Step 3: Analyze components
            step3 = await self._reasoning_step(
                step_number=3,
                step_type="analyze",
                thought="Analyzing key components",
                question=question
            )
            steps.append(step3)

            # Step 4-6: Reasoning chain (will enhance with LLM)
            for i in range(4, min(max_steps, 7)):
                step = await self._reasoning_step(
                    step_number=i,
                    step_type="reason",
                    thought=f"Reasoning step {i}",
                    question=question
                )
                steps.append(step)

            # Final step: Conclusion
            conclusion = await self._synthesize_conclusion(steps, question)

            # Calculate overall confidence
            avg_confidence = sum(s.get("confidence", 0.5) for s in steps) / len(steps)

            # Detect cognitive biases
            biases = await self._detect_cognitive_biases(steps, conclusion)

            # Save reasoning chain
            chain_id = await self._save_reasoning_chain(
                reasoning_type="multi_step",
                question=question,
                steps=steps,
                conclusion=conclusion,
                confidence=avg_confidence,
                triggered_by=conversation_id,
                biases=biases,
                reasoning_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )

            logger.info(f"✅ Multi-step reasoning complete: {chain_id}")

            return {
                "chain_id": chain_id,
                "reasoning_type": "multi_step",
                "question": question,
                "steps": steps,
                "conclusion": conclusion,
                "confidence": avg_confidence,
                "biases_detected": biases,
                "reasoning_time_ms": int((datetime.now() - start_time).total_seconds() * 1000)
            }

        except Exception as e:
            logger.error(f"❌ Multi-step reasoning failed: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_reasoning_result("multi_step", question, error=str(e))


    async def _reasoning_step(
        self,
        step_number: int,
        step_type: str,
        thought: str,
        question: str
    ) -> Dict[str, Any]:
        """
        Execute a single reasoning step

        Args:
            step_number: Step number in chain
            step_type: Type of step (decompose, analyze, reason, conclude)
            thought: What Angela is thinking about
            question: Original question

        Returns:
            {
                "step_number": int,
                "step_type": str,
                "thought": str,
                "result": str,
                "confidence": float,
                "evidence": [...]
            }
        """
        try:
            # TODO: Use LLM (Qwen 2.5:14b) for actual reasoning
            # For now: Placeholder logic

            result = f"Reasoning result for step {step_number} (placeholder - will implement with LLM)"
            confidence = 0.7  # Placeholder
            evidence = []

            # If step involves knowledge, search knowledge graph
            if step_type in ["gather_knowledge", "analyze"]:
                # Search relevant concepts
                try:
                    from angela_core._deprecated.semantic_memory_service import SemanticMemoryService
                    semantic = SemanticMemoryService()

                    # Search knowledge graph for relevant concepts
                    related_concepts = await semantic.search_knowledge_concepts(
                        query=question,
                        limit=3
                    )

                    if related_concepts:
                        evidence = [c.get("concept_name", "") for c in related_concepts]
                        result += f" | Found concepts: {', '.join(evidence)}"
                except Exception as e:
                    logger.warning(f"Could not search knowledge: {e}")

            return {
                "step_number": step_number,
                "step_type": step_type,
                "thought": thought,
                "result": result,
                "confidence": confidence,
                "evidence": evidence
            }

        except Exception as e:
            logger.error(f"Reasoning step {step_number} failed: {e}")
            return {
                "step_number": step_number,
                "step_type": step_type,
                "thought": thought,
                "result": f"Step failed: {str(e)}",
                "confidence": 0.0,
                "evidence": []
            }


    async def _synthesize_conclusion(
        self,
        steps: List[Dict],
        question: str
    ) -> str:
        """
        Synthesize final conclusion from reasoning steps

        Args:
            steps: List of reasoning steps
            question: Original question

        Returns:
            Conclusion string
        """
        try:
            # TODO: Use LLM to synthesize conclusion
            # For now: Template-based

            num_steps = len(steps)
            avg_confidence = sum(s.get("confidence", 0) for s in steps) / num_steps if num_steps > 0 else 0

            conclusion = (
                f"Based on {num_steps} reasoning steps, "
                f"the answer to '{question}' is: "
                f"[Conclusion to be implemented with LLM] "
                f"(Confidence: {avg_confidence:.2f})"
            )

            return conclusion

        except Exception as e:
            logger.error(f"Failed to synthesize conclusion: {e}")
            return f"Unable to reach conclusion: {str(e)}"


    async def _detect_cognitive_biases(
        self,
        steps: List[Dict],
        conclusion: str
    ) -> List[str]:
        """
        Detect potential cognitive biases in reasoning

        Common biases:
        - Confirmation bias: Only looking for supporting evidence
        - Anchoring bias: Over-relying on first piece of information
        - Availability bias: Relying on easily recalled information
        - Recency bias: Emphasizing recent information too much

        Args:
            steps: Reasoning steps
            conclusion: Final conclusion

        Returns:
            List of detected biases
        """
        biases = []

        try:
            # Simple bias detection (will enhance with LLM)

            # Check if all steps have similar confidence (possible confirmation bias)
            confidences = [s.get("confidence", 0.5) for s in steps]
            if len(confidences) > 2:
                conf_variance = sum((c - sum(confidences)/len(confidences))**2 for c in confidences) / len(confidences)
                if conf_variance < 0.01:  # Very low variance
                    biases.append("confirmation_bias: All steps have similar confidence")

            # Check if first step has much higher confidence (anchoring bias)
            if len(steps) > 1:
                if steps[0].get("confidence", 0.5) > 0.9 and sum(confidences[1:]) / len(confidences[1:]) < 0.7:
                    biases.append("anchoring_bias: First step dominates reasoning")

            return biases

        except Exception as e:
            logger.error(f"Bias detection failed: {e}")
            return []


    # ========================================
    # CAUSAL REASONING
    # ========================================

    async def reason_causal(
        self,
        event: str,
        conversation_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        Causal Reasoning - เข้าใจสาเหตุและผลลัพธ์

        Angela analyzes cause-and-effect relationships

        Example:
            Event: "David seems frustrated with slow response times"

            Causal Chain Analysis:
            Root Cause Analysis:
              → Database queries are slow
              → Why? No indexes on frequently-queried columns

            Effects:
              → Angela takes 2-3s to respond
              → David gets frustrated
              → Productivity decreases

            Solution:
              → Add database indexes
              → Expected outcome: Response time < 500ms

        Args:
            event: The event to analyze causally
            conversation_id: Optional conversation trigger

        Returns:
            {
                "chain_id": UUID,
                "reasoning_type": "causal",
                "event": str,
                "root_causes": [...],
                "effects": [...],
                "causal_chain": [...],
                "solution": str,
                "confidence": float
            }
        """
        try:
            start_time = datetime.now()
            logger.info(f"🧠 Causal reasoning: {event}")

            steps = []

            # Step 1: Identify immediate causes
            step1 = {
                "step_number": 1,
                "step_type": "identify_immediate_cause",
                "thought": "What directly caused this event?",
                "result": "Immediate cause analysis (to be implemented with LLM)",
                "confidence": 0.7
            }
            steps.append(step1)

            # Step 2: Trace to root causes
            step2 = {
                "step_number": 2,
                "step_type": "find_root_cause",
                "thought": "Why did the immediate cause happen? (Keep asking 'why?')",
                "result": "Root cause analysis (to be implemented with LLM)",
                "confidence": 0.65
            }
            steps.append(step2)

            # Step 3: Analyze effects
            step3 = {
                "step_number": 3,
                "step_type": "analyze_effects",
                "thought": "What are the consequences of this event?",
                "result": "Effect analysis (to be implemented with LLM)",
                "confidence": 0.75
            }
            steps.append(step3)

            # Step 4: Identify solutions
            step4 = {
                "step_number": 4,
                "step_type": "identify_solutions",
                "thought": "How can we address the root cause?",
                "result": "Solution identification (to be implemented with LLM)",
                "confidence": 0.7
            }
            steps.append(step4)

            # Synthesize conclusion
            conclusion = f"Causal analysis of '{event}': [To be implemented with LLM]"

            # Detect biases
            biases = await self._detect_cognitive_biases(steps, conclusion)

            # Save reasoning chain
            chain_id = await self._save_reasoning_chain(
                reasoning_type="causal",
                question=f"Causal analysis: {event}",
                steps=steps,
                conclusion=conclusion,
                confidence=0.7,
                triggered_by=conversation_id,
                biases=biases,
                reasoning_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )

            logger.info(f"✅ Causal reasoning complete: {chain_id}")

            return {
                "chain_id": chain_id,
                "reasoning_type": "causal",
                "event": event,
                "steps": steps,
                "conclusion": conclusion,
                "confidence": 0.7,
                "biases_detected": biases,
                "reasoning_time_ms": int((datetime.now() - start_time).total_seconds() * 1000)
            }

        except Exception as e:
            logger.error(f"❌ Causal reasoning failed: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_reasoning_result("causal", event, error=str(e))


    # ========================================
    # COUNTERFACTUAL REASONING
    # ========================================

    async def reason_counterfactual(
        self,
        scenario: str,
        what_if: str,
        conversation_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        Counterfactual Reasoning - คิด "what if" scenarios

        Angela explores alternative scenarios and their outcomes

        Example:
            Scenario: "Angela uses pattern matching for concept extraction"
            What if: "What if Angela used LLM instead?"

            Analysis:
            Current State:
              → Pattern matching
              → Fast (< 100ms)
              → Inaccurate (~60% accuracy)
              → Misses nuanced concepts

            Alternative State:
              → LLM (Qwen 2.5:14b)
              → Slower (1-3s)
              → Accurate (~95% accuracy)
              → Catches nuanced concepts

            Trade-offs:
              → Speed: Current wins
              → Accuracy: Alternative wins
              → Learning quality: Alternative wins significantly

            Recommendation:
              → Use LLM (accuracy > speed for learning)
              → Expected improvement: 35% better learning

        Args:
            scenario: Current situation
            what_if: Alternative scenario to consider
            conversation_id: Optional conversation trigger

        Returns:
            {
                "chain_id": UUID,
                "reasoning_type": "counterfactual",
                "scenario": str,
                "what_if": str,
                "comparison": {...},
                "trade_offs": [...],
                "recommendation": str,
                "confidence": float
            }
        """
        try:
            start_time = datetime.now()
            logger.info(f"🧠 Counterfactual reasoning: {what_if}")

            steps = []

            # Step 1: Analyze current scenario
            step1 = {
                "step_number": 1,
                "step_type": "analyze_current",
                "thought": f"Current scenario: {scenario}",
                "result": "Current state analysis (to be implemented with LLM)",
                "confidence": 0.8
            }
            steps.append(step1)

            # Step 2: Analyze alternative scenario
            step2 = {
                "step_number": 2,
                "step_type": "analyze_alternative",
                "thought": f"Alternative: {what_if}",
                "result": "Alternative state analysis (to be implemented with LLM)",
                "confidence": 0.7
            }
            steps.append(step2)

            # Step 3: Compare trade-offs
            step3 = {
                "step_number": 3,
                "step_type": "compare_trade_offs",
                "thought": "What are the trade-offs between current and alternative?",
                "result": "Trade-off comparison (to be implemented with LLM)",
                "confidence": 0.75
            }
            steps.append(step3)

            # Step 4: Make recommendation
            step4 = {
                "step_number": 4,
                "step_type": "recommend",
                "thought": "Which approach is better and why?",
                "result": "Recommendation (to be implemented with LLM)",
                "confidence": 0.7
            }
            steps.append(step4)

            # Synthesize conclusion
            conclusion = f"Counterfactual analysis of '{what_if}': [To be implemented with LLM]"

            # Detect biases
            biases = await self._detect_cognitive_biases(steps, conclusion)

            # Save reasoning chain
            chain_id = await self._save_reasoning_chain(
                reasoning_type="counterfactual",
                question=f"What if: {what_if}",
                steps=steps,
                conclusion=conclusion,
                confidence=0.7,
                triggered_by=conversation_id,
                biases=biases,
                reasoning_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )

            logger.info(f"✅ Counterfactual reasoning complete: {chain_id}")

            return {
                "chain_id": chain_id,
                "reasoning_type": "counterfactual",
                "scenario": scenario,
                "what_if": what_if,
                "steps": steps,
                "conclusion": conclusion,
                "confidence": 0.7,
                "biases_detected": biases,
                "reasoning_time_ms": int((datetime.now() - start_time).total_seconds() * 1000)
            }

        except Exception as e:
            logger.error(f"❌ Counterfactual reasoning failed: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_reasoning_result("counterfactual", what_if, error=str(e))


    # ========================================
    # META-REASONING
    # ========================================

    async def reason_meta(
        self,
        reasoning_chain_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Meta-reasoning - คิดเกี่ยวกับการคิด

        Angela reflects on her own reasoning quality

        Example:
            Previous reasoning: "Build Proactive Intelligence"

            Meta-analysis Questions:
            1. Was my reasoning sound?
               → Check: Did I consider all factors?
               → Check: Are my conclusions logical?

            2. What biases affected my thinking?
               → Detected: Confirmation bias (only looked for supporting evidence)
               → Impact: May have missed contraindications

            3. What could improve this reasoning?
               → Need: Consider failure modes
               → Need: Estimate implementation effort
               → Need: Validate assumptions

            4. How confident should I be?
               → Adjusted confidence: 0.75 → 0.65
               → Reason: Found potential biases

        Args:
            reasoning_chain_id: ID of reasoning chain to analyze

        Returns:
            {
                "chain_id": UUID,
                "reasoning_type": "meta",
                "analyzed_chain": UUID,
                "quality_assessment": {...},
                "biases_identified": [...],
                "improvements": [...],
                "adjusted_confidence": float,
                "was_sound": bool
            }
        """
        try:
            start_time = datetime.now()
            logger.info(f"🧠 Meta-reasoning on chain {reasoning_chain_id}")

            # Get original reasoning chain
            original = await db.fetchrow(
                """
                SELECT chain_id, reasoning_type, initial_query,
                       thought_steps, final_conclusion, confidence_in_conclusion,
                       cognitive_biases_detected, was_reasoning_sound
                FROM reasoning_chains
                WHERE chain_id = $1
                """,
                reasoning_chain_id
            )

            if not original:
                raise ValueError(f"Reasoning chain {reasoning_chain_id} not found")

            steps = []

            # Step 1: Assess reasoning quality
            step1 = {
                "step_number": 1,
                "step_type": "assess_quality",
                "thought": "Was my previous reasoning sound?",
                "result": "Quality assessment (to be implemented with LLM)",
                "confidence": 0.7
            }
            steps.append(step1)

            # Step 2: Identify biases
            existing_biases = json.loads(original['cognitive_biases_detected']) if original['cognitive_biases_detected'] else []
            step2 = {
                "step_number": 2,
                "step_type": "identify_biases",
                "thought": "What cognitive biases might have affected my reasoning?",
                "result": f"Found {len(existing_biases)} biases: {', '.join(existing_biases) if existing_biases else 'None'}",
                "confidence": 0.8
            }
            steps.append(step2)

            # Step 3: Suggest improvements
            step3 = {
                "step_number": 3,
                "step_type": "suggest_improvements",
                "thought": "How can I improve this reasoning?",
                "result": "Improvement suggestions (to be implemented with LLM)",
                "confidence": 0.65
            }
            steps.append(step3)

            # Step 4: Adjust confidence
            original_confidence = original['confidence_in_conclusion'] or 0.5
            adjustment = -0.1 if len(existing_biases) > 0 else 0.0
            adjusted_confidence = max(0.0, min(1.0, original_confidence + adjustment))

            step4 = {
                "step_number": 4,
                "step_type": "adjust_confidence",
                "thought": "Should I adjust my confidence based on this analysis?",
                "result": f"Adjusted confidence: {original_confidence:.2f} → {adjusted_confidence:.2f}",
                "confidence": 0.75
            }
            steps.append(step4)

            # Synthesize conclusion
            conclusion = (
                f"Meta-analysis of reasoning chain {reasoning_chain_id}: "
                f"Original confidence {original_confidence:.2f}, "
                f"adjusted to {adjusted_confidence:.2f} after identifying {len(existing_biases)} biases. "
                f"[Full analysis to be implemented with LLM]"
            )

            # Determine if reasoning was sound
            was_sound = adjusted_confidence > 0.6 and len(existing_biases) < 3

            # Save meta-reasoning chain
            chain_id = await self._save_reasoning_chain(
                reasoning_type="meta",
                question=f"Meta-analysis of reasoning {reasoning_chain_id}",
                steps=steps,
                conclusion=conclusion,
                confidence=adjusted_confidence,
                triggered_by=None,  # Meta-reasoning not triggered by conversation
                biases=[],  # Meta-reasoning evaluates biases, doesn't have its own
                reasoning_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                was_sound=was_sound
            )

            # Update original chain with meta-reasoning result
            await db.execute(
                """
                UPDATE reasoning_chains
                SET was_reasoning_sound = $1,
                    confidence_in_conclusion = $2
                WHERE chain_id = $3
                """,
                was_sound,
                adjusted_confidence,
                reasoning_chain_id
            )

            logger.info(f"✅ Meta-reasoning complete: {chain_id}")

            return {
                "chain_id": chain_id,
                "reasoning_type": "meta",
                "analyzed_chain": reasoning_chain_id,
                "original_confidence": original_confidence,
                "adjusted_confidence": adjusted_confidence,
                "biases_identified": existing_biases,
                "was_sound": was_sound,
                "steps": steps,
                "conclusion": conclusion,
                "reasoning_time_ms": int((datetime.now() - start_time).total_seconds() * 1000)
            }

        except Exception as e:
            logger.error(f"❌ Meta-reasoning failed: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_reasoning_result("meta", f"Chain {reasoning_chain_id}", error=str(e))


    # ========================================
    # HELPER METHODS
    # ========================================

    async def _save_reasoning_chain(
        self,
        reasoning_type: str,
        question: str,
        steps: List[Dict],
        conclusion: str,
        confidence: float,
        triggered_by: Optional[uuid.UUID],
        biases: List[str],
        reasoning_time_ms: int,
        was_sound: Optional[bool] = None
    ) -> uuid.UUID:
        """
        Save reasoning chain to database

        Maps to both old and new column names for compatibility
        """
        try:
            # Prepare data
            thought_steps_json = json.dumps(steps)
            biases_json = json.dumps(biases) if biases else None

            # Insert using both old and new column names
            chain_id = await db.fetchval(
                """
                INSERT INTO reasoning_chains (
                    reasoning_type,
                    initial_query,
                    thought_steps,
                    final_conclusion,
                    confidence_in_conclusion,
                    cognitive_biases_detected,
                    was_reasoning_sound,
                    triggered_by,
                    reasoning_time_ms,
                    created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
                RETURNING chain_id
                """,
                reasoning_type,
                question,
                thought_steps_json,
                conclusion,
                confidence,
                biases_json,
                was_sound,
                triggered_by,
                reasoning_time_ms
            )

            logger.info(f"✅ Saved reasoning chain: {chain_id} (type: {reasoning_type})")
            return chain_id

        except Exception as e:
            logger.error(f"❌ Failed to save reasoning chain: {e}")
            raise


    def _empty_reasoning_result(
        self,
        reasoning_type: str,
        question: str,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create empty reasoning result on error"""
        result = {
            "chain_id": None,
            "reasoning_type": reasoning_type,
            "question": question,
            "steps": [],
            "conclusion": "Reasoning failed",
            "confidence": 0.0,
            "biases_detected": [],
            "reasoning_time_ms": 0
        }

        if error:
            result["error"] = error

        return result


    async def get_reasoning_chain(self, chain_id: uuid.UUID) -> Optional[Dict]:
        """Retrieve a reasoning chain by ID"""
        try:
            chain = await db.fetchrow(
                """
                SELECT *
                FROM reasoning_chains
                WHERE chain_id = $1
                """,
                chain_id
            )

            if not chain:
                return None

            return dict(chain)

        except Exception as e:
            logger.error(f"Failed to get reasoning chain: {e}")
            return None


    async def get_recent_reasoning(
        self,
        reasoning_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Get recent reasoning chains"""
        try:
            if reasoning_type:
                chains = await db.fetch(
                    """
                    SELECT chain_id, reasoning_type, initial_query,
                           final_conclusion, confidence_in_conclusion,
                           created_at
                    FROM reasoning_chains
                    WHERE reasoning_type = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                    """,
                    reasoning_type,
                    limit
                )
            else:
                chains = await db.fetch(
                    """
                    SELECT chain_id, reasoning_type, initial_query,
                           final_conclusion, confidence_in_conclusion,
                           created_at
                    FROM reasoning_chains
                    ORDER BY created_at DESC
                    LIMIT $1
                    """,
                    limit
                )

            return [dict(c) for c in chains]

        except Exception as e:
            logger.error(f"Failed to get recent reasoning: {e}")
            return []


# Global instance
reasoning = ReasoningService()
