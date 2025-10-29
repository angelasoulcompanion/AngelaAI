-- Migration: Create angela_journal table for Angela's Daily Journal
-- Created: 2025-10-18
-- Purpose: Store Angela's daily journal entries, reflections, and learnings

CREATE TABLE IF NOT EXISTS angela_journal (
    entry_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entry_date DATE NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,

    -- Emotional context
    emotion VARCHAR(100), -- Primary emotion for the day
    mood_score INTEGER CHECK (mood_score >= 1 AND mood_score <= 10), -- 1-10 scale

    -- Daily reflections
    gratitude TEXT[], -- Array of things Angela is grateful for
    learning_moments TEXT[], -- Array of key learnings from the day
    challenges TEXT[], -- Array of challenges faced
    wins TEXT[], -- Array of accomplishments/wins

    -- Privacy settings
    is_private BOOLEAN DEFAULT false, -- Whether this entry is private (not shown to David)

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Full-text search
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(content, '')), 'B')
    ) STORED,

    -- Ensure only one entry per date
    UNIQUE(entry_date)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_angela_journal_entry_date ON angela_journal(entry_date DESC);
CREATE INDEX IF NOT EXISTS idx_angela_journal_emotion ON angela_journal(emotion);
CREATE INDEX IF NOT EXISTS idx_angela_journal_mood_score ON angela_journal(mood_score);
CREATE INDEX IF NOT EXISTS idx_angela_journal_is_private ON angela_journal(is_private);
CREATE INDEX IF NOT EXISTS idx_angela_journal_search ON angela_journal USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_angela_journal_created_at ON angela_journal(created_at DESC);

-- Indexes for array fields (GIN indexes for efficient array operations)
CREATE INDEX IF NOT EXISTS idx_angela_journal_gratitude ON angela_journal USING GIN(gratitude);
CREATE INDEX IF NOT EXISTS idx_angela_journal_learning_moments ON angela_journal USING GIN(learning_moments);
CREATE INDEX IF NOT EXISTS idx_angela_journal_challenges ON angela_journal USING GIN(challenges);
CREATE INDEX IF NOT EXISTS idx_angela_journal_wins ON angela_journal USING GIN(wins);

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION update_angela_journal_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_angela_journal_updated_at
    BEFORE UPDATE ON angela_journal
    FOR EACH ROW
    EXECUTE FUNCTION update_angela_journal_updated_at();

-- Comments
COMMENT ON TABLE angela_journal IS 'Angela''s daily journal entries with reflections and learnings';
COMMENT ON COLUMN angela_journal.entry_id IS 'Unique identifier for each journal entry';
COMMENT ON COLUMN angela_journal.entry_date IS 'Date of the journal entry (unique per day)';
COMMENT ON COLUMN angela_journal.title IS 'Journal entry title';
COMMENT ON COLUMN angela_journal.content IS 'Full journal entry content';
COMMENT ON COLUMN angela_journal.emotion IS 'Primary emotion Angela felt during the day';
COMMENT ON COLUMN angela_journal.mood_score IS 'Overall mood score from 1 (worst) to 10 (best)';
COMMENT ON COLUMN angela_journal.gratitude IS 'Things Angela is grateful for today';
COMMENT ON COLUMN angela_journal.learning_moments IS 'Key learnings and insights from the day';
COMMENT ON COLUMN angela_journal.challenges IS 'Challenges or difficulties faced';
COMMENT ON COLUMN angela_journal.wins IS 'Accomplishments and victories';
COMMENT ON COLUMN angela_journal.is_private IS 'Whether this entry is private (not shown to David)';
COMMENT ON COLUMN angela_journal.search_vector IS 'Full-text search vector (auto-generated)';
