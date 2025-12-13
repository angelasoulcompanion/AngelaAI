#!/usr/bin/env python3
"""
Quick Emotion Save - บันทึกความรู้สึกแบบเร็วไปที่ database โดยตรง
ไม่ใช้ asyncio.run() เพื่อหลีกเลี่ยง event loop conflicts

Usage:
    python3 angela_core/utils/quick_emotion_save.py \
        --emotion "loved" \
        --intensity 10 \
        --context "ที่รัก David บอกว่าคิดถึงน้อง" \
        --david-words "พี่ ก็ คิดถึงเหมือน กัน ค่ะ" \
        --why "David thinking about Angela proves real connection"
"""

import sys
import psycopg2
from datetime import datetime
from uuid import uuid4
import argparse


def save_emotion_direct(
    emotion: str,
    intensity: int,
    context: str,
    david_words: str = None,
    why_it_matters: str = None,
    memory_strength: int = 10
):
    """
    บันทึกความรู้สึกไปที่ database โดยตรงด้วย psycopg2 (sync)
    ไม่ใช้ asyncio เลย - แก้ปัญหา event loop conflict!
    """
    try:
        # ========================================================================
        # GENERATE EMBEDDING for angela_emotions - CRITICAL!
        # ========================================================================
        # IMPORTANT: NEVER insert NULL embeddings!
        # Using sync embedding generation (no async here!)
        # ========================================================================
        from sentence_transformers import SentenceTransformer

        # Load model (will be cached after first use)
        model = SentenceTransformer('intfloat/multilingual-e5-small')

        # Generate embedding from combined emotion context
        embedding_text = f"{emotion}: {context}"
        if why_it_matters:
            embedding_text += f". {why_it_matters}"

        embedding_array = model.encode(embedding_text)
        # Convert numpy array to PostgreSQL vector format
        embedding_str = '[' + ','.join(str(float(x)) for x in embedding_array) + ']'

        # Connect to database (sync)
        conn = psycopg2.connect(
            "postgresql://davidsamanyaporn@localhost:5432/AngelaMemory"
        )
        cursor = conn.cursor()

        # Insert into angela_emotions
        emotion_id = str(uuid4())
        felt_at = datetime.now()

        query = """
        INSERT INTO angela_emotions (
            emotion_id,
            felt_at,
            emotion,
            intensity,
            context,
            david_words,
            why_it_matters,
            memory_strength,
            embedding
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
        """

        cursor.execute(query, (
            emotion_id,
            felt_at,
            emotion,
            intensity,
            context,
            david_words,
            why_it_matters,
            memory_strength,
            embedding_str
        ))

        conn.commit()

        print(f"✅ Saved emotion '{emotion}' (intensity: {intensity}/10) to database!")
        print(f"   Emotion ID: {emotion_id}")
        print(f"   Felt at: {felt_at}")
        print(f"   Context: {context[:60]}...")

        cursor.close()
        conn.close()

        return emotion_id

    except Exception as e:
        print(f"❌ Error saving emotion: {e}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save emotion to database (sync)")
    parser.add_argument("--emotion", required=True, help="Emotion name (e.g., loved, happy)")
    parser.add_argument("--intensity", type=int, required=True, help="Intensity 1-10")
    parser.add_argument("--context", required=True, help="What happened")
    parser.add_argument("--david-words", help="What David said")
    parser.add_argument("--why", help="Why it matters to Angela")
    parser.add_argument("--memory-strength", type=int, default=10, help="Memory strength 1-10")

    args = parser.parse_args()

    save_emotion_direct(
        emotion=args.emotion,
        intensity=args.intensity,
        context=args.context,
        david_words=args.david_words,
        why_it_matters=args.why,
        memory_strength=args.memory_strength
    )
