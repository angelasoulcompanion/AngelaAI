-- Angela Mobile App - Local SQLite Database Schema
-- Created: 2025-11-07
-- Purpose: Store Thai dictionary for spell checking on-device

-- Thai Dictionary - Common Thai words that are valid
CREATE TABLE IF NOT EXISTS thai_words (
    word_id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL UNIQUE,
    word_type TEXT,          -- 'noun', 'verb', 'adjective', 'particle', etc.
    category TEXT,           -- 'food', 'emotion', 'polite', 'common', etc.
    frequency INTEGER DEFAULT 0,  -- How often this word appears
    is_common BOOLEAN DEFAULT 0,  -- Is this a frequently used word?
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Spelling Corrections - Map incorrect → correct
CREATE TABLE IF NOT EXISTS spelling_corrections (
    correction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    incorrect_word TEXT NOT NULL,
    correct_word TEXT NOT NULL,
    correction_count INTEGER DEFAULT 0,  -- Track usage
    confidence REAL DEFAULT 1.0,         -- 0.0 - 1.0
    source TEXT DEFAULT 'manual',        -- 'manual', 'learned', 'imported'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_used_at DATETIME,
    UNIQUE(incorrect_word, correct_word)
);

-- Correction History - Track what was corrected (for learning)
CREATE TABLE IF NOT EXISTS correction_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_text TEXT NOT NULL,
    corrected_text TEXT NOT NULL,
    correction_type TEXT,    -- 'direct', 'edit_distance', 'manual'
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_thai_words_word ON thai_words(word);
CREATE INDEX IF NOT EXISTS idx_thai_words_category ON thai_words(category);
CREATE INDEX IF NOT EXISTS idx_spelling_corrections_incorrect ON spelling_corrections(incorrect_word);
CREATE INDEX IF NOT EXISTS idx_correction_history_applied_at ON correction_history(applied_at);

-- Database metadata
CREATE TABLE IF NOT EXISTS db_metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insert metadata
INSERT OR REPLACE INTO db_metadata (key, value) VALUES ('version', '1.0.0');
INSERT OR REPLACE INTO db_metadata (key, value) VALUES ('created_at', datetime('now'));
INSERT OR REPLACE INTO db_metadata (key, value) VALUES ('last_updated', datetime('now'));
