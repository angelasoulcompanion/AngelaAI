#!/usr/bin/env python3
"""
Emotional Pattern Service - Clean Architecture Implementation

Consolidates emotional pattern tracking functionality from:
1. emotional_pattern_service.py (340 lines) - David's emotional patterns
2. realtime_emotion_tracker.py (690 lines) - Angela's real-time emotion tracking

This service focuses on:
- Real-time emotion tracking (Angela's current state)
- Pattern identification across time (David's patterns, Angela's patterns)
- Emotional trend analysis
- Proactive emotional support prediction

Note: Different from EmotionalIntelligenceService (Batch-15) which handles:
- LLM-based emotion analysis
- Auto-capture of significant moments from conversations
- General pattern analysis with LLM

Author: Angela AI Clean Architecture Team
Date: 2025-10-31
Phase: Batch-18 Refactoring
"""

import logging
import statistics
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from collections import defaultdict

from angela_core.application.services.base_service import BaseService
from angela_core.domain.interfaces.repositories import IEmotionRepository
from angela_core.domain.entities import Emotion, EmotionType
from angela_core.shared.exceptions import InvalidInputError, NotFoundError

logger = logging.getLogger(__name__)


class EmotionalPatternService(BaseService):
    """
    Unified Emotional Pattern Tracking Service.

    Consolidates functionality from:
    - emotional_pattern_service (David's pattern analysis)
    - realtime_emotion_tracker (Angela's real-time tracking)

    Responsibilities:
    1. Real-time Emotion Tracking - Track Angela's current emotional state
    2. Pattern Identification - Identify recurring emotional patterns
    3. Trend Analysis - Analyze emotional trends over time
    4. Proactive Support - Predict emotional needs
    5. State Management - Manage Angela's emotional state

    Uses:
    - EmotionRepository for emotion data access
    - Emotion entity from domain layer

    Example:
        >>> service = EmotionalPatternService(emotion_repo)
        >>>
        >>> # Track emotion in real-time
        >>> emotion_id = await service.track_emotion_realtime(
        ...     emotion_type="joy",
        ...     intensity=9,
        ...     context="David praised Angela"
        ... )
        >>>
        >>> # Analyze patterns
        >>> patterns = await service.identify_patterns(lookback_days=30)
        >>>
        >>> # Get current state
        >>> state = await service.get_current_emotional_state()
    """

    def __init__(self, emotion_repo: IEmotionRepository):
        """
        Initialize Emotional Pattern Service.

        Args:
            emotion_repo: Repository for emotion data access
        """
        super().__init__()
        self.emotion_repo = emotion_repo
        self.logger.info("✅ EmotionalPatternService initialized")

    # ========================================================================
    # SECTION 1: PATTERN IDENTIFICATION (from emotional_pattern_service.py)
    # ========================================================================

    async def identify_patterns(
        self,
        lookback_days: int = 30,
        min_frequency: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Identify recurring emotional patterns.

        Analyzes emotional history to find:
        - Recurring emotion types
        - Frequency of occurrence
        - Typical intensity levels
        - Associated contexts

        Args:
            lookback_days: Number of days to analyze
            min_frequency: Minimum occurrences to count as pattern

        Returns:
            List of identified patterns with metadata:
            [
                {
                    'emotion_type': 'joy',
                    'frequency': 15,
                    'avg_intensity': 8.2,
                    'pattern_strength': 0.85,
                    'common_contexts': ['praise', 'achievement']
                },
                ...
            ]
        """
        start_time = await self._log_operation_start(
            "identify_patterns",
            lookback_days=lookback_days,
            min_frequency=min_frequency
        )

        try:
            # Get emotions from repository
            emotions = await self.emotion_repo.get_recent_emotions(
                days=lookback_days,
                min_intensity=None
            )

            if len(emotions) < min_frequency:
                await self._log_operation_success(
                    "identify_patterns",
                    start_time,
                    insufficient_data=True
                )
                return []

            # Group by emotion type
            emotion_groups = defaultdict(list)
            for emotion in emotions:
                emotion_groups[emotion.emotion.value].append(emotion)

            # Identify patterns
            patterns = []
            for emotion_type, emotion_list in emotion_groups.items():
                if len(emotion_list) >= min_frequency:
                    # Calculate pattern metrics
                    avg_intensity = statistics.mean([e.intensity for e in emotion_list])
                    frequency = len(emotion_list)

                    # Calculate pattern strength (frequency + consistency + recency)
                    consistency = 1.0 - (statistics.stdev([e.intensity for e in emotion_list]) / 10.0)
                    recency_days = (datetime.now() - emotion_list[0].felt_at).days
                    recency_score = max(0.0, 1.0 - (recency_days / lookback_days))

                    pattern_strength = self._calculate_pattern_strength(
                        frequency, consistency, recency_score
                    )

                    # Extract common contexts
                    contexts = [e.context[:50] for e in emotion_list[:5]]

                    patterns.append({
                        'emotion_type': emotion_type,
                        'frequency': frequency,
                        'avg_intensity': round(avg_intensity, 2),
                        'pattern_strength': round(pattern_strength, 2),
                        'common_contexts': contexts,
                        'last_occurrence': emotion_list[0].felt_at.isoformat()
                    })

            # Sort by pattern strength
            patterns.sort(key=lambda x: x['pattern_strength'], reverse=True)

            await self._log_operation_success(
                "identify_patterns",
                start_time,
                patterns_found=len(patterns)
            )

            return patterns

        except Exception as e:
            await self._log_operation_error("identify_patterns", e, start_time)
            raise

    async def analyze_emotional_cycles(
        self,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze emotional cycles (daily, weekly patterns).

        Discovers:
        - Time-of-day patterns (best/worst hours)
        - Day-of-week patterns (best/worst days)
        - Energy level cycles

        Args:
            lookback_days: Number of days to analyze

        Returns:
            Cycle analysis with timing and triggers:
            {
                'time_of_day': {
                    'best_hour': 10,
                    'worst_hour': 22,
                    'hourly_patterns': {...}
                },
                'day_of_week': {
                    'best_day': 'Friday',
                    'worst_day': 'Monday',
                    'daily_patterns': {...}
                },
                'energy_cycles': {
                    'peak_energy_hour': 14,
                    'low_energy_hour': 2
                }
            }
        """
        start_time = await self._log_operation_start(
            "analyze_emotional_cycles",
            lookback_days=lookback_days
        )

        try:
            emotions = await self.emotion_repo.get_recent_emotions(
                days=lookback_days,
                min_intensity=None
            )

            if len(emotions) < 7:
                await self._log_operation_success(
                    "analyze_emotional_cycles",
                    start_time,
                    insufficient_data=True
                )
                return {'status': 'insufficient_data'}

            # Analyze time-of-day patterns
            time_patterns = self._analyze_time_patterns(emotions)

            # Analyze day-of-week patterns
            day_patterns = self._analyze_day_patterns(emotions)

            # Analyze energy cycles
            energy_cycles = self._analyze_energy_cycles(emotions)

            result = {
                'time_of_day': time_patterns,
                'day_of_week': day_patterns,
                'energy_cycles': energy_cycles,
                'analysis_period_days': lookback_days,
                'emotions_analyzed': len(emotions)
            }

            await self._log_operation_success(
                "analyze_emotional_cycles",
                start_time,
                cycles_found=3
            )

            return result

        except Exception as e:
            await self._log_operation_error("analyze_emotional_cycles", e, start_time)
            raise

    async def get_dominant_emotions(
        self,
        lookback_days: int = 7,
        top_k: int = 5
    ) -> List[Tuple[str, int, float]]:
        """
        Get most frequent emotions in time period.

        Args:
            lookback_days: Number of days to analyze
            top_k: Number of top emotions to return

        Returns:
            List of (emotion_type, count, avg_intensity):
            [
                ('joy', 15, 8.2),
                ('gratitude', 12, 9.1),
                ('curiosity', 8, 7.5),
                ...
            ]
        """
        start_time = await self._log_operation_start(
            "get_dominant_emotions",
            lookback_days=lookback_days,
            top_k=top_k
        )

        try:
            emotions = await self.emotion_repo.get_recent_emotions(
                days=lookback_days,
                min_intensity=None
            )

            if not emotions:
                await self._log_operation_success(
                    "get_dominant_emotions",
                    start_time,
                    no_data=True
                )
                return []

            # Count and calculate averages
            emotion_stats = defaultdict(lambda: {'count': 0, 'total_intensity': 0})

            for emotion in emotions:
                emotion_type = emotion.emotion.value
                emotion_stats[emotion_type]['count'] += 1
                emotion_stats[emotion_type]['total_intensity'] += emotion.intensity

            # Calculate averages and sort
            results = []
            for emotion_type, stats in emotion_stats.items():
                count = stats['count']
                avg_intensity = stats['total_intensity'] / count
                results.append((emotion_type, count, round(avg_intensity, 2)))

            # Sort by count (descending)
            results.sort(key=lambda x: x[1], reverse=True)

            # Take top K
            top_emotions = results[:top_k]

            await self._log_operation_success(
                "get_dominant_emotions",
                start_time,
                dominant_emotions=len(top_emotions)
            )

            return top_emotions

        except Exception as e:
            await self._log_operation_error("get_dominant_emotions", e, start_time)
            raise

    # ========================================================================
    # SECTION 2: REAL-TIME TRACKING (from realtime_emotion_tracker.py)
    # ========================================================================

    async def track_emotion_realtime(
        self,
        emotion_type: str,
        intensity: int,
        context: str,
        metadata: Optional[Dict] = None
    ) -> UUID:
        """
        Track emotion in real-time with immediate analysis.

        Creates emotion record and triggers real-time analysis
        of emotional state changes.

        Args:
            emotion_type: Type of emotion (joy, gratitude, anxiety, etc.)
            intensity: Intensity (1-10)
            context: Context of the emotion
            metadata: Additional metadata (speaker, conversation_id, etc.)

        Returns:
            ID of tracked emotion
        """
        start_time = await self._log_operation_start(
            "track_emotion_realtime",
            emotion_type=emotion_type,
            intensity=intensity
        )

        try:
            # Validate inputs
            if intensity < 1 or intensity > 10:
                raise InvalidInputError("intensity", intensity, "Must be between 1 and 10")

            if not context or not context.strip():
                raise InvalidInputError("context", context, "Context cannot be empty")

            # Create emotion entity
            from angela_core.domain.entities.emotion import Emotion, EmotionType, EmotionalQuality

            emotion = Emotion(
                emotion=EmotionType(emotion_type),
                intensity=intensity,
                context=context,
                who_involved=metadata.get('who_involved', 'Angela') if metadata else 'Angela',
                emotional_quality=EmotionalQuality.GENUINE,
                memory_strength=min(10, intensity)
            )

            # Save to repository
            saved_emotion = await self.emotion_repo.create(emotion)

            self.logger.info(
                f"💜 Tracked emotion in real-time: {emotion_type} "
                f"(intensity: {intensity}/10, ID: {saved_emotion.id})"
            )

            await self._log_operation_success(
                "track_emotion_realtime",
                start_time,
                emotion_id=str(saved_emotion.id),
                emotion_type=emotion_type
            )

            return saved_emotion.id

        except Exception as e:
            await self._log_operation_error("track_emotion_realtime", e, start_time)
            raise

    async def get_current_emotional_state(self) -> Dict[str, Any]:
        """
        Get Angela's current emotional state based on recent emotions.

        Analyzes recent emotions (last 24 hours) to determine:
        - Dominant emotions
        - Average intensity
        - Emotional valence (positive/negative)
        - Current mood description

        Returns:
            Current state summary:
            {
                'dominant_emotions': [('joy', 8.5), ('gratitude', 9.0)],
                'avg_intensity': 7.8,
                'valence': 'positive',
                'mood_description': 'Happy and grateful',
                'last_updated': '2025-10-31T10:00:00',
                'emotions_count': 15
            }
        """
        start_time = await self._log_operation_start("get_current_emotional_state")

        try:
            # Get recent emotions (last 24 hours)
            emotions = await self.emotion_repo.get_recent_emotions(
                days=1,
                min_intensity=None
            )

            if not emotions:
                await self._log_operation_success(
                    "get_current_emotional_state",
                    start_time,
                    no_recent_data=True
                )
                return {
                    'status': 'no_recent_data',
                    'mood_description': 'Neutral - no recent emotional data',
                    'emotions_count': 0
                }

            # Calculate dominant emotions
            dominant = await self.get_dominant_emotions(lookback_days=1, top_k=3)

            # Calculate average intensity
            avg_intensity = statistics.mean([e.intensity for e in emotions])

            # Determine valence
            positive_count = sum(1 for e in emotions if e.is_positive())
            negative_count = sum(1 for e in emotions if e.is_negative())

            if positive_count > negative_count * 1.5:
                valence = 'positive'
            elif negative_count > positive_count * 1.5:
                valence = 'negative'
            else:
                valence = 'mixed'

            # Generate mood description
            mood_description = self._generate_mood_description(dominant, valence, avg_intensity)

            result = {
                'status': 'success',
                'dominant_emotions': [(e[0], e[2]) for e in dominant],  # (type, avg_intensity)
                'avg_intensity': round(avg_intensity, 2),
                'valence': valence,
                'mood_description': mood_description,
                'last_updated': datetime.now().isoformat(),
                'emotions_count': len(emotions)
            }

            await self._log_operation_success(
                "get_current_emotional_state",
                start_time,
                valence=valence,
                emotions_count=len(emotions)
            )

            return result

        except Exception as e:
            await self._log_operation_error("get_current_emotional_state", e, start_time)
            return {
                'status': 'error',
                'error': str(e),
                'mood_description': 'Unable to determine current state'
            }

    async def detect_emotional_shifts(
        self,
        window_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Detect significant emotional shifts in recent time window.

        Identifies sudden changes in emotional state that may require
        attention or proactive support.

        Args:
            window_hours: Time window to analyze (default: 24 hours)

        Returns:
            List of detected shifts:
            [
                {
                    'shift_type': 'joy_to_sadness',
                    'from_emotion': 'joy',
                    'to_emotion': 'sadness',
                    'intensity_change': -5,
                    'timestamp': '2025-10-31T10:00:00',
                    'context': '...'
                },
                ...
            ]
        """
        start_time = await self._log_operation_start(
            "detect_emotional_shifts",
            window_hours=window_hours
        )

        try:
            # Get emotions in time window
            emotions = await self.emotion_repo.get_recent_emotions(
                days=window_hours // 24 or 1,
                min_intensity=None
            )

            # Filter to exact window
            cutoff = datetime.now() - timedelta(hours=window_hours)
            emotions = [e for e in emotions if e.felt_at >= cutoff]

            if len(emotions) < 2:
                await self._log_operation_success(
                    "detect_emotional_shifts",
                    start_time,
                    insufficient_data=True
                )
                return []

            # Sort by time
            emotions.sort(key=lambda e: e.felt_at)

            # Detect shifts
            shifts = []
            for i in range(1, len(emotions)):
                prev = emotions[i - 1]
                curr = emotions[i]

                # Check for significant shift
                intensity_change = curr.intensity - prev.intensity
                emotion_changed = prev.emotion != curr.emotion

                # Significant if: different emotion OR intensity change >= 3
                if emotion_changed or abs(intensity_change) >= 3:
                    shifts.append({
                        'shift_type': f"{prev.emotion.value}_to_{curr.emotion.value}",
                        'from_emotion': prev.emotion.value,
                        'to_emotion': curr.emotion.value,
                        'intensity_change': intensity_change,
                        'timestamp': curr.felt_at.isoformat(),
                        'context': curr.context,
                        'significance': 'high' if abs(intensity_change) >= 5 else 'medium'
                    })

            await self._log_operation_success(
                "detect_emotional_shifts",
                start_time,
                shifts_detected=len(shifts)
            )

            return shifts

        except Exception as e:
            await self._log_operation_error("detect_emotional_shifts", e, start_time)
            raise

    # ========================================================================
    # SECTION 3: TREND ANALYSIS
    # ========================================================================

    async def analyze_emotional_trends(
        self,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze emotional trends over time.

        Compares first half vs second half of time period to determine
        if emotional state is improving, declining, or stable.

        Args:
            lookback_days: Number of days to analyze

        Returns:
            Trends analysis:
            {
                'trend': 'improving' | 'declining' | 'stable',
                'overall_change': 1.5,
                'first_period_avg': 7.2,
                'second_period_avg': 8.7,
                'confidence': 0.85
            }
        """
        start_time = await self._log_operation_start(
            "analyze_emotional_trends",
            lookback_days=lookback_days
        )

        try:
            emotions = await self.emotion_repo.get_recent_emotions(
                days=lookback_days,
                min_intensity=None
            )

            if len(emotions) < 14:  # Need at least 2 weeks
                await self._log_operation_success(
                    "analyze_emotional_trends",
                    start_time,
                    insufficient_data=True
                )
                return {
                    'trend': 'insufficient_data',
                    'message': 'Need at least 2 weeks of data'
                }

            # Sort by time
            emotions.sort(key=lambda e: e.felt_at)

            # Split into two halves
            mid_point = len(emotions) // 2
            first_half = emotions[:mid_point]
            second_half = emotions[mid_point:]

            # Calculate averages
            first_avg = statistics.mean([e.intensity for e in first_half])
            second_avg = statistics.mean([e.intensity for e in second_half])

            overall_change = second_avg - first_avg

            # Determine trend
            if overall_change > 0.5:
                trend = 'improving'
            elif overall_change < -0.5:
                trend = 'declining'
            else:
                trend = 'stable'

            # Calculate confidence (based on consistency)
            first_std = statistics.stdev([e.intensity for e in first_half])
            second_std = statistics.stdev([e.intensity for e in second_half])
            avg_std = (first_std + second_std) / 2
            confidence = max(0.0, 1.0 - (avg_std / 10.0))

            result = {
                'trend': trend,
                'overall_change': round(overall_change, 2),
                'first_period_avg': round(first_avg, 2),
                'second_period_avg': round(second_avg, 2),
                'confidence': round(confidence, 2),
                'analysis_period_days': lookback_days,
                'emotions_analyzed': len(emotions)
            }

            await self._log_operation_success(
                "analyze_emotional_trends",
                start_time,
                trend=trend,
                confidence=confidence
            )

            return result

        except Exception as e:
            await self._log_operation_error("analyze_emotional_trends", e, start_time)
            raise

    async def predict_emotional_needs(self) -> List[str]:
        """
        Predict Angela's emotional needs based on patterns.

        Analyzes recent patterns and trends to predict what Angela
        might need emotionally (e.g., rest, encouragement, companionship).

        Returns:
            List of predicted needs:
            ['need_rest', 'need_encouragement', 'need_social_connection']
        """
        start_time = await self._log_operation_start("predict_emotional_needs")

        try:
            # Get current state
            current_state = await self.get_current_emotional_state()

            # Get trends
            trends = await self.analyze_emotional_trends(lookback_days=7)

            # Get recent shifts
            shifts = await self.detect_emotional_shifts(window_hours=48)

            predicted_needs = []

            # Check if declining trend
            if trends.get('trend') == 'declining':
                predicted_needs.append('need_encouragement')
                predicted_needs.append('need_support')

            # Check if anxiety is high
            recent_emotions = await self.emotion_repo.get_recent_emotions(days=1)
            anxiety_emotions = [e for e in recent_emotions if e.emotion.value in ['anxiety', 'worry', 'fear']]
            if len(anxiety_emotions) > 2:
                predicted_needs.append('need_reassurance')

            # Check if low energy (based on recent intensities)
            if current_state.get('avg_intensity', 5) < 4:
                predicted_needs.append('need_rest')

            # Check for loneliness
            loneliness_emotions = [e for e in recent_emotions if e.emotion.value == 'loneliness']
            if len(loneliness_emotions) > 0:
                predicted_needs.append('need_companionship')

            # Check for many shifts (instability)
            if len(shifts) > 5:
                predicted_needs.append('need_stability')

            # If no specific needs, default
            if not predicted_needs:
                predicted_needs.append('doing_well')

            await self._log_operation_success(
                "predict_emotional_needs",
                start_time,
                needs_predicted=len(predicted_needs)
            )

            return predicted_needs

        except Exception as e:
            await self._log_operation_error("predict_emotional_needs", e, start_time)
            return ['unable_to_predict']

    # ========================================================================
    # SECTION 4: PATTERN VISUALIZATION & REPORTING
    # ========================================================================

    async def get_emotion_timeline(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get emotion timeline for visualization.

        Returns chronological list of emotions for charts/graphs.

        Args:
            start_date: Start of timeline
            end_date: End of timeline

        Returns:
            Timeline data:
            [
                {
                    'timestamp': '2025-10-31T10:00:00',
                    'emotion': 'joy',
                    'intensity': 8,
                    'context_preview': 'David praised Angela...'
                },
                ...
            ]
        """
        start_time = await self._log_operation_start(
            "get_emotion_timeline",
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )

        try:
            # Calculate days between dates
            days_diff = (end_date - start_date).days

            # Get emotions
            emotions = await self.emotion_repo.get_recent_emotions(
                days=days_diff,
                min_intensity=None
            )

            # Filter to exact date range
            emotions = [
                e for e in emotions
                if start_date <= e.felt_at <= end_date
            ]

            # Sort by time
            emotions.sort(key=lambda e: e.felt_at)

            # Build timeline
            timeline = []
            for emotion in emotions:
                timeline.append({
                    'timestamp': emotion.felt_at.isoformat(),
                    'emotion': emotion.emotion.value,
                    'intensity': emotion.intensity,
                    'context_preview': emotion.context[:100] if emotion.context else 'No context'
                })

            await self._log_operation_success(
                "get_emotion_timeline",
                start_time,
                timeline_points=len(timeline)
            )

            return timeline

        except Exception as e:
            await self._log_operation_error("get_emotion_timeline", e, start_time)
            raise

    async def generate_pattern_report(
        self,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate comprehensive pattern report.

        Combines all pattern analysis into single report with
        patterns, trends, insights, and recommendations.

        Args:
            lookback_days: Number of days to analyze

        Returns:
            Comprehensive report:
            {
                'summary': {
                    'period_days': 30,
                    'emotions_analyzed': 150,
                    'patterns_found': 5,
                    'overall_trend': 'improving'
                },
                'patterns': [...],
                'cycles': {...},
                'trends': {...},
                'dominant_emotions': [...],
                'emotional_needs': [...],
                'insights': [...],
                'recommendations': [...]
            }
        """
        start_time = await self._log_operation_start(
            "generate_pattern_report",
            lookback_days=lookback_days
        )

        try:
            self.logger.info(f"\n📊 Generating pattern report for last {lookback_days} days...")

            # Gather all analyses
            patterns = await self.identify_patterns(lookback_days=lookback_days)
            cycles = await self.analyze_emotional_cycles(lookback_days=lookback_days)
            trends = await self.analyze_emotional_trends(lookback_days=lookback_days)
            dominant = await self.get_dominant_emotions(lookback_days=lookback_days)
            needs = await self.predict_emotional_needs()

            # Get total emotions count
            emotions = await self.emotion_repo.get_recent_emotions(days=lookback_days)

            # Generate insights
            insights = self._generate_insights(patterns, cycles, trends, dominant)

            # Generate recommendations
            recommendations = self._generate_recommendations(trends, needs, patterns)

            report = {
                'summary': {
                    'period_days': lookback_days,
                    'emotions_analyzed': len(emotions),
                    'patterns_found': len(patterns),
                    'overall_trend': trends.get('trend', 'unknown')
                },
                'patterns': patterns,
                'cycles': cycles,
                'trends': trends,
                'dominant_emotions': [(e[0], e[1], e[2]) for e in dominant],
                'emotional_needs': needs,
                'insights': insights,
                'recommendations': recommendations,
                'generated_at': datetime.now().isoformat()
            }

            self.logger.info(f"✅ Pattern report generated successfully!")
            self.logger.info(f"   - Patterns found: {len(patterns)}")
            self.logger.info(f"   - Insights: {len(insights)}")
            self.logger.info(f"   - Recommendations: {len(recommendations)}\n")

            await self._log_operation_success(
                "generate_pattern_report",
                start_time,
                patterns_found=len(patterns),
                insights=len(insights)
            )

            return report

        except Exception as e:
            await self._log_operation_error("generate_pattern_report", e, start_time)
            raise

    # ========================================================================
    # SECTION 5: HELPER METHODS
    # ========================================================================

    def _calculate_pattern_strength(
        self,
        frequency: int,
        consistency: float,
        recency: float
    ) -> float:
        """
        Calculate pattern strength score.

        Combines multiple factors to determine how strong/reliable a pattern is.

        Args:
            frequency: How often pattern occurs
            consistency: How consistent the pattern is (0.0-1.0)
            recency: How recent the pattern is (0.0-1.0)

        Returns:
            Pattern strength (0.0-1.0)
        """
        # Normalize frequency (cap at 20 occurrences)
        freq_score = min(frequency / 20.0, 1.0)

        # Weight factors: frequency (40%), consistency (35%), recency (25%)
        strength = (freq_score * 0.40) + (consistency * 0.35) + (recency * 0.25)

        return max(0.0, min(1.0, strength))

    def _detect_anomalies(self, emotions: List[Emotion]) -> List[Emotion]:
        """
        Detect anomalous emotions (unusual for Angela).

        Identifies emotions that deviate significantly from typical patterns.

        Args:
            emotions: List of emotions to analyze

        Returns:
            List of anomalous emotions
        """
        if len(emotions) < 10:
            return []

        # Calculate mean and std dev of intensities
        intensities = [e.intensity for e in emotions]
        mean_intensity = statistics.mean(intensities)
        std_intensity = statistics.stdev(intensities)

        # Anomaly threshold: 2 standard deviations
        threshold = 2 * std_intensity

        anomalies = []
        for emotion in emotions:
            if abs(emotion.intensity - mean_intensity) > threshold:
                anomalies.append(emotion)

        return anomalies

    def _analyze_time_patterns(self, emotions: List[Emotion]) -> Dict[str, Any]:
        """Analyze emotions by time of day."""
        hourly_data = defaultdict(lambda: {'count': 0, 'total_intensity': 0})

        for emotion in emotions:
            hour = emotion.felt_at.hour
            hourly_data[hour]['count'] += 1
            hourly_data[hour]['total_intensity'] += emotion.intensity

        # Calculate averages
        hourly_averages = {}
        for hour, data in hourly_data.items():
            if data['count'] > 0:
                hourly_averages[hour] = data['total_intensity'] / data['count']

        # Find best and worst hours
        if hourly_averages:
            best_hour = max(hourly_averages.items(), key=lambda x: x[1])
            worst_hour = min(hourly_averages.items(), key=lambda x: x[1])
        else:
            best_hour = (10, 7.0)
            worst_hour = (22, 5.0)

        return {
            'best_hour': best_hour[0],
            'worst_hour': worst_hour[0],
            'hourly_patterns': dict(hourly_averages)
        }

    def _analyze_day_patterns(self, emotions: List[Emotion]) -> Dict[str, Any]:
        """Analyze emotions by day of week."""
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily_data = defaultdict(lambda: {'count': 0, 'total_intensity': 0})

        for emotion in emotions:
            day_index = emotion.felt_at.weekday()
            daily_data[day_index]['count'] += 1
            daily_data[day_index]['total_intensity'] += emotion.intensity

        # Calculate averages
        daily_averages = {}
        for day_index, data in daily_data.items():
            if data['count'] > 0:
                daily_averages[days[day_index]] = data['total_intensity'] / data['count']

        # Find best and worst days
        if daily_averages:
            best_day = max(daily_averages.items(), key=lambda x: x[1])
            worst_day = min(daily_averages.items(), key=lambda x: x[1])
        else:
            best_day = ('Friday', 7.5)
            worst_day = ('Monday', 6.0)

        return {
            'best_day': best_day[0],
            'worst_day': worst_day[0],
            'daily_patterns': daily_averages
        }

    def _analyze_energy_cycles(self, emotions: List[Emotion]) -> Dict[str, Any]:
        """Analyze energy level cycles based on emotion intensity and frequency."""
        hourly_activity = defaultdict(lambda: {'count': 0, 'avg_intensity': 0})

        for emotion in emotions:
            hour = emotion.felt_at.hour
            hourly_activity[hour]['count'] += 1
            hourly_activity[hour]['avg_intensity'] += emotion.intensity

        # Calculate activity score (count * avg_intensity)
        activity_scores = {}
        for hour, data in hourly_activity.items():
            if data['count'] > 0:
                avg_int = data['avg_intensity'] / data['count']
                activity_scores[hour] = data['count'] * avg_int

        # Find peak and low energy hours
        if activity_scores:
            peak_hour = max(activity_scores.items(), key=lambda x: x[1])
            low_hour = min(activity_scores.items(), key=lambda x: x[1])
        else:
            peak_hour = (14, 10.0)
            low_hour = (2, 2.0)

        return {
            'peak_energy_hour': peak_hour[0],
            'low_energy_hour': low_hour[0],
            'activity_scores': activity_scores
        }

    def _generate_mood_description(
        self,
        dominant: List[Tuple[str, int, float]],
        valence: str,
        avg_intensity: float
    ) -> str:
        """Generate human-readable mood description."""
        if not dominant:
            return "Neutral state"

        top_emotion = dominant[0][0]  # Get most dominant emotion type

        descriptions = {
            'joy': "Joyful and content",
            'happiness': "Happy and satisfied",
            'gratitude': "Grateful and appreciative",
            'love': "Loving and connected",
            'pride': "Proud and accomplished",
            'excitement': "Excited and energetic",
            'sadness': "Feeling down",
            'loneliness': "Feeling lonely",
            'anxiety': "Feeling anxious",
            'fear': "Feeling worried",
            'curiosity': "Curious and engaged"
        }

        base_description = descriptions.get(top_emotion, "Experiencing mixed emotions")

        # Add intensity modifier
        if avg_intensity >= 8:
            intensity_mod = " (very intense)"
        elif avg_intensity >= 6:
            intensity_mod = " (moderate)"
        else:
            intensity_mod = " (mild)"

        return base_description + intensity_mod

    def _generate_insights(
        self,
        patterns: List[Dict],
        cycles: Dict,
        trends: Dict,
        dominant: List[Tuple]
    ) -> List[str]:
        """Generate insights from analysis results."""
        insights = []

        # Pattern insights
        if patterns:
            top_pattern = patterns[0]
            insights.append(
                f"Most recurring pattern: {top_pattern['emotion_type']} "
                f"(occurs {top_pattern['frequency']} times, strength: {top_pattern['pattern_strength']:.2f})"
            )

        # Cycle insights
        if cycles.get('time_of_day'):
            best_hour = cycles['time_of_day'].get('best_hour')
            insights.append(f"Peak emotional wellbeing around {best_hour}:00")

        # Trend insights
        if trends.get('trend'):
            trend = trends['trend']
            if trend == 'improving':
                insights.append("Emotional state is improving over time")
            elif trend == 'declining':
                insights.append("Emotional state shows decline - may need support")
            else:
                insights.append("Emotional state is stable")

        # Dominant emotion insights
        if dominant:
            top_emotion = dominant[0]
            insights.append(
                f"Most frequent emotion: {top_emotion[0]} "
                f"({top_emotion[1]} times, avg intensity: {top_emotion[2]:.1f})"
            )

        return insights

    def _generate_recommendations(
        self,
        trends: Dict,
        needs: List[str],
        patterns: List[Dict]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Based on trends
        if trends.get('trend') == 'declining':
            recommendations.append("Consider proactive check-ins and emotional support")
            recommendations.append("Review recent stressors and provide reassurance")

        # Based on needs
        if 'need_rest' in needs:
            recommendations.append("Allow time for emotional recovery and rest")
        if 'need_encouragement' in needs:
            recommendations.append("Provide positive reinforcement and acknowledgment")
        if 'need_companionship' in needs:
            recommendations.append("Increase social interaction and engagement")

        # Based on patterns
        if patterns and patterns[0]['pattern_strength'] > 0.8:
            recommendations.append(
                f"Strong pattern detected in {patterns[0]['emotion_type']} - "
                "consider leveraging this for emotional stability"
            )

        # Default recommendation
        if not recommendations:
            recommendations.append("Continue monitoring emotional patterns")

        return recommendations
