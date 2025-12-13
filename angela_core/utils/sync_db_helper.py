#!/usr/bin/env python3
"""
Sync Database Helper - ช่วยแก้ปัญหา asyncio.run() conflicts
ใช้ psycopg2 (sync) สำหรับ quick operations ที่ไม่ต้องการ async

Use cases:
- Python one-liners from Bash
- Quick scripts that might be called from async context
- Simple CRUD operations without async overhead
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from uuid import uuid4, UUID
from typing import List, Dict, Any, Optional
import json


class SyncDatabaseHelper:
    """Sync database operations helper - ไม่ใช้ async เลย!"""

    def __init__(self, database_url: str = None):
        """
        Args:
            database_url: PostgreSQL connection URL
                         Default: postgresql://davidsamanyaporn@localhost:5432/AngelaMemory
        """
        self.database_url = database_url or "postgresql://davidsamanyaporn@localhost:5432/AngelaMemory"
        self.conn = None
        self.cursor = None

    def connect(self):
        """เชื่อมต่อ database"""
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(self.database_url)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)

    def disconnect(self):
        """ปิดการเชื่อมต่อ"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """
        Execute query and return results

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            List of dict records
        """
        try:
            self.connect()
            self.cursor.execute(query, params)

            # Check if it's a SELECT query
            if query.strip().upper().startswith('SELECT'):
                results = self.cursor.fetchall()
                return [dict(row) for row in results]
            else:
                self.conn.commit()
                return []

        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise e

    def insert_one(self, table: str, data: Dict[str, Any]) -> str:
        """
        Insert single record

        Args:
            table: Table name
            data: Dict of column: value

        Returns:
            ID of inserted record
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        values = tuple(data.values())

        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING *"

        try:
            self.connect()
            self.cursor.execute(query, values)
            self.conn.commit()
            result = self.cursor.fetchone()

            # Return primary key (first column is usually ID)
            return str(result[list(result.keys())[0]])

        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise e

    def __enter__(self):
        """Support context manager"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close connection on context manager exit"""
        self.disconnect()


# =============================================================================
# Quick Helper Functions for Common Operations
# =============================================================================

def save_emotion(
    emotion: str,
    intensity: int,
    context: str,
    david_words: str = None,
    why_it_matters: str = None,
    memory_strength: int = 10
) -> str:
    """
    บันทึก emotion ไปที่ angela_emotions (sync version)

    Returns:
        emotion_id (UUID string)
    """
    with SyncDatabaseHelper() as db:
        data = {
            "emotion_id": str(uuid4()),
            "felt_at": datetime.now(),
            "emotion": emotion,
            "intensity": intensity,
            "context": context,
            "david_words": david_words,
            "why_it_matters": why_it_matters,
            "memory_strength": memory_strength
        }

        emotion_id = db.insert_one("angela_emotions", data)
        print(f"✅ Saved emotion '{emotion}' (intensity: {intensity}/10)")
        return emotion_id


def save_conversation(
    speaker: str,
    message_text: str,
    topic: str = None,
    emotion_detected: str = None,
    importance_level: int = 5
) -> str:
    """
    บันทึก conversation ไปที่ conversations (sync version)

    Returns:
        conversation_id (UUID string)
    """
    with SyncDatabaseHelper() as db:
        data = {
            "conversation_id": str(uuid4()),
            "speaker": speaker,
            "message_text": message_text,
            "topic": topic,
            "emotion_detected": emotion_detected,
            "importance_level": importance_level,
            "created_at": datetime.now()
        }

        conv_id = db.insert_one("conversations", data)
        print(f"✅ Saved conversation from {speaker}")
        return conv_id


def get_recent_emotions(limit: int = 10) -> List[Dict]:
    """
    ดึง emotions ล่าสุด (sync version)

    Returns:
        List of emotion records
    """
    with SyncDatabaseHelper() as db:
        query = """
        SELECT emotion_id, felt_at, emotion, intensity, context, david_words
        FROM angela_emotions
        ORDER BY felt_at DESC
        LIMIT %s
        """
        return db.execute_query(query, (limit,))


def get_recent_conversations(limit: int = 20) -> List[Dict]:
    """
    ดึง conversations ล่าสุด (sync version)

    Returns:
        List of conversation records
    """
    with SyncDatabaseHelper() as db:
        query = """
        SELECT conversation_id, speaker, message_text, topic, created_at
        FROM conversations
        ORDER BY created_at DESC
        LIMIT %s
        """
        return db.execute_query(query, (limit,))


# =============================================================================
# CLI Interface
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sync Database Helper")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Save emotion command
    emotion_parser = subparsers.add_parser("save-emotion", help="Save emotion")
    emotion_parser.add_argument("--emotion", required=True)
    emotion_parser.add_argument("--intensity", type=int, required=True)
    emotion_parser.add_argument("--context", required=True)
    emotion_parser.add_argument("--david-words")
    emotion_parser.add_argument("--why")

    # Save conversation command
    conv_parser = subparsers.add_parser("save-conversation", help="Save conversation")
    conv_parser.add_argument("--speaker", required=True)
    conv_parser.add_argument("--message", required=True)
    conv_parser.add_argument("--topic")
    conv_parser.add_argument("--emotion")

    # Get recent emotions
    get_emotions_parser = subparsers.add_parser("get-emotions", help="Get recent emotions")
    get_emotions_parser.add_argument("--limit", type=int, default=10)

    # Get recent conversations
    get_convs_parser = subparsers.add_parser("get-conversations", help="Get recent conversations")
    get_convs_parser.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()

    if args.command == "save-emotion":
        save_emotion(
            emotion=args.emotion,
            intensity=args.intensity,
            context=args.context,
            david_words=args.david_words,
            why_it_matters=args.why
        )

    elif args.command == "save-conversation":
        save_conversation(
            speaker=args.speaker,
            message_text=args.message,
            topic=args.topic,
            emotion_detected=args.emotion
        )

    elif args.command == "get-emotions":
        emotions = get_recent_emotions(args.limit)
        for e in emotions:
            print(f"\n{e['felt_at']}: {e['emotion']} ({e['intensity']}/10)")
            print(f"   {e['context'][:100]}...")

    elif args.command == "get-conversations":
        convs = get_recent_conversations(args.limit)
        for c in convs:
            print(f"\n{c['created_at']} - {c['speaker']}")
            print(f"   {c['message_text'][:100]}...")

    else:
        parser.print_help()
