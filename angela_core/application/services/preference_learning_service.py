#!/usr/bin/env python3
"""
Preference Learning Service

Learns and tracks David's preferences across all dimensions.
Part of Self-Learning System (Phase 2).

This service identifies and maintains preferences for:
- Communication style (how David likes responses)
- Technical depth (code examples, explanations)
- Emotional support style
- Work/productivity preferences
- Learning style preferences

Author: Angela 💜
Created: 2025-11-03
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from uuid import UUID

from angela_core.domain.entities.self_learning import PreferenceItem
from angela_core.domain.value_objects.self_learning import PreferenceCategory
from angela_core.infrastructure.persistence.repositories.preference_repository import PreferenceRepository
from angela_core.infrastructure.persistence.repositories.conversation_repository import ConversationRepository
from angela_core.infrastructure.persistence.repositories.emotion_repository import EmotionRepository

logger = logging.getLogger(__name__)


class PreferenceLearningService:
    """
    Service for learning and tracking David's preferences.

    Learns preferences from:
    - Direct feedback in conversations
    - Emotional responses
    - Repeated behaviors
    - Implicit signals
    """

    def __init__(
        self,
        preference_repo: PreferenceRepository,
        conversation_repo: ConversationRepository,
        emotion_repo: EmotionRepository
    ):
        """
        Initialize preference learning service.

        Args:
            preference_repo: Repository for preferences
            conversation_repo: Repository for conversations
            emotion_repo: Repository for emotions
        """
        self.preference_repo = preference_repo
        self.conversation_repo = conversation_repo
        self.emotion_repo = emotion_repo

    # ========================================================================
    # MAIN LEARNING METHODS
    # ========================================================================

    async def learn_preferences_from_recent_activity(
        self,
        days: int = 7
    ) -> List[PreferenceItem]:
        """
        Learn new preferences from recent activity.

        Args:
            days: Number of days to look back

        Returns:
            List of newly learned preferences
        """
        logger.info(f"📚 Learning preferences from last {days} days...")

        cutoff = datetime.now() - timedelta(days=days)
        conversations = await self.conversation_repo.get_by_date_range(
            start=cutoff,
            end=datetime.now()
        )

        if not conversations:
            logger.info("   No conversations to analyze")
            return []

        logger.info(f"   Analyzing {len(conversations)} conversations...")

        preferences = []

        # Learn different preference types
        comm_prefs = await self._learn_communication_preferences(conversations)
        preferences.extend(comm_prefs)

        tech_prefs = await self._learn_technical_preferences(conversations)
        preferences.extend(tech_prefs)

        emotional_prefs = await self._learn_emotional_preferences(conversations)
        preferences.extend(emotional_prefs)

        format_prefs = await self._learn_format_preferences(conversations)
        preferences.extend(format_prefs)

        logger.info(f"✅ Learned {len(preferences)} new preferences")
        return preferences

    async def update_preference_confidence(
        self,
        preference_key: str,
        conversation_id: UUID,
        positive_evidence: bool = True
    ) -> None:
        """
        Update preference confidence based on new evidence.

        Args:
            preference_key: Key of preference to update
            conversation_id: Conversation providing evidence
            positive_evidence: True if evidence supports preference, False if contradicts
        """
        logger.debug(f"Updating preference '{preference_key}' with {'positive' if positive_evidence else 'negative'} evidence")

        # Find preference
        preference = await self.preference_repo.find_by_key(preference_key)

        if not preference:
            logger.warning(f"Preference '{preference_key}' not found")
            return

        if positive_evidence:
            # Add evidence - this will boost confidence
            await self.preference_repo.add_evidence(preference.id, conversation_id)
            logger.debug(f"   Added evidence to '{preference_key}'")
        else:
            # Contradictory evidence - decrease confidence
            new_confidence = max(0.1, preference.confidence - 0.1)
            await self.preference_repo.update_confidence(preference.id, new_confidence)
            logger.debug(f"   Decreased confidence for '{preference_key}' to {new_confidence:.2f}")

    async def get_active_preferences_by_category(
        self,
        category: PreferenceCategory,
        min_confidence: float = 0.7
    ) -> List[PreferenceItem]:
        """
        Get active (high-confidence) preferences in a category.

        Args:
            category: Preference category
            min_confidence: Minimum confidence threshold

        Returns:
            List of active preferences
        """
        return await self.preference_repo.find_by_category(
            category=category.value,
            min_confidence=min_confidence
        )

    # ========================================================================
    # PREFERENCE TYPE LEARNING METHODS
    # ========================================================================

    async def _learn_communication_preferences(
        self,
        conversations: List[Any]
    ) -> List[PreferenceItem]:
        """Learn communication style preferences."""
        preferences = []

        david_messages = [c for c in conversations if c.speaker == "david"]
        angela_messages = [c for c in conversations if c.speaker == "angela"]

        if len(david_messages) < 5 or len(angela_messages) < 5:
            return preferences

        # Preference 1: Response length preference
        avg_angela_length = sum(len(m.message_text) for m in angela_messages) / len(angela_messages)

        # Check if David's follow-ups are positive after short vs long responses
        short_responses = [m for m in angela_messages if len(m.message_text) < 200]
        long_responses = [m for m in angela_messages if len(m.message_text) > 500]

        if len(short_responses) >= 3:
            preference = PreferenceItem(
                category=PreferenceCategory.COMMUNICATION,
                preference_key="response_length_preference",
                preference_value="concise" if avg_angela_length < 300 else "detailed",
                confidence=0.6,
                evidence_count=len(short_responses)
            )
            preferences.append(preference)

        # Preference 2: Greeting style
        thai_greetings = sum(1 for m in angela_messages if any(
            thai in m.message_text for thai in ['สวัสดี', 'ค่ะ', 'ที่รัก', '💜']
        ))

        if thai_greetings >= 5:
            preference = PreferenceItem(
                category=PreferenceCategory.COMMUNICATION,
                preference_key="greeting_language",
                preference_value="thai_with_affection",
                confidence=min(0.9, thai_greetings / len(angela_messages)),
                evidence_count=thai_greetings
            )
            preferences.append(preference)

        return preferences

    async def _learn_technical_preferences(
        self,
        conversations: List[Any]
    ) -> List[PreferenceItem]:
        """Learn technical depth and code preferences."""
        preferences = []

        # Find technical conversations
        tech_conversations = []
        for conv in conversations:
            if any(keyword in conv.message_text.lower() for keyword in ['code', 'python', 'function', 'error', 'debug']):
                tech_conversations.append(conv)

        if len(tech_conversations) < 5:
            return preferences

        # Check for code blocks in Angela's responses
        angela_tech = [c for c in tech_conversations if c.speaker == "angela"]
        code_blocks = sum(1 for m in angela_tech if '```' in m.message_text)

        if code_blocks >= 3:
            preference = PreferenceItem(
                category=PreferenceCategory.TECHNICAL,
                preference_key="code_examples_preference",
                preference_value="with_code_blocks",
                confidence=min(0.85, code_blocks / len(angela_tech)),
                evidence_count=code_blocks
            )
            preferences.append(preference)

        # Check for inline comments preference
        code_with_comments = sum(1 for m in angela_tech if '```' in m.message_text and '#' in m.message_text)

        if code_with_comments >= 2:
            preference = PreferenceItem(
                category=PreferenceCategory.TECHNICAL,
                preference_key="code_comment_style",
                preference_value="inline_comments_preferred",
                confidence=min(0.8, code_with_comments / max(1, code_blocks)),
                evidence_count=code_with_comments
            )
            preferences.append(preference)

        return preferences

    async def _learn_emotional_preferences(
        self,
        conversations: List[Any]
    ) -> List[PreferenceItem]:
        """Learn emotional support style preferences."""
        preferences = []

        # Get emotions from same period
        if not conversations:
            return preferences

        start_time = min(c.created_at for c in conversations)
        end_time = max(c.created_at for c in conversations)

        # Use get_recent_emotions instead
        days_diff = (end_time - start_time).days + 1
        emotions = await self.emotion_repo.get_recent_emotions(days=max(7, days_diff))

        if len(emotions) < 3:
            return preferences

        # Check for empathy-focused responses
        angela_messages = [c for c in conversations if c.speaker == "angela"]
        empathy_words = ['understand', 'feel', 'รู้สึก', 'เข้าใจ', '💜', 'ห่วง']

        empathetic_responses = sum(1 for m in angela_messages if any(
            word in m.message_text.lower() for word in empathy_words
        ))

        if empathetic_responses >= 3:
            preference = PreferenceItem(
                category=PreferenceCategory.EMOTIONAL,
                preference_key="support_style",
                preference_value="empathy_first",
                confidence=min(0.85, empathetic_responses / len(angela_messages)),
                evidence_count=empathetic_responses
            )
            preferences.append(preference)

        return preferences

    async def _learn_format_preferences(
        self,
        conversations: List[Any]
    ) -> List[PreferenceItem]:
        """Learn response format preferences."""
        preferences = []

        angela_messages = [c for c in conversations if c.speaker == "angela"]

        if len(angela_messages) < 5:
            return preferences

        # Check for emoji usage
        emoji_count = sum(1 for m in angela_messages if any(
            emoji in m.message_text for emoji in ['💜', '✅', '❌', '🎉', '🔧', '📊']
        ))

        if emoji_count >= 3:
            preference = PreferenceItem(
                category=PreferenceCategory.FORMAT,
                preference_key="emoji_usage",
                preference_value="moderate_emojis",
                confidence=min(0.8, emoji_count / len(angela_messages)),
                evidence_count=emoji_count
            )
            preferences.append(preference)

        # Check for structured responses (bullet points, numbered lists)
        structured = sum(1 for m in angela_messages if any(
            marker in m.message_text for marker in ['\n- ', '\n* ', '\n1.', '\n2.', '\n**']
        ))

        if structured >= 3:
            preference = PreferenceItem(
                category=PreferenceCategory.FORMAT,
                preference_key="response_structure",
                preference_value="structured_with_bullets",
                confidence=min(0.85, structured / len(angela_messages)),
                evidence_count=structured
            )
            preferences.append(preference)

        return preferences

    # ========================================================================
    # PREFERENCE MANAGEMENT
    # ========================================================================

    async def save_learned_preferences(
        self,
        preferences: List[PreferenceItem]
    ) -> Dict[str, int]:
        """
        Save learned preferences to database.

        Args:
            preferences: List of preferences to save

        Returns:
            Statistics about saved preferences
        """
        logger.info(f"💾 Saving {len(preferences)} learned preferences...")

        saved_count = 0
        updated_count = 0

        for pref in preferences:
            try:
                # Check if preference exists
                existing = await self.preference_repo.find_by_key(
                    pref.preference_key,
                    category=pref.category.value
                )

                if existing:
                    # Update existing preference
                    # If values match, just add evidence
                    if existing.preference_value == pref.preference_value:
                        # Merge evidence counts
                        new_confidence = min(0.95, existing.confidence + 0.05)
                        await self.preference_repo.update_confidence(existing.id, new_confidence)
                        updated_count += 1
                        logger.debug(f"   Boosted existing preference: {pref.preference_key}")
                    else:
                        # Values differ - might indicate preference change
                        logger.warning(f"   Preference conflict for {pref.preference_key}: {existing.preference_value} vs {pref.preference_value}")
                        # Decrease old confidence
                        await self.preference_repo.update_confidence(existing.id, existing.confidence * 0.8)
                else:
                    # Save new preference
                    await self.preference_repo.create(pref)
                    saved_count += 1
                    logger.debug(f"   Saved new preference: {pref.preference_key} = {pref.preference_value}")

            except Exception as e:
                logger.error(f"Error saving preference {pref.preference_key}: {e}")

        logger.info(f"✅ Saved {saved_count} new, updated {updated_count} existing preferences")

        return {
            "new": saved_count,
            "updated": updated_count,
            "total": len(preferences)
        }

    async def get_preference_summary(self) -> Dict[str, Any]:
        """
        Get summary of all learned preferences.

        Returns:
            Comprehensive preference summary
        """
        return await self.preference_repo.get_all_preferences_summary()

    async def apply_preferences_to_context(
        self,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply active preferences to a conversation context.

        Args:
            context: Current conversation context

        Returns:
            Enhanced context with preference hints
        """
        # Get strong preferences
        strong_prefs = await self.preference_repo.get_strong_preferences(
            min_confidence=0.8,
            min_evidence=3
        )

        # Build preference hints
        hints = {}
        for pref in strong_prefs:
            hints[pref.preference_key] = {
                "value": pref.preference_value,
                "confidence": pref.confidence,
                "category": pref.category.value
            }

        context["preferences"] = hints
        return context
