#!/usr/bin/env python3
"""
Angela Document Processor
Process and store documents for RAG system

Features:
- PDF extraction (PyPDF2)
- Text file support
- Semantic chunking
- Automatic embedding generation
- Thai language support
"""

import asyncpg
import asyncio
import uuid
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime
import re

# PDF extraction
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

# Thai text processing
try:
    from pythainlp import word_tokenize
except ImportError:
    word_tokenize = None

# from angela_core.embedding_service import  # REMOVED: Migration 009 embedding

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process documents for Angela's RAG system"""

    def __init__(self, db_connection: asyncpg.Connection = None):
        """
        Initialize document processor

        Args:
            db_connection: Database connection (optional, will use context manager if not provided)
        """
        self.db = db_connection
        self.embedding_service = embedding

        # Chunking parameters
        self.chunk_size = 500  # words
        self.chunk_overlap = 50  # words
        self.min_chunk_size = 100  # minimum words per chunk

        logger.info("📄 DocumentProcessor initialized")

    async def process_document(
        self,
        file_path: str,
        title: str,
        category: str = "general",
        tags: List[str] = None
    ) -> Dict:
        """
        Process a document and store in database

        Args:
            file_path: Path to document file
            title: Document title
            category: Document category
            tags: Optional tags list

        Returns:
            Dict with processing results
        """
        try:
            logger.info(f"📄 Processing document: {title}")

            # Extract text
            text = await self._extract_text(file_path)

            if not text or len(text.strip()) < 100:
                return {
                    'success': False,
                    'error': 'Document is too short or empty'
                }

            # Analyze document
            analysis = self._analyze_text(text)

            # Create chunks
            chunks = self._create_chunks(text)

            if not chunks:
                return {
                    'success': False,
                    'error': 'Failed to create chunks'
                }

            logger.info(f"  Created {len(chunks)} chunks")

            # Generate embeddings for all chunks
            logger.info(f"  Generating embeddings...")
            chunk_texts = [chunk['content'] for chunk in chunks]
            embeddings = await self.embedding_service.generate_embeddings_batch(
                chunk_texts,
                batch_delay=0.1
            )

            # Save to database
            document_id = await self._save_document(
                title=title,
                category=category,
                language=analysis['language'],
                thai_word_count=analysis['thai_word_count'],
                english_word_count=analysis['english_word_count'],
                total_sentences=analysis['total_sentences'],
                total_chunks=len(chunks),
                tags=tags
            )

            # Save chunks with embeddings
            await self._save_chunks(
                document_id=document_id,
                chunks=chunks,
                embeddings=embeddings
            )

            logger.info(f"✅ Document processed successfully: {document_id}")

            return {
                'success': True,
                'document_id': str(document_id),
                'title': title,
                'chunks': len(chunks),
                'thai_words': analysis['thai_word_count'],
                'english_words': analysis['english_word_count'],
                'language': analysis['language']
            }

        except Exception as e:
            logger.error(f"❌ Failed to process document: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }

    async def _extract_text(self, file_path: str) -> str:
        """
        Extract text from file

        Supports:
        - PDF (.pdf)
        - Text files (.txt, .md, .html)
        """
        path = Path(file_path)
        suffix = path.suffix.lower()

        try:
            if suffix == '.pdf':
                return await self._extract_pdf(file_path)
            elif suffix in ['.txt', '.md', '.html', '.htm']:
                return await self._extract_text_file(file_path)
            else:
                raise ValueError(f"Unsupported file type: {suffix}")

        except Exception as e:
            logger.error(f"❌ Text extraction failed: {e}")
            raise

    async def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF using PyPDF2"""
        if PyPDF2 is None:
            raise ImportError("PyPDF2 is not installed. Install with: pip install PyPDF2")

        text_parts = []

        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)

                logger.info(f"  PDF has {num_pages} pages")

                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()

                    if text:
                        text_parts.append(text)

            full_text = "\n\n".join(text_parts)
            logger.info(f"  Extracted {len(full_text)} characters from PDF")

            return full_text

        except Exception as e:
            logger.error(f"❌ PDF extraction failed: {e}")
            raise

    async def _extract_text_file(self, file_path: str) -> str:
        """Extract text from text file"""
        try:
            # Try different encodings
            for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        text = file.read()
                        logger.info(f"  Extracted {len(text)} characters (encoding: {encoding})")
                        return text
                except UnicodeDecodeError:
                    continue

            raise ValueError("Could not decode file with any supported encoding")

        except Exception as e:
            logger.error(f"❌ Text file extraction failed: {e}")
            raise

    def _analyze_text(self, text: str) -> Dict:
        """
        Analyze text and extract statistics

        Returns:
            Dict with language, word counts, sentence count
        """
        # Count sentences (rough estimate)
        sentences = re.split(r'[.!?]+', text)
        total_sentences = len([s for s in sentences if s.strip()])

        # Detect Thai characters
        thai_chars = len(re.findall(r'[\u0E00-\u0E7F]', text))

        # Count words
        if word_tokenize:
            # Use pythainlp for Thai
            thai_words = word_tokenize(text, engine='newmm')
            thai_word_count = len([w for w in thai_words if re.search(r'[\u0E00-\u0E7F]', w)])
        else:
            # Rough estimate
            thai_word_count = thai_chars // 3  # Average Thai word is ~3 chars

        # Count English words
        english_words = re.findall(r'\b[a-zA-Z]+\b', text)
        english_word_count = len(english_words)

        # Determine language
        if thai_word_count > english_word_count:
            language = 'th'
        elif english_word_count > 0:
            language = 'en'
        else:
            language = 'mixed'

        return {
            'language': language,
            'thai_word_count': thai_word_count,
            'english_word_count': english_word_count,
            'total_sentences': total_sentences,
            'total_chars': len(text)
        }

    def _create_chunks(self, text: str) -> List[Dict]:
        """
        Create semantic chunks from text

        Strategy:
        1. Split by paragraphs first
        2. Combine small paragraphs
        3. Split large paragraphs by sentences
        4. Ensure chunks are within target size
        """
        # Split into paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        chunks = []
        current_chunk = []
        current_word_count = 0

        for para in paragraphs:
            # Count words in paragraph
            if word_tokenize:
                para_words = word_tokenize(para, engine='newmm')
            else:
                para_words = para.split()

            para_word_count = len(para_words)

            # If adding this paragraph exceeds chunk size, save current chunk
            if current_word_count + para_word_count > self.chunk_size and current_chunk:
                chunk_text = "\n\n".join(current_chunk)
                chunks.append({
                    'content': chunk_text,
                    'word_count': current_word_count
                })

                # Start new chunk with overlap
                # Keep last paragraph for context
                current_chunk = [current_chunk[-1]] if current_chunk else []
                if word_tokenize:
                    current_word_count = len(word_tokenize(current_chunk[0], engine='newmm')) if current_chunk else 0
                else:
                    current_word_count = len(current_chunk[0].split()) if current_chunk else 0

            current_chunk.append(para)
            current_word_count += para_word_count

        # Add remaining chunk
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            if current_word_count >= self.min_chunk_size:
                chunks.append({
                    'content': chunk_text,
                    'word_count': current_word_count
                })

        # Add metadata to chunks
        for i, chunk in enumerate(chunks):
            chunk['chunk_index'] = i
            chunk['page_number'] = None  # TODO: Extract from PDF if available
            chunk['section_title'] = None  # TODO: Extract section titles

            # Analyze chunk
            analysis = self._analyze_text(chunk['content'])
            chunk['thai_word_count'] = analysis['thai_word_count']
            chunk['english_word_count'] = analysis['english_word_count']

            # Calculate importance score (placeholder)
            chunk['importance_score'] = 1.0

        return chunks

    async def _save_document(
        self,
        title: str,
        category: str,
        language: str,
        thai_word_count: int,
        english_word_count: int,
        total_sentences: int,
        total_chunks: int,
        tags: List[str] = None
    ) -> uuid.UUID:
        """Save document metadata to database"""
        try:
            query = """
                INSERT INTO document_library (
                    document_id, title, category, language,
                    thai_word_count, english_word_count,
                    total_sentences, total_chunks,
                    tags, created_at, updated_at, is_active
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW(), TRUE)
                RETURNING document_id
            """

            document_id = uuid.uuid4()

            await self.db.execute(
                query,
                document_id,
                title,
                category,
                language,
                thai_word_count,
                english_word_count,
                total_sentences,
                total_chunks,
                tags or []
            )

            return document_id

        except Exception as e:
            logger.error(f"❌ Failed to save document: {e}")
            raise

    async def _save_chunks(
        self,
        document_id: uuid.UUID,
        chunks: List[Dict],
        embeddings: List[List[float]]
    ):
        """Save document chunks with embeddings to database"""
        try:
            query = """
                INSERT INTO document_chunks (
                    chunk_id, document_id, chunk_index, content,
                    thai_word_count, english_word_count,
                    page_number, section_title, importance_score,
                    embedding, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::vector, NOW())
            """

            for chunk, embedding in zip(chunks, embeddings):
                chunk_id = uuid.uuid4()

                await self.db.execute(
                    query,
                    chunk_id,
                    document_id,
                    chunk['chunk_index'],
                    chunk['content'],
                    chunk['thai_word_count'],
                    chunk['english_word_count'],
                    chunk['page_number'],
                    chunk['section_title'],
                    chunk['importance_score'],
                    str(embedding)  # Convert to PostgreSQL vector format
                )

            logger.info(f"  Saved {len(chunks)} chunks to database")

        except Exception as e:
            logger.error(f"❌ Failed to save chunks: {e}")
            raise

    async def delete_document(self, document_id: uuid.UUID) -> Dict:
        """
        Delete a document and all its chunks

        Args:
            document_id: UUID of document to delete

        Returns:
            Dict with success status
        """
        try:
            # Chunks will be deleted automatically due to CASCADE foreign key
            # Delete document from document_library
            result = await self.db.execute(
                "DELETE FROM document_library WHERE document_id = $1",
                document_id
            )

            if result == "DELETE 0":
                return {
                    'success': False,
                    'error': 'Document not found'
                }

            logger.info(f"✅ Deleted document: {document_id}")

            return {'success': True}

        except Exception as e:
            logger.error(f"❌ Failed to delete document: {e}")
            return {
                'success': False,
                'error': str(e)
            }
