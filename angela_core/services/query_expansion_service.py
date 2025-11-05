#!/usr/bin/env python3
"""
Query Expansion Service
ขยายคำค้นหาเพื่อให้ครอบคลุมมากขึ้น

Features:
- Thai/English synonym expansion
- Related terms addition
- Keyword extraction
- Query reformulation
"""

import re
import logging
from typing import List, Set, Dict

logger = logging.getLogger(__name__)


class QueryExpansionService:
    """Service for expanding queries with synonyms and related terms"""

    # Thai synonyms dictionary (expandable)
    THAI_SYNONYMS = {
        # Business terms
        'บริษัท': ['องค์กร', 'ธุรกิจ', 'หน่วยงาน'],
        'CEO': ['ซีอีโอ', 'ผู้บริหาร', 'กรรมการผู้จัดการ', 'ประธานเจ้าหน้าที่บริหาร'],
        'กรรมการ': ['คณะกรรมการ', 'ผู้บริหาร'],

        # Document terms
        'เอกสาร': ['ไฟล์', 'ข้อมูล', 'รายงาน'],
        'รายงาน': ['เอกสาร', 'สรุป', 'บันทึก'],

        # Action terms
        'ทำงาน': ['ดำเนินการ', 'ปฏิบัติงาน', 'ดำเนินงาน'],
        'จัดการ': ['บริหาร', 'ดูแล', 'ควบคุม'],

        # General terms
        'ชื่อ': ['นาม', 'คือ'],
        'อะไร': ['คืออะไร', 'หมายถึง'],
        'อย่างไร': ['วิธีการ', 'ขั้นตอน', 'กระบวนการ'],
        'ที่ไหน': ['สถานที่', 'ตำแหน่ง', 'location'],
    }

    # English synonyms dictionary
    ENGLISH_SYNONYMS = {
        'CEO': ['Chief Executive Officer', 'President', 'Executive Director'],
        'company': ['corporation', 'business', 'organization', 'firm'],
        'document': ['file', 'report', 'record', 'paper'],
        'report': ['document', 'summary', 'statement'],
        'name': ['title', 'called', 'known as'],
        'work': ['operate', 'function', 'run', 'perform'],
        'manage': ['handle', 'control', 'oversee', 'administer'],
        'how': ['method', 'way', 'process', 'procedure'],
        'what': ['which', 'describe'],
        'where': ['location', 'place', 'position'],
    }

    # Common Thai stopwords (words to skip)
    THAI_STOPWORDS = {
        'ของ', 'ที่', 'มี', 'ได้', 'เป็น', 'และ', 'จาก', 'ใน', 'กับ',
        'มั้ย', 'ไหม', 'คะ', 'ค่ะ', 'ครับ', 'นะ', 'จ้า', 'จ๊ะ'
    }

    @staticmethod
    def extract_keywords(query: str) -> List[str]:
        """
        Extract important keywords from query

        Args:
            query: Search query

        Returns:
            List of keywords
        """
        # Remove punctuation
        cleaned = re.sub(r'[^\w\s\u0E00-\u0E7F]', ' ', query.lower())

        # Split into words
        words = cleaned.split()

        # Filter out stopwords and short words
        keywords = [
            word for word in words
            if len(word) > 1 and word not in QueryExpansionService.THAI_STOPWORDS
        ]

        return keywords

    @staticmethod
    def expand_with_synonyms(query: str, max_synonyms: int = 2) -> List[str]:
        """
        Expand query with synonyms

        Args:
            query: Original query
            max_synonyms: Maximum synonyms per term

        Returns:
            List of expanded queries (including original)
        """
        expanded_queries = [query]

        # Extract keywords
        keywords = QueryExpansionService.extract_keywords(query)

        if not keywords:
            return expanded_queries

        # Find synonyms
        for keyword in keywords:
            # Check Thai synonyms
            if keyword in QueryExpansionService.THAI_SYNONYMS:
                synonyms = QueryExpansionService.THAI_SYNONYMS[keyword][:max_synonyms]

                for synonym in synonyms:
                    # Replace keyword with synonym in query
                    expanded = query.replace(keyword, synonym)
                    if expanded != query:
                        expanded_queries.append(expanded)

            # Check English synonyms
            if keyword in QueryExpansionService.ENGLISH_SYNONYMS:
                synonyms = QueryExpansionService.ENGLISH_SYNONYMS[keyword][:max_synonyms]

                for synonym in synonyms:
                    expanded = query.replace(keyword, synonym)
                    if expanded != query:
                        expanded_queries.append(expanded)

        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for q in expanded_queries:
            if q not in seen:
                seen.add(q)
                unique_queries.append(q)

        logger.info(f"🔍 Query expansion: 1 → {len(unique_queries)} queries")

        return unique_queries[:5]  # Limit to 5 variations

    @staticmethod
    def add_related_terms(query: str) -> str:
        """
        Add related terms to boost search relevance

        Args:
            query: Original query

        Returns:
            Enhanced query with related terms
        """
        # Detect query intent and add related terms
        query_lower = query.lower()

        related_terms = []

        # CEO/Executive queries
        if any(term in query_lower for term in ['ceo', 'ซีอีโอ', 'ผู้บริหาร']):
            related_terms.extend(['กรรมการผู้จัดการ', 'ประธาน', 'executive'])

        # Name queries
        if any(term in query_lower for term in ['ชื่อ', 'name', 'called']):
            related_terms.extend(['นาม', 'title'])

        # Document queries
        if any(term in query_lower for term in ['เอกสาร', 'document', 'รายงาน']):
            related_terms.extend(['ไฟล์', 'file', 'report'])

        # Company queries
        if any(term in query_lower for term in ['บริษัท', 'company', 'องค์กร']):
            related_terms.extend(['ธุรกิจ', 'business', 'corporation'])

        # Add related terms to query
        if related_terms:
            enhanced = f"{query} {' '.join(related_terms[:3])}"
            logger.info(f"📎 Added related terms: {related_terms[:3]}")
            return enhanced

        return query

    @staticmethod
    def enhance_query(
        query: str,
        use_synonyms: bool = True,
        use_related: bool = True
    ) -> Dict[str, any]:
        """
        Full query enhancement pipeline

        Args:
            query: Original query
            use_synonyms: Enable synonym expansion
            use_related: Enable related terms

        Returns:
            Dict with original, expanded queries, and enhanced query
        """
        result = {
            'original': query,
            'keywords': QueryExpansionService.extract_keywords(query),
            'expanded_queries': [query],
            'enhanced_query': query
        }

        # Expand with synonyms
        if use_synonyms:
            result['expanded_queries'] = QueryExpansionService.expand_with_synonyms(query)

        # Add related terms
        if use_related:
            result['enhanced_query'] = QueryExpansionService.add_related_terms(query)

        logger.info(f"✨ Query enhanced: '{query}' → {len(result['expanded_queries'])} variations")

        return result

    @staticmethod
    def add_synonym(language: str, term: str, synonyms: List[str]):
        """
        Add custom synonym to dictionary (runtime)

        Args:
            language: 'thai' or 'english'
            term: Main term
            synonyms: List of synonyms
        """
        if language.lower() == 'thai':
            QueryExpansionService.THAI_SYNONYMS[term] = synonyms
        elif language.lower() == 'english':
            QueryExpansionService.ENGLISH_SYNONYMS[term] = synonyms

        logger.info(f"➕ Added synonym: {term} → {synonyms}")
