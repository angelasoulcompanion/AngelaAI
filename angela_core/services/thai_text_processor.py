"""
Thai Text Processing Service for RAG System
Optimized for Thai language with proper tokenization, normalization, and analysis
"""

import re
from typing import List, Dict, Tuple
from collections import Counter
import asyncio

from pythainlp import word_tokenize, sent_tokenize, pos_tag
from pythainlp.util import normalize as thai_normalize
from pythainlp.corpus import thai_stopwords
try:
    from pythainlp.tag.named_entity import NER
    # Initialize NER with corpus-based engine (no deep learning required)
    ner_tagger = NER(engine='thainer')
    ner_available = True
except Exception as e:
    # Fallback if NER is not available or fails to initialize
    ner_tagger = None
    ner_available = False
import logging

logger = logging.getLogger(__name__)


class ThaiTextProcessor:
    """ระบบประมวลผลภาษาไทยแบบลึก"""

    def __init__(self):
        """Initialize Thai text processor with all necessary resources"""
        self.stopwords = thai_stopwords()

        # Custom Thai stopwords to filter
        self.custom_stopwords = {
            'ค่ะ', 'ครับ', 'คะ', 'นะคะ', 'นะครับ',
            'จ้า', 'จ๊ะ', 'จ้ะ', 'ขา', 'เถอะ',
            'ที่', 'และ', 'กับ', 'เป็น', 'ได้',
            'มา', 'ไป', 'อยู่', 'ให้', 'ว่า'
        }

        # Common Thai abbreviations mapping
        self.abbreviations = {
            'ม.ค.': 'มกราคม',
            'ก.พ.': 'กุมภาพันธ์',
            'มี.ค.': 'มีนาคม',
            'เม.ย.': 'เมษายน',
            'พ.ค.': 'พฤษภาคม',
            'มิ.ย.': 'มิถุนายน',
            'ก.ค.': 'กรกฎาคม',
            'ส.ค.': 'สิงหาคม',
            'ก.ย.': 'กันยายน',
            'ต.ค.': 'ตุลาคม',
            'พ.ย.': 'พฤศจิกายน',
            'ธ.ค.': 'ธันวาคม',
            'พบ.': 'พบ',
            'เก.ล.': 'เกาะลันตา',
            'ต.': 'ตำบล',
            'อ.': 'อำเภอ',
            'จ.': 'จังหวัด',
            'สพ.': 'สำนักพิมพ์',
        }

        logger.info("✅ ThaiTextProcessor initialized")

    async def preprocess_thai_text(self, text: str) -> str:
        """ทำความสะอาดและเตรียมข้อความภาษาไทย"""

        # 1. Normalize Thai text (แก้การแสดงผลของสระ วรรณยุกต์)
        text = thai_normalize(text)

        # 2. Expand abbreviations
        text = await self._expand_abbreviations(text)

        # 3. Handle mixed language
        text = await self._handle_mixed_language(text)

        # 4. Remove extra whitespace
        text = ' '.join(text.split())

        # 5. Fix common typos
        text = await self._correct_common_typos(text)

        return text

    async def _expand_abbreviations(self, text: str) -> str:
        """ขยายคำย่อ เช่น ม.ค. → มกราคม"""
        for abbr, full in self.abbreviations.items():
            text = text.replace(abbr, full)
        return text

    async def _handle_mixed_language(self, text: str) -> str:
        """จัดการข้อความที่มีภาษาไทยผสมอังกฤษ"""
        # Keep both Thai and English text, just normalize spacing
        return text

    async def _correct_common_typos(self, text: str) -> str:
        """แก้ไขการสะกดผิดที่พบบ่อย"""
        common_typos = {
            'ทำให้': 'ทำให้',  # Common variant
            'ยังไง': 'ยังไง',  # Colloquial
            'เค้า': 'เขา',     # They
            'มั้ย': 'ไหม',     # Yes/no question particle
        }

        for typo, correct in common_typos.items():
            if typo in text:
                text = text.replace(typo, correct)

        return text

    def detect_language(self, text: str) -> str:
        """ตรวจหาภาษาของข้อความ (th, en, mixed)"""
        thai_pattern = re.compile(r'[\u0E00-\u0E7F]')  # Thai Unicode range
        english_pattern = re.compile(r'[a-zA-Z]')

        has_thai = bool(thai_pattern.search(text))
        has_english = bool(english_pattern.search(text))

        if has_thai and has_english:
            return 'mixed'
        elif has_thai:
            return 'th'
        elif has_english:
            return 'en'
        else:
            return 'other'

    def tokenize_thai(self, text: str, engine: str = "newmm") -> List[str]:
        """ตัดคำภาษาไทย"""
        try:
            tokens = word_tokenize(text, engine=engine)
            return tokens
        except Exception as e:
            logger.error(f"❌ Tokenization error: {e}")
            return text.split()

    def get_sentences(self, text: str) -> List[str]:
        """ตัดประโยค"""
        try:
            sentences = sent_tokenize(text, engine="crfcut")
            return sentences
        except Exception as e:
            logger.error(f"❌ Sentence tokenization error: {e}")
            return text.split('\n')

    async def smart_chunk_thai(
        self,
        text: str,
        chunk_size: int = 500,  # จำนวนคำ (ไม่ใช่ characters)
        overlap: int = 100
    ) -> List[Dict]:
        """ตัดข้อความไทยอย่างชาญฉลาด"""

        try:
            # 1. Split into sentences
            sentences = self.get_sentences(text)

            chunks = []
            current_chunk = []
            current_word_count = 0

            for sentence in sentences:
                # Tokenize sentence
                words = self.tokenize_thai(sentence)
                sentence_word_count = len(words)

                # If adding this sentence exceeds chunk_size, save current chunk
                if current_word_count + sentence_word_count > chunk_size:
                    if current_chunk:
                        chunk_text = ' '.join(current_chunk)
                        chunks.append({
                            'content': chunk_text,
                            'word_count': current_word_count,
                            'sentence_count': len(current_chunk),
                            'chunk_index': len(chunks),
                            'metadata': {
                                'language': 'th',
                                'has_english': self.detect_language(chunk_text) == 'mixed'
                            }
                        })

                    # Start new chunk with overlap (last 2 sentences or 1)
                    if len(current_chunk) > 2:
                        overlap_sentences = current_chunk[-2:]
                    elif len(current_chunk) > 0:
                        overlap_sentences = current_chunk[-1:]
                    else:
                        overlap_sentences = []

                    current_chunk = overlap_sentences + [sentence]
                    current_word_count = sum(
                        len(self.tokenize_thai(s))
                        for s in current_chunk
                    )
                else:
                    current_chunk.append(sentence)
                    current_word_count += sentence_word_count

            # Add final chunk
            if current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'content': chunk_text,
                    'word_count': current_word_count,
                    'sentence_count': len(current_chunk),
                    'chunk_index': len(chunks),
                    'metadata': {
                        'language': self.detect_language(chunk_text)
                    }
                })

            logger.info(f"✅ Created {len(chunks)} chunks from Thai text")
            return chunks

        except Exception as e:
            logger.error(f"❌ Error in chunking: {e}")
            # Fallback: simple character-based chunking
            return [{
                'content': text[i:i+chunk_size],
                'word_count': len(text[i:i+chunk_size].split()),
                'chunk_index': idx
            } for idx, i in enumerate(range(0, len(text), chunk_size))]

    async def extract_keywords_thai(self, text: str, top_k: int = 20) -> List[str]:
        """สกัด keywords สำคัญจากภาษาไทย"""

        try:
            # 1. Tokenize
            words = self.tokenize_thai(text)

            # 2. POS tagging
            pos_tagged = pos_tag(words, engine="perceptron")

            # 3. Filter meaningful words with priority scoring
            # PROPN (ชื่อเฉพาะ) = highest priority for exact matching
            # NOUN = high priority
            # VERB, ADJ = medium priority
            weighted_words = []
            for word, pos in pos_tagged:
                if word in self.stopwords or word in self.custom_stopwords or len(word) <= 1:
                    continue

                if pos == 'PROPN':  # ชื่อเฉพาะ (บริษัท, คน, สถานที่)
                    weighted_words.extend([word] * 3)  # 3x weight
                elif pos == 'NOUN':  # คำนาม
                    weighted_words.extend([word] * 2)  # 2x weight
                elif pos in ['VERB', 'ADJ']:
                    weighted_words.append(word)  # 1x weight

            # 4. Count frequency (with weights)
            word_freq = Counter(weighted_words)
            keywords = [word for word, _ in word_freq.most_common(top_k)]

            logger.info(f"✅ Extracted {len(keywords)} keywords (PROPN boosted)")
            return keywords

        except Exception as e:
            logger.error(f"❌ Error extracting keywords: {e}")
            return []

    async def extract_entities_thai(self, text: str) -> Dict[str, List[str]]:
        """สกัด Named Entities จากภาษาไทย (บุคคล, สถานที่, องค์กร)"""

        result = {
            'PERSON': [],
            'LOCATION': [],
            'ORGANIZATION': [],
            'OTHER': []
        }

        try:
            # Check if NER is available
            if not ner_available or ner_tagger is None:
                logger.debug("⚠️ pythainlp NER not available, returning empty entities")
                return result

            # Use pythainlp NER with tag=True to get (token, label) tuples
            entities = ner_tagger.tag(text, tag=True)

            for word, tag in entities:
                if tag == 'PERSON':
                    result['PERSON'].append(word)
                elif tag == 'LOCATION':
                    result['LOCATION'].append(word)
                elif tag == 'ORGANIZATION':
                    result['ORGANIZATION'].append(word)
                elif tag != 'O':  # O = not an entity
                    result['OTHER'].append(word)

            logger.info(f"✅ Extracted entities: {len(result['PERSON'])} persons, "
                       f"{len(result['LOCATION'])} locations, "
                       f"{len(result['ORGANIZATION'])} organizations")

            return result

        except Exception as e:
            logger.error(f"❌ Error extracting entities: {e}")
            return result  # Return empty result instead of empty dict

    def calculate_thai_readability(self, text: str) -> Dict:
        """คำนวณ Readability Score สำหรับภาษาไทย"""

        try:
            sentences = self.get_sentences(text)
            words = self.tokenize_thai(text)

            total_sentences = len(sentences)
            total_words = len(words)
            total_chars = len(text)

            # Avoid division by zero
            if total_sentences == 0 or total_words == 0:
                return {
                    'avg_word_length': 0,
                    'avg_words_per_sentence': 0,
                    'difficulty_level': 'unknown'
                }

            avg_word_length = total_chars / total_words
            avg_words_per_sentence = total_words / total_sentences

            # Simple difficulty classification for Thai
            if avg_word_length > 4 and avg_words_per_sentence > 15:
                difficulty = 'hard'
            elif avg_word_length > 3 and avg_words_per_sentence > 10:
                difficulty = 'medium'
            else:
                difficulty = 'easy'

            return {
                'avg_word_length': round(avg_word_length, 2),
                'avg_words_per_sentence': round(avg_words_per_sentence, 2),
                'total_words': total_words,
                'total_sentences': total_sentences,
                'total_characters': total_chars,
                'difficulty_level': difficulty
            }

        except Exception as e:
            logger.error(f"❌ Error calculating readability: {e}")
            return {}

    def contains_english(self, text: str) -> bool:
        """ตรวจสอบว่าข้อความมีภาษาอังกฤษ"""
        return self.detect_language(text) in ['en', 'mixed']

    async def normalize_for_embedding(self, text: str) -> str:
        """เตรียมข้อความให้พร้อมสำหรับ embedding"""

        # 1. Preprocess
        text = await self.preprocess_thai_text(text)

        # 2. Convert to lowercase (for English part)
        text = text.lower()

        # 3. Remove special characters but keep Thai characters
        # Keep Thai chars (U+0E00-U+0E7F), alphanumeric, and spaces
        text = re.sub(r'[^\u0E00-\u0E7Fa-z0-9\s]', '', text)

        # 4. Normalize whitespace
        text = ' '.join(text.split())

        return text

    async def batch_process_texts(
        self,
        texts: List[str],
        operation: str = 'tokenize'
    ) -> List:
        """ประมวลผลข้อความแบบ batch"""

        tasks = []

        if operation == 'tokenize':
            return [self.tokenize_thai(t) for t in texts]
        elif operation == 'chunk':
            tasks = [self.smart_chunk_thai(t) for t in texts]
        elif operation == 'keywords':
            tasks = [self.extract_keywords_thai(t) for t in texts]
        elif operation == 'entities':
            tasks = [self.extract_entities_thai(t) for t in texts]

        if tasks:
            return await asyncio.gather(*tasks)

        return []

    async def analyze_document(self, text: str) -> Dict:
        """วิเคราะห์เอกสารทั้งหมด"""

        logger.info("🔍 Starting comprehensive document analysis...")

        try:
            # Preprocess
            processed = await self.preprocess_thai_text(text)

            # Language detection
            language = self.detect_language(text)

            # Extract features
            keywords = await self.extract_keywords_thai(text)
            entities = await self.extract_entities_thai(text)
            readability = self.calculate_thai_readability(text)

            result = {
                'language': language,
                'keywords': keywords,
                'entities': entities,
                'readability': readability,
                'is_processed': True
            }

            logger.info(f"✅ Analysis complete: {language} language, "
                       f"{len(keywords)} keywords, {len(entities)} entities")

            return result

        except Exception as e:
            logger.error(f"❌ Document analysis error: {e}")
            return {'error': str(e), 'is_processed': False}
