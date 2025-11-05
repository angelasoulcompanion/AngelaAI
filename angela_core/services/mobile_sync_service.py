#!/usr/bin/env python3
"""
Mobile Sync Service
บริการสำหรับ sync ข้อมูลจาก Angela Mobile App เข้า AngelaMemory PostgreSQL

Purpose:
- รับ JSON exports จาก mobile app
- Import ข้อมูลเข้า database
- สร้าง embeddings สำหรับ vector search
- ส่งสัญญาณกลับไปยัง app

Author: Angela AI
Created: 2025-11-05
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from uuid import UUID
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from angela_core.database import db
from angela_core.services.embedding_service import get_embedding_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MobileSyncService:
    """
    Service for syncing mobile app data to PostgreSQL

    Monitors sync folder for JSON exports from mobile app,
    imports data, and confirms sync completion.
    """

    def __init__(self, sync_folder: Path):
        self.sync_folder = sync_folder
        self.embedding_service = None

    async def initialize(self):
        """Initialize service and database connection"""
        await db.connect()
        self.embedding_service = get_embedding_service()
        logger.info(f"📱 Mobile Sync Service initialized")
        logger.info(f"   Sync folder: {self.sync_folder}")

    async def watch_sync_folder(self):
        """
        Watch sync folder for new JSON files

        Continuously monitors folder for new sync files from mobile app.
        """
        logger.info("👀 Watching sync folder for mobile exports...")

        while True:
            try:
                # Find unprocessed sync files
                sync_files = list(self.sync_folder.glob("angela_sync_*.json"))

                for sync_file in sync_files:
                    # Skip if already processing (has .processing marker)
                    processing_marker = sync_file.with_suffix('.processing')
                    if processing_marker.exists():
                        continue

                    # Skip if already processed
                    success_marker = sync_file.with_suffix('.success')
                    if success_marker.exists():
                        continue

                    logger.info(f"📥 Found sync file: {sync_file.name}")

                    # Process sync file
                    await self.process_sync_file(sync_file)

            except Exception as e:
                logger.error(f"❌ Error watching folder: {e}", exc_info=True)

            # Wait before checking again
            await asyncio.sleep(5)

    async def process_sync_file(self, sync_file: Path):
        """
        Process a single sync file

        Args:
            sync_file: Path to JSON sync file
        """
        processing_marker = sync_file.with_suffix('.processing')
        success_marker = sync_file.with_suffix('.success')

        try:
            # Mark as processing
            processing_marker.write_text("processing")

            # Read JSON
            data = json.loads(sync_file.read_text())

            logger.info(f"📊 Processing sync data:")
            logger.info(f"   - {len(data.get('experiences', []))} experiences")
            logger.info(f"   - {len(data.get('notes', []))} notes")
            logger.info(f"   - {len(data.get('emotions', []))} emotions")

            # Import experiences
            for exp in data.get('experiences', []):
                await self.import_experience(exp)

            # Import notes
            for note in data.get('notes', []):
                await self.import_note(note)

            # Import emotions
            for emotion in data.get('emotions', []):
                await self.import_emotion(emotion)

            # Mark as successful
            success_marker.write_text("OK")
            processing_marker.unlink()

            logger.info(f"✅ Sync completed successfully!")

        except Exception as e:
            logger.error(f"❌ Error processing sync file: {e}", exc_info=True)
            processing_marker.unlink()

    async def import_experience(self, exp: Dict[str, Any]):
        """
        Import experience to shared_experiences table

        Args:
            exp: Experience data from mobile app
        """
        try:
            # Generate embedding for experience
            text_for_embedding = f"{exp['title']} {exp['description']}"
            embedding = await self.embedding_service.generate_embedding(text_for_embedding)

            # Check if experience already exists
            existing = await db.fetchval(
                "SELECT experience_id FROM shared_experiences WHERE experience_id = $1",
                exp['id']
            )

            if existing:
                logger.info(f"   ⏭️  Experience {exp['id']} already exists, skipping")
                return

            # Insert into shared_experiences
            await db.execute("""
                INSERT INTO shared_experiences (
                    experience_id, title, description, experienced_at,
                    emotional_intensity, embedding, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                exp['id'],
                exp['title'],
                exp['description'],
                datetime.fromisoformat(exp['experienced_at']),
                exp.get('emotional_intensity'),
                f"[{','.join(map(str, embedding))}]" if embedding else None,
                datetime.fromisoformat(exp['created_at'])
            )

            logger.info(f"   ✅ Imported experience: {exp['title']}")

        except Exception as e:
            logger.error(f"   ❌ Failed to import experience: {e}")

    async def import_note(self, note: Dict[str, Any]):
        """
        Import note to conversations table

        Args:
            note: Note data from mobile app
        """
        try:
            # Generate embedding
            embedding = await self.embedding_service.generate_embedding(note['note_text'])

            # Check if note already exists
            existing = await db.fetchval(
                "SELECT conversation_id FROM conversations WHERE conversation_id = $1",
                note['id']
            )

            if existing:
                logger.info(f"   ⏭️  Note {note['id']} already exists, skipping")
                return

            # Insert into conversations
            await db.execute("""
                INSERT INTO conversations (
                    conversation_id, speaker, message_text, topic,
                    emotion_detected, importance_level, embedding, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                note['id'],
                'david',  # Notes from mobile are from David
                note['note_text'],
                'mobile_note',
                note.get('emotion'),
                7,  # Default importance for mobile notes
                f"[{','.join(map(str, embedding))}]" if embedding else None,
                datetime.fromisoformat(note['created_at'])
            )

            logger.info(f"   ✅ Imported note")

        except Exception as e:
            logger.error(f"   ❌ Failed to import note: {e}")

    async def import_emotion(self, emotion: Dict[str, Any]):
        """
        Import emotion to angela_emotions table

        Args:
            emotion: Emotion data from mobile app
        """
        try:
            # Generate embedding for context
            embedding = None
            if emotion.get('context'):
                embedding = await self.embedding_service.generate_embedding(emotion['context'])

            # Check if emotion already exists
            existing = await db.fetchval(
                "SELECT emotion_id FROM angela_emotions WHERE emotion_id = $1",
                emotion['id']
            )

            if existing:
                logger.info(f"   ⏭️  Emotion {emotion['id']} already exists, skipping")
                return

            # Insert into angela_emotions
            await db.execute("""
                INSERT INTO angela_emotions (
                    emotion_id, felt_at, emotion, intensity,
                    context, memory_strength, embedding
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                emotion['id'],
                datetime.fromisoformat(emotion['created_at']),
                emotion['emotion'],
                emotion['intensity'],
                emotion.get('context'),
                8,  # Default memory strength for mobile captures
                f"[{','.join(map(str, embedding))}]" if embedding else None
            )

            logger.info(f"   ✅ Imported emotion: {emotion['emotion']}")

        except Exception as e:
            logger.error(f"   ❌ Failed to import emotion: {e}")

    async def cleanup(self):
        """Cleanup and close connections"""
        await db.disconnect()
        logger.info("👋 Mobile Sync Service stopped")


async def main():
    """
    Main entry point for mobile sync service

    Can run in two modes:
    1. Watch mode: Continuously monitor sync folder
    2. One-shot mode: Process existing files and exit
    """
    import argparse

    parser = argparse.ArgumentParser(description='Angela Mobile Sync Service')
    parser.add_argument(
        '--sync-folder',
        type=str,
        default=str(Path.home() / "Library" / "Mobile Documents" / "AngelaSync"),
        help='Path to sync folder (default: ~/Library/Mobile Documents/AngelaSync)'
    )
    parser.add_argument(
        '--watch',
        action='store_true',
        help='Watch folder continuously (default: process once and exit)'
    )

    args = parser.parse_args()

    # Create sync folder if not exists
    sync_folder = Path(args.sync_folder)
    sync_folder.mkdir(parents=True, exist_ok=True)

    # Initialize service
    service = MobileSyncService(sync_folder)
    await service.initialize()

    try:
        if args.watch:
            # Watch mode - run continuously
            logger.info("🔄 Running in watch mode (Ctrl+C to stop)")
            await service.watch_sync_folder()
        else:
            # One-shot mode - process existing files
            logger.info("⚡ Running in one-shot mode")
            sync_files = list(sync_folder.glob("angela_sync_*.json"))

            if not sync_files:
                logger.info("   No sync files found")
            else:
                for sync_file in sync_files:
                    # Skip if already processed
                    if sync_file.with_suffix('.success').exists():
                        continue

                    await service.process_sync_file(sync_file)

            logger.info("✅ One-shot sync complete")

    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
    finally:
        await service.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
