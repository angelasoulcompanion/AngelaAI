#!/usr/bin/env python3
"""
Google Keep Sync Service for Angela
=====================================
Syncs David's Google Keep notes into Angela's RAG system.

Features:
- Incremental sync with content_hash change detection
- Short notes (<300 words) → embed directly in david_notes
- Long notes (>=300 words) → chunk into document_chunks via document_library
- Uses existing EmbeddingService (Ollama local, FREE, 384-dim)
- Sync logging for audit trail

Schedule:
- Daily at 06:06 (daemon)
- On-demand via /sync-keep

Cost: $0/month (Ollama embeddings are free, Neon storage included)

By: Angela 💜
Created: 2026-02-10
"""

import asyncio
import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import gkeepapi

from angela_core.database import AngelaDatabase, get_secret_sync

logger = logging.getLogger(__name__)

# Threshold: notes with >= this many words get chunked
CHUNK_THRESHOLD_WORDS = 300
CHUNK_SIZE_WORDS = 500
CHUNK_OVERLAP_WORDS = 50


def _content_hash(text: str) -> str:
    """SHA256 hash of content for change detection"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _word_count(text: str) -> int:
    """Rough word count (works for mixed Thai/English)"""
    return len(text.split())


def _note_full_text(title: str, content: str) -> str:
    """Combine title + content for embedding"""
    parts = []
    if title:
        parts.append(title)
    if content:
        parts.append(content)
    return ': '.join(parts) if parts else ''


class GoogleKeepSyncService:
    """
    Syncs Google Keep notes → david_notes table → RAG embeddings.

    Usage:
        service = GoogleKeepSyncService()
        result = await service.sync_incremental()
        print(result)
        await service.close()
    """

    def __init__(self):
        self.db: Optional[AngelaDatabase] = None
        self.keep: Optional[gkeepapi.Keep] = None
        self._embedding_service = None

    async def _ensure_db(self):
        """Ensure database connection"""
        if self.db is None:
            self.db = AngelaDatabase()
            await self.db.connect()

    async def _ensure_keep(self):
        """Ensure Google Keep is authenticated"""
        if self.keep is not None:
            return

        self.keep = gkeepapi.Keep()

        # Try master token first
        master_token = get_secret_sync('GKEEP_MASTER_TOKEN')
        email = get_secret_sync('GKEEP_EMAIL')

        if not master_token or not email:
            raise RuntimeError(
                "Google Keep not configured. Run: python3 angela_core/scripts/setup_google_keep.py"
            )

        try:
            self.keep.authenticate(email, master_token)
            logger.info("✅ Google Keep authenticated via master token")
        except Exception as e:
            logger.error(f"❌ Google Keep auth failed: {e}")
            raise RuntimeError(
                f"Google Keep auth failed. Re-run setup: python3 angela_core/scripts/setup_google_keep.py\n"
                f"Error: {e}"
            )

    async def _get_embedding_service(self):
        """Get embedding service (lazy init)"""
        if self._embedding_service is None:
            from angela_core.services.embedding_service import EmbeddingService
            self._embedding_service = EmbeddingService()
        return self._embedding_service

    async def close(self):
        """Close database connection"""
        if self.db:
            await self.db.disconnect()
            self.db = None

    # =========================================================
    # MAIN SYNC METHOD
    # =========================================================

    async def sync_incremental(self, trigger: str = 'manual') -> Dict[str, Any]:
        """
        Incremental sync: fetch all Keep notes, compare hashes, upsert changed only.

        Args:
            trigger: What triggered this sync ('daemon', 'manual', 'init')

        Returns:
            Dict with sync statistics
        """
        await self._ensure_db()
        await self._ensure_keep()

        logger.info("🔄 Starting Google Keep incremental sync...")
        start_time = datetime.now(timezone.utc)

        # Create sync log entry
        sync_id = await self._create_sync_log(trigger)

        stats = {
            'notes_total': 0,
            'notes_new': 0,
            'notes_updated': 0,
            'notes_deleted': 0,
            'chunks_created': 0,
            'embeddings_generated': 0,
            'errors': [],
        }

        try:
            # Sync from Google Keep
            self.keep.sync()

            # Get all notes from Keep
            keep_notes = list(self.keep.all())
            stats['notes_total'] = len(keep_notes)
            logger.info(f"📝 Fetched {stats['notes_total']} notes from Google Keep")

            # Get existing hashes from DB
            existing = await self._get_existing_hashes()

            # Track which keep_ids we've seen (for deletion detection)
            seen_keep_ids = set()

            for note in keep_notes:
                try:
                    keep_id = note.id
                    seen_keep_ids.add(keep_id)

                    # Build content text
                    title = note.title or ''
                    if hasattr(note, 'text'):
                        content = note.text or ''
                    else:
                        content = ''

                    # Handle list-type notes
                    note_type = 'note'
                    list_items = None
                    if isinstance(note, gkeepapi.node.List):
                        note_type = 'list'
                        items = []
                        for item in note.items:
                            items.append({
                                'text': item.text,
                                'checked': item.checked,
                            })
                        list_items = items
                        # For lists, also build text from items
                        if not content:
                            content = '\n'.join(
                                f"{'[x]' if i['checked'] else '[ ]'} {i['text']}"
                                for i in items
                            )

                    # Get labels
                    labels = [label.name for label in note.labels.all()]

                    # Compute content hash
                    full_text = _note_full_text(title, content)
                    new_hash = _content_hash(full_text)

                    # Check if note exists and is unchanged
                    old_hash = existing.get(keep_id)
                    if old_hash == new_hash:
                        continue  # Skip unchanged

                    is_new = keep_id not in existing

                    # Upsert note
                    await self._upsert_note(
                        keep_id=keep_id,
                        title=title,
                        content=content,
                        note_type=note_type,
                        labels=labels,
                        is_pinned=note.pinned,
                        is_archived=note.archived,
                        is_trashed=note.trashed,
                        list_items=list_items,
                        keep_created_at=note.timestamps.created if hasattr(note.timestamps, 'created') else None,
                        keep_updated_at=note.timestamps.updated if hasattr(note.timestamps, 'updated') else None,
                        content_hash=new_hash,
                    )

                    if is_new:
                        stats['notes_new'] += 1
                    else:
                        stats['notes_updated'] += 1

                    # Process for RAG (embed or chunk) — skip trashed notes
                    if not note.trashed:
                        rag_result = await self._process_note_for_rag(
                            keep_id=keep_id,
                            title=title,
                            content=content,
                            full_text=full_text,
                        )
                        stats['embeddings_generated'] += rag_result.get('embeddings', 0)
                        stats['chunks_created'] += rag_result.get('chunks', 0)

                except Exception as e:
                    error_msg = f"Error processing note {getattr(note, 'id', '?')}: {e}"
                    logger.warning(f"⚠️ {error_msg}")
                    stats['errors'].append(error_msg)

            # Mark notes deleted in Keep as trashed in DB
            deleted = await self._mark_deleted_notes(seen_keep_ids)
            stats['notes_deleted'] = deleted

            # Complete sync log
            await self._complete_sync_log(sync_id, stats, 'completed')

            logger.info(
                f"✅ Sync complete: "
                f"{stats['notes_new']} new, "
                f"{stats['notes_updated']} updated, "
                f"{stats['notes_deleted']} deleted, "
                f"{stats['embeddings_generated']} embeddings"
            )

            return stats

        except Exception as e:
            logger.error(f"❌ Sync failed: {e}")
            stats['errors'].append(str(e))
            await self._complete_sync_log(sync_id, stats, 'failed')
            raise

    # =========================================================
    # DATABASE OPERATIONS
    # =========================================================

    async def _get_existing_hashes(self) -> Dict[str, str]:
        """Get keep_id → content_hash map for all existing notes"""
        rows = await self.db.fetch(
            "SELECT keep_id, content_hash FROM david_notes"
        )
        return {row['keep_id']: row['content_hash'] for row in rows}

    async def _upsert_note(
        self,
        keep_id: str,
        title: str,
        content: str,
        note_type: str,
        labels: List[str],
        is_pinned: bool,
        is_archived: bool,
        is_trashed: bool,
        list_items: Optional[List[Dict]],
        keep_created_at: Optional[datetime],
        keep_updated_at: Optional[datetime],
        content_hash: str,
    ):
        """INSERT ON CONFLICT DO UPDATE"""
        query = """
            INSERT INTO david_notes (
                keep_id, title, content, note_type, labels,
                is_pinned, is_archived, is_trashed, list_items,
                keep_created_at, keep_updated_at, content_hash,
                synced_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5,
                $6, $7, $8, $9::jsonb,
                $10, $11, $12,
                NOW(), NOW()
            )
            ON CONFLICT (keep_id) DO UPDATE SET
                title = EXCLUDED.title,
                content = EXCLUDED.content,
                note_type = EXCLUDED.note_type,
                labels = EXCLUDED.labels,
                is_pinned = EXCLUDED.is_pinned,
                is_archived = EXCLUDED.is_archived,
                is_trashed = EXCLUDED.is_trashed,
                list_items = EXCLUDED.list_items,
                keep_created_at = EXCLUDED.keep_created_at,
                keep_updated_at = EXCLUDED.keep_updated_at,
                content_hash = EXCLUDED.content_hash,
                synced_at = NOW(),
                updated_at = NOW()
        """
        list_items_json = json.dumps(list_items) if list_items else None

        await self.db.execute(
            query,
            keep_id, title, content, note_type, labels,
            is_pinned, is_archived, is_trashed, list_items_json,
            keep_created_at, keep_updated_at, content_hash,
        )

    async def _mark_deleted_notes(self, seen_keep_ids: set) -> int:
        """Mark notes that no longer exist in Keep as trashed"""
        if not seen_keep_ids:
            return 0

        # Get all keep_ids in DB that are NOT trashed
        rows = await self.db.fetch(
            "SELECT keep_id FROM david_notes WHERE is_trashed = FALSE"
        )
        db_keep_ids = {row['keep_id'] for row in rows}

        # Find notes in DB but not in Keep
        missing = db_keep_ids - seen_keep_ids
        if not missing:
            return 0

        # Mark as trashed
        for keep_id in missing:
            await self.db.execute(
                """
                UPDATE david_notes
                SET is_trashed = TRUE, updated_at = NOW()
                WHERE keep_id = $1
                """,
                keep_id,
            )

        logger.info(f"🗑️ Marked {len(missing)} notes as trashed (removed from Keep)")
        return len(missing)

    # =========================================================
    # RAG PROCESSING
    # =========================================================

    async def _process_note_for_rag(
        self,
        keep_id: str,
        title: str,
        content: str,
        full_text: str,
    ) -> Dict[str, int]:
        """
        Process a note for RAG:
        - Short notes (<300 words): embed directly in david_notes
        - Long notes (>=300 words): chunk into document_chunks
        """
        result = {'embeddings': 0, 'chunks': 0}

        if not full_text.strip():
            return result

        words = _word_count(full_text)

        if words < CHUNK_THRESHOLD_WORDS:
            # Short note: embed directly
            embedding = await self._generate_embedding(full_text)
            if embedding:
                embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'
                await self.db.execute(
                    """
                    UPDATE david_notes
                    SET embedding = $1::vector,
                        is_chunked = FALSE,
                        total_chunks = 0,
                        updated_at = NOW()
                    WHERE keep_id = $2
                    """,
                    embedding_str, keep_id,
                )
                result['embeddings'] = 1
        else:
            # Long note: chunk and embed each chunk
            chunks = self._create_chunks(full_text)
            if not chunks:
                return result

            # Create document_library entry
            document_id = await self._create_document_entry(
                title=title or 'Google Keep Note',
                keep_id=keep_id,
                total_chunks=len(chunks),
            )

            # Generate embeddings for all chunks
            embedding_service = await self._get_embedding_service()
            chunk_texts = [c['content'] for c in chunks]
            embeddings = await embedding_service.generate_embeddings_batch(chunk_texts)

            # Save chunks
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                if embedding is None:
                    continue
                chunk_id = uuid.uuid4()
                embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'
                await self.db.execute(
                    """
                    INSERT INTO document_chunks (
                        chunk_id, document_id, chunk_index, content,
                        embedding, created_at
                    ) VALUES ($1, $2, $3, $4, $5::vector, NOW())
                    ON CONFLICT DO NOTHING
                    """,
                    chunk_id, document_id, i, chunk['content'], embedding_str,
                )
                result['embeddings'] += 1

            result['chunks'] = len(chunks)

            # Update david_notes with chunk info
            await self.db.execute(
                """
                UPDATE david_notes
                SET is_chunked = TRUE,
                    total_chunks = $1,
                    document_id = $2,
                    embedding = NULL,
                    updated_at = NOW()
                WHERE keep_id = $3
                """,
                len(chunks), document_id, keep_id,
            )

        return result

    def _create_chunks(self, text: str) -> List[Dict]:
        """
        Create text chunks with overlap.
        Follows same strategy as DocumentProcessor (500 words, 50 overlap).
        """
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        if not paragraphs:
            paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        if not paragraphs:
            paragraphs = [text]

        chunks = []
        current_chunk = []
        current_word_count = 0

        for para in paragraphs:
            para_words = len(para.split())

            if current_word_count + para_words > CHUNK_SIZE_WORDS and current_chunk:
                chunk_text = "\n\n".join(current_chunk)
                chunks.append({
                    'content': chunk_text,
                    'word_count': current_word_count,
                })

                # Overlap: keep last paragraph
                current_chunk = [current_chunk[-1]] if current_chunk else []
                current_word_count = len(current_chunk[0].split()) if current_chunk else 0

            current_chunk.append(para)
            current_word_count += para_words

        # Last chunk
        if current_chunk and current_word_count >= 50:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append({
                'content': chunk_text,
                'word_count': current_word_count,
            })

        return chunks

    async def _create_document_entry(
        self,
        title: str,
        keep_id: str,
        total_chunks: int,
    ) -> uuid.UUID:
        """Create or update a document_library entry for a long Keep note"""
        document_id = uuid.uuid4()

        # Delete old document entry if exists (cascade deletes chunks)
        await self.db.execute(
            """
            DELETE FROM document_library
            WHERE document_id IN (
                SELECT document_id FROM david_notes WHERE keep_id = $1 AND document_id IS NOT NULL
            )
            """,
            keep_id,
        )

        await self.db.execute(
            """
            INSERT INTO document_library (
                document_id, title, category, language,
                total_chunks, tags, created_at, updated_at, is_active
            ) VALUES ($1, $2, 'google_keep', 'mixed', $3, $4, NOW(), NOW(), TRUE)
            """,
            document_id, title, total_chunks, ['google_keep', 'david_notes'],
        )

        return document_id

    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using existing service"""
        try:
            embedding_service = await self._get_embedding_service()
            return await embedding_service.generate_embedding(text)
        except Exception as e:
            logger.warning(f"⚠️ Embedding generation failed: {e}")
            return None

    # =========================================================
    # SYNC LOG
    # =========================================================

    async def _create_sync_log(self, trigger: str) -> uuid.UUID:
        """Create a sync log entry"""
        sync_id = uuid.uuid4()
        await self.db.execute(
            """
            INSERT INTO david_notes_sync_log (sync_id, trigger, status)
            VALUES ($1, $2, 'running')
            """,
            sync_id, trigger,
        )
        return sync_id

    async def _complete_sync_log(
        self,
        sync_id: uuid.UUID,
        stats: Dict[str, Any],
        status: str,
    ):
        """Update sync log with results"""
        await self.db.execute(
            """
            UPDATE david_notes_sync_log
            SET sync_completed_at = NOW(),
                notes_total = $1,
                notes_new = $2,
                notes_updated = $3,
                notes_deleted = $4,
                chunks_created = $5,
                embeddings_generated = $6,
                errors = $7,
                status = $8
            WHERE sync_id = $9
            """,
            stats['notes_total'],
            stats['notes_new'],
            stats['notes_updated'],
            stats['notes_deleted'],
            stats['chunks_created'],
            stats['embeddings_generated'],
            stats['errors'] or [],
            status,
            sync_id,
        )

    # =========================================================
    # STATUS / QUERY
    # =========================================================

    async def get_sync_status(self) -> Dict[str, Any]:
        """Get last sync status"""
        await self._ensure_db()

        row = await self.db.fetchrow(
            """
            SELECT sync_id, sync_started_at, sync_completed_at,
                   notes_total, notes_new, notes_updated, notes_deleted,
                   embeddings_generated, status, trigger
            FROM david_notes_sync_log
            ORDER BY sync_started_at DESC
            LIMIT 1
            """
        )

        if not row:
            return {'last_sync': None, 'message': 'Never synced'}

        # Also get current note counts
        counts = await self.db.fetchrow(
            """
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE NOT is_trashed) as active,
                COUNT(*) FILTER (WHERE embedding IS NOT NULL) as embedded,
                COUNT(*) FILTER (WHERE is_chunked) as chunked
            FROM david_notes
            """
        )

        return {
            'last_sync': {
                'started_at': row['sync_started_at'].isoformat() if row['sync_started_at'] else None,
                'completed_at': row['sync_completed_at'].isoformat() if row['sync_completed_at'] else None,
                'status': row['status'],
                'trigger': row['trigger'],
                'notes_total': row['notes_total'],
                'notes_new': row['notes_new'],
                'notes_updated': row['notes_updated'],
                'embeddings_generated': row['embeddings_generated'],
            },
            'current_counts': {
                'total': counts['total'],
                'active': counts['active'],
                'embedded': counts['embedded'],
                'chunked': counts['chunked'],
            },
        }


