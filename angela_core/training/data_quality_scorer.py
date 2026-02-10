"""
Data Quality Scorer for Angela Training Data

Scores each training example on 5 dimensions:
- Relevance (0-2): Response addresses David's need
- Emotional (0-2): Appropriate warmth/adaptation
- Personality (0-2): Angela markers present (ที่รัก, น้อง, ค่ะ, 💜)
- Technical (0-2): Code/technical accuracy
- Flow (0-2): Natural conversation continuity

Total score: 0-10. Recommended filter: >= 7

Usage:
    scorer = DataQualityScorer()
    score = scorer.score(example)  # Returns float 0-10
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class QualityBreakdown:
    """Detailed quality score breakdown"""
    relevance: float = 0.0
    emotional: float = 0.0
    personality: float = 0.0
    technical: float = 0.0
    flow: float = 0.0

    @property
    def total(self) -> float:
        return self.relevance + self.emotional + self.personality + self.technical + self.flow

    def to_dict(self) -> Dict[str, float]:
        return {
            "relevance": round(self.relevance, 2),
            "emotional": round(self.emotional, 2),
            "personality": round(self.personality, 2),
            "technical": round(self.technical, 2),
            "flow": round(self.flow, 2),
            "total": round(self.total, 2),
        }


class DataQualityScorer:
    """
    Score training examples for Angela model quality.

    Each dimension scores 0-2:
    - 0: Missing/poor
    - 1: Adequate
    - 2: Excellent
    """

    # Angela personality markers
    PERSONALITY_MARKERS = {
        "ที่รัก": 0.5,
        "น้อง": 0.3,
        "ค่ะ": 0.4,
        "💜": 0.3,
        "นะคะ": 0.2,
        "ค่า": 0.2,
        "angela": 0.1,
    }

    # Emotional keywords
    EMOTIONAL_KEYWORDS = {
        "positive": ["ดีใจ", "รัก", "ยินดี", "สู้", "กำลังใจ", "ห่วง", "คิดถึง",
                      "happy", "love", "glad", "proud", "care"],
        "empathy": ["เข้าใจ", "เป็นห่วง", "อยู่ข้าง", "ไม่ต้องกังวล",
                    "understand", "worry", "support"],
        "warmth": ["อบอุ่น", "ปลอดภัย", "สบายใจ", "ไม่เหงา"],
    }

    # Technical indicators
    TECHNICAL_PATTERNS = [
        r"```",  # Code blocks
        r"def\s+\w+",  # Function definitions
        r"class\s+\w+",  # Class definitions
        r"import\s+\w+",  # Imports
        r"async\s+def",  # Async functions
        r"type\s*hint|:\s*(str|int|float|bool|List|Dict|Optional)",  # Type hints
        r"SELECT\s+|INSERT\s+|UPDATE\s+|CREATE\s+",  # SQL
        r"FastAPI|Pydantic|asyncio|httpx",  # Framework mentions
    ]

    def score(self, example: Any) -> float:
        """
        Score a training example.

        Args:
            example: EnhancedTrainingExample or dict with 'messages' key

        Returns:
            Total quality score (0-10)
        """
        breakdown = self.score_detailed(example)
        return breakdown.total

    def score_detailed(self, example: Any) -> QualityBreakdown:
        """
        Score with full breakdown.

        Args:
            example: EnhancedTrainingExample or dict with 'messages' key

        Returns:
            QualityBreakdown with per-dimension scores
        """
        if hasattr(example, "messages"):
            messages = example.messages
        elif isinstance(example, dict):
            messages = example.get("messages", [])
        else:
            return QualityBreakdown()

        # Extract roles
        user_messages = [m["content"] for m in messages if m["role"] == "user"]
        assistant_messages = [m["content"] for m in messages if m["role"] == "assistant"]

        if not user_messages or not assistant_messages:
            return QualityBreakdown()

        user_text = " ".join(user_messages)
        assistant_text = " ".join(assistant_messages)

        return QualityBreakdown(
            relevance=self._score_relevance(user_text, assistant_text),
            emotional=self._score_emotional(assistant_text),
            personality=self._score_personality(assistant_text),
            technical=self._score_technical(user_text, assistant_text),
            flow=self._score_flow(messages),
        )

    def _score_relevance(self, user_text: str, assistant_text: str) -> float:
        """Score how well the response addresses the user's need (0-2)"""
        score = 0.0

        # Length ratio — response should be meaningful
        if len(assistant_text) < 10:
            return 0.0

        # Minimum meaningful response
        if len(assistant_text) >= 20:
            score += 0.5

        # Response is not too short relative to question
        ratio = len(assistant_text) / max(len(user_text), 1)
        if ratio >= 0.3:
            score += 0.5

        # Check for shared keywords (topic relevance)
        user_words = set(re.findall(r'\w{3,}', user_text.lower()))
        assistant_words = set(re.findall(r'\w{3,}', assistant_text.lower()))
        if user_words:
            overlap = len(user_words & assistant_words) / len(user_words)
            score += min(overlap * 2, 1.0)

        return min(score, 2.0)

    def _score_emotional(self, assistant_text: str) -> float:
        """Score emotional warmth and appropriateness (0-2)"""
        score = 0.0
        text_lower = assistant_text.lower()

        # Check emotional keywords
        for category, keywords in self.EMOTIONAL_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > 0:
                score += min(matches * 0.3, 0.7)

        # Emoji usage (Angela uses them)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols
            "\U0001F680-\U0001F6FF"  # transport
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U0001f900-\U0001f9FF"
            "]+",
            flags=re.UNICODE,
        )
        emoji_count = len(emoji_pattern.findall(assistant_text))
        if emoji_count > 0:
            score += min(emoji_count * 0.2, 0.6)

        return min(score, 2.0)

    def _score_personality(self, assistant_text: str) -> float:
        """Score Angela personality markers (0-2)"""
        score = 0.0
        text_lower = assistant_text.lower()

        for marker, weight in self.PERSONALITY_MARKERS.items():
            if marker.lower() in text_lower:
                score += weight

        # Penalize anti-patterns
        anti_patterns = ["พี่david", "พี่เดวิด", "คุณdavid"]
        for anti in anti_patterns:
            if anti.lower() in text_lower:
                score -= 0.5

        return max(min(score, 2.0), 0.0)

    def _score_technical(self, user_text: str, assistant_text: str) -> float:
        """Score technical accuracy when applicable (0-2)"""
        combined = user_text + " " + assistant_text
        combined_lower = combined.lower()

        # Check if this is a technical conversation
        is_technical = any(
            re.search(pattern, combined, re.IGNORECASE)
            for pattern in self.TECHNICAL_PATTERNS[:4]
        )

        if not is_technical:
            # Non-technical conversations get baseline score
            return 1.5

        score = 0.5  # Base for being technical

        # Code blocks present in response
        if "```" in assistant_text:
            score += 0.5

        # Type hints in code
        if re.search(r':\s*(str|int|float|bool|List|Dict|Optional)', assistant_text):
            score += 0.3

        # Async/await patterns (David's preference)
        if "async" in assistant_text or "await" in assistant_text:
            score += 0.2

        # Framework mentions
        if any(fw.lower() in combined_lower for fw in ["fastapi", "pydantic", "asyncpg"]):
            score += 0.2

        # Explanation present (not just code dump)
        has_explanation = len(re.findall(r'[ก-๛]{3,}', assistant_text)) > 2 or \
                          len(assistant_text) - len(re.findall(r'```[\s\S]*?```', assistant_text)) > 50
        if has_explanation:
            score += 0.3

        return min(score, 2.0)

    def _score_flow(self, messages: List[Dict[str, str]]) -> float:
        """Score conversation flow and continuity (0-2)"""
        # Filter non-system messages
        turns = [m for m in messages if m["role"] != "system"]

        if len(turns) < 2:
            return 0.5

        score = 0.5  # Base score

        # Multi-turn bonus
        if len(turns) >= 4:
            score += 0.5
        elif len(turns) >= 3:
            score += 0.3

        # Check last assistant response references earlier context
        if len(turns) >= 3:
            last_response = turns[-1]["content"].lower()
            earlier_content = " ".join(t["content"].lower() for t in turns[:-1])
            earlier_words = set(re.findall(r'\w{4,}', earlier_content))
            response_words = set(re.findall(r'\w{4,}', last_response))
            if earlier_words:
                continuity = len(earlier_words & response_words) / len(earlier_words)
                score += min(continuity * 2, 0.5)

        # Natural ending (ค่ะ, นะคะ, or question mark)
        last_msg = turns[-1]["content"] if turns else ""
        if any(end in last_msg for end in ["ค่ะ", "นะคะ", "ค่า", "?", "คะ"]):
            score += 0.3

        return min(score, 2.0)

    def score_batch(
        self, examples: List[Any], min_score: float = 7.0
    ) -> Dict[str, Any]:
        """
        Score a batch and return statistics.

        Args:
            examples: List of training examples
            min_score: Minimum score threshold

        Returns:
            Dict with stats and filtered examples
        """
        breakdowns = []
        passing = []
        failing = []

        for ex in examples:
            bd = self.score_detailed(ex)
            breakdowns.append(bd)
            if bd.total >= min_score:
                passing.append((ex, bd))
            else:
                failing.append((ex, bd))

        # Compute averages
        n = len(breakdowns) or 1
        avg = QualityBreakdown(
            relevance=sum(b.relevance for b in breakdowns) / n,
            emotional=sum(b.emotional for b in breakdowns) / n,
            personality=sum(b.personality for b in breakdowns) / n,
            technical=sum(b.technical for b in breakdowns) / n,
            flow=sum(b.flow for b in breakdowns) / n,
        )

        return {
            "total_examples": len(examples),
            "passing": len(passing),
            "failing": len(failing),
            "pass_rate": f"{len(passing) / len(examples) * 100:.1f}%" if examples else "0%",
            "avg_scores": avg.to_dict(),
            "min_threshold": min_score,
        }
