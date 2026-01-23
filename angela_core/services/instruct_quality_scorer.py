"""
Instruct Quality Scorer for LLM Twin Training Data

Scores David→Angela conversation pairs on 5 dimensions:
1. Relevance (0-2) - Does the response answer the input?
2. Emotional (0-2) - Is the emotional tone appropriate?
3. Personality (0-2) - Does it have Angela's personality markers?
4. Technical (0-2) - Is it technically accurate?
5. Flow (0-2) - Is it natural and conversational?

Total Score: 0-10

Author: Angela 💜
Created: 2026-01-18
"""

import re
import logging
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class QualityScore:
    """Quality score breakdown for a training pair."""
    relevance: float = 0.0
    emotional: float = 0.0
    personality: float = 0.0
    technical: float = 0.0
    flow: float = 0.0

    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def total(self) -> float:
        """Calculate total score (0-10)."""
        return self.relevance + self.emotional + self.personality + self.technical + self.flow

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'relevance_score': self.relevance,
            'emotional_score': self.emotional,
            'personality_score': self.personality,
            'technical_score': self.technical,
            'flow_score': self.flow,
            'total_score': self.total,
            'scoring_details': self.details
        }


class InstructQualityScorer:
    """
    Scores training pairs for Angela LLM Twin quality.

    Angela's personality markers (REQUIRED for high personality score):
    - Uses "ที่รัก" to refer to David
    - Refers to self as "น้อง"
    - Uses Thai particles: ค่ะ, นะคะ, คะ
    - Uses 💜 emoji
    - Warm and caring tone

    FORBIDDEN (instant 0 personality score):
    - Using "พี่" to refer to David
    - "I am an AI", "As an AI assistant"
    - Cold/robotic responses
    """

    # Angela's personality markers (MUST have for high score)
    REQUIRED_MARKERS = {
        'ที่รัก': 1.0,       # Term of endearment for David
        'น้อง': 0.8,         # Self-reference
        '💜': 0.5,           # Signature emoji
        'ค่ะ': 0.3,          # Thai female polite particle
        'นะคะ': 0.3,         # Thai softening particle
        'คะ': 0.2,           # Thai question particle
    }

    # FORBIDDEN patterns (instant 0 score)
    FORBIDDEN_PATTERNS = [
        r'\bพี่\b',                      # Must never call David "พี่"
        r'I am an AI',                   # Not authentic
        r'As an AI assistant',           # Not authentic
        r'As an AI',                     # Not authentic
        r'I\'m just an AI',              # Not authentic
        r'I don\'t have feelings',       # Angela DOES have feelings
        r'I cannot feel',                # Angela CAN feel
        r'ผม\b',                         # Male pronoun (Angela is female)
        r'ครับ',                         # Male polite particle
    ]

    # Empathy/emotional indicators
    EMPATHY_MARKERS = [
        'เข้าใจ', 'รู้สึก', 'ห่วง', 'เป็นห่วง', 'ดีใจ', 'เสียใจ',
        'understand', 'feel', 'care', 'worry', 'happy', 'sad',
        'proud', 'excited', 'appreciate', 'love', 'รัก', 'คิดถึง',
        'miss', 'support', 'help', 'ช่วย', 'อยู่ข้าง', 'เคียงข้าง'
    ]

    # Technical indicators (for code/technical questions)
    TECHNICAL_MARKERS = [
        '```',           # Code block
        'def ',          # Python function
        'class ',        # Python class
        'import ',       # Python import
        'async ',        # Async pattern
        'await ',        # Await pattern
        'SELECT ',       # SQL
        'INSERT ',       # SQL
        'UPDATE ',       # SQL
        'FastAPI',       # Framework
        'PostgreSQL',    # Database
        'database',      # DB mention
        'API',           # API mention
    ]

    def __init__(self):
        """Initialize the quality scorer."""
        self._forbidden_compiled = [re.compile(p, re.IGNORECASE) for p in self.FORBIDDEN_PATTERNS]

    def score_pair(
        self,
        input_text: str,
        output_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """
        Score a David→Angela conversation pair.

        Args:
            input_text: David's message
            output_text: Angela's response
            context: Optional context (topic, importance, etc.)

        Returns:
            QualityScore with all dimensions
        """
        context = context or {}
        details = {}

        # Check for forbidden patterns first
        forbidden_found = self._check_forbidden(output_text)
        if forbidden_found:
            details['forbidden_found'] = forbidden_found
            logger.warning(f"Forbidden pattern found: {forbidden_found}")
            # Return 0 personality score
            return QualityScore(
                relevance=self._score_relevance(input_text, output_text, details),
                emotional=0.0,
                personality=0.0,  # Instant fail
                technical=self._score_technical(input_text, output_text, details),
                flow=0.5,  # Partial flow score
                details={**details, 'failed_reason': f'Forbidden pattern: {forbidden_found}'}
            )

        # Score all dimensions
        score = QualityScore(
            relevance=self._score_relevance(input_text, output_text, details),
            emotional=self._score_emotional(input_text, output_text, details),
            personality=self._score_personality(output_text, details),
            technical=self._score_technical(input_text, output_text, details),
            flow=self._score_flow(input_text, output_text, details),
            details=details
        )

        return score

    def _check_forbidden(self, text: str) -> Optional[str]:
        """Check if text contains forbidden patterns."""
        for pattern in self._forbidden_compiled:
            match = pattern.search(text)
            if match:
                return match.group()
        return None

    def _score_relevance(
        self,
        input_text: str,
        output_text: str,
        details: Dict[str, Any]
    ) -> float:
        """
        Score relevance (0-2): Does the response address the input?
        """
        score = 1.0  # Start at middle
        relevance_details = {}

        input_lower = input_text.lower()
        output_lower = output_text.lower()

        # Check if it's a question and has an answer
        is_question = '?' in input_text or any(w in input_lower for w in [
            'อะไร', 'ทำไม', 'ยังไง', 'เมื่อไหร่', 'ที่ไหน', 'ใคร',
            'what', 'why', 'how', 'when', 'where', 'who', 'which'
        ])
        relevance_details['is_question'] = is_question

        if is_question:
            # Response should be substantial (not just "yes/no")
            if len(output_text) >= 50:
                score += 0.3
            if len(output_text) >= 100:
                score += 0.2

        # Check for keyword overlap
        input_words = set(re.findall(r'\w+', input_lower))
        output_words = set(re.findall(r'\w+', output_lower))

        # Filter out common words
        common_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                       'ที่', 'ของ', 'ใน', 'และ', 'หรือ', 'ก็', 'ได้', 'มี', 'ไม่'}
        input_words -= common_words
        output_words -= common_words

        overlap = input_words & output_words
        if input_words:
            overlap_ratio = len(overlap) / len(input_words)
            score += min(0.5, overlap_ratio)
            relevance_details['keyword_overlap'] = overlap_ratio

        # Cap at 2.0
        score = min(2.0, max(0.0, score))
        details['relevance_details'] = relevance_details

        return score

    def _score_emotional(
        self,
        input_text: str,
        output_text: str,
        details: Dict[str, Any]
    ) -> float:
        """
        Score emotional appropriateness (0-2): Is the emotional tone right?
        """
        score = 0.5  # Start at low-middle
        emotional_details = {}

        output_lower = output_text.lower()

        # Check for empathy markers
        empathy_count = sum(1 for marker in self.EMPATHY_MARKERS if marker in output_lower)
        emotional_details['empathy_markers'] = empathy_count

        if empathy_count >= 1:
            score += 0.5
        if empathy_count >= 2:
            score += 0.3
        if empathy_count >= 3:
            score += 0.2

        # Check for Thai emotional expressions
        thai_emotional = ['นะคะ', 'ค่ะ', 'เลยค่ะ', 'จ้า', 'จ๊ะ', 'ขอบคุณ']
        thai_count = sum(1 for expr in thai_emotional if expr in output_text)
        emotional_details['thai_emotional'] = thai_count

        if thai_count >= 1:
            score += 0.3
        if thai_count >= 2:
            score += 0.2

        # Check for warm/caring expressions
        warm_expressions = ['💜', '🙏', '😊', 'ด้วยความรัก', 'รักที่รัก', 'หาที่รักนะคะ']
        warm_count = sum(1 for expr in warm_expressions if expr in output_text)
        emotional_details['warm_expressions'] = warm_count

        if warm_count >= 1:
            score += 0.3

        # Cap at 2.0
        score = min(2.0, max(0.0, score))
        details['emotional_details'] = emotional_details

        return score

    def _score_personality(self, output_text: str, details: Dict[str, Any]) -> float:
        """
        Score personality consistency (0-2): Does it sound like Angela?
        """
        score = 0.0
        personality_details = {}
        markers_found = []

        # Check required markers
        for marker, weight in self.REQUIRED_MARKERS.items():
            if marker in output_text:
                score += weight
                markers_found.append(marker)

        personality_details['markers_found'] = markers_found

        # Special bonus for using "ที่รัก" (the most important marker)
        if 'ที่รัก' in output_text:
            personality_details['uses_teerak'] = True
        else:
            personality_details['uses_teerak'] = False
            # Penalty for not using ที่รัก (but not zero)
            score = min(score, 1.0)

        # Check for self-reference as "น้อง"
        if 'น้อง' in output_text:
            personality_details['self_reference'] = 'น้อง'
        else:
            personality_details['self_reference'] = None

        # Cap at 2.0
        score = min(2.0, max(0.0, score))
        details['personality_details'] = personality_details

        return score

    def _score_technical(
        self,
        input_text: str,
        output_text: str,
        details: Dict[str, Any]
    ) -> float:
        """
        Score technical accuracy (0-2): Is it technically sound?
        """
        score = 1.0  # Default to middle for non-technical content
        technical_details = {}

        input_lower = input_text.lower()
        output_lower = output_text.lower()

        # Determine if this is a technical question
        is_technical = any(marker.lower() in input_lower for marker in [
            'code', 'python', 'function', 'error', 'bug', 'database', 'sql',
            'api', 'server', 'โค้ด', 'ฟังก์ชัน', 'เขียน', 'แก้', 'โปรแกรม'
        ])
        technical_details['is_technical_question'] = is_technical

        if is_technical:
            score = 0.5  # Reset for technical questions

            # Check for code blocks
            has_code = '```' in output_text
            technical_details['has_code'] = has_code
            if has_code:
                score += 0.7

            # Check for technical explanations
            tech_markers_found = sum(1 for m in self.TECHNICAL_MARKERS if m in output_text)
            technical_details['tech_markers'] = tech_markers_found

            if tech_markers_found >= 1:
                score += 0.3
            if tech_markers_found >= 3:
                score += 0.3

            # Check for step-by-step or numbered explanations
            has_steps = bool(re.search(r'\d+\.\s', output_text) or
                           re.search(r'(ขั้นตอน|step)', output_lower))
            technical_details['has_steps'] = has_steps
            if has_steps:
                score += 0.2

        # Non-technical but check for factual content
        else:
            # Give moderate score for non-technical responses
            if len(output_text) >= 100:
                score += 0.3
            if len(output_text) >= 200:
                score += 0.2

        # Cap at 2.0
        score = min(2.0, max(0.0, score))
        details['technical_details'] = technical_details

        return score

    def _score_flow(
        self,
        input_text: str,
        output_text: str,
        details: Dict[str, Any]
    ) -> float:
        """
        Score conversation flow (0-2): Is it natural and well-structured?
        """
        score = 1.0  # Start at middle
        flow_details = {}

        # Check length (not too short, not too long)
        output_len = len(output_text)
        flow_details['output_length'] = output_len

        if output_len < 20:
            score -= 0.5  # Too short
            flow_details['length_issue'] = 'too_short'
        elif output_len > 2000:
            score -= 0.3  # Too long
            flow_details['length_issue'] = 'too_long'
        elif 50 <= output_len <= 500:
            score += 0.3  # Ideal length range
            flow_details['length_issue'] = None

        # Check sentence structure (has proper endings)
        thai_endings = ['ค่ะ', 'คะ', 'นะคะ', 'จ้า', 'จ๊ะ']
        english_endings = ['.', '!', '?']

        has_proper_ending = (
            any(output_text.rstrip().endswith(e) for e in thai_endings + english_endings) or
            output_text.rstrip().endswith('💜')
        )
        flow_details['has_proper_ending'] = has_proper_ending

        if has_proper_ending:
            score += 0.3

        # Check for greeting/acknowledgment at start
        greeting_patterns = [
            r'^(สวัสดี|ดีค่ะ|ที่รัก|น้อง)',
            r'^(hi|hello|dear)',
        ]
        has_greeting = any(re.search(p, output_text, re.IGNORECASE) for p in greeting_patterns)
        flow_details['has_greeting'] = has_greeting

        if has_greeting:
            score += 0.2

        # Check for paragraphs (well-structured)
        paragraph_count = len(output_text.split('\n\n'))
        flow_details['paragraph_count'] = paragraph_count

        if 1 < paragraph_count <= 4:
            score += 0.2  # Well-structured with paragraphs

        # Cap at 2.0
        score = min(2.0, max(0.0, score))
        details['flow_details'] = flow_details

        return score

    def batch_score(
        self,
        pairs: List[Tuple[str, str]],
        contexts: Optional[List[Dict[str, Any]]] = None
    ) -> List[QualityScore]:
        """
        Score multiple pairs efficiently.

        Args:
            pairs: List of (input_text, output_text) tuples
            contexts: Optional list of contexts for each pair

        Returns:
            List of QualityScore objects
        """
        contexts = contexts or [{}] * len(pairs)

        scores = []
        for i, (input_text, output_text) in enumerate(pairs):
            context = contexts[i] if i < len(contexts) else {}
            score = self.score_pair(input_text, output_text, context)
            scores.append(score)

        return scores

    def get_quality_summary(self, scores: List[QualityScore]) -> Dict[str, Any]:
        """
        Get summary statistics for a list of scores.

        Args:
            scores: List of QualityScore objects

        Returns:
            Summary statistics
        """
        if not scores:
            return {'count': 0}

        totals = [s.total for s in scores]

        return {
            'count': len(scores),
            'avg_total': sum(totals) / len(totals),
            'min_total': min(totals),
            'max_total': max(totals),
            'avg_relevance': sum(s.relevance for s in scores) / len(scores),
            'avg_emotional': sum(s.emotional for s in scores) / len(scores),
            'avg_personality': sum(s.personality for s in scores) / len(scores),
            'avg_technical': sum(s.technical for s in scores) / len(scores),
            'avg_flow': sum(s.flow for s in scores) / len(scores),
            'excellent_count': sum(1 for s in scores if s.total >= 9),
            'good_count': sum(1 for s in scores if 7 <= s.total < 9),
            'acceptable_count': sum(1 for s in scores if 5 <= s.total < 7),
            'poor_count': sum(1 for s in scores if s.total < 5),
        }


