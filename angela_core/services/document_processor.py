"""
Document Processing Service for RAG System
Handles document upload, chunking, embedding, and storage
"""

import asyncio
import asyncpg
import httpx
from typing import List, Dict, Optional, Tuple
from uuid import UUID, uuid4
from pathlib import Path
import json
import logging
from datetime import datetime
import warnings

from .thai_text_processor import ThaiTextProcessor

# Import centralized embedding service
from angela_core.embedding_service import embedding as embedding_service

logger = logging.getLogger(__name__)

# Suppress pdfplumber warnings about PDF color values
warnings.filterwarnings("ignore", message="Cannot set gray.*")
logging.getLogger("pdfminer").setLevel(logging.ERROR)


class DocumentProcessor:
    """ระบบประมวลผลเอกสารพร้อม Embedding"""

    def __init__(self, db_connection, ollama_base_url: str = "http://localhost:11434"):
        """Initialize document processor"""
        self.db = db_connection
        self.ollama_url = ollama_base_url
        self.thai_processor = ThaiTextProcessor()
        self.embedding_model = "nomic-embed-text"
        self.embedding_dimension = 768

        logger.info("✅ DocumentProcessor initialized")

    async def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from different file types"""

        try:
            file_path = Path(file_path)
            # Convert to lowercase for case-insensitive comparison
            suffix = file_path.suffix.lower()

            if suffix == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()

            elif suffix == '.md':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()

            elif suffix == '.pdf':
                try:
                    import pdfplumber
                    import warnings

                    # Suppress pdfplumber color warnings
                    with warnings.catch_warnings():
                        warnings.filterwarnings("ignore", message="Cannot set gray.*")

                        with pdfplumber.open(file_path) as pdf:
                            text = ""
                            for page in pdf.pages:
                                text += page.extract_text() or ""
                            return text
                except ImportError:
                    logger.warning("⚠️ pdfplumber not installed, skipping PDF extraction")
                    return ""

            elif suffix == '.docx':
                try:
                    from docx import Document
                    doc = Document(file_path)
                    return '\n'.join([p.text for p in doc.paragraphs])
                except ImportError:
                    logger.warning("⚠️ python-docx not installed, skipping DOCX extraction")
                    return ""

            else:
                logger.warning(f"⚠️ Unsupported file type: {suffix}")
                return ""

        except Exception as e:
            logger.error(f"❌ Error extracting text from file: {e}")
            return ""

    async def embed_text(self, text: str) -> Optional[List[float]]:
        """Generate embedding using Ollama"""

        try:
            # Prepare text for embedding
            embedding_text = await self.thai_processor.normalize_for_embedding(text)

            # Use centralized embedding service
            return await embedding_service.generate_embedding(embedding_text)

        except Exception as e:
            logger.error(f"❌ Embedding error: {e}")
            return None

    async def process_document(
        self,
        file_path: str,
        title: str,
        category: str = "general",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
        progress_callback=None
    ) -> Dict:
        """Full document processing pipeline with progress tracking"""

        document_id = uuid4()

        try:
            logger.info(f"🔄 Processing document: {title}")

            # 1. Extract text from file
            logger.info("📄 Extracting text...")
            if progress_callback:
                await progress_callback("extracting", 10, f"📄 กำลัง extract ข้อความจาก {title}...")
            raw_text = await self.extract_text_from_file(file_path)

            if not raw_text:
                raise ValueError("Could not extract text from file")

            # 2. Preprocess text
            logger.info("🧹 Preprocessing Thai text...")
            if progress_callback:
                await progress_callback("preprocessing", 25, "🧹 กำลัง preprocess ภาษาไทย...")
            processed_text = await self.thai_processor.preprocess_thai_text(raw_text)

            # 3. Analyze document
            logger.info("🔍 Analyzing document...")
            if progress_callback:
                await progress_callback("analyzing", 35, "🔍 กำลังวิเคราะห์เอกสาร...")
            analysis = await self.thai_processor.analyze_document(processed_text)

            # 4. Create chunks
            logger.info("✂️ Creating chunks...")
            if progress_callback:
                await progress_callback("chunking", 45, "✂️ กำลังแบ่งเป็น chunks...")
            chunks = await self.thai_processor.smart_chunk_thai(
                processed_text,
                chunk_size=500,
                overlap=100
            )

            # 5. Generate embeddings for all chunks
            logger.info("🧠 Generating embeddings...")
            if progress_callback:
                await progress_callback("embedding", 55, f"🧠 กำลังสร้าง embeddings ({len(chunks)} chunks)...")

            embeddings = []
            for i, chunk in enumerate(chunks):
                embedding = await self.embed_text(chunk['content'])
                embeddings.append(embedding)

                # Update progress for each embedding
                if progress_callback and (i + 1) % 5 == 0:  # Update every 5 chunks
                    progress = 55 + int((i + 1) / len(chunks) * 30)  # 55-85%
                    await progress_callback("embedding", progress, f"🧠 สร้าง embeddings ({i + 1}/{len(chunks)})...")

            # 6. Store document and chunks in database
            logger.info("💾 Storing in database...")
            if progress_callback:
                await progress_callback("storing", 90, "💾 กำลังบันทึกลงฐานข้อมูล...")
            document_info = await self._store_document_and_chunks(
                document_id,
                title,
                file_path,
                category,
                tags or [],
                metadata or {},
                analysis,
                chunks,
                embeddings
            )

            logger.info(f"✅ Document processed successfully: {document_id}")

            if progress_callback:
                await progress_callback("complete", 100, "✅ เสร็จสมบูรณ์!")

            return {
                'success': True,
                'document_id': str(document_id),
                'title': title,
                'chunks_created': len(chunks),
                'analysis': analysis,
                'stats': {
                    'thai_word_count': analysis.get('readability', {}).get('total_words', 0),
                    'total_sentences': analysis.get('readability', {}).get('total_sentences', 0),
                    'difficulty': analysis.get('readability', {}).get('difficulty_level', 'unknown')
                }
            }

        except Exception as e:
            logger.error(f"❌ Document processing failed: {e}")
            if progress_callback:
                await progress_callback("error", 0, f"❌ เกิดข้อผิดพลาด: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'document_id': str(document_id)
            }

    async def _store_document_and_chunks(
        self,
        document_id: UUID,
        title: str,
        file_path: str,
        category: str,
        tags: List[str],
        metadata: Dict,
        analysis: Dict,
        chunks: List[Dict],
        embeddings: List[Optional[List[float]]]
    ) -> Dict:
        """Store document and its chunks in database"""

        try:
            # Get language from analysis
            language = analysis.get('language', 'th')
            keywords_thai = analysis.get('keywords', [])[:20]
            readability = analysis.get('readability', {})
            entities = analysis.get('entities', {})

            # Insert main document
            insert_doc_query = """
                INSERT INTO document_library
                (document_id, title, file_path, language, category, tags,
                 keywords_thai, thai_word_count, total_sentences, total_chunks,
                 metadata, processing_status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """

            metadata['entities'] = entities
            metadata['extracted_at'] = datetime.utcnow().isoformat()

            await self.db.execute(
                insert_doc_query,
                document_id,
                title,
                file_path,
                language,
                category,
                tags,
                keywords_thai,
                readability.get('total_words', 0),
                readability.get('total_sentences', 0),
                len(chunks),
                json.dumps(metadata),
                'completed'
            )

            logger.info(f"✅ Document stored: {document_id}")

            # Insert chunks with embeddings
            insert_chunk_query = """
                INSERT INTO document_chunks
                (chunk_id, document_id, chunk_index, content, content_normalized,
                 content_tokens, thai_word_count, english_word_count, has_mixed_language,
                 sentence_boundaries, embedding, embedding_model, page_number,
                 section_title, section_level, importance_score, readability_score, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
            """

            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                if embedding is None or isinstance(embedding, Exception):
                    logger.warning(f"⚠️ Skipping chunk {idx} due to embedding error")
                    continue

                chunk_id = uuid4()
                content_norm = await self.thai_processor.normalize_for_embedding(chunk['content'])
                tokens = self.thai_processor.tokenize_thai(chunk['content'])
                word_count = chunk.get('word_count', len(tokens))

                # Detect English words
                english_words = [t for t in chunk['content'].split() if t.isascii() and t.isalpha()]
                english_word_count = len(english_words)
                has_mixed = english_word_count > 0 and word_count > 0

                # Get sentence boundaries (simplified - split by Thai sentence markers)
                sentences = chunk['content'].split('.')
                sentence_boundaries = []
                pos = 0
                for sent in sentences:
                    if sent.strip():
                        pos += len(sent) + 1
                        sentence_boundaries.append(pos)

                # Calculate importance based on position (first chunks more important)
                importance = 1.0 - (idx / len(chunks)) * 0.5

                # Calculate readability (character count / word count ratio)
                readability = len(chunk['content']) / max(word_count, 1) if word_count > 0 else 0

                chunk_metadata = {
                    'language': chunk.get('metadata', {}).get('language', 'th'),
                    'has_english': has_mixed,
                    'extraction_time': datetime.utcnow().isoformat(),
                    'chunk_size': len(chunk['content'])
                }

                # Extract page number and section info from chunk metadata if available
                page_number = chunk.get('page_number', None)
                section_title = chunk.get('section_title', None)
                section_level = chunk.get('section_level', None)

                # Convert embedding list to pgvector format string
                embedding_str = str(embedding) if embedding else None

                await self.db.execute(
                    insert_chunk_query,
                    chunk_id,
                    document_id,
                    idx,
                    chunk['content'],
                    content_norm,
                    tokens,  # content_tokens
                    word_count,  # thai_word_count
                    english_word_count,
                    has_mixed,  # has_mixed_language
                    sentence_boundaries,
                    embedding_str,
                    'nomic-embed-text',  # embedding_model
                    page_number,
                    section_title,
                    section_level,
                    importance,  # importance_score
                    readability,  # readability_score
                    json.dumps(chunk_metadata)
                )

            logger.info(f"✅ Stored {len(chunks)} chunks for document {document_id}")

            return {
                'document_id': document_id,
                'chunks_stored': len([e for e in embeddings if e is not None and not isinstance(e, Exception)])
            }

        except Exception as e:
            logger.error(f"❌ Error storing document in database: {e}")
            raise

    async def batch_process_documents(
        self,
        file_paths: List[str],
        category: str = "general",
        tags: Optional[List[str]] = None
    ) -> List[Dict]:
        """Process multiple documents in batch"""

        logger.info(f"📚 Batch processing {len(file_paths)} documents...")

        tasks = []
        for file_path in file_paths:
            file_name = Path(file_path).stem
            task = self.process_document(
                file_path,
                title=file_name,
                category=category,
                tags=tags
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful = [r for r in results if isinstance(r, dict) and r.get('success')]
        failed = [r for r in results if isinstance(r, dict) and not r.get('success')]

        logger.info(f"✅ Batch processing complete: {len(successful)} successful, {len(failed)} failed")

        return {
            'total': len(file_paths),
            'successful': len(successful),
            'failed': len(failed),
            'results': results
        }

    async def reprocess_document(self, document_id: UUID) -> Dict:
        """Reprocess an existing document (re-chunk and re-embed)"""

        try:
            logger.info(f"🔄 Reprocessing document: {document_id}")

            # Get document from database
            doc_query = "SELECT file_path, title, category, tags, metadata FROM document_library WHERE document_id = $1"
            doc = await self.db.fetchrow(doc_query, document_id)

            if not doc:
                raise ValueError(f"Document not found: {document_id}")

            # Delete existing chunks
            await self.db.execute("DELETE FROM document_chunks WHERE document_id = $1", document_id)

            # Reprocess
            result = await self.process_document(
                doc['file_path'],
                title=doc['title'],
                category=doc['category'],
                tags=list(doc['tags']) if doc['tags'] else [],
                metadata=json.loads(doc['metadata']) if doc['metadata'] else {}
            )

            return result

        except Exception as e:
            logger.error(f"❌ Error reprocessing document: {e}")
            return {'success': False, 'error': str(e)}

    async def get_document_stats(self, document_id: UUID) -> Dict:
        """Get statistics about a document"""

        try:
            query = """
                SELECT
                    document_id, title, language, thai_word_count,
                    total_sentences, total_chunks, created_at,
                    access_count
                FROM document_library
                WHERE document_id = $1
            """

            doc = await self.db.fetchrow(query, document_id)

            if not doc:
                return {'error': 'Document not found'}

            # Get chunk statistics
            chunks_query = """
                SELECT COUNT(*) as total_chunks,
                       AVG(thai_word_count) as avg_words_per_chunk,
                       SUM(thai_word_count) as total_words
                FROM document_chunks
                WHERE document_id = $1
            """

            chunk_stats = await self.db.fetchrow(chunks_query, document_id)

            return {
                'document_id': str(document_id),
                'title': doc['title'],
                'language': doc['language'],
                'word_count': doc['thai_word_count'],
                'total_sentences': doc['total_sentences'],
                'total_chunks': chunk_stats['total_chunks'],
                'avg_words_per_chunk': chunk_stats['avg_words_per_chunk'],
                'access_count': doc['access_count'],
                'created_at': doc['created_at'].isoformat() if doc['created_at'] else None
            }

        except Exception as e:
            logger.error(f"❌ Error getting document stats: {e}")
            return {'error': str(e)}

    async def delete_document(self, document_id: UUID) -> Dict:
        """Delete a document and all its chunks"""

        try:
            logger.info(f"🗑️  Deleting document: {document_id}")

            # Chunks will be automatically deleted due to CASCADE
            await self.db.execute(
                "DELETE FROM document_library WHERE document_id = $1",
                document_id
            )

            logger.info(f"✅ Document deleted: {document_id}")
            return {'success': True, 'message': 'Document deleted successfully'}

        except Exception as e:
            logger.error(f"❌ Error deleting document: {e}")
            return {'success': False, 'error': str(e)}
