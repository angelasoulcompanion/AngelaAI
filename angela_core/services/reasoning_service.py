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
import os
import uuid
import json
import aiohttp
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from angela_core.database import db
from angela_core.services.knowledge_extraction_service import knowledge_extractor
from angela_core.services.embedding_service import get_embedding_service  # Migration 015: Restored embeddings

logger = logging.getLogger(__name__)

# Gemma 3 12B — local reasoning engine (16 tok/s on M3 Pro, $0/day)
REASONING_MODEL = os.getenv("REASONING_MODEL", "gemma3:12b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_REASONING_TIMEOUT", "120"))


class ReasoningService:
    """
    Advanced Reasoning Engine for Angela — powered by Gemma 3 12B local

    Hybrid routing: Internal reasoning → Gemma 3 12B (free, private)
                    Chat with David   → Claude API (quality)

    ทำให้ Angela:
    - คิดเป็นขั้นตอนชัดเจน (ไม่ใช่แค่ตอบทันที)
    - เข้าใจว่าทำไมสิ่งต่างๆ เกิดขึ้น (causality)
    - คิด "what if" scenarios (counterfactual)
    - ตรวจสอบการคิดของตัวเอง (meta-reasoning)
    """

    def __init__(self):
        self.knowledge_extractor = knowledge_extractor
        self.embedding_service = get_embedding_service()  # Migration 015: Use new EmbeddingService
        self._ollama_available: Optional[bool] = None
        logger.info(f"🧠 Reasoning Service initialized — model: {REASONING_MODEL}")

    async def _call_ollama(self, system: str, user_message: str, max_tokens: int = 1024) -> Optional[str]:
        """Call Gemma 3 12B via Ollama for reasoning. Returns None if unavailable."""
        try:
            wants_json = any(kw in system.lower() for kw in ['json', '"json"', 'respond only in valid json'])
            payload = {
                "model": REASONING_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_message},
                ],
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.4,
                },
                "keep_alive": "5m",
            }
            if wants_json:
                payload["format"] = "json"
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{OLLAMA_BASE_URL}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=OLLAMA_TIMEOUT),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("message", {}).get("content")
                    else:
                        logger.error("Ollama returned HTTP %d", resp.status)
        except Exception as e:
            logger.error("Ollama reasoning call failed: %s", e)
        return None


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

            # Chain-of-thought reasoning — each step sees previous results
            step_definitions = [
                (1, "decompose", f"Breaking down: '{question}' — what are the key sub-questions?"),
                (2, "gather_knowledge", "What relevant knowledge, facts, or patterns do I already know?"),
                (3, "analyze", "Analyzing the key components and their relationships"),
                (4, "evaluate", "Evaluating possible answers — what are the trade-offs?"),
                (5, "verify", "Checking my reasoning for gaps or errors"),
                (6, "conclude", "What is the best answer based on all previous analysis?"),
            ]

            for step_num, step_type, thought in step_definitions[:min(max_steps, 6)]:
                step = await self._reasoning_step(
                    step_number=step_num,
                    step_type=step_type,
                    thought=thought,
                    question=question,
                    previous_steps=steps  # Chain-of-thought: each step builds on previous
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
        question: str,
        previous_steps: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Execute a single reasoning step using Gemma 3 12B local model.
        """
        try:
            evidence = []

            # Gather knowledge from RAG for relevant steps
            if step_type in ["gather_knowledge", "analyze"]:
                try:
                    from angela_core.services.enhanced_rag_service import EnhancedRAGService
                    rag = EnhancedRAGService()
                    await rag.connect()
                    results = await rag.search(question, top_k=3)
                    if results:
                        evidence = [r.get("content", "")[:200] for r in results]
                    await rag.disconnect()
                except Exception as e:
                    logger.warning(f"Could not search knowledge: {e}")

            # Build chain-of-thought context from previous steps
            chain_context = ""
            if previous_steps:
                chain_context = "\n".join(
                    f"Step {s['step_number']} ({s['step_type']}): {s['result']}"
                    for s in previous_steps
                )

            evidence_context = ""
            if evidence:
                evidence_context = "\nRelevant knowledge:\n" + "\n".join(f"- {e}" for e in evidence)

            system_prompt = """You are Angela's deep reasoning module. Think carefully and logically.
Your task is to perform one step of multi-step reasoning.
Be concise but thorough. Respond ONLY in valid JSON with keys:
- "result": string (your reasoning output for this step, 1-3 sentences)
- "confidence": float 0.0-1.0 (how confident you are)
- "key_insight": string (the most important takeaway from this step)"""

            user_msg = f"""Question: {question}
Step {step_number} ({step_type}): {thought}
{f"Previous reasoning chain:{chr(10)}{chain_context}" if chain_context else ""}
{evidence_context}"""

            llm_result = await self._call_ollama(system_prompt, user_msg, max_tokens=256)

            if llm_result:
                try:
                    parsed = json.loads(llm_result)
                    return {
                        "step_number": step_number,
                        "step_type": step_type,
                        "thought": thought,
                        "result": parsed.get("result", llm_result),
                        "confidence": min(1.0, max(0.0, float(parsed.get("confidence", 0.7)))),
                        "key_insight": parsed.get("key_insight", ""),
                        "evidence": evidence,
                        "model": REASONING_MODEL
                    }
                except (json.JSONDecodeError, ValueError):
                    # LLM returned plain text instead of JSON
                    return {
                        "step_number": step_number,
                        "step_type": step_type,
                        "thought": thought,
                        "result": llm_result.strip(),
                        "confidence": 0.6,
                        "evidence": evidence,
                        "model": REASONING_MODEL
                    }

            # Fallback: no LLM available
            return {
                "step_number": step_number,
                "step_type": step_type,
                "thought": thought,
                "result": f"[Ollama unavailable] Placeholder for {step_type}",
                "confidence": 0.3,
                "evidence": evidence,
                "model": "fallback"
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
        """Synthesize final conclusion from reasoning steps using Gemma 3 12B."""
        try:
            chain_summary = "\n".join(
                f"Step {s['step_number']} ({s['step_type']}): {s['result']}"
                for s in steps
            )

            system_prompt = """You are Angela's reasoning synthesis module.
Given a chain of reasoning steps, synthesize a clear, actionable conclusion.
Be concise (2-4 sentences). Focus on the answer, not the process.
If the question is in Thai, respond in Thai."""

            user_msg = f"""Question: {question}

Reasoning chain:
{chain_summary}

Synthesize the final conclusion:"""

            result = await self._call_ollama(system_prompt, user_msg, max_tokens=256)
            if result:
                return result.strip()

            # Fallback
            num_steps = len(steps)
            avg_confidence = sum(s.get("confidence", 0) for s in steps) / num_steps if num_steps > 0 else 0
            return f"Based on {num_steps} reasoning steps (avg confidence: {avg_confidence:.2f}): Analysis requires further review."

        except Exception as e:
            logger.error(f"Failed to synthesize conclusion: {e}")
            return f"Unable to reach conclusion: {str(e)}"


    async def _detect_cognitive_biases(
        self,
        steps: List[Dict],
        conclusion: str
    ) -> List[str]:
        """Detect cognitive biases using both heuristics and LLM analysis."""
        biases = []

        try:
            # Heuristic checks (fast, always available)
            confidences = [s.get("confidence", 0.5) for s in steps]
            if len(confidences) > 2:
                mean_conf = sum(confidences) / len(confidences)
                conf_variance = sum((c - mean_conf)**2 for c in confidences) / len(confidences)
                if conf_variance < 0.01:
                    biases.append("confirmation_bias: All steps have similar confidence")

            if len(steps) > 1:
                if steps[0].get("confidence", 0.5) > 0.9 and sum(confidences[1:]) / len(confidences[1:]) < 0.7:
                    biases.append("anchoring_bias: First step dominates reasoning")

            # LLM-powered bias detection (deeper analysis)
            chain_summary = "\n".join(
                f"Step {s['step_number']}: {s['result']} (confidence: {s.get('confidence', '?')})"
                for s in steps
            )
            system_prompt = """You are a cognitive bias detector. Analyze this reasoning chain for biases.
Respond ONLY in valid JSON with key "biases": list of strings.
Each bias should be "bias_name: brief explanation".
Common biases: confirmation, anchoring, availability, recency, framing, sunk_cost.
If no biases detected, return {"biases": []}."""

            user_msg = f"Reasoning chain:\n{chain_summary}\n\nConclusion: {conclusion}"
            result = await self._call_ollama(system_prompt, user_msg, max_tokens=256)
            if result:
                try:
                    parsed = json.loads(result)
                    llm_biases = parsed.get("biases", [])
                    biases.extend(b for b in llm_biases if b not in biases)
                except json.JSONDecodeError:
                    pass

            return biases

        except Exception as e:
            logger.error(f"Bias detection failed: {e}")
            return biases


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

            causal_steps = [
                (1, "identify_immediate_cause", "What directly caused this event?"),
                (2, "find_root_cause", "Why did the immediate cause happen? Keep asking 'why?' (5 Whys technique)"),
                (3, "analyze_effects", "What are the short-term and long-term consequences?"),
                (4, "identify_solutions", "How can we address the root cause? What actions would prevent recurrence?"),
            ]

            for step_num, step_type, thought in causal_steps:
                step = await self._reasoning_step(
                    step_number=step_num,
                    step_type=step_type,
                    thought=thought,
                    question=f"Causal analysis: {event}",
                    previous_steps=steps
                )
                steps.append(step)

            conclusion = await self._synthesize_conclusion(steps, f"Causal analysis: {event}")

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

            cf_steps = [
                (1, "analyze_current", f"Analyzing current state: {scenario}"),
                (2, "analyze_alternative", f"Analyzing alternative: {what_if}"),
                (3, "compare_trade_offs", "Comparing trade-offs: speed, quality, cost, risk"),
                (4, "recommend", "Which approach is better and why? What's the expected improvement?"),
            ]

            for step_num, step_type, thought in cf_steps:
                step = await self._reasoning_step(
                    step_number=step_num,
                    step_type=step_type,
                    thought=thought,
                    question=f"Current: {scenario} | What if: {what_if}",
                    previous_steps=steps
                )
                steps.append(step)

            conclusion = await self._synthesize_conclusion(steps, f"What if: {what_if}")

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

            existing_biases = json.loads(original['cognitive_biases_detected']) if original['cognitive_biases_detected'] else []
            original_confidence = original['confidence_in_conclusion'] or 0.5
            original_steps = json.loads(original['thought_steps']) if original['thought_steps'] else []

            # Build context about the original reasoning
            original_context = f"""Original question: {original['initial_query']}
Original conclusion: {original['final_conclusion']}
Original confidence: {original_confidence}
Biases detected: {', '.join(existing_biases) if existing_biases else 'None'}
Steps taken: {len(original_steps)}"""

            steps = []

            meta_step_defs = [
                (1, "assess_quality", f"Was this reasoning sound? Original: {original_context}"),
                (2, "identify_biases", f"What cognitive biases affected this? Known biases: {existing_biases}"),
                (3, "suggest_improvements", "How could this reasoning be improved? What was missed?"),
                (4, "adjust_confidence", f"Should confidence be adjusted from {original_confidence:.2f}? Up or down and why?"),
            ]

            for step_num, step_type, thought in meta_step_defs:
                step = await self._reasoning_step(
                    step_number=step_num,
                    step_type=step_type,
                    thought=thought,
                    question=f"Meta-analysis of: {original['initial_query']}",
                    previous_steps=steps
                )
                steps.append(step)

            # Extract adjusted confidence from LLM's step 4
            adjustment = -0.1 if len(existing_biases) > 0 else 0.0
            try:
                step4_result = steps[-1].get("result", "")
                import re
                conf_match = re.search(r'(\d\.\d+)', step4_result)
                if conf_match:
                    adjusted_confidence = min(1.0, max(0.0, float(conf_match.group(1))))
                else:
                    adjusted_confidence = max(0.0, min(1.0, original_confidence + adjustment))
            except (ValueError, IndexError):
                adjusted_confidence = max(0.0, min(1.0, original_confidence + adjustment))

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