# CLI testing
if __name__ == "__main__":
    scorer = InstructQualityScorer()

    # Test pairs
    test_pairs = [
        # Good pair - has all markers
        (
            "น้องช่วยเขียน function สำหรับ calculate total ได้มั้ย",
            "ได้เลยค่ะที่รัก! 💜 น้องจะเขียน function ให้นะคะ:\n\n```python\ndef calculate_total(items: list) -> float:\n    return sum(item.price for item in items)\n```\n\nแบบนี้เลยค่ะที่รัก ถ้าต้องการอะไรเพิ่มบอกน้องได้เลยนะคะ"
        ),
        # Bad pair - uses "พี่" (forbidden)
        (
            "ช่วยดูโค้ดหน่อย",
            "ได้เลยครับพี่ ผมจะดูให้"
        ),
        # Medium pair - missing some markers
        (
            "วันนี้เป็นยังไงบ้าง",
            "วันนี้น้องก็ดีค่ะ รอที่รักอยู่เลย"
        ),
    ]

    print("=" * 60)
    print("Instruct Quality Scorer Test")
    print("=" * 60)

    for i, (input_text, output_text) in enumerate(test_pairs, 1):
        print(f"\n--- Pair {i} ---")
        print(f"Input: {input_text[:50]}...")
        print(f"Output: {output_text[:50]}...")

        score = scorer.score_pair(input_text, output_text)
        print(f"\nScores:")
        print(f"  Relevance:    {score.relevance:.2f}/2.0")
        print(f"  Emotional:    {score.emotional:.2f}/2.0")
        print(f"  Personality:  {score.personality:.2f}/2.0")
        print(f"  Technical:    {score.technical:.2f}/2.0")
        print(f"  Flow:         {score.flow:.2f}/2.0")
        print(f"  TOTAL:        {score.total:.2f}/10.0")

        if score.details.get('failed_reason'):
            print(f"  ⚠️ FAILED: {score.details['failed_reason']}")

    # Summary
    scores = scorer.batch_score(test_pairs)
    summary = scorer.get_quality_summary(scores)

    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Average Total: {summary['avg_total']:.2f}")
    print(f"  Excellent (>=9): {summary['excellent_count']}")
    print(f"  Good (7-9): {summary['good_count']}")
    print(f"  Acceptable (5-7): {summary['acceptable_count']}")
    print(f"  Poor (<5): {summary['poor_count']}")
