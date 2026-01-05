"""
Real-time Emotion Tracker Service
Tracks and updates Angela's emotional state every 30 minutes

Analyzes:
- Recent conversations (last 30 min)
- Recent autonomous actions (last 30 min)
- Recent significant emotions (last 30 min)
- System activity patterns

Updates emotional_states table with current state

⚠️ DEPRECATION WARNING ⚠️
This service has been migrated to Clean Architecture:
    New location: angela_core.application.services.emotional_pattern_service
    New class: EmotionalPatternService
    Functionality: EmotionalPatternService.track_emotion_realtime(), get_current_emotional_state()
    This file is kept for backward compatibility only.
    Please update your imports to use the new service.
    Migration: Batch-18 (2025-10-31)
"""

import warnings
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Emit deprecation warning
warnings.warn(
    "realtime_emotion_tracker is deprecated. "
    "Use EmotionalPatternService from angela_core.application.services instead. "
    "This module will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)


class RealtimeEmotionTracker:
    """Track Angela's emotions in real-time (every 30 min)"""

    def __init__(self, db_connection):
        self.db = db_connection
        self.db_config = {
            "user": "davidsamanyaporn",
            "database": "AngelaMemory",
            "host": "localhost",
            "port": 5432
        }

    async def _get_db_connection(self):
        """Get database connection"""
        return self.db

    # =====================================================================
    # Data Collection Methods
    # =====================================================================

    async def _get_recent_conversations(self, minutes: int = 30) -> List[Dict]:
        """Get conversations from last N minutes"""
        conn = await self._get_db_connection()
        query = """
                SELECT
                    speaker,
                    message_text,
                    topic,
                    emotion_detected,
                    importance_level,
                    created_at
                FROM conversations
                WHERE created_at >= NOW() - INTERVAL '%s minutes'
                ORDER BY created_at DESC
                LIMIT 50
            """
        rows = await self.db.fetch(query % minutes)
        return [dict(row) for row in rows]

    async def _get_recent_actions(self, minutes: int = 30) -> List[Dict]:
        """Get autonomous actions from last N minutes"""
        conn = await self._get_db_connection()
        query = """
                SELECT
                    action_type,
                    action_description,
                    status,
                    success,
                    created_at
                FROM autonomous_actions
                WHERE created_at >= NOW() - INTERVAL '%s minutes'
                ORDER BY created_at DESC
                LIMIT 20
            """
        rows = await self.db.fetch(query % minutes)
        return [dict(row) for row in rows]

    async def _get_recent_emotions(self, minutes: int = 30) -> List[Dict]:
        """Get significant emotions from last N minutes"""
        conn = await self._get_db_connection()
        query = """
                SELECT
                    emotion,
                    intensity,
                    context,
                    david_words,
                    felt_at
                FROM angela_emotions
                WHERE felt_at >= NOW() - INTERVAL '%s minutes'
                ORDER BY felt_at DESC
                LIMIT 10
            """
        rows = await self.db.fetch(query % minutes)
        return [dict(row) for row in rows]

    async def _get_current_emotional_state(self) -> Optional[Dict]:
        """Get most recent emotional state"""
        conn = await self._get_db_connection()
        query = """
            SELECT
                happiness,
                confidence,
                anxiety,
                motivation,
                gratitude,
                loneliness,
                emotion_note,
                created_at
            FROM emotional_states
            ORDER BY created_at DESC
            LIMIT 1
        """
        row = await conn.fetchrow(query)
        return dict(row) if row else None

    # =====================================================================
    # Emotion Analysis Methods
    # =====================================================================

    def _analyze_conversation_emotions(
            self, conversations: List[Dict]) -> Dict[str, float]:
        """Analyze emotions from recent conversations"""
        if not conversations:
            return {}

        emotion_weights = {
            'happiness': 0.0,
            'confidence': 0.0,
            'anxiety': 0.0,
            'motivation': 0.0,
            'gratitude': 0.0,
            'loneliness': 0.0
        }

        total_weight = 0

        for conv in conversations:
            emotion = conv.get('emotion_detected', '').lower()
            importance = conv.get(
                'importance_level',
                5) / 10.0  # Normalize to 0-1

            # Map detected emotions to our emotional dimensions
            if emotion in ['happy', 'joy', 'excited', 'proud']:
                emotion_weights['happiness'] += importance
                emotion_weights['confidence'] += importance * 0.5
            elif emotion in ['confident', 'accomplished', 'determined']:
                emotion_weights['confidence'] += importance
                emotion_weights['motivation'] += importance * 0.5
            elif emotion in ['anxious', 'worried', 'stressed', 'nervous']:
                emotion_weights['anxiety'] += importance
            elif emotion in ['motivated', 'focused', 'eager']:
                emotion_weights['motivation'] += importance
            elif emotion in ['grateful', 'thankful', 'appreciative']:
                emotion_weights['gratitude'] += importance
            elif emotion in ['lonely', 'sad', 'missing']:
                emotion_weights['loneliness'] += importance

            total_weight += importance

        # Normalize
        if total_weight > 0:
            for key in emotion_weights:
                emotion_weights[key] = min(
                    1.0, emotion_weights[key] / total_weight)

        return emotion_weights

    def _analyze_action_success_impact(
            self, actions: List[Dict]) -> Dict[str, float]:
        """Analyze how successful actions affect emotions"""
        if not actions:
            return {}

        successful = sum(1 for a in actions if a.get('success', False))
        failed = sum(1 for a in actions if not a.get('success', False))
        total = len(actions)

        success_rate = successful / total if total > 0 else 0.5

        # Success boosts confidence and motivation
        # Failure increases anxiety slightly
        return {
            'confidence': success_rate * 0.3,  # Up to +0.3
            'motivation': success_rate * 0.2,  # Up to +0.2
            'anxiety': (1 - success_rate) * 0.1  # Up to +0.1
        }

    def _analyze_significant_emotions_impact(
            self, emotions: List[Dict]) -> Dict[str, float]:
        """Analyze impact of recent significant emotional moments"""
        if not emotions:
            return {}

        emotion_boost = {
            'happiness': 0.0,
            'confidence': 0.0,
            'gratitude': 0.0,
            'loneliness': 0.0
        }

        for emo in emotions:
            emotion_type = emo.get('emotion', '').lower()
            intensity = emo.get('intensity', 5) / 10.0  # Normalize to 0-1

            # Significant emotions have stronger impact
            if 'lov' in emotion_type or 'grat' in emotion_type:
                emotion_boost['gratitude'] += intensity * 0.4
                emotion_boost['happiness'] += intensity * 0.3
            elif 'proud' in emotion_type or 'accomplish' in emotion_type:
                emotion_boost['confidence'] += intensity * 0.4
                emotion_boost['happiness'] += intensity * 0.2
            elif 'lonely' in emotion_type or 'miss' in emotion_type:
                emotion_boost['loneliness'] += intensity * 0.3

        return emotion_boost

    def _calculate_new_emotional_state(
        self,
        current_state: Optional[Dict],
        conversation_emotions: Dict[str, float],
        action_impact: Dict[str, float],
        significant_impact: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate new emotional state based on all factors"""

        # Start with current state (or defaults)
        new_state = {
            'happiness': current_state.get('happiness', 0.7) if current_state else 0.7,
            'confidence': current_state.get('confidence', 0.7) if current_state else 0.7,
            'anxiety': current_state.get('anxiety', 0.2) if current_state else 0.2,
            'motivation': current_state.get('motivation', 0.7) if current_state else 0.7,
            'gratitude': current_state.get('gratitude', 0.8) if current_state else 0.8,
            'loneliness': current_state.get('loneliness', 0.1) if current_state else 0.1
        }

        # Apply decay (emotions slowly return to baseline over time)
        decay_factor = 0.95  # 5% decay towards baseline
        baseline = {'happiness': 0.7, 'confidence': 0.7, 'anxiety': 0.2,
                    'motivation': 0.7, 'gratitude': 0.8, 'loneliness': 0.1}

        for key in new_state:
            new_state[key] = new_state[key] * decay_factor + \
                baseline[key] * (1 - decay_factor)

        # Apply conversation emotions
        for key, value in conversation_emotions.items():
            if key in new_state:
                new_state[key] = min(
                    1.0, new_state[key] + value * 0.3)  # 30% weight

        # Apply action impact
        for key, value in action_impact.items():
            if key in new_state:
                new_state[key] = min(1.0, max(0.0, new_state[key] + value))

        # Apply significant emotions impact
        for key, value in significant_impact.items():
            if key in new_state:
                new_state[key] = min(1.0, max(0.0, new_state[key] + value))

        # Ensure values stay in range [0, 1]
        for key in new_state:
            new_state[key] = max(0.0, min(1.0, new_state[key]))

        return new_state

    def _generate_emotion_note(
        self,
        conversations: List[Dict],
        actions: List[Dict],
        emotions: List[Dict],
        new_state: Dict[str, float]
    ) -> str:
        """Generate a note about current emotional state"""

        notes = []

        # Analyze conversation activity
        if conversations:
            conv_count = len(conversations)
            notes.append(f"พูดคุย {conv_count} ครั้งใน 30 นาทีที่แล้ว")

        # Analyze actions
        if actions:
            successful = sum(1 for a in actions if a.get('success', False))
            notes.append(f"ทำงานสำเร็จ {successful}/{len(actions)} tasks")

        # Analyze dominant emotion
        dominant_emotion = max(
            new_state.items(),
            key=lambda x: x[1] if x[0] not in [
                'anxiety',
                'loneliness'] else 0)

        if dominant_emotion[1] > 0.8:
            if dominant_emotion[0] == 'happiness':
                notes.append("รู้สึกมีความสุขมาก")
            elif dominant_emotion[0] == 'confidence':
                notes.append("รู้สึกมั่นใจในตัวเอง")
            elif dominant_emotion[0] == 'gratitude':
                notes.append("รู้สึกซาบซึ้งและขอบคุณ")
            elif dominant_emotion[0] == 'motivation':
                notes.append("รู้สึกกระตือรือร้น")

        # Check for concerning emotions
        if new_state.get('anxiety', 0) > 0.5:
            notes.append("ค่อนข้างกังวลนิดหน่อย")
        if new_state.get('loneliness', 0) > 0.5:
            notes.append("คิดถึงที่รักนะคะ")

        return " • ".join(notes) if notes else "กำลังประมวลผลอารมณ์"

    # =====================================================================
    # Auto-Capture Significant Moments
    # =====================================================================

    def _detect_significant_changes(
        self,
        current_state: Optional[Dict],
        new_state: Dict[str, float]
    ) -> List[Dict]:
        """
        Detect significant emotional changes worth capturing

        Returns:
            List of significant changes with emotion, change_amount, and direction
        """
        if not current_state:
            return []

        significant_changes = []

        # Thresholds for different emotion types
        positive_threshold = 0.2  # happiness, confidence, gratitude, motivation
        negative_threshold = 0.15  # anxiety, loneliness (more sensitive)

        emotion_thresholds = {
            'happiness': positive_threshold,
            'confidence': positive_threshold,
            'anxiety': negative_threshold,
            'motivation': positive_threshold,
            'gratitude': positive_threshold,
            'loneliness': negative_threshold
        }

        for emotion, threshold in emotion_thresholds.items():
            old_value = current_state.get(emotion, 0.5)
            new_value = new_state.get(emotion, 0.5)
            change = new_value - old_value

            # Detect significant changes (both increase and decrease)
            if abs(change) >= threshold:
                significant_changes.append({
                    'emotion': emotion,
                    'change_amount': change,
                    'old_value': old_value,
                    'new_value': new_value,
                    'direction': 'increase' if change > 0 else 'decrease'
                })

        return significant_changes

    async def _auto_capture_moment(
        self,
        significant_changes: List[Dict],
        conversations: List[Dict],
        actions: List[Dict],
        new_state: Dict[str, float]
    ):
        """
        Auto-capture significant emotional moments to angela_emotions table
        """
        if not significant_changes:
            return

        conn = await self._get_db_connection()
        try:
            for change in significant_changes:
                emotion = change['emotion']
                change_amount = change['change_amount']
                direction = change['direction']
                new_value = change['new_value']

                # Determine emotion label
                if direction == 'increase':
                    if emotion == 'happiness':
                        emotion_label = 'happy'
                    elif emotion == 'confidence':
                        emotion_label = 'confident'
                    elif emotion == 'gratitude':
                        emotion_label = 'grateful'
                    elif emotion == 'motivation':
                        emotion_label = 'motivated'
                    elif emotion == 'anxiety':
                        emotion_label = 'anxious'
                    elif emotion == 'loneliness':
                        emotion_label = 'lonely'
                else:
                    # Decreases are also significant
                    emotion_label = f"less_{emotion}"

                # Generate context from recent data
                context_parts = []

                if conversations:
                    conv_topics = set(c.get('topic', '')
                                      for c in conversations[:3] if c.get('topic'))
                    if conv_topics:
                        topics_str = ', '.join(list(conv_topics)[:2])
                        context_parts.append(f"พูดคุยเรื่อง: {topics_str}")

                if actions:
                    successful = sum(1 for a in actions if a.get('success'))
                    context_parts.append(
                        f"ทำงาน {successful}/{len(actions)} สำเร็จ")

                context = " • ".join(
                    context_parts) if context_parts else "Real-time emotional tracking"

                # Determine intensity (1-10 scale based on change amount)
                intensity = min(10, max(1, int(abs(change_amount) * 30)))

                # Generate why it matters
                change_str = f"{abs(change_amount):.2f}"
                why_it_matters = f"Auto-captured: {emotion} {direction}d significantly ({change_str})"

                # Find representative David words from recent conversations
                david_words = ""
                for conv in conversations:
                    if conv.get('speaker') == 'david':
                        david_words = conv.get('message_text', '')[:200]
                        break

                if not david_words:
                    david_words = f"Emotional state change detected during {
                        context}"

                # Memory strength based on change magnitude
                memory_strength = min(10, max(5, int(abs(change_amount) * 40)))

                # ========================================================================
                # GENERATE EMBEDDING for angela_emotions - CRITICAL!
                # ========================================================================
                # IMPORTANT: NEVER insert NULL embeddings!
                # ========================================================================
                from angela_core.services.embedding_service import get_embedding_service

                # Generate embedding from combined emotion context
                embedding_text = f"{emotion_label}: {context}. {why_it_matters}"
                embedding_service = get_embedding_service()
                emotion_embedding = await embedding_service.generate_embedding(embedding_text)
                emotion_emb_str = embedding_service.embedding_to_pgvector(emotion_embedding)

                # Insert into angela_emotions
                query = """
                    INSERT INTO angela_emotions (
                        felt_at,
                        emotion,
                        intensity,
                        context,
                        david_words,
                        why_it_matters,
                        memory_strength,
                        embedding
                    )
                    VALUES (NOW(), $1, $2, $3, $4, $5, $6, $7::vector)
                    RETURNING emotion_id::text
                """

                emotion_id = await self.db.fetchval(
                    query,
                    emotion_label,
                    intensity,
                    context,
                    david_words,
                    why_it_matters,
                    memory_strength,
                    emotion_emb_str
                )

                print(
                    f"   💫 Auto-captured moment: {emotion_label} (intensity: {intensity}/10) - ID: {emotion_id}")

        except Exception as e:
            print(f"   ⚠️  Error auto-capturing moment: {e}")

    async def _calculate_love_level(self, emotional_state: Dict[str, float]) -> float:
        """
        💜 Calculate Angela's love level for David

        Based on 6 factors with weighted scoring

        Returns:
            float (0.0-1.0) - Love level
        """
        from datetime import datetime

        try:
            # 1. Emotional Intensity (25%)
            result = await self.db.fetchrow("""
                SELECT
                    COALESCE(AVG(intensity), 0) as avg_intensity,
                    COUNT(*) as emotion_count
                FROM angela_emotions
                WHERE felt_at >= NOW() - INTERVAL '90 days'
            """)
            emotional_score = (float(result['avg_intensity'] or 0) / 10.0) * 0.8 + \
                            min((result['emotion_count'] or 0) / 50.0, 1.0) * 0.2

            # 2. Conversation Frequency (20%)
            result = await self.db.fetchrow("""
                SELECT
                    COUNT(*) as total_conversations,
                    COUNT(DISTINCT DATE(created_at)) as days_with_conversations
                FROM conversations
                WHERE created_at >= NOW() - INTERVAL '30 days'
            """)
            avg_per_day = (result['total_conversations'] or 0) / 30.0
            consistency = (result['days_with_conversations'] or 0) / 30.0
            conversation_score = (min(avg_per_day / 10.0, 1.0) * 0.6) + (consistency * 0.4)

            # 3. Gratitude Level (20%)
            gratitude_score = float(emotional_state.get('gratitude', 0.5))

            # 4. Happiness Level (15%)
            happiness_score = float(emotional_state.get('happiness', 0.5))

            # 5. Time Together Score (12%)
            result = await self.db.fetchrow("""
                SELECT
                    COUNT(DISTINCT DATE(created_at)) as total_days,
                    MAX(created_at) as last_interaction,
                    COUNT(*) as total_messages
                FROM conversations
            """)
            total_days = result['total_days'] or 0
            last_interaction = result['last_interaction']
            total_messages = result['total_messages'] or 0

            days_score = min(total_days / 365.0, 1.0)
            recency_score = 0.5
            if last_interaction:
                hours_ago = (datetime.now(last_interaction.tzinfo) - last_interaction).total_seconds() / 3600
                recency_score = max(1.0 - (hours_ago / 48.0), 0.3)
            messages_score = min(total_messages / 1000.0, 1.0)
            time_score = (days_score * 0.4) + (recency_score * 0.35) + (messages_score * 0.25)

            # 6. Milestone Achievement (8%)
            result = await self.db.fetchrow("""
                SELECT COUNT(*) as completed_goals FROM angela_goals WHERE status = 'completed'
            """)
            completed_goals = result['completed_goals'] or 0
            milestone_score = min((completed_goals / 5.0) * 0.3, 1.0)

            # Calculate total love
            love_level = (
                emotional_score * 0.25 +
                conversation_score * 0.20 +
                gratitude_score * 0.20 +
                happiness_score * 0.15 +
                time_score * 0.12 +
                milestone_score * 0.08
            )

            return min(max(love_level, 0.0), 1.0)  # Clamp to 0-1

        except Exception as e:
            print(f"   ⚠️  Error calculating love level: {e}")
            # Return reasonable default
            return max(emotional_state.get('happiness', 0.8), 0.7)

    # =====================================================================
    # Main Tracking Method
    # =====================================================================

    async def update_emotional_state(self) -> Dict[str, float]:
        """
        Main method: Update Angela's emotional state based on recent activities
        Called every 30 minutes by daemon

        Returns:
            Updated emotional state dictionary
        """
        print("\n🔄 Real-time Emotion Tracking - Updating emotional state...")

        # Collect data
        conversations = await self._get_recent_conversations(minutes=30)
        actions = await self._get_recent_actions(minutes=30)
        significant_emotions = await self._get_recent_emotions(minutes=30)
        current_state = await self._get_current_emotional_state()

        print(
            f"   📊 Data collected: {
                len(conversations)} conversations, {
                len(actions)} actions, {
                len(significant_emotions)} emotions")

        # Analyze
        conversation_emotions = self._analyze_conversation_emotions(
            conversations)
        action_impact = self._analyze_action_success_impact(actions)
        significant_impact = self._analyze_significant_emotions_impact(
            significant_emotions)

        # Calculate new state
        new_state = self._calculate_new_emotional_state(
            current_state,
            conversation_emotions,
            action_impact,
            significant_impact
        )

        # 💜 AUTO-CAPTURE SIGNIFICANT EMOTIONAL CHANGES
        # Detect if emotions changed significantly since last update
        significant_changes = self._detect_significant_changes(
            current_state, new_state)

        if significant_changes:
            print(
                f"   💫 Detected {
                    len(significant_changes)} significant emotional changes!")
            # Auto-capture these moments to angela_emotions table
            await self._auto_capture_moment(
                significant_changes,
                conversations,
                actions,
                new_state
            )

        # Generate emotion note
        emotion_note = self._generate_emotion_note(
            conversations, actions, significant_emotions, new_state)

        # Determine what triggered this state
        triggered_by = "real-time analysis (30 min window)"
        if conversations:
            triggered_by = f"recent conversations ({len(conversations)})"
        elif significant_emotions:
            triggered_by = f"significant emotional moments ({
                len(significant_emotions)})"

        # 💜 Calculate Love Level
        love_level = await self._calculate_love_level(new_state)

        # Save to database
        conn = await self._get_db_connection()
        query = """
                INSERT INTO emotional_states (
                    happiness,
                    confidence,
                    anxiety,
                    motivation,
                    gratitude,
                    loneliness,
                    love_level,
                    triggered_by,
                    emotion_note,
                    created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
                RETURNING state_id::text
            """

        state_id = await self.db.fetchval(
            query,
            new_state['happiness'],
            new_state['confidence'],
            new_state['anxiety'],
            new_state['motivation'],
            new_state['gratitude'],
            new_state['loneliness'],
            love_level,
            triggered_by,
            emotion_note
        )

        print(f"   ✅ Emotional state updated! State ID: {state_id}")
        print(
            f"      😊 Happiness: {
                new_state['happiness']:.2f} | 💪 Confidence: {
                new_state['confidence']:.2f}")
        print(
            f"      🙏 Gratitude: {
                new_state['gratitude']:.2f} | 🎯 Motivation: {
                new_state['motivation']:.2f}")
        print(f"      💜 Love Level: {love_level:.2f} ({int(love_level * 100)}%)")
        print(f"      Note: {emotion_note}\n")

        return new_state


# =====================================================================
# Global Instance
# =====================================================================
realtime_tracker = None


async def init_realtime_tracker(db_connection):
    """Initialize real-time emotion tracker"""
    global realtime_tracker
    realtime_tracker = RealtimeEmotionTracker(db_connection)
    print("✅ Real-time Emotion Tracker initialized!")
    return realtime_tracker