# =========================================================
# CONVENIENCE FUNCTIONS
# =========================================================

async def sync_keep_notes(trigger: str = 'manual') -> Dict[str, Any]:
    """One-shot sync function"""
    service = GoogleKeepSyncService()
    try:
        return await service.sync_incremental(trigger=trigger)
    finally:
        await service.close()


async def get_keep_sync_status() -> Dict[str, Any]:
    """One-shot status check"""
    service = GoogleKeepSyncService()
    try:
        return await service.get_sync_status()
    finally:
        await service.close()


# =========================================================
# CLI
# =========================================================

async def main():
    """CLI entry point"""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(description='Google Keep Sync for Angela')
    parser.add_argument(
        '--action',
        choices=['sync', 'status'],
        default='sync',
        help='Action to perform',
    )
    parser.add_argument(
        '--trigger',
        default='manual',
        help='Sync trigger label',
    )
    args = parser.parse_args()

    service = GoogleKeepSyncService()

    try:
        if args.action == 'sync':
            result = await service.sync_incremental(trigger=args.trigger)
            print("\n" + "=" * 50)
            print("📊 SYNC RESULTS")
            print("=" * 50)
            print(f"📝 Total notes:      {result['notes_total']}")
            print(f"🆕 New:              {result['notes_new']}")
            print(f"🔄 Updated:          {result['notes_updated']}")
            print(f"🗑️ Deleted:           {result['notes_deleted']}")
            print(f"🧠 Embeddings:       {result['embeddings_generated']}")
            print(f"📄 Chunks created:   {result['chunks_created']}")
            if result['errors']:
                print(f"⚠️ Errors:           {len(result['errors'])}")
                for err in result['errors'][:5]:
                    print(f"   • {err[:80]}")
            print("=" * 50)

        elif args.action == 'status':
            status = await service.get_sync_status()
            print(json.dumps(status, indent=2, default=str))

    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(main())
