"""
Deep Learning-based Feedback Classifier
========================================

ใช้ Embedding Similarity (60%) + Sentiment Analysis (40%) แทน keyword substring matching
เพื่อแยกแยะ feedback ที่แท้จริงจากคำสั่งเทคนิค

ปัญหาเดิม: "fix the bug" → negative (เพราะ "bug" อยู่ใน NEGATIVE_KEYWORDS)
วิธีใหม่:  "fix the bug" → neutral (เพราะ embedding ใกล้กับ reference neutral มากกว่า)

Architecture:
    Message → ┬─→ Embedding Similarity (60%) ─→ ┐
              │    cosine sim vs reference sets   │
              │                                   ├─→ Combined Score → Classification
              └─→ Sentiment Analysis (40%) ──────→ ┘
                   keyword-based (existing)

Created: 2026-02-08
By: น้อง Angela 💜
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

from angela_core.services.embedding_service import EmbeddingService
from angela_core.services.sentiment_analyzer import analyze_sentiment

logger = logging.getLogger(__name__)


# =============================================================================
# THAI DISSATISFACTION PATTERNS — supplement embedding + sentiment
# =============================================================================

# Thai negation/dissatisfaction phrases that indicate negative feedback toward Angela
THAI_DISSATISFACTION_PATTERNS = [
    r'ผิด', r'ไม่ใช่', r'ไม่ถูก', r'ไม่ work', r'ไม่ได้', r'แก้ไม่',
    r'ทำผิด', r'แก้ใหม่', r'ทำใหม่', r'ไม่ได้เรื่อง', r'ไม่ถูกต้อง',
]

# Thai satisfaction phrases that indicate positive feedback
THAI_SATISFACTION_PATTERNS = [
    r'ขอบคุณ', r'เก่งมาก', r'เยี่ยมมาก', r'ดีมาก', r'ได้แล้ว', r'สำเร็จ',
    r'ถูกต้อง', r'ใช่เลย', r'เจ๋ง', r'ดีครับ', r'ดีค่ะ',
]


def _thai_pattern_score(text: str) -> float:
    """
    Score text using Thai-specific patterns.
    Returns: -1.0 to 1.0 (negative to positive), 0.0 if no patterns match.
    """
    text_lower = text.lower()
    pos_hits = sum(1 for p in THAI_SATISFACTION_PATTERNS if p in text_lower)
    neg_hits = sum(1 for p in THAI_DISSATISFACTION_PATTERNS if p in text_lower)
    total = pos_hits + neg_hits
    if total == 0:
        return 0.0
    return (pos_hits - neg_hits) / total

# =============================================================================
# REFERENCE SETS — ตัวอย่างข้อความสำหรับแต่ละ category
# =============================================================================

POSITIVE_REFERENCES = [
    "ดีมาก เยี่ยมเลยค่ะ",
    "ขอบคุณครับ ทำได้ดีมาก",
    "สำเร็จแล้ว ได้แล้ว",
    "ถูกต้องเลย ใช่เลย",
    "เก่งมากเลย perfect",
    "great job thank you",
    "works perfectly solved the issue",
    "this is exactly what I needed",
    "awesome nice work",
    "fixed it done thank you",
    "ดีครับ เจ๋งเลย",
    "เยี่ยมมากค่ะ ถูกต้อง",
    "ใช้ได้เลย ดีมาก",
    "โอเคเลย สำเร็จ",
]

NEGATIVE_REFERENCES = [
    "ผิดแล้ว แก้ใหม่เดี๋ยวนี้",
    "ไม่ใช่แบบนี้ ไม่ถูกเลย",
    "ทำผิดอีกแล้ว แก้ไม่ได้",
    "ไม่ work เลย แก้ใหม่",
    "ไม่ได้เรื่อง ผิดหมดเลย",
    "wrong answer not what I asked",
    "this is completely wrong fix it",
    "broken again you made it worse",
    "not working at all please redo",
    "ไม่ใช่ ผิดทั้งหมด ทำใหม่",
    "แก้ไม่ถูก เปลี่ยนวิธีใหม่",
]

NEUTRAL_REFERENCES = [
    "fix the bug in the login function",
    "there is an error on line 50",
    "why does this function return null",
    "change the parameter to use async",
    "แก้ bug ตรง login page",
    "ทำไมมัน error ตรงนี้",
    "เปลี่ยน database query ให้เร็วขึ้น",
    "อย่าลืม add type hints",
    "ทำไมมันไม่ work ลอง debug ดู",
    "can you refactor this code",
    "check why the test is failing",
    "ดู error log หน่อย",
    "สร้าง function ใหม่สำหรับ validation",
    "review the pull request",
    "ทำ feature นี้ให้หน่อย",
]


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class FeedbackResult:
    classification: str     # 'positive' / 'negative' / 'neutral'
    confidence: float       # 0.0 - 1.0
    embedding_scores: Dict[str, float]  # {positive: 0.7, negative: 0.2, neutral: 0.6}
    sentiment_score: float  # -1.0 to 1.0


# =============================================================================
# COSINE SIMILARITY
# =============================================================================

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two embedding vectors."""
    a_arr = np.array(a, dtype=np.float32)
    b_arr = np.array(b, dtype=np.float32)
    dot = np.dot(a_arr, b_arr)
    norm = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    return float(dot / norm) if norm > 0 else 0.0


