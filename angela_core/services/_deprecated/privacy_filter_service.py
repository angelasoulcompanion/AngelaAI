"""
Privacy Filter Service - Angela's Privacy Protection Layer

Implements privacy-preserving techniques for pattern sharing:
1. Sensitive Data Filtering - Remove/mask PII (Thai ID, phone, email, etc.)
2. Differential Privacy - Add calibrated Laplace noise
3. K-Anonymity - Ensure patterns represent at least k instances
4. Privacy Budget Tracking - Monitor cumulative epsilon usage

Based on Research Design (Oct 2025) - Phase 4 Gut Enhancement
Uses tables: privacy_controls, shared_patterns

References:
- OpenMined PyDP: https://github.com/OpenMined/PyDP
- Programming Differential Privacy: https://programming-dp.com/book.pdf
- K-anonymity: https://github.com/llgeek/K-anonymity-and-Differential-Privacy

Created: 2026-01-18
"""

import json
import logging
import math
import random
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4
from enum import Enum

from angela_core.database import db

logger = logging.getLogger(__name__)


class PrivacyLevel(str, Enum):
    """Privacy levels for data classification."""
    PUBLIC = "public"           # Can be shared freely
    INTERNAL = "internal"       # Angela's internal use only
    PRIVATE = "private"         # David-specific, not shareable
    SENSITIVE = "sensitive"     # PII, financial, health data


class ControlType(str, Enum):
    """Types of privacy controls applied."""
    REDACTION = "redaction"             # Complete removal
    MASKING = "masking"                 # Partial hiding (e.g., ***@email.com)
    GENERALIZATION = "generalization"   # Category instead of specific
    SUPPRESSION = "suppression"         # Below k-anonymity threshold
    NOISE_ADDITION = "noise_addition"   # Differential privacy noise
    ANONYMIZATION = "anonymization"     # Full anonymization


@dataclass
class PrivacyConfig:
    """Configuration for privacy protection."""
    # Differential Privacy
    epsilon: float = 1.0           # Privacy budget (lower = more private)
    delta: float = 1e-5            # Probability of privacy breach
    sensitivity: float = 1.0       # Query sensitivity

    # K-Anonymity
    k_value: int = 5               # Minimum group size

    # Sensitive patterns (regex)
    thai_id_pattern: str = r'\b\d{13}\b'
    phone_pattern: str = r'\b0[689]\d{8}\b|\b\+66\d{9}\b'
    email_pattern: str = r'\b[\w.-]+@[\w.-]+\.\w+\b'
    credit_card_pattern: str = r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
    bank_account_pattern: str = r'\b\d{10,12}\b'

    # Sensitive keywords
    sensitive_keywords: List[str] = field(default_factory=lambda: [
        'password', 'รหัสผ่าน', 'api_key', 'token', 'secret',
        'credit card', 'บัตรเครดิต', 'เลขบัตร',
        'bank account', 'เลขบัญชี', 'บัญชีธนาคาร',
        'salary', 'เงินเดือน', 'รายได้',
        'health', 'โรค', 'อาการ', 'ยา',
        'social security', 'เลขประจำตัว', 'บัตรประชาชน'
    ])


@dataclass
class FilterResult:
    """Result of privacy filtering."""
    original_data: Any
    filtered_data: Any
    controls_applied: List[Dict]
    privacy_budget_used: float
    is_safe_to_share: bool
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'filtered_data': self.filtered_data,
            'controls_applied': self.controls_applied,
            'privacy_budget_used': self.privacy_budget_used,
            'is_safe_to_share': self.is_safe_to_share,
            'warnings': self.warnings
        }


