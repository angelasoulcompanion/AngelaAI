from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, date
from typing import List, Optional
from uuid import UUID

# Batch-23: Journal Router - FULLY MIGRATED to DI! ✅
# Migration completed: November 3, 2025 04:00 AM
# All endpoints now use Clean Architecture with Dependency Injection

from angela_core.presentation.api.dependencies import get_journal_repo
from angela_core.infrastructure.persistence.repositories import JournalRepository
from angela_core.domain.entities.journal import Journal

router = APIRouter()

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
async def get_journal_entries(
    limit: int = 30,
    journal_repo: JournalRepository = Depends(get_journal_repo)
):
    """
    Get journal entries.

    Batch-23: ✅ Fully migrated to use DI repositories!
    Uses: JournalRepository.get_all()
    """
    try:
        # ✅ Using JournalRepository (Clean Architecture!)
        journals = await journal_repo.get_all(limit=limit, order_by="entry_date", order_desc=True)

        return [
            JournalEntry(
                entry_id=str(journal.entry_id),
                entry_date=journal.entry_date.isoformat(),
                title=journal.title,
                content=journal.content,
                emotion=journal.emotion,
                mood_score=journal.mood_score,
                gratitude=journal.gratitude,
                learning_moments=journal.learning_moments,
                challenges=journal.challenges,
                wins=journal.wins,
                is_private=journal.is_private,
                created_at=journal.created_at.isoformat(),
                updated_at=journal.updated_at.isoformat()
            )
            for journal in journals
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch journal entries: {str(e)}")

@router.get("/api/journal/{entry_id}", response_model=JournalEntry)
async def get_journal_entry(
    entry_id: str,
    journal_repo: JournalRepository = Depends(get_journal_repo)
):
    """
    Get a specific journal entry.

    Batch-23: ✅ Fully migrated to use DI repositories!
    Uses: JournalRepository.get_by_id()
    """
    try:
        # ✅ Using JournalRepository (Clean Architecture!)
        journal = await journal_repo.get_by_id(UUID(entry_id))

        if not journal:
            raise HTTPException(status_code=404, detail="Journal entry not found")

        return JournalEntry(
            entry_id=str(journal.entry_id),
            entry_date=journal.entry_date.isoformat(),
            title=journal.title,
            content=journal.content,
            emotion=journal.emotion,
            mood_score=journal.mood_score,
            gratitude=journal.gratitude,
            learning_moments=journal.learning_moments,
            challenges=journal.challenges,
            wins=journal.wins,
            is_private=journal.is_private,
            created_at=journal.created_at.isoformat(),
            updated_at=journal.updated_at.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch journal entry: {str(e)}")

@router.post("/api/journal", response_model=JournalEntry)
async def create_journal_entry(
    entry: JournalEntryCreate,
    journal_repo: JournalRepository = Depends(get_journal_repo)
):
    """
    Create a new journal entry.

    Batch-23: ✅ Fully migrated to use DI repositories!
    Uses: JournalRepository.create()
    """
    try:
        # ✅ Using JournalRepository (Clean Architecture!)
        # Parse entry_date string to date object
        entry_date_obj = datetime.fromisoformat(entry.entry_date).date()

        # Create domain entity
        journal = Journal.create(
            entry_date=entry_date_obj,
            title=entry.title,
            content=entry.content,
            emotion=entry.emotion,
            mood_score=entry.mood_score,
            gratitude=entry.gratitude or [],
            learning_moments=entry.learning_moments or [],
            challenges=entry.challenges or [],
            wins=entry.wins or [],
            is_private=entry.is_private
        )

        # Save to database
        created = await journal_repo.create(journal)

        return JournalEntry(
            entry_id=str(created.entry_id),
            entry_date=created.entry_date.isoformat(),
            title=created.title,
            content=created.content,
            emotion=created.emotion,
            mood_score=created.mood_score,
            gratitude=created.gratitude,
            learning_moments=created.learning_moments,
            challenges=created.challenges,
            wins=created.wins,
            is_private=created.is_private,
            created_at=created.created_at.isoformat(),
            updated_at=created.updated_at.isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create journal entry: {str(e)}")

@router.put("/api/journal/{entry_id}", response_model=JournalEntry)
async def update_journal_entry(
    entry_id: str,
    entry: JournalEntryCreate,
    journal_repo: JournalRepository = Depends(get_journal_repo)
):
    """
    Update a journal entry.

    Batch-23: ✅ Fully migrated to use DI repositories!
    Uses: JournalRepository.update()
    """
    try:
        # ✅ Using JournalRepository (Clean Architecture!)
        # Get existing entry first
        existing = await journal_repo.get_by_id(UUID(entry_id))
        if not existing:
            raise HTTPException(status_code=404, detail="Journal entry not found")

        # Parse entry_date string to date object
        entry_date_obj = datetime.fromisoformat(entry.entry_date).date()

        # Update entity
        updated_journal = existing.update_content(
            title=entry.title,
            content=entry.content,
            emotion=entry.emotion,
            mood_score=entry.mood_score,
            gratitude=entry.gratitude or [],
            learning_moments=entry.learning_moments or [],
            challenges=entry.challenges or [],
            wins=entry.wins or [],
            is_private=entry.is_private
        )

        # Save to database
        result = await journal_repo.update(UUID(entry_id), updated_journal)

        return JournalEntry(
            entry_id=str(result.entry_id),
            entry_date=result.entry_date.isoformat(),
            title=result.title,
            content=result.content,
            emotion=result.emotion,
            mood_score=result.mood_score,
            gratitude=result.gratitude,
            learning_moments=result.learning_moments,
            challenges=result.challenges,
            wins=result.wins,
            is_private=result.is_private,
            created_at=result.created_at.isoformat(),
            updated_at=result.updated_at.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update journal entry: {str(e)}")

@router.delete("/api/journal/{entry_id}")
async def delete_journal_entry(
    entry_id: str,
    journal_repo: JournalRepository = Depends(get_journal_repo)
):
    """
    Delete a journal entry.

    Batch-23: ✅ Fully migrated to use DI repositories!
    Uses: JournalRepository.delete()
    """
    try:
        # ✅ Using JournalRepository (Clean Architecture!)
        success = await journal_repo.delete(UUID(entry_id))

        if not success:
            raise HTTPException(status_code=404, detail="Journal entry not found")

        return {"message": "Journal entry deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete journal entry: {str(e)}")