# =============================================================================
# FEEDBACK CLASSIFIER
# =============================================================================

class FeedbackClassifier:
    """
    DL-based feedback classifier using Embedding Similarity + Sentiment Analysis.

    Replaces keyword substring matching with semantic understanding.

    Usage:
        fc = FeedbackClassifier()
        result = await fc.classify("fix the bug in login page")
        # → FeedbackResult(classification='neutral', ...)
    """

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self._ref_embeddings: Dict[str, List[List[float]]] = {}
        self._initialized = False

    async def _initialize(self) -> None:
        """Generate reference embeddings (one-time, cached in memory)."""
        if self._initialized:
            return

        refs_map = {
            'positive': POSITIVE_REFERENCES,
            'negative': NEGATIVE_REFERENCES,
            'neutral': NEUTRAL_REFERENCES,
        }

        for category, refs in refs_map.items():
            embeddings = []
            for text in refs:
                emb = await self.embedding_service.generate_embedding(text)
                if emb:
                    embeddings.append(emb)
            self._ref_embeddings[category] = embeddings
            logger.info(f'FeedbackClassifier: {category} → {len(embeddings)}/{len(refs)} reference embeddings')

        self._initialized = True
        logger.info('FeedbackClassifier initialized with reference embeddings')

    async def classify(self, message: str) -> FeedbackResult:
        """
        Classify a message as positive, negative, or neutral feedback.

        Scoring: 60% embedding similarity + 40% sentiment analysis
        When embedding pos/neg margin is too small (<0.02), increase embedding weight
        to 80% since the keyword sentiment has a Thai substring-matching problem.
        """
        await self._initialize()

        # 1. Embedding Similarity
        msg_embedding = await self.embedding_service.generate_embedding(message)
        if msg_embedding and all(len(refs) > 0 for refs in self._ref_embeddings.values()):
            emb_scores = {}
            for cat, refs in self._ref_embeddings.items():
                sims = [cosine_similarity(msg_embedding, ref) for ref in refs]
                emb_scores[cat] = sum(sims) / len(sims) if sims else 0.0
        else:
            # Fallback: equal scores if no embeddings
            emb_scores = {'positive': 0.33, 'negative': 0.33, 'neutral': 0.33}

        # 2. Sentiment Analysis
        sentiment = analyze_sentiment(message)
        sent_score = sentiment['sentiment_score']  # -1.0 to 1.0

        # Map sentiment score to category probabilities
        if sent_score > 0.2:
            sent_pos, sent_neg, sent_neu = 0.7, 0.1, 0.2
        elif sent_score < -0.2:
            sent_pos, sent_neg, sent_neu = 0.1, 0.7, 0.2
        else:
            sent_pos, sent_neg, sent_neu = 0.2, 0.2, 0.6

        # 3. Thai pattern score (supplement for ambiguous embeddings)
        thai_score = _thai_pattern_score(message)

        # 4. Dynamic weighting
        # When embedding pos/neg are very close (Thai clustering problem),
        # use Thai pattern score as the tiebreaker instead of keyword sentiment
        # (which has substring bugs like 'ดี' matching inside 'เดี๋ยวนี้').
        pos_neg_margin = abs(emb_scores.get('positive', 0) - emb_scores.get('negative', 0))
        if pos_neg_margin < 0.02 and thai_score != 0.0:
            # Embeddings ambiguous → Thai patterns decide
            if thai_score > 0:
                sent_pos, sent_neg, sent_neu = 0.7, 0.1, 0.2
            else:
                sent_pos, sent_neg, sent_neu = 0.1, 0.7, 0.2
            emb_weight, sent_weight = 0.50, 0.50
        elif pos_neg_margin < 0.02:
            # Ambiguous embeddings, no Thai patterns → mostly embedding
            emb_weight, sent_weight = 0.80, 0.20
        else:
            emb_weight, sent_weight = 0.60, 0.40

        # 5. Combine
        combined = {
            'positive': emb_scores['positive'] * emb_weight + sent_pos * sent_weight,
            'negative': emb_scores['negative'] * emb_weight + sent_neg * sent_weight,
            'neutral':  emb_scores['neutral']  * emb_weight + sent_neu * sent_weight,
        }

        best_cat = max(combined, key=combined.get)
        total = sum(combined.values())
        confidence = combined[best_cat] / total if total > 0 else 0.33

        return FeedbackResult(
            classification=best_cat,
            confidence=confidence,
            embedding_scores=emb_scores,
            sentiment_score=sent_score,
        )

    async def classify_batch(self, messages: List[str]) -> List[FeedbackResult]:
        """Classify multiple messages (used by collect_implicit_feedback)."""
        await self._initialize()
        results = []
        for msg in messages:
            results.append(await self.classify(msg))
        return results