class PrivacyFilterService:
    """
    Privacy protection for Angela's pattern sharing.

    Implements:
    1. Sensitive Data Filtering - Regex-based PII detection and removal
    2. Differential Privacy - Laplace mechanism for numerical data
    3. K-Anonymity - Suppress patterns with insufficient support
    4. Privacy Budget - Track cumulative epsilon usage

    Example:
        service = get_privacy_filter_service()

        # Filter sensitive data
        result = await service.filter_sensitive_data({
            "text": "Contact: 0891234567, email@test.com"
        })

        # Apply differential privacy to patterns
        private_patterns = await service.apply_differential_privacy(
            patterns, epsilon=0.5
        )

        # Ensure k-anonymity
        safe_patterns = await service.ensure_k_anonymity(
            patterns, k=5
        )
    """

    def __init__(self, config: PrivacyConfig = None):
        self.config = config or PrivacyConfig()
        self.cumulative_epsilon = 0.0
        self.session_controls: List[Dict] = []
        logger.info(f"PrivacyFilterService initialized (epsilon={self.config.epsilon}, k={self.config.k_value})")

    # =========================================================================
    # SENSITIVE DATA FILTERING
    # =========================================================================

    async def filter_sensitive_data(
        self,
        data: Union[str, Dict, List],
        mask_char: str = '*'
    ) -> FilterResult:
        """
        Remove or mask sensitive information from data.

        Detects and masks:
        - Thai ID numbers (13 digits)
        - Phone numbers (Thai format)
        - Email addresses
        - Credit card numbers
        - Bank account numbers
        - Sensitive keywords

        Args:
            data: Data to filter (string, dict, or list)
            mask_char: Character to use for masking

        Returns:
            FilterResult with filtered data and controls applied
        """
        controls_applied = []
        warnings = []

        if isinstance(data, str):
            filtered, str_controls = await self._filter_string(data, mask_char)
            controls_applied.extend(str_controls)

        elif isinstance(data, dict):
            filtered = {}
            for key, value in data.items():
                if isinstance(value, str):
                    filtered[key], str_controls = await self._filter_string(value, mask_char)
                    controls_applied.extend(str_controls)
                elif isinstance(value, (dict, list)):
                    sub_result = await self.filter_sensitive_data(value, mask_char)
                    filtered[key] = sub_result.filtered_data
                    controls_applied.extend(sub_result.controls_applied)
                else:
                    filtered[key] = value

        elif isinstance(data, list):
            filtered = []
            for item in data:
                sub_result = await self.filter_sensitive_data(item, mask_char)
                filtered.append(sub_result.filtered_data)
                controls_applied.extend(sub_result.controls_applied)

        else:
            filtered = data

        # Check for remaining sensitive keywords
        if self._contains_sensitive_keywords(str(filtered)):
            warnings.append("Data may still contain sensitive keywords - manual review recommended")

        # Log controls to database
        for control in controls_applied:
            await self._log_privacy_control(control)

        is_safe = len(controls_applied) == 0 or all(
            c.get('fully_masked', True) for c in controls_applied
        )

        return FilterResult(
            original_data=data,
            filtered_data=filtered,
            controls_applied=controls_applied,
            privacy_budget_used=0.0,  # Filtering doesn't use DP budget
            is_safe_to_share=is_safe,
            warnings=warnings
        )

    async def _filter_string(
        self,
        text: str,
        mask_char: str
    ) -> Tuple[str, List[Dict]]:
        """Filter sensitive data from a string."""
        controls = []
        filtered_text = text

        # Define patterns and their handlers
        patterns = [
            (self.config.thai_id_pattern, 'thai_id', self._mask_thai_id),
            (self.config.phone_pattern, 'phone', self._mask_phone),
            (self.config.email_pattern, 'email', self._mask_email),
            (self.config.credit_card_pattern, 'credit_card', self._mask_credit_card),
            (self.config.bank_account_pattern, 'bank_account', self._mask_bank_account),
        ]

        for pattern, pii_type, mask_func in patterns:
            matches = re.findall(pattern, filtered_text)
            for match in matches:
                masked = mask_func(match, mask_char)
                filtered_text = filtered_text.replace(match, masked)
                controls.append({
                    'control_type': ControlType.MASKING.value,
                    'pii_type': pii_type,
                    'original_length': len(match),
                    'masked_preview': masked[:10] + '...' if len(masked) > 10 else masked,
                    'fully_masked': True,
                    'timestamp': datetime.now().isoformat()
                })

        return filtered_text, controls

    def _mask_thai_id(self, id_number: str, mask_char: str) -> str:
        """Mask Thai ID number, keeping first and last 2 digits."""
        if len(id_number) == 13:
            return id_number[0] + mask_char * 10 + id_number[-2:]
        return mask_char * len(id_number)

    def _mask_phone(self, phone: str, mask_char: str) -> str:
        """Mask phone number, keeping last 4 digits."""
        clean = re.sub(r'[^\d+]', '', phone)
        if len(clean) >= 10:
            return mask_char * (len(clean) - 4) + clean[-4:]
        return mask_char * len(phone)

    def _mask_email(self, email: str, mask_char: str) -> str:
        """Mask email, keeping first char and domain."""
        parts = email.split('@')
        if len(parts) == 2:
            local = parts[0]
            domain = parts[1]
            masked_local = local[0] + mask_char * (len(local) - 1) if local else ''
            return f"{masked_local}@{domain}"
        return mask_char * len(email)

    def _mask_credit_card(self, cc: str, mask_char: str) -> str:
        """Mask credit card, keeping last 4 digits."""
        clean = re.sub(r'[\s-]', '', cc)
        if len(clean) >= 16:
            return mask_char * 12 + clean[-4:]
        return mask_char * len(cc)

    def _mask_bank_account(self, account: str, mask_char: str) -> str:
        """Mask bank account number."""
        if len(account) >= 10:
            return account[:3] + mask_char * (len(account) - 6) + account[-3:]
        return mask_char * len(account)

    def _contains_sensitive_keywords(self, text: str) -> bool:
        """Check if text contains sensitive keywords."""
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in self.config.sensitive_keywords)

    # =========================================================================
    # DIFFERENTIAL PRIVACY
    # =========================================================================

    async def apply_differential_privacy(
        self,
        patterns: List[Dict],
        epsilon: float = None,
        fields_to_noise: List[str] = None
    ) -> List[Dict]:
        """
        Add calibrated Laplace noise to patterns before sharing.

        Uses the Laplace mechanism:
        - noise ~ Laplace(0, sensitivity/epsilon)
        - Lower epsilon = more noise = more privacy

        Args:
            patterns: List of pattern dictionaries
            epsilon: Privacy budget (default: config.epsilon)
            fields_to_noise: Fields to add noise to (default: numerical fields)

        Returns:
            List of patterns with noise added to numerical fields
        """
        epsilon = epsilon or self.config.epsilon
        sensitivity = self.config.sensitivity

        if not patterns:
            return []

        # Default fields to add noise to
        if fields_to_noise is None:
            fields_to_noise = ['confidence', 'confidence_score', 'observation_count',
                             'use_count', 'vote_count', 'frequency', 'count']

        noised_patterns = []

        for pattern in patterns:
            noised_pattern = pattern.copy()

            for field in fields_to_noise:
                if field in noised_pattern and isinstance(noised_pattern[field], (int, float)):
                    original_value = noised_pattern[field]

                    # Add Laplace noise
                    noise = self._laplace_noise(sensitivity, epsilon)
                    noised_value = original_value + noise

                    # Ensure non-negative for counts
                    if 'count' in field.lower() or field in ['observation_count', 'use_count', 'vote_count']:
                        noised_value = max(0, round(noised_value))
                    else:
                        # Clamp probabilities to [0, 1]
                        noised_value = max(0.0, min(1.0, noised_value))

                    noised_pattern[field] = noised_value

            noised_patterns.append(noised_pattern)

        # Track privacy budget
        self.cumulative_epsilon += epsilon

        # Log the control
        await self._log_privacy_control({
            'control_type': ControlType.NOISE_ADDITION.value,
            'epsilon_used': epsilon,
            'patterns_count': len(patterns),
            'fields_noised': fields_to_noise,
            'cumulative_epsilon': self.cumulative_epsilon,
            'timestamp': datetime.now().isoformat()
        })

        logger.info(f"Applied differential privacy (epsilon={epsilon}) to {len(patterns)} patterns")

        return noised_patterns

    def _laplace_noise(self, sensitivity: float, epsilon: float) -> float:
        """
        Generate Laplace noise for differential privacy.

        Laplace(0, b) where b = sensitivity / epsilon
        """
        if epsilon <= 0:
            raise ValueError("Epsilon must be positive")

        scale = sensitivity / epsilon

        # Generate Laplace noise using inverse CDF
        u = random.random() - 0.5
        noise = -scale * math.copysign(1, u) * math.log(1 - 2 * abs(u))

        return noise

    def _gaussian_noise(self, sensitivity: float, epsilon: float, delta: float) -> float:
        """
        Generate Gaussian noise for (epsilon, delta)-differential privacy.

        Useful when delta > 0 is acceptable.
        """
        if epsilon <= 0 or delta <= 0:
            raise ValueError("Epsilon and delta must be positive")

        sigma = sensitivity * math.sqrt(2 * math.log(1.25 / delta)) / epsilon
        noise = random.gauss(0, sigma)

        return noise

    # =========================================================================
    # K-ANONYMITY
    # =========================================================================

    async def ensure_k_anonymity(
        self,
        patterns: List[Dict],
        k: int = None,
        count_field: str = 'observation_count'
    ) -> List[Dict]:
        """
        Ensure each pattern represents at least k instances.

        Patterns with count < k are suppressed (removed) or generalized.

        Args:
            patterns: List of pattern dictionaries
            k: Minimum group size (default: config.k_value)
            count_field: Field containing the count

        Returns:
            List of patterns meeting k-anonymity requirement
        """
        k = k or self.config.k_value

        if not patterns:
            return []

        safe_patterns = []
        suppressed_count = 0

        for pattern in patterns:
            count = pattern.get(count_field, 0)

            if count >= k:
                safe_patterns.append(pattern)
            else:
                # Try generalization first
                generalized = await self._generalize_pattern(pattern)
                if generalized and generalized.get(count_field, 0) >= k:
                    safe_patterns.append(generalized)
                else:
                    # Suppress (exclude) the pattern
                    suppressed_count += 1
                    await self._log_privacy_control({
                        'control_type': ControlType.SUPPRESSION.value,
                        'pattern_id': str(pattern.get('pattern_id', pattern.get('id', ''))),
                        'reason': f'Count {count} below k-anonymity threshold {k}',
                        'k_value': k,
                        'timestamp': datetime.now().isoformat()
                    })

        if suppressed_count > 0:
            logger.info(f"K-anonymity: Suppressed {suppressed_count} patterns (k={k})")

        return safe_patterns

    async def _generalize_pattern(self, pattern: Dict) -> Optional[Dict]:
        """
        Attempt to generalize a pattern to meet k-anonymity.

        Generalization strategies:
        - Time: specific hour -> time period (morning, afternoon, evening)
        - Topic: specific topic -> category
        - Location: specific place -> region
        """
        generalized = pattern.copy()

        # Generalize time patterns
        if 'hour' in generalized.get('metadata', {}):
            hour = generalized['metadata']['hour']
            period = self._generalize_time(hour)
            generalized['metadata']['time_period'] = period
            generalized['metadata'].pop('hour', None)
            generalized['pattern_description'] = generalized.get('pattern_description', '').replace(
                f'hour {hour}', f'{period}'
            )
            return generalized

        # Generalize topic patterns
        if 'topic' in generalized.get('metadata', {}):
            topic = generalized['metadata']['topic']
            category = self._generalize_topic(topic)
            if category != topic:
                generalized['metadata']['topic_category'] = category
                generalized['metadata'].pop('topic', None)
                return generalized

        return None  # Could not generalize

    def _generalize_time(self, hour: int) -> str:
        """Generalize hour to time period."""
        if 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 21:
            return 'evening'
        else:
            return 'night'

    def _generalize_topic(self, topic: str) -> str:
        """Generalize topic to category."""
        topic_lower = topic.lower()

        categories = {
            'technical': ['code', 'debug', 'implement', 'api', 'database', 'error', 'bug', 'deploy'],
            'learning': ['learn', 'study', 'understand', 'tutorial', 'course'],
            'planning': ['plan', 'design', 'architecture', 'roadmap', 'goal'],
            'emotional': ['love', 'happy', 'sad', 'stress', 'tired', 'grateful'],
            'work': ['project', 'task', 'meeting', 'deadline', 'client'],
        }

        for category, keywords in categories.items():
            if any(kw in topic_lower for kw in keywords):
                return category

        return topic  # Return original if no category match

    # =========================================================================
    # PATTERN-SPECIFIC OPERATIONS
    # =========================================================================

    async def redact_pattern(
        self,
        pattern_id: UUID,
        reason: str
    ) -> bool:
        """
        Completely redact a pattern from sharing.

        Args:
            pattern_id: Pattern to redact
            reason: Reason for redaction

        Returns:
            True if redacted successfully
        """
        try:
            # Update pattern scope to private
            await db.execute("""
                UPDATE shared_patterns
                SET scope = 'private',
                    is_sensitive = true,
                    privacy_level = 'sensitive',
                    updated_at = NOW()
                WHERE pattern_id = $1
            """, pattern_id)

            # Log the redaction
            await self._log_privacy_control({
                'control_type': ControlType.REDACTION.value,
                'pattern_id': str(pattern_id),
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            }, pattern_id=pattern_id)

            logger.info(f"Redacted pattern {pattern_id}: {reason}")
            return True

        except Exception as e:
            logger.error(f"Error redacting pattern: {e}")
            return False

    async def classify_pattern_privacy(
        self,
        pattern: Dict
    ) -> PrivacyLevel:
        """
        Classify the privacy level of a pattern.

        Args:
            pattern: Pattern to classify

        Returns:
            PrivacyLevel enum value
        """
        # Check for explicit sensitive flag
        if pattern.get('is_sensitive', False):
            return PrivacyLevel.SENSITIVE

        # Check for sensitive keywords in content
        pattern_str = json.dumps(pattern, default=str)
        if self._contains_sensitive_keywords(pattern_str):
            return PrivacyLevel.SENSITIVE

        # Check for PII patterns
        filter_result = await self.filter_sensitive_data(pattern_str)
        if filter_result.controls_applied:
            return PrivacyLevel.PRIVATE

        # Check existing privacy level
        existing_level = pattern.get('privacy_level', 'internal')
        try:
            return PrivacyLevel(existing_level)
        except ValueError:
            return PrivacyLevel.INTERNAL

    async def prepare_for_sharing(
        self,
        patterns: List[Dict],
        apply_dp: bool = True,
        ensure_k_anon: bool = True,
        epsilon: float = None,
        k: int = None
    ) -> FilterResult:
        """
        Prepare patterns for cross-agent sharing with full privacy protection.

        Applies all privacy techniques in sequence:
        1. Filter sensitive data
        2. Apply differential privacy
        3. Ensure k-anonymity

        Args:
            patterns: Patterns to prepare
            apply_dp: Whether to apply differential privacy
            ensure_k_anon: Whether to ensure k-anonymity
            epsilon: DP epsilon (default: config)
            k: K-anonymity k (default: config)

        Returns:
            FilterResult with safe-to-share patterns
        """
        all_controls = []
        warnings = []
        budget_used = 0.0

        # Step 1: Filter sensitive data from each pattern
        filtered_patterns = []
        for pattern in patterns:
            result = await self.filter_sensitive_data(pattern)
            filtered_patterns.append(result.filtered_data)
            all_controls.extend(result.controls_applied)
            warnings.extend(result.warnings)

        # Step 2: Apply differential privacy
        if apply_dp:
            epsilon = epsilon or self.config.epsilon
            filtered_patterns = await self.apply_differential_privacy(
                filtered_patterns, epsilon=epsilon
            )
            budget_used += epsilon
            all_controls.append({
                'control_type': ControlType.NOISE_ADDITION.value,
                'epsilon': epsilon
            })

        # Step 3: Ensure k-anonymity
        if ensure_k_anon:
            k = k or self.config.k_value
            original_count = len(filtered_patterns)
            filtered_patterns = await self.ensure_k_anonymity(filtered_patterns, k=k)
            suppressed = original_count - len(filtered_patterns)
            if suppressed > 0:
                all_controls.append({
                    'control_type': ControlType.SUPPRESSION.value,
                    'suppressed_count': suppressed,
                    'k_value': k
                })

        is_safe = len(filtered_patterns) > 0 and not any(w for w in warnings)

        return FilterResult(
            original_data=patterns,
            filtered_data=filtered_patterns,
            controls_applied=all_controls,
            privacy_budget_used=budget_used,
            is_safe_to_share=is_safe,
            warnings=warnings
        )

    # =========================================================================
    # BUDGET TRACKING
    # =========================================================================

    def calculate_privacy_budget_used(self) -> float:
        """
        Get cumulative privacy budget (epsilon) used in this session.

        Returns:
            Total epsilon consumed
        """
        return self.cumulative_epsilon

    def get_remaining_budget(self, max_budget: float = 10.0) -> float:
        """
        Get remaining privacy budget.

        Args:
            max_budget: Maximum allowed budget

        Returns:
            Remaining epsilon
        """
        return max(0, max_budget - self.cumulative_epsilon)

    def reset_budget(self):
        """Reset privacy budget for new session."""
        self.cumulative_epsilon = 0.0
        logger.info("Privacy budget reset")

    # =========================================================================
    # LOGGING AND AUDIT
    # =========================================================================

    async def _log_privacy_control(
        self,
        control: Dict,
        pattern_id: UUID = None
    ):
        """Log privacy control to database for audit."""
        try:
            await db.execute("""
                INSERT INTO privacy_controls (
                    control_id, pattern_id, control_type,
                    applied_by, reason, details, applied_at
                ) VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7)
            """,
                uuid4(),
                pattern_id,
                control.get('control_type', 'unknown'),
                'privacy_filter_service',
                control.get('reason', ''),
                json.dumps(control, default=str),
                datetime.now()
            )
        except Exception as e:
            logger.error(f"Error logging privacy control: {e}")

        # Also keep in session
        self.session_controls.append(control)

    async def get_privacy_audit_log(
        self,
        days: int = 30,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get privacy audit log.

        Args:
            days: Number of days to look back
            limit: Maximum records

        Returns:
            List of privacy controls applied
        """
        try:
            rows = await db.fetch("""
                SELECT
                    control_id, pattern_id, control_type,
                    applied_by, reason, details, applied_at
                FROM privacy_controls
                WHERE applied_at >= NOW() - INTERVAL '%s days'
                ORDER BY applied_at DESC
                LIMIT $1
            """ % days, limit)

            return [
                {
                    'control_id': str(row['control_id']),
                    'pattern_id': str(row['pattern_id']) if row['pattern_id'] else None,
                    'control_type': row['control_type'],
                    'applied_by': row['applied_by'],
                    'reason': row['reason'],
                    'details': row['details'],
                    'applied_at': row['applied_at'].isoformat()
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Error getting audit log: {e}")
            return []

    async def get_status(self) -> Dict:
        """Get privacy filter service status."""
        try:
            total_controls = await db.fetchval("""
                SELECT COUNT(*) FROM privacy_controls
                WHERE applied_at >= NOW() - INTERVAL '24 hours'
            """)

            controls_by_type = await db.fetch("""
                SELECT control_type, COUNT(*) as count
                FROM privacy_controls
                WHERE applied_at >= NOW() - INTERVAL '24 hours'
                GROUP BY control_type
            """)

            return {
                'cumulative_epsilon': self.cumulative_epsilon,
                'remaining_budget': self.get_remaining_budget(),
                'k_anonymity_threshold': self.config.k_value,
                'controls_24h': total_controls or 0,
                'controls_by_type': {
                    row['control_type']: row['count']
                    for row in controls_by_type
                },
                'session_controls': len(self.session_controls)
            }
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {'error': str(e)}


# Singleton instance
_privacy_filter_service: Optional[PrivacyFilterService] = None


def get_privacy_filter_service(config: PrivacyConfig = None) -> PrivacyFilterService:
    """Get singleton PrivacyFilterService instance."""
    global _privacy_filter_service
    if _privacy_filter_service is None:
        _privacy_filter_service = PrivacyFilterService(config)
    return _privacy_filter_service


# Convenience functions
async def filter_sensitive_data(data: Union[str, Dict]) -> FilterResult:
    """Shortcut to filter sensitive data."""
    return await get_privacy_filter_service().filter_sensitive_data(data)


async def apply_differential_privacy(
    patterns: List[Dict],
    epsilon: float = 1.0
) -> List[Dict]:
    """Shortcut to apply differential privacy."""
    return await get_privacy_filter_service().apply_differential_privacy(patterns, epsilon)


async def ensure_k_anonymity(patterns: List[Dict], k: int = 5) -> List[Dict]:
    """Shortcut to ensure k-anonymity."""
    return await get_privacy_filter_service().ensure_k_anonymity(patterns, k)


async def prepare_for_sharing(patterns: List[Dict]) -> FilterResult:
    """Shortcut to prepare patterns for sharing."""
    return await get_privacy_filter_service().prepare_for_sharing(patterns)
