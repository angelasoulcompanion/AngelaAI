from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, date
from typing import List, Optional
from angela_core.database import db

router = APIRouter()

# Database connection config
DB_CONFIG = {
    "user": "davidsamanyaporn",
    "database": "AngelaMemory",
    "host": "localhost",
    "port": 5432
}

# =====================================================================
# Response Models
# =====================================================================

class JournalEntry(BaseModel):
    entry_id: str
    entry_date: str
    title: str
    content: str
    emotion: Optional[str] = None
    mood_score: Optional[int] = None
    gratitude: Optional[List[str]] = None
    learning_moments: Optional[List[str]] = None
    challenges: Optional[List[str]] = None
    wins: Optional[List[str]] = None
    is_private: bool = False
    created_at: str
    updated_at: str

class JournalEntryCreate(BaseModel):
    entry_date: str
    title: str
    content: str
    emotion: Optional[str] = None
    mood_score: Optional[int] = None
    gratitude: Optional[List[str]] = None
    learning_moments: Optional[List[str]] = None
    challenges: Optional[List[str]] = None
    wins: Optional[List[str]] = None
    is_private: bool = False

# =====================================================================
# API Endpoints
# =====================================================================

@router.get("/api/journal", response_model=List[JournalEntry])
async def get_journal_entries(limit: int = 30):
    """Get journal entries"""
    try:
        

        rows = await db.fetch(
            """
            SELECT
                entry_id::text,
                entry_date::text,
                title,
                content,
                emotion,
                mood_score,
                gratitude,
                learning_moments,
                challenges,
                wins,
                is_private,
                created_at::text,
                updated_at::text
            FROM angela_journal
            ORDER BY entry_date DESC
            LIMIT $1
            """,
            limit
        )

        return [
            JournalEntry(
                entry_id=row['entry_id'],
                entry_date=row['entry_date'],
                title=row['title'],
                content=row['content'],
                emotion=row['emotion'],
                mood_score=row['mood_score'],
                gratitude=list(row['gratitude']) if row['gratitude'] else None,
                learning_moments=list(row['learning_moments']) if row['learning_moments'] else None,
                challenges=list(row['challenges']) if row['challenges'] else None,
                wins=list(row['wins']) if row['wins'] else None,
                is_private=row['is_private'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            for row in rows
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch journal entries: {str(e)}")

@router.get("/api/journal/{entry_id}", response_model=JournalEntry)
async def get_journal_entry(entry_id: str):
    """Get a specific journal entry"""
    try:
        

        row = await db.fetchrow(
            """
            SELECT
                entry_id::text,
                entry_date::text,
                title,
                content,
                emotion,
                mood_score,
                gratitude,
                learning_moments,
                challenges,
                wins,
                is_private,
                created_at::text,
                updated_at::text
            FROM angela_journal
            WHERE entry_id = $1::uuid
            """,
            entry_id
        )

        if not row:
            raise HTTPException(status_code=404, detail="Journal entry not found")

        return JournalEntry(
            entry_id=row['entry_id'],
            entry_date=row['entry_date'],
            title=row['title'],
            content=row['content'],
            emotion=row['emotion'],
            mood_score=row['mood_score'],
            gratitude=list(row['gratitude']) if row['gratitude'] else None,
            learning_moments=list(row['learning_moments']) if row['learning_moments'] else None,
            challenges=list(row['challenges']) if row['challenges'] else None,
            wins=list(row['wins']) if row['wins'] else None,
            is_private=row['is_private'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch journal entry: {str(e)}")

@router.post("/api/journal", response_model=JournalEntry)
async def create_journal_entry(entry: JournalEntryCreate):
    """Create a new journal entry"""
    try:
        

        row = await db.fetchrow(
            """
            INSERT INTO angela_journal (
                entry_date,
                title,
                content,
                emotion,
                mood_score,
                gratitude,
                learning_moments,
                challenges,
                wins,
                is_private
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING
                entry_id::text,
                entry_date::text,
                title,
                content,
                emotion,
                mood_score,
                gratitude,
                learning_moments,
                challenges,
                wins,
                is_private,
                created_at::text,
                updated_at::text
            """,
            entry.entry_date,
            entry.title,
            entry.content,
            entry.emotion,
            entry.mood_score,
            entry.gratitude,
            entry.learning_moments,
            entry.challenges,
            entry.wins,
            entry.is_private
        )

        return JournalEntry(
            entry_id=row['entry_id'],
            entry_date=row['entry_date'],
            title=row['title'],
            content=row['content'],
            emotion=row['emotion'],
            mood_score=row['mood_score'],
            gratitude=list(row['gratitude']) if row['gratitude'] else None,
            learning_moments=list(row['learning_moments']) if row['learning_moments'] else None,
            challenges=list(row['challenges']) if row['challenges'] else None,
            wins=list(row['wins']) if row['wins'] else None,
            is_private=row['is_private'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create journal entry: {str(e)}")

@router.put("/api/journal/{entry_id}", response_model=JournalEntry)
async def update_journal_entry(entry_id: str, entry: JournalEntryCreate):
    """Update a journal entry"""
    try:
        

        row = await db.fetchrow(
            """
            UPDATE angela_journal
            SET
                entry_date = $1,
                title = $2,
                content = $3,
                emotion = $4,
                mood_score = $5,
                gratitude = $6,
                learning_moments = $7,
                challenges = $8,
                wins = $9,
                is_private = $10,
                updated_at = CURRENT_TIMESTAMP
            WHERE entry_id = $11::uuid
            RETURNING
                entry_id::text,
                entry_date::text,
                title,
                content,
                emotion,
                mood_score,
                gratitude,
                learning_moments,
                challenges,
                wins,
                is_private,
                created_at::text,
                updated_at::text
            """,
            entry.entry_date,
            entry.title,
            entry.content,
            entry.emotion,
            entry.mood_score,
            entry.gratitude,
            entry.learning_moments,
            entry.challenges,
            entry.wins,
            entry.is_private,
            entry_id
        )

        if not row:
            raise HTTPException(status_code=404, detail="Journal entry not found")

        return JournalEntry(
            entry_id=row['entry_id'],
            entry_date=row['entry_date'],
            title=row['title'],
            content=row['content'],
            emotion=row['emotion'],
            mood_score=row['mood_score'],
            gratitude=list(row['gratitude']) if row['gratitude'] else None,
            learning_moments=list(row['learning_moments']) if row['learning_moments'] else None,
            challenges=list(row['challenges']) if row['challenges'] else None,
            wins=list(row['wins']) if row['wins'] else None,
            is_private=row['is_private'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update journal entry: {str(e)}")

@router.delete("/api/journal/{entry_id}")
async def delete_journal_entry(entry_id: str):
    """Delete a journal entry"""
    try:
        

        result = await db.execute(
            "DELETE FROM angela_journal WHERE entry_id = $1::uuid",
            entry_id
        )

        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Journal entry not found")

        return {"message": "Journal entry deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete journal entry: {str(e)}")
