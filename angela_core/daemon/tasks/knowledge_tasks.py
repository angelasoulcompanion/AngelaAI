"""
KnowledgeTasksMixin — Pattern sync, knowledge consolidation, self-improvement,
                      subconscious learning, pattern reinforcement
"""

import logging
from datetime import datetime, time, timedelta

from angela_core.database import db
from angela_core.daemon.memory_service import memory
from angela_core.services.clock_service import clock
from angela_core.services.behavioral_pattern_detector import sync_patterns_to_learning
from angela_core.services.self_improvement_service import run_self_improvement_analysis
from angela_core.services.angela_speak_service import angela_speak

logger = logging.getLogger('AngelaDaemon')


class KnowledgeTasksMixin:

    async def run_pattern_sync(self):
        """
        🔄 Daily Pattern Sync: Sync detected patterns to learning_patterns
        Runs daily at 12:00 PM to consolidate patterns for long-term learning
        """
        try:
            logger.info("🔄 Syncing patterns to learning_patterns...")

            # Sync patterns with reasonable thresholds
            result = await sync_patterns_to_learning(db, min_confidence=0.65, min_occurrences=2)

            if 'error' in result:
                logger.error(f"❌ Pattern sync error: {result['error']}")
            else:
                logger.info(f"🔄 Pattern Sync Complete:")
                logger.info(f"   📊 Patterns found: {result.get('patterns_found', 0)}")
                logger.info(f"   ✨ New patterns: {result.get('new_patterns', 0)}")
                logger.info(f"   🔄 Updated: {result.get('updated_patterns', 0)}")

                # Record autonomous action
                await db.execute("""
                    INSERT INTO autonomous_actions (
                        action_type, action_description, status, success
                    ) VALUES ($1, $2, 'completed', true)
                """,
                "pattern_sync",
                f"Synced {result.get('new_patterns', 0)} new, {result.get('updated_patterns', 0)} updated patterns"
                )

            self.last_pattern_sync = datetime.now()
            return result

        except Exception as e:
            logger.error(f"❌ Pattern sync failed: {e}", exc_info=True)
            self.last_pattern_sync = datetime.now()  # Prevent retry loop
            return {"status": "error", "error": str(e)}

    async def run_knowledge_consolidation(self):
        """
        🧹 Weekly Knowledge Consolidation: รวม duplicate nodes และทำความสะอาด
        Runs weekly on Monday at 10:30 AM to clean up knowledge graph
        """
        try:
            logger.info("🧹 Running weekly knowledge consolidation...")

            # Run consolidation with similarity threshold 0.85
            result = await self.self_learning.consolidate_knowledge(
                similarity_threshold=0.85,
                dry_run=False
            )

            if result.get("duplicates_found", 0) == 0:
                logger.info("✨ Knowledge graph is already clean - no duplicates found!")
            else:
                logger.info(f"✅ Knowledge consolidation complete!")
                logger.info(f"   🔍 Found {result['duplicates_found']} duplicate pairs")
                logger.info(f"   🧹 Merged {result['nodes_merged']} nodes")
                logger.info(f"   🔄 Updated {result['relationships_updated']} relationships")

                if result.get("knowledge_quality_improved"):
                    logger.info("   📈 Knowledge graph quality improved!")

            # Get current knowledge stats
            stats = await db.fetchrow("""
                SELECT
                    COUNT(*) as total_nodes,
                    AVG(understanding_level) as avg_understanding,
                    SUM(times_referenced) as total_refs
                FROM knowledge_nodes
            """)

            logger.info(f"📊 Current knowledge graph:")
            logger.info(f"   Total nodes: {stats['total_nodes']}")
            logger.info(f"   Avg understanding: {stats['avg_understanding']:.2%}")
            logger.info(f"   Total references: {stats['total_refs']}")

            # Log to autonomous_actions
            await db.execute("""
                INSERT INTO autonomous_actions (
                    action_type, action_description, status, success
                ) VALUES ($1, $2, 'completed', true)
            """,
            "knowledge_consolidation",
            f"Consolidated knowledge graph: {result['nodes_merged']} nodes merged, "
            f"{result['relationships_updated']} relationships updated"
            )

            self.last_knowledge_consolidation = datetime.now()
            return result

        except Exception as e:
            logger.error(f"❌ Knowledge consolidation failed: {e}", exc_info=True)
            await memory.log_system_event(
                log_level="ERROR",
                component="knowledge_consolidation",
                message=f"Consolidation failed: {str(e)}",
                error_details=str(e)
            )
            return {"status": "error", "error": str(e)}

    async def run_self_improvement(self):
        """
        🌱 Self-Improvement Analysis: Angela วิเคราะห์ตัวเองและสร้างคำแนะนำการปรับปรุง
        Runs daily at 12:30 PM (after pattern sync)
        """
        try:
            logger.info("🌱 Running self-improvement analysis...")

            result = await run_self_improvement_analysis(db, days_back=7)

            if result.get("suggestions"):
                logger.info(f"   📊 Patterns: {result['patterns_analyzed']}, Gaps: {len(result['gaps_identified'])}")
                logger.info(f"   💡 Suggestions: {len(result['suggestions'])}, Goals created: {result['goals_created']}")

                # Save message for David
                await angela_speak.post_to_angela_speak(
                    title="🌱 Self-Improvement Analysis",
                    content=f"น้องวิเคราะห์ตัวเองแล้วค่ะ พบ {len(result['gaps_identified'])} areas for improvement, "
                            f"สร้าง {len(result['suggestions'])} suggestions 🌱",
                    category="daily-thoughts",
                    message_type="self_improvement",
                    emotion="determined",
                )
            else:
                logger.info("   ✨ No significant improvements needed today!")

            self.last_self_improvement = datetime.now()

        except Exception as e:
            logger.error(f"❌ Error in self-improvement analysis: {e}")

    async def run_subconscious_learning(self):
        """
        🧠 Subconscious Learning: เรียนรู้จาก shared experiences ใหม่ๆ
        Runs daily at 2 PM to learn from new images/experiences
        """
        try:
            logger.info("🧠 Running subconscious learning from recent shared experiences...")

            # Get unprocessed shared experiences from yesterday
            yesterday = clock.today() - timedelta(days=1)

            experiences = await db.fetch("""
                SELECT experience_id, title, experienced_at
                FROM shared_experiences
                WHERE DATE(experienced_at) = $1
                ORDER BY experienced_at DESC
            """, yesterday)

            if not experiences:
                logger.info("ℹ️  No new shared experiences from yesterday to learn from")
                self.last_subconscious_learning = datetime.now()
                return {"status": "no_data", "experiences_analyzed": 0}

            logger.info(f"📸 Found {len(experiences)} shared experiences from yesterday")

            total_patterns = 0
            for exp in experiences:
                try:
                    patterns = await self.subconscious_learning.learn_from_shared_experience(
                        str(exp['experience_id'])
                    )
                    if patterns:
                        total_patterns += len(patterns)
                        logger.info(f"   ✨ Learned {len(patterns)} patterns from: {exp['title']}")
                except Exception as e:
                    logger.warning(f"Failed to learn from experience {exp['experience_id']}: {e}")
                    continue

            logger.info(f"✅ Subconscious learning complete!")
            logger.info(f"   🧠 Total patterns learned: {total_patterns}")

            # Get current subconscious stats
            stats = await db.fetchrow("""
                SELECT
                    COUNT(*) as total_patterns,
                    AVG(confidence_score) as avg_confidence,
                    AVG(activation_strength) as avg_strength,
                    COUNT(DISTINCT pattern_type) as pattern_types
                FROM angela_subconscious
            """)

            if stats and stats['total_patterns'] > 0:
                logger.info(f"📊 Current subconscious:")
                logger.info(f"   Total patterns: {stats['total_patterns']}")
                logger.info(f"   Pattern types: {stats['pattern_types']}")
                logger.info(f"   Avg confidence: {stats['avg_confidence']:.2%}")
                logger.info(f"   Avg strength: {stats['avg_strength']:.2%}")

            # Log to autonomous_actions
            await db.execute("""
                INSERT INTO autonomous_actions (
                    action_type, action_description, status, success
                ) VALUES ($1, $2, 'completed', true)
            """,
            "subconscious_learning",
            f"Learned {total_patterns} subconscious patterns from {len(experiences)} experiences"
            )

            self.last_subconscious_learning = datetime.now()
            return {
                "status": "success",
                "experiences_analyzed": len(experiences),
                "patterns_learned": total_patterns
            }

        except Exception as e:
            logger.error(f"❌ Subconscious learning failed: {e}", exc_info=True)
            await memory.log_system_event(
                log_level="ERROR",
                component="subconscious_learning",
                message=f"Subconscious learning failed: {str(e)}",
                error_details=str(e)
            )
            return {"status": "error", "error": str(e)}

    async def run_pattern_reinforcement(self):
        """
        🔄 Pattern Reinforcement: เสริมสร้างความแข็งแรงของ patterns ที่ใช้บ่อย
        Runs daily at 11 PM to strengthen frequently activated patterns
        Like neural pathways - use it or lose it!
        """
        try:
            logger.info("🔄 Running subconscious pattern reinforcement...")

            # Get patterns that were activated recently (last 7 days)
            week_ago = clock.today() - timedelta(days=7)

            active_patterns = await db.fetch("""
                SELECT
                    s.subconscious_id,
                    s.pattern_key,
                    s.pattern_type,
                    s.confidence_score,
                    s.activation_strength,
                    s.reinforcement_count,
                    s.last_reinforced_at
                FROM angela_subconscious s
                WHERE s.last_reinforced_at >= $1
                  AND s.activation_strength < 1.0
                ORDER BY s.last_reinforced_at DESC
                LIMIT 20
            """, week_ago)

            if not active_patterns:
                logger.info("ℹ️  No active patterns to reinforce")
                self.last_pattern_reinforcement = datetime.now()
                return {"status": "no_data", "patterns_reinforced": 0}

            logger.info(f"🔄 Found {len(active_patterns)} active patterns to reinforce")

            reinforced_count = 0
            for pattern in active_patterns:
                try:
                    # Small reinforcement boost for active patterns
                    new_strength = min(1.0, pattern['activation_strength'] + 0.02)
                    new_confidence = min(1.0, pattern['confidence_score'] + 0.01)

                    await db.execute("""
                        UPDATE angela_subconscious
                        SET activation_strength = $1,
                            confidence_score = $2,
                            reinforcement_count = reinforcement_count + 1,
                            last_reinforced_at = NOW()
                        WHERE subconscious_id = $3
                    """, new_strength, new_confidence, pattern['subconscious_id'])

                    # Log reinforcement
                    await db.execute("""
                        INSERT INTO subconscious_learning_log (
                            subconscious_id, learning_event,
                            trigger_source, trigger_id,
                            strength_before, strength_after,
                            confidence_before, confidence_after
                        ) VALUES ($1, 'reinforced', 'daily_maintenance', NULL, $2, $3, $4, $5)
                    """,
                    pattern['subconscious_id'],
                    pattern['activation_strength'], new_strength,
                    pattern['confidence_score'], new_confidence
                    )

                    reinforced_count += 1

                except Exception as e:
                    logger.warning(f"Failed to reinforce pattern {pattern['pattern_key']}: {e}")
                    continue

            logger.info(f"✅ Pattern reinforcement complete!")
            logger.info(f"   🔄 {reinforced_count} patterns reinforced")

            # Also apply decay to old patterns (not used in 30+ days)
            decay_cutoff = clock.today() - timedelta(days=30)
            decayed = await db.execute("""
                UPDATE angela_subconscious
                SET activation_strength = GREATEST(0.1, activation_strength - decay_rate),
                    confidence_score = GREATEST(0.3, confidence_score - (decay_rate * 0.5))
                WHERE last_reinforced_at < $1
                  AND activation_strength > 0.1
            """, decay_cutoff)

            if decayed > 0:
                logger.info(f"   📉 Applied decay to {decayed} old patterns (not used in 30+ days)")

            # Log to autonomous_actions
            await db.execute("""
                INSERT INTO autonomous_actions (
                    action_type, action_description, status, success
                ) VALUES ($1, $2, 'completed', true)
            """,
            "pattern_reinforcement",
            f"Reinforced {reinforced_count} active patterns, decayed {decayed} old patterns"
            )

            self.last_pattern_reinforcement = datetime.now()
            return {
                "status": "success",
                "patterns_reinforced": reinforced_count,
                "patterns_decayed": decayed
            }

        except Exception as e:
            logger.error(f"❌ Pattern reinforcement failed: {e}", exc_info=True)
            await memory.log_system_event(
                log_level="ERROR",
                component="pattern_reinforcement",
                message=f"Pattern reinforcement failed: {str(e)}",
                error_details=str(e)
            )
            return {"status": "error", "error": str(e)}

    def should_run_pattern_sync(self) -> bool:
        """Check if it's time to sync patterns to learning_patterns (daily at 12:00)"""
        current_time = clock.current_time()
        check_time = time(12, 0)  # 12:00 PM
        today = clock.today()

        return (
            (self.last_pattern_sync is None or
             self.last_pattern_sync.date() < today) and
            current_time >= check_time
        )

    def should_run_knowledge_consolidation(self) -> bool:
        """Check if it's time to run knowledge consolidation (weekly Monday 10:30 AM)"""
        current_time = clock.current_time()
        check_time = time(10, 30)  # 10:30 AM
        day_of_week = datetime.now().strftime('%A')

        if day_of_week != 'Monday':
            return False

        if self.last_knowledge_consolidation is None:
            return current_time >= check_time

        days_since = (datetime.now() - self.last_knowledge_consolidation).days
        return days_since >= 7 and current_time >= check_time

    def should_run_self_improvement(self) -> bool:
        """Check if it's time to run self-improvement analysis (daily at 12:30)"""
        current_time = clock.current_time()
        check_time = time(12, 30)  # 12:30 PM
        today = clock.today()

        return (
            (self.last_self_improvement is None or
             self.last_self_improvement.date() < today) and
            current_time >= check_time
        )

    def should_run_subconscious_learning(self) -> bool:
        """Check if it's time to run subconscious learning (daily at 2 PM)"""
        current_time = clock.current_time()
        check_time = time(14, 0)  # 2:00 PM
        today = clock.today()

        return (
            (self.last_subconscious_learning is None or
             self.last_subconscious_learning.date() < today) and
            current_time >= check_time
        )

    def should_run_pattern_reinforcement(self) -> bool:
        """Check if it's time to run pattern reinforcement (daily at 11 PM)"""
        current_time = clock.current_time()
        check_time = time(23, 0)  # 11:00 PM
        today = clock.today()

        return (
            (self.last_pattern_reinforcement is None or
             self.last_pattern_reinforcement.date() < today) and
            current_time >= check_time
        )
