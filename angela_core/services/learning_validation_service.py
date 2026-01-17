#!/usr/bin/env python3
"""
💜 Learning Validation Service
Angela Intelligence Enhancement - Phase 1.3

Validates and improves learning over time by:
- Tracking which learnings are correct/incorrect
- Auto-adjusting confidence levels
- Learning from David's corrections
- Identifying patterns in learning failures

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │              LEARNING VALIDATION SERVICE                    │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │
    │  │  Correction  │   │  Feedback    │   │  Confidence  │   │
    │  │   Tracker    │   │   Analyzer   │   │  Adjuster    │   │
    │  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘   │
    │         │                  │                   │           │
    │         └──────────────────┼───────────────────┘           │
    │                            │                               │
    │                     ┌──────▼───────┐                       │
    │                     │  VALIDATION  │                       │
    │                     │     CORE     │                       │
    │                     └──────┬───────┘                       │
    │                            │                               │
    │              ┌─────────────┼─────────────┐                 │
    │              │             │             │                 │
    │         ┌────▼────┐  ┌─────▼─────┐  ┌───▼────┐            │
    │         │ Pattern │  │  Report   │  │ Alert  │            │
    │         │ Finder  │  │ Generator │  │ System │            │
    │         └─────────┘  └───────────┘  └────────┘            │
    └─────────────────────────────────────────────────────────────┘

Created: 2026-01-17
Author: น้อง Angela 💜
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from collections import defaultdict

from angela_core.database import db

logger = logging.getLogger(__name__)


class ValidationResult(Enum):
    """Results of learning validation."""
    CORRECT = "correct"           # Learning was accurate
    INCORRECT = "incorrect"       # Learning was wrong
    PARTIALLY_CORRECT = "partial" # Some parts right, some wrong
    UNVALIDATED = "unvalidated"   # Not yet validated
    OUTDATED = "outdated"         # Was correct but now outdated


class FeedbackType(Enum):
    """Types of feedback from David."""
    EXPLICIT_POSITIVE = "explicit_positive"   # "ดี!", "Good job!"
    EXPLICIT_NEGATIVE = "explicit_negative"   # "ผิดนะ", "That's wrong"
    IMPLICIT_POSITIVE = "implicit_positive"   # Using Angela's suggestion
    IMPLICIT_NEGATIVE = "implicit_negative"   # Ignoring or doing opposite
    CORRECTION = "correction"                 # Direct correction
    NO_FEEDBACK = "no_feedback"               # No feedback given


@dataclass
class LearningValidation:
    """Record of a learning validation."""
    validation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    learning_id: str = ""  # ID of the learning being validated
    learning_topic: str = ""
    learning_content: str = ""
    validation_result: ValidationResult = ValidationResult.UNVALIDATED
    feedback_type: FeedbackType = FeedbackType.NO_FEEDBACK
    confidence_before: float = 0.5
    confidence_after: float = 0.5
    david_feedback: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    validated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'validation_id': self.validation_id,
            'learning_id': self.learning_id,
            'learning_topic': self.learning_topic,
            'validation_result': self.validation_result.value,
            'feedback_type': self.feedback_type.value,
            'confidence_before': self.confidence_before,
            'confidence_after': self.confidence_after,
            'david_feedback': self.david_feedback,
            'validated_at': self.validated_at.isoformat()
        }


@dataclass
class ValidationStats:
    """Statistics about learning validation."""
    total_validations: int = 0
    correct_count: int = 0
    incorrect_count: int = 0
    partial_count: int = 0
    accuracy_rate: float = 0.0
    avg_confidence_change: float = 0.0
    most_corrected_topics: List[str] = field(default_factory=list)
    improvement_trend: str = "stable"  # improving, declining, stable

    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_validations': self.total_validations,
            'correct_count': self.correct_count,
            'incorrect_count': self.incorrect_count,
            'partial_count': self.partial_count,
            'accuracy_rate': self.accuracy_rate,
            'avg_confidence_change': self.avg_confidence_change,
            'most_corrected_topics': self.most_corrected_topics,
            'improvement_trend': self.improvement_trend
        }


class LearningValidationService:
    """
    Validates learning and adjusts confidence over time.

    This service helps Angela learn from mistakes by:
    1. Tracking which learnings are correct/incorrect
    2. Adjusting confidence based on validation results
    3. Identifying patterns in learning failures
    4. Generating improvement recommendations

    Usage:
        validator = LearningValidationService()

        # Record a validation
        await validator.validate_learning(
            learning_id="123",
            result=ValidationResult.CORRECT,
            feedback_type=FeedbackType.EXPLICIT_POSITIVE,
            david_feedback="Good job remembering that!"
        )

        # Get validation statistics
        stats = await validator.get_validation_stats(days=30)
    """

    # Confidence adjustment factors
    CONFIDENCE_ADJUSTMENTS = {
        ValidationResult.CORRECT: 0.05,           # Small increase
        ValidationResult.PARTIALLY_CORRECT: 0.0,  # No change
        ValidationResult.INCORRECT: -0.15,        # Larger decrease
        ValidationResult.OUTDATED: -0.05,         # Small decrease
    }

    def __init__(self):
        self.validation_history: List[LearningValidation] = []
        self.correction_patterns: Dict[str, int] = defaultdict(int)
        self._callbacks: List[callable] = []

        logger.info("💜 LearningValidationService initialized")

    async def validate_learning(
        self,
        learning_id: str,
        result: ValidationResult,
        feedback_type: FeedbackType = FeedbackType.NO_FEEDBACK,
        david_feedback: str = "",
        context: Optional[Dict] = None
    ) -> LearningValidation:
        """
        Validate a learning and adjust confidence.

        Args:
            learning_id: ID of the learning to validate
            result: Validation result
            feedback_type: Type of feedback received
            david_feedback: David's feedback text
            context: Additional context

        Returns:
            LearningValidation record
        """
        logger.info(f"📝 Validating learning {learning_id}: {result.value}")

        try:
            # Get current learning from database
            learning = await self._get_learning(learning_id)
            if not learning:
                logger.warning(f"Learning {learning_id} not found")
                return None

            confidence_before = learning.get('confidence_level', 0.5)

            # Calculate new confidence
            confidence_after = await self._calculate_new_confidence(
                confidence_before, result, feedback_type
            )

            # Create validation record
            validation = LearningValidation(
                learning_id=learning_id,
                learning_topic=learning.get('topic', 'unknown'),
                learning_content=learning.get('insight', '')[:200],
                validation_result=result,
                feedback_type=feedback_type,
                confidence_before=confidence_before,
                confidence_after=confidence_after,
                david_feedback=david_feedback,
                context=context or {}
            )

            # Update learning confidence in database
            await self._update_learning_confidence(learning_id, confidence_after)

            # Record validation
            await self._save_validation(validation)
            self.validation_history.append(validation)

            # Track correction patterns
            if result in [ValidationResult.INCORRECT, ValidationResult.PARTIALLY_CORRECT]:
                topic = learning.get('topic', 'unknown')
                self.correction_patterns[topic] += 1

            # Trigger callbacks
            await self._trigger_callbacks(validation)

            logger.info(
                f"✅ Validation complete: "
                f"confidence {confidence_before:.2f} → {confidence_after:.2f}"
            )

            return validation

        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            return None

    async def validate_from_correction(
        self,
        original_content: str,
        correction: str,
        learning_topic: Optional[str] = None
    ) -> LearningValidation:
        """
        Create validation from David's correction.

        When David corrects Angela, this finds and validates the relevant learning.

        Args:
            original_content: What Angela said that was wrong
            correction: What David said it should be
            learning_topic: Optional topic to narrow search

        Returns:
            LearningValidation record
        """
        logger.info("⚠️ Processing correction for validation")

        try:
            # Find related learning
            related_learning = await self._find_related_learning(
                original_content, learning_topic
            )

            if related_learning:
                # Validate as incorrect
                validation = await self.validate_learning(
                    learning_id=related_learning['learning_id'],
                    result=ValidationResult.INCORRECT,
                    feedback_type=FeedbackType.CORRECTION,
                    david_feedback=correction,
                    context={
                        'original': original_content,
                        'correction': correction
                    }
                )
            else:
                # Create new validation without linked learning
                validation = LearningValidation(
                    learning_topic=learning_topic or 'unknown',
                    learning_content=original_content[:200],
                    validation_result=ValidationResult.INCORRECT,
                    feedback_type=FeedbackType.CORRECTION,
                    david_feedback=correction,
                    context={
                        'original': original_content,
                        'correction': correction,
                        'no_linked_learning': True
                    }
                )

                await self._save_validation(validation)
                self.validation_history.append(validation)

            # Record correction for learning
            await self._save_correction_as_learning(original_content, correction)

            return validation

        except Exception as e:
            logger.error(f"❌ Correction validation failed: {e}")
            return None

    async def validate_from_feedback(
        self,
        feedback_text: str,
        recent_learning_ids: Optional[List[str]] = None
    ) -> List[LearningValidation]:
        """
        Validate learnings based on David's feedback.

        Analyzes feedback text to determine if it's positive/negative
        and validates recent learnings accordingly.

        Args:
            feedback_text: David's feedback
            recent_learning_ids: Optional list of recent learning IDs to validate

        Returns:
            List of LearningValidation records
        """
        logger.info("📝 Processing feedback for validation")

        validations = []

        try:
            # Detect feedback type
            feedback_type = self._detect_feedback_type(feedback_text)

            # Determine validation result
            if feedback_type in [FeedbackType.EXPLICIT_POSITIVE, FeedbackType.IMPLICIT_POSITIVE]:
                result = ValidationResult.CORRECT
            elif feedback_type in [FeedbackType.EXPLICIT_NEGATIVE, FeedbackType.IMPLICIT_NEGATIVE]:
                result = ValidationResult.INCORRECT
            elif feedback_type == FeedbackType.CORRECTION:
                result = ValidationResult.INCORRECT
            else:
                return validations  # No clear feedback

            # Get recent learnings if not provided
            if not recent_learning_ids:
                recent_learnings = await self._get_recent_learnings(limit=3)
                recent_learning_ids = [l['learning_id'] for l in recent_learnings]

            # Validate each learning
            for learning_id in recent_learning_ids:
                validation = await self.validate_learning(
                    learning_id=learning_id,
                    result=result,
                    feedback_type=feedback_type,
                    david_feedback=feedback_text
                )
                if validation:
                    validations.append(validation)

            return validations

        except Exception as e:
            logger.error(f"❌ Feedback validation failed: {e}")
            return validations

    async def get_validation_stats(self, days: int = 30) -> ValidationStats:
        """
        Get validation statistics over a period.

        Args:
            days: Number of days to analyze

        Returns:
            ValidationStats
        """
        try:
            cutoff = datetime.now() - timedelta(days=days)

            # Get validations from database
            rows = await db.fetch("""
                SELECT
                    validation_result,
                    confidence_before,
                    confidence_after,
                    learning_topic,
                    validated_at
                FROM learning_validations
                WHERE validated_at >= $1
                ORDER BY validated_at DESC
            """, cutoff)

            if not rows:
                # Try in-memory history
                recent = [v for v in self.validation_history if v.validated_at >= cutoff]
            else:
                recent = rows

            if not recent:
                return ValidationStats()

            # Calculate stats
            total = len(recent)
            correct = sum(1 for r in recent if self._get_result(r) == 'correct')
            incorrect = sum(1 for r in recent if self._get_result(r) == 'incorrect')
            partial = sum(1 for r in recent if self._get_result(r) == 'partial')

            # Calculate confidence changes
            confidence_changes = []
            for r in recent:
                before = self._get_confidence_before(r)
                after = self._get_confidence_after(r)
                confidence_changes.append(after - before)

            avg_change = sum(confidence_changes) / len(confidence_changes) if confidence_changes else 0

            # Find most corrected topics
            topic_corrections = defaultdict(int)
            for r in recent:
                result = self._get_result(r)
                if result in ['incorrect', 'partial']:
                    topic = self._get_topic(r)
                    topic_corrections[topic] += 1

            most_corrected = sorted(
                topic_corrections.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]

            # Calculate trend
            trend = self._calculate_trend(recent)

            stats = ValidationStats(
                total_validations=total,
                correct_count=correct,
                incorrect_count=incorrect,
                partial_count=partial,
                accuracy_rate=correct / total if total > 0 else 0,
                avg_confidence_change=avg_change,
                most_corrected_topics=[t[0] for t in most_corrected],
                improvement_trend=trend
            )

            return stats

        except Exception as e:
            logger.error(f"❌ Failed to get validation stats: {e}")
            return ValidationStats()

    async def get_improvement_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate recommendations for improving learning accuracy.

        Returns:
            List of recommendations
        """
        recommendations = []

        try:
            stats = await self.get_validation_stats(days=30)

            # Low accuracy recommendation
            if stats.accuracy_rate < 0.7:
                recommendations.append({
                    'type': 'low_accuracy',
                    'priority': 'high',
                    'message': f"Learning accuracy is {stats.accuracy_rate:.0%}. Focus on validation before applying.",
                    'action': 'Ask for confirmation when uncertain'
                })

            # Frequent correction topics
            if stats.most_corrected_topics:
                for topic in stats.most_corrected_topics[:3]:
                    recommendations.append({
                        'type': 'frequent_correction',
                        'priority': 'medium',
                        'message': f"Topic '{topic}' is frequently corrected",
                        'action': f"Review and update knowledge about {topic}"
                    })

            # Declining trend
            if stats.improvement_trend == 'declining':
                recommendations.append({
                    'type': 'declining_trend',
                    'priority': 'high',
                    'message': "Learning accuracy is declining over time",
                    'action': "Analyze recent failures and adjust learning approach"
                })

            # Negative confidence change
            if stats.avg_confidence_change < -0.05:
                recommendations.append({
                    'type': 'confidence_dropping',
                    'priority': 'medium',
                    'message': f"Average confidence change is {stats.avg_confidence_change:.2f}",
                    'action': "Be more conservative with confidence levels"
                })

            return recommendations

        except Exception as e:
            logger.error(f"❌ Failed to generate recommendations: {e}")
            return []

    # ========================================
    # INTERNAL METHODS
    # ========================================

    async def _calculate_new_confidence(
        self,
        current: float,
        result: ValidationResult,
        feedback_type: FeedbackType
    ) -> float:
        """Calculate new confidence level based on validation."""
        # Base adjustment from result
        adjustment = self.CONFIDENCE_ADJUSTMENTS.get(result, 0)

        # Modify based on feedback type
        if feedback_type == FeedbackType.EXPLICIT_POSITIVE:
            adjustment += 0.02  # Explicit feedback counts more
        elif feedback_type == FeedbackType.EXPLICIT_NEGATIVE:
            adjustment -= 0.03
        elif feedback_type == FeedbackType.CORRECTION:
            adjustment -= 0.05  # Corrections are clear signals

        # Apply adjustment with bounds
        new_confidence = max(0.1, min(1.0, current + adjustment))

        return new_confidence

    def _detect_feedback_type(self, text: str) -> FeedbackType:
        """Detect feedback type from text."""
        text_lower = text.lower()

        # Explicit positive markers
        positive_markers = ['ดี', 'เก่ง', 'ถูก', 'good', 'great', 'correct', 'right', 'thanks', 'perfect']
        if any(m in text_lower for m in positive_markers):
            return FeedbackType.EXPLICIT_POSITIVE

        # Explicit negative markers
        negative_markers = ['ผิด', 'ไม่ถูก', 'ไม่ใช่', 'wrong', 'incorrect', 'no,', 'nope']
        if any(m in text_lower for m in negative_markers):
            return FeedbackType.EXPLICIT_NEGATIVE

        # Correction markers
        correction_markers = ['actually', 'จริงๆ', 'should be', 'ควรจะ', 'not', 'but']
        if any(m in text_lower for m in correction_markers):
            return FeedbackType.CORRECTION

        return FeedbackType.NO_FEEDBACK

    def _calculate_trend(self, validations: List) -> str:
        """Calculate improvement trend from validations."""
        if len(validations) < 10:
            return "insufficient_data"

        # Split into first and second half
        mid = len(validations) // 2
        first_half = validations[mid:]  # Older
        second_half = validations[:mid]  # Newer

        # Calculate accuracy for each half
        first_accuracy = sum(1 for v in first_half if self._get_result(v) == 'correct') / len(first_half)
        second_accuracy = sum(1 for v in second_half if self._get_result(v) == 'correct') / len(second_half)

        diff = second_accuracy - first_accuracy

        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "declining"
        else:
            return "stable"

    def _get_result(self, row) -> str:
        """Get validation result from row or object."""
        if isinstance(row, LearningValidation):
            return row.validation_result.value
        return row.get('validation_result', 'unvalidated')

    def _get_confidence_before(self, row) -> float:
        """Get confidence_before from row or object."""
        if isinstance(row, LearningValidation):
            return row.confidence_before
        return row.get('confidence_before', 0.5)

    def _get_confidence_after(self, row) -> float:
        """Get confidence_after from row or object."""
        if isinstance(row, LearningValidation):
            return row.confidence_after
        return row.get('confidence_after', 0.5)

    def _get_topic(self, row) -> str:
        """Get learning topic from row or object."""
        if isinstance(row, LearningValidation):
            return row.learning_topic
        return row.get('learning_topic', 'unknown')

    async def _get_learning(self, learning_id: str) -> Optional[Dict]:
        """Get learning from database."""
        try:
            # Try as UUID first
            try:
                learning_uuid = uuid.UUID(learning_id)
                row = await db.fetchrow("""
                    SELECT learning_id, topic, insight, confidence_level
                    FROM learnings
                    WHERE learning_id = $1
                """, learning_uuid)
            except ValueError:
                # Not a UUID, try as string topic
                row = await db.fetchrow("""
                    SELECT learning_id, topic, insight, confidence_level
                    FROM learnings
                    WHERE topic = $1
                    ORDER BY created_at DESC
                    LIMIT 1
                """, learning_id)

            return dict(row) if row else None

        except Exception as e:
            logger.error(f"Failed to get learning: {e}")
            return None

    async def _find_related_learning(
        self,
        content: str,
        topic: Optional[str]
    ) -> Optional[Dict]:
        """Find learning related to content."""
        try:
            if topic:
                row = await db.fetchrow("""
                    SELECT learning_id, topic, insight, confidence_level
                    FROM learnings
                    WHERE topic ILIKE $1
                    ORDER BY created_at DESC
                    LIMIT 1
                """, f"%{topic}%")
            else:
                # Search by content similarity (simple keyword match)
                keywords = content.lower().split()[:5]
                for keyword in keywords:
                    if len(keyword) > 3:
                        row = await db.fetchrow("""
                            SELECT learning_id, topic, insight, confidence_level
                            FROM learnings
                            WHERE LOWER(insight) LIKE $1
                            ORDER BY created_at DESC
                            LIMIT 1
                        """, f"%{keyword}%")
                        if row:
                            return dict(row)
                return None

            return dict(row) if row else None

        except Exception as e:
            logger.error(f"Failed to find related learning: {e}")
            return None

    async def _get_recent_learnings(self, limit: int = 5) -> List[Dict]:
        """Get recent learnings."""
        try:
            rows = await db.fetch("""
                SELECT learning_id, topic, insight, confidence_level
                FROM learnings
                ORDER BY created_at DESC
                LIMIT $1
            """, limit)

            return [dict(r) for r in rows]

        except Exception as e:
            logger.error(f"Failed to get recent learnings: {e}")
            return []

    async def _update_learning_confidence(
        self,
        learning_id: str,
        new_confidence: float
    ) -> None:
        """Update learning confidence in database."""
        try:
            await db.execute("""
                UPDATE learnings
                SET confidence_level = $1,
                    times_reinforced = times_reinforced + 1
                WHERE learning_id = $2
            """, new_confidence, uuid.UUID(learning_id))

        except Exception as e:
            logger.error(f"Failed to update confidence: {e}")

    async def _save_validation(self, validation: LearningValidation) -> None:
        """Save validation to database."""
        try:
            # Try to create table if not exists
            await db.execute("""
                CREATE TABLE IF NOT EXISTS learning_validations (
                    validation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    learning_id VARCHAR(36),
                    learning_topic VARCHAR(200),
                    learning_content TEXT,
                    validation_result VARCHAR(50),
                    feedback_type VARCHAR(50),
                    confidence_before DECIMAL(3,2),
                    confidence_after DECIMAL(3,2),
                    david_feedback TEXT,
                    context JSONB,
                    validated_at TIMESTAMP DEFAULT NOW()
                )
            """)

            await db.execute("""
                INSERT INTO learning_validations (
                    validation_id, learning_id, learning_topic,
                    learning_content, validation_result, feedback_type,
                    confidence_before, confidence_after, david_feedback,
                    context, validated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
                uuid.UUID(validation.validation_id),
                validation.learning_id or None,
                validation.learning_topic,
                validation.learning_content,
                validation.validation_result.value,
                validation.feedback_type.value,
                validation.confidence_before,
                validation.confidence_after,
                validation.david_feedback,
                json.dumps(validation.context),
                validation.validated_at
            )

        except Exception as e:
            logger.error(f"Failed to save validation: {e}")

    async def _save_correction_as_learning(
        self,
        original: str,
        correction: str
    ) -> None:
        """Save correction as new learning."""
        try:
            await db.execute("""
                INSERT INTO learnings (
                    topic, category, insight,
                    confidence_level, source, created_at
                ) VALUES ($1, $2, $3, $4, $5, NOW())
            """,
                "correction_learned",
                "correction",
                f"WRONG: {original[:200]}... CORRECT: {correction[:200]}",
                1.0,  # High confidence for corrections
                "david_correction"
            )

        except Exception as e:
            logger.error(f"Failed to save correction as learning: {e}")

    async def _trigger_callbacks(self, validation: LearningValidation) -> None:
        """Trigger registered callbacks."""
        for callback in self._callbacks:
            try:
                await callback(validation)
            except Exception as e:
                logger.error(f"Callback failed: {e}")

    def register_callback(self, callback: callable) -> None:
        """Register a callback for validation events."""
        self._callbacks.append(callback)
        logger.info("📝 Validation callback registered")


# Global instance
learning_validator = LearningValidationService()


# ========================================
# CONVENIENCE FUNCTIONS
# ========================================

async def validate_learning(
    learning_id: str,
    result: str,  # 'correct', 'incorrect', 'partial'
    feedback: str = ""
) -> Optional[LearningValidation]:
    """
    Convenience function to validate a learning.

    Usage:
        from angela_core.services.learning_validation_service import validate_learning

        await validate_learning("learning-123", "correct", "Good job!")
    """
    result_map = {
        'correct': ValidationResult.CORRECT,
        'incorrect': ValidationResult.INCORRECT,
        'partial': ValidationResult.PARTIALLY_CORRECT
    }

    return await learning_validator.validate_learning(
        learning_id=learning_id,
        result=result_map.get(result, ValidationResult.UNVALIDATED),
        david_feedback=feedback
    )


async def process_correction(original: str, correction: str) -> Optional[LearningValidation]:
    """
    Convenience function to process a correction.

    Usage:
        from angela_core.services.learning_validation_service import process_correction

        await process_correction(
            original="Python 4 is the latest version",
            correction="Python 3 is the latest stable version"
        )
    """
    return await learning_validator.validate_from_correction(
        original_content=original,
        correction=correction
    )


async def get_learning_accuracy() -> float:
    """Get current learning accuracy rate."""
    stats = await learning_validator.get_validation_stats(days=30)
    return stats.accuracy_rate


# ========================================
# TESTING
# ========================================

if __name__ == "__main__":
    async def test():
        print("💜 Testing LearningValidationService...\n")

        await db.connect()

        # Test validation
        print("1. Testing learning validation...")
        # This would need a real learning_id from the database

        # Test stats
        print("\n2. Getting validation stats...")
        stats = await learning_validator.get_validation_stats(days=30)
        print(f"   Total validations: {stats.total_validations}")
        print(f"   Accuracy rate: {stats.accuracy_rate:.0%}")
        print(f"   Trend: {stats.improvement_trend}")

        # Test recommendations
        print("\n3. Getting recommendations...")
        recommendations = await learning_validator.get_improvement_recommendations()
        for rec in recommendations:
            print(f"   [{rec['priority']}] {rec['message']}")

        await db.disconnect()
        print("\n✅ LearningValidationService test complete!")

    asyncio.run(test())
