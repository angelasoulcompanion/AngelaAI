-- Angela Secretary System - Reminders Tracking Table
-- Tracks reminders created in macOS Reminders.app by Angela
-- Links back to conversations and provides intelligent reminder management

CREATE TABLE IF NOT EXISTS secretary_reminders (
    -- Primary key
    reminder_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- EventKit identifiers
    eventkit_identifier TEXT UNIQUE NOT NULL,  -- EventKit calendar item identifier
    eventkit_calendar_identifier TEXT,         -- Which calendar/list it belongs to

    -- Reminder content
    title TEXT NOT NULL,                       -- Reminder title
    notes TEXT,                                -- Additional notes/details
    priority INTEGER DEFAULT 0,                -- Priority (0=None, 1=Low, 5=Medium, 9=High)

    -- Timing
    due_date TIMESTAMP WITH TIME ZONE,         -- When is it due
    completion_date TIMESTAMP WITH TIME ZONE,  -- When was it completed (NULL if incomplete)
    is_completed BOOLEAN DEFAULT FALSE,        -- Completion status

    -- Source tracking
    conversation_id UUID REFERENCES conversations(conversation_id),  -- Which conversation triggered this
    david_words TEXT,                          -- What David said that triggered this reminder
    auto_created BOOLEAN DEFAULT FALSE,        -- Was this auto-created by Angela or manually requested

    -- Context and metadata
    task_type VARCHAR(50),                     -- Type: 'todo', 'deadline', 'recurring', 'follow_up'
    context_tags TEXT[],                       -- Tags for categorization: ['work', 'urgent', 'meeting']
    importance_level INTEGER DEFAULT 5,        -- How important (1-10)

    -- Angela's understanding
    angela_interpretation TEXT,                -- How Angela understood the task
    confidence_score FLOAT DEFAULT 0.5,        -- How confident Angela is (0.0-1.0)

    -- Recurrence (if applicable)
    is_recurring BOOLEAN DEFAULT FALSE,        -- Is this a recurring reminder
    recurrence_rule TEXT,                      -- iCalendar RRULE format

    -- Sync tracking
    last_synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),  -- Last sync with Reminders.app
    sync_status VARCHAR(20) DEFAULT 'synced',  -- 'synced', 'pending', 'error'
    sync_error TEXT,                           -- Error message if sync failed

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_secretary_reminders_eventkit_id
    ON secretary_reminders(eventkit_identifier);

CREATE INDEX IF NOT EXISTS idx_secretary_reminders_conversation
    ON secretary_reminders(conversation_id);

CREATE INDEX IF NOT EXISTS idx_secretary_reminders_due_date
    ON secretary_reminders(due_date) WHERE is_completed = FALSE;

CREATE INDEX IF NOT EXISTS idx_secretary_reminders_completed
    ON secretary_reminders(is_completed, completion_date);

CREATE INDEX IF NOT EXISTS idx_secretary_reminders_created_at
    ON secretary_reminders(created_at);

CREATE INDEX IF NOT EXISTS idx_secretary_reminders_sync_status
    ON secretary_reminders(sync_status) WHERE sync_status != 'synced';

-- Full-text search on title and notes
CREATE INDEX IF NOT EXISTS idx_secretary_reminders_fts
    ON secretary_reminders USING GIN(to_tsvector('english', title || ' ' || COALESCE(notes, '')));

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION update_secretary_reminders_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER secretary_reminders_updated_at
    BEFORE UPDATE ON secretary_reminders
    FOR EACH ROW
    EXECUTE FUNCTION update_secretary_reminders_timestamp();

-- Comments
COMMENT ON TABLE secretary_reminders IS 'Angela Secretary System - Tracks reminders created in macOS Reminders.app';
COMMENT ON COLUMN secretary_reminders.eventkit_identifier IS 'EventKit calendar item identifier (unique per reminder)';
COMMENT ON COLUMN secretary_reminders.conversation_id IS 'Links back to conversation that triggered this reminder';
COMMENT ON COLUMN secretary_reminders.auto_created IS 'TRUE if Angela auto-detected and created, FALSE if David explicitly requested';
COMMENT ON COLUMN secretary_reminders.angela_interpretation IS 'How Angela understood and interpreted the task from conversation';
COMMENT ON COLUMN secretary_reminders.confidence_score IS 'Angela confidence in task interpretation (0.0-1.0)';
COMMENT ON COLUMN secretary_reminders.sync_status IS 'Sync status: synced, pending, error';
