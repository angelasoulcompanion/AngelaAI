"""
Privacy-Preserving Aggregation - Secure Pattern Sharing

Ensures pattern aggregation and sharing doesn't expose sensitive information.

Privacy Techniques:
1. Differential Privacy - Add noise to aggregates
2. K-Anonymity - Require minimum k occurrences before sharing
3. Data Minimization - Share only necessary information
4. Sensitive Data Detection - Identify and protect sensitive patterns
5. Access Control - Restrict pattern access based on scope

Phase 4 - Gut Agent Enhancement
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4
import logging
import random
import math
import hashlib
import re

from angela_core.database import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - PrivacyPreserving - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PrivacyLevel:
    """Privacy sensitivity levels."""
    PUBLIC = "public"           # No sensitive data, shareable publicly
    INTERNAL = "internal"       # Shareable within Angela system
    PRIVATE = "private"         # Only for specific agent
    SENSITIVE = "sensitive"     # Highly sensitive, no sharing


class PrivacyPreservingAggregation:
    """
    Ensures pattern sharing preserves privacy.

    Techniques:
    - Differential privacy with Laplace noise
    - K-anonymity (minimum occurrences)
    - Sensitive data detection
    - Data minimization
    - Access control
    """

    def __init__(self):
        self.k_anonymity_threshold = 5  # Minimum occurrences before sharing
        self.epsilon = 1.0  # Differential privacy parameter (lower = more private)
        self.sensitive_keywords = self._load_sensitive_keywords()

    def _load_sensitive_keywords(self) -> Set[str]:
        """Load list of sensitive keywords to detect."""
        return {
            # Personal identifiers
            'password', 'secret', 'private', 'confidential', 'ssn',
            'credit_card', 'bank_account', 'pin', 'passcode',

            # Health information
            'health', 'medical', 'diagnosis', 'medication', 'doctor',
            'hospital', 'illness', 'disease', 'symptom',

            # Financial
            'salary', 'income', 'financial', 'debt', 'loan',

            # Personal relationships
            'affair', 'divorce', 'conflict', 'argument',

            # Location
            'address', 'home', 'location', 'gps', 'coordinates'
        }

    async def classify_pattern_privacy(self, pattern_data: Dict) -> str:
        """
        Classify privacy level of a pattern.

        Args:
            pattern_data: Pattern to classify

        Returns:
            Privacy level (PUBLIC/INTERNAL/PRIVATE/SENSITIVE)
        """
        # Check for sensitive keywords
        pattern_str = str(pattern_data).lower()

        for keyword in self.sensitive_keywords:
            if keyword in pattern_str:
                logger.warning(f"Pattern contains sensitive keyword: {keyword}")
                return PrivacyLevel.SENSITIVE

        # Check for personal identifiers using regex
        if self._contains_personal_identifiers(pattern_str):
            return PrivacyLevel.SENSITIVE

        # Check frequency (k-anonymity)
        frequency = pattern_data.get('frequency', 0)
        if frequency < self.k_anonymity_threshold:
            return PrivacyLevel.PRIVATE

        # Check if involves specific individuals
        if self._references_individuals(pattern_data):
            return PrivacyLevel.INTERNAL

        # Otherwise, safe to share
        return PrivacyLevel.PUBLIC

    def _contains_personal_identifiers(self, text: str) -> bool:
        """Check if text contains personal identifiers."""
        patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN format
            r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',  # Credit card
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{10,}\b',  # Phone number
        ]

        for pattern in patterns:
            if re.search(pattern, text):
                return True

        return False

    def _references_individuals(self, pattern_data: Dict) -> bool:
        """Check if pattern references specific individuals."""
        # Check if pattern mentions speaker names
        if 'speaker' in pattern_data or 'david' in str(pattern_data).lower():
            return True

        return False

    async def anonymize_pattern(self, pattern_data: Dict) -> Dict:
        """
        Anonymize pattern data for sharing.

        Techniques:
        - Remove personal identifiers
        - Generalize specific details
        - Add differential privacy noise
        """
        anonymized = pattern_data.copy()

        # Remove speaker information
        if 'speaker' in anonymized:
            del anonymized['speaker']

        # Generalize time to hour (not exact minute)
        if 'timestamp' in anonymized:
            timestamp = anonymized['timestamp']
            if isinstance(timestamp, datetime):
                anonymized['timestamp'] = timestamp.replace(minute=0, second=0, microsecond=0)

        # Add noise to frequency counts (differential privacy)
        if 'frequency' in anonymized and isinstance(anonymized['frequency'], (int, float)):
            noise = self._laplace_noise(self.epsilon)
            anonymized['frequency'] = max(0, int(anonymized['frequency'] + noise))

        # Generalize topics to categories
        if 'topic' in anonymized:
            anonymized['topic_category'] = self._categorize_topic(anonymized['topic'])
            # Optionally remove specific topic
            if self._is_sensitive_topic(anonymized['topic']):
                del anonymized['topic']

        return anonymized

    def _laplace_noise(self, epsilon: float) -> float:
        """
        Generate Laplace noise for differential privacy.

        Args:
            epsilon: Privacy parameter (lower = more noise)

        Returns:
            Noise value
        """
        # Laplace mechanism: noise ~ Laplace(0, sensitivity/epsilon)
        sensitivity = 1.0  # Assume sensitivity of 1 for counts
        scale = sensitivity / epsilon

        # Generate Laplace noise
        u = random.random() - 0.5
        noise = -scale * math.copysign(1, u) * math.log(1 - 2 * abs(u))

        return noise

    def _categorize_topic(self, topic: str) -> str:
        """Categorize specific topic into broader category."""
        topic_lower = topic.lower()

        if any(word in topic_lower for word in ['code', 'bug', 'debug', 'implement']):
            return 'development'
        elif any(word in topic_lower for word in ['meeting', 'call', 'discuss']):
            return 'collaboration'
        elif any(word in topic_lower for word in ['email', 'message', 'chat']):
            return 'communication'
        elif any(word in topic_lower for word in ['learn', 'study', 'understand']):
            return 'learning'
        elif any(word in topic_lower for word in ['happy', 'sad', 'emotion']):
            return 'emotional'
        else:
            return 'general'

    def _is_sensitive_topic(self, topic: str) -> bool:
        """Check if topic is sensitive."""
        topic_lower = topic.lower()
        return any(keyword in topic_lower for keyword in self.sensitive_keywords)

    async def aggregate_patterns_safely(self,
                                       patterns: List[Dict],
                                       aggregation_type: str = 'count') -> Dict:
        """
        Aggregate multiple patterns with privacy preservation.

        Args:
            patterns: Patterns to aggregate
            aggregation_type: Type of aggregation (count/average/sum)

        Returns:
            Aggregated result with privacy guarantees
        """
        if len(patterns) < self.k_anonymity_threshold:
            logger.warning(f"Not enough patterns for k-anonymity: {len(patterns)} < {self.k_anonymity_threshold}")
            return {
                'error': 'Insufficient data for privacy-preserving aggregation',
                'required_minimum': self.k_anonymity_threshold,
                'actual_count': len(patterns)
            }

        # Anonymize all patterns first
        anonymized_patterns = [await self.anonymize_pattern(p) for p in patterns]

        # Perform aggregation
        if aggregation_type == 'count':
            result = {
                'count': len(anonymized_patterns),
                'aggregation_type': 'count'
            }
        elif aggregation_type == 'average':
            # Average frequency
            frequencies = [p.get('frequency', 0) for p in anonymized_patterns]
            avg = sum(frequencies) / len(frequencies) if frequencies else 0
            result = {
                'average_frequency': avg,
                'aggregation_type': 'average',
                'sample_size': len(anonymized_patterns)
            }
        elif aggregation_type == 'distribution':
            # Category distribution
            categories = [p.get('topic_category', 'unknown') for p in anonymized_patterns]
            distribution = {}
            for category in set(categories):
                count = categories.count(category)
                # Add noise to each count
                noise = self._laplace_noise(self.epsilon)
                distribution[category] = max(0, int(count + noise))

            result = {
                'distribution': distribution,
                'aggregation_type': 'distribution',
                'total': len(anonymized_patterns)
            }
        else:
            result = {'error': f'Unknown aggregation type: {aggregation_type}'}

        # Add privacy metadata
        result['privacy_level'] = 'anonymized'
        result['k_anonymity'] = len(patterns)
        result['epsilon'] = self.epsilon

        return result

    async def check_sharing_permissions(self,
                                       pattern_id: UUID,
                                       requesting_agent: str,
                                       pattern_scope: str) -> bool:
        """
        Check if an agent has permission to access a pattern.

        Args:
            pattern_id: Pattern to access
            requesting_agent: Agent requesting access
            pattern_scope: Scope of pattern (private/shared/global)

        Returns:
            True if access granted, False otherwise
        """
        # Global patterns are accessible to all
        if pattern_scope == 'global':
            return True

        # Shared patterns accessible to all agents
        if pattern_scope == 'shared':
            return True

        # Private patterns only accessible by owner
        if pattern_scope == 'private':
            async with get_db_connection() as conn:
                pattern = await conn.fetchrow("""
                    SELECT source_agent FROM shared_patterns
                    WHERE pattern_id = $1
                """, pattern_id)

                if pattern and pattern['source_agent'] == requesting_agent:
                    return True
                else:
                    logger.warning(f"Access denied: {requesting_agent} cannot access private pattern from {pattern.get('source_agent') if pattern else 'unknown'}")
                    return False

        return False

    async def redact_sensitive_data(self, text: str) -> Tuple[str, List[str]]:
        """
        Redact sensitive information from text.

        Args:
            text: Text to redact

        Returns:
            (redacted_text, list of redaction types)
        """
        redactions = []
        redacted = text

        # Redact email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, redacted)
        if emails:
            redacted = re.sub(email_pattern, '[EMAIL]', redacted)
            redactions.append('email')

        # Redact phone numbers
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        phones = re.findall(phone_pattern, redacted)
        if phones:
            redacted = re.sub(phone_pattern, '[PHONE]', redacted)
            redactions.append('phone')

        # Redact SSN
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        ssns = re.findall(ssn_pattern, redacted)
        if ssns:
            redacted = re.sub(ssn_pattern, '[SSN]', redacted)
            redactions.append('ssn')

        # Redact credit cards
        cc_pattern = r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'
        ccs = re.findall(cc_pattern, redacted)
        if ccs:
            redacted = re.sub(cc_pattern, '[CREDIT_CARD]', redacted)
            redactions.append('credit_card')

        return redacted, redactions

    async def generate_privacy_report(self, days: int = 30) -> Dict:
        """
        Generate privacy report showing what patterns are shared.

        Returns:
            Report with sharing statistics and privacy metrics
        """
        async with get_db_connection() as conn:
            # Count patterns by scope
            scope_stats = await conn.fetch("""
                SELECT
                    scope,
                    COUNT(*) as pattern_count,
                    COUNT(*) FILTER (WHERE is_sensitive = true) as sensitive_count
                FROM shared_patterns
                WHERE discovered_at >= NOW() - INTERVAL '%s days'
                GROUP BY scope
            """ % days)

            # Privacy violations (if any)
            violations = await conn.fetch("""
                SELECT
                    pattern_id,
                    pattern_type,
                    discovered_at
                FROM shared_patterns
                WHERE is_sensitive = true
                  AND scope IN ('shared', 'global')
                  AND discovered_at >= NOW() - INTERVAL '%s days'
            """ % days)

            report = {
                'period_days': days,
                'timestamp': datetime.now().isoformat(),
                'scope_distribution': [
                    {
                        'scope': row['scope'],
                        'total_patterns': row['pattern_count'],
                        'sensitive_patterns': row['sensitive_count']
                    }
                    for row in scope_stats
                ],
                'privacy_violations': [
                    {
                        'pattern_id': v['pattern_id'],
                        'pattern_type': v['pattern_type'],
                        'discovered_at': v['discovered_at'].isoformat()
                    }
                    for v in violations
                ],
                'k_anonymity_threshold': self.k_anonymity_threshold,
                'epsilon': self.epsilon,
                'status': 'VIOLATION' if len(violations) > 0 else 'OK'
            }

        return report


# Singleton instance
_privacy_service = None

def get_privacy_service() -> PrivacyPreservingAggregation:
    """Get singleton PrivacyPreservingAggregation instance."""
    global _privacy_service
    if _privacy_service is None:
        _privacy_service = PrivacyPreservingAggregation()
    return _privacy_service
