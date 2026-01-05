-- Migration: 011_executive_news.sql
-- Executive News Summary - Angela's personalized news briefings for David
-- Created: 2026-01-05

-- =====================================================
-- Table: executive_news_summaries
-- Daily summary header - one per day
-- =====================================================
CREATE TABLE IF NOT EXISTS executive_news_summaries (
    summary_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    summary_date DATE NOT NULL UNIQUE,  -- One summary per day

    -- Angela's Summary
    overall_summary TEXT NOT NULL,       -- Overall summary for the day
    angela_mood VARCHAR(50),             -- Angela's mood: optimistic, concerned, excited, neutral

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for date lookup
CREATE INDEX IF NOT EXISTS idx_executive_news_date ON executive_news_summaries(summary_date DESC);

-- =====================================================
-- Table: executive_news_categories
-- Categories within each daily summary (MCP-based)
-- =====================================================
CREATE TABLE IF NOT EXISTS executive_news_categories (
    category_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    summary_id UUID NOT NULL REFERENCES executive_news_summaries(summary_id) ON DELETE CASCADE,

    -- Category Info (MCP-based)
    category_name VARCHAR(100) NOT NULL,  -- "Tech News", "AI & LLM", "Thai Finance", etc.
    category_type VARCHAR(50) NOT NULL,   -- tech, topic, thai, trending
    category_icon VARCHAR(50),            -- SF Symbol name (cpu.fill, brain, flag.fill, etc.)
    category_color VARCHAR(20),           -- Hex color (#10B981, #3B82F6, etc.)

    -- Angela's Analysis
    summary_text TEXT NOT NULL,           -- Summary of news in this category
    angela_opinion TEXT NOT NULL,         -- Angela's opinion and thoughts
    importance_level INTEGER DEFAULT 5 CHECK (importance_level >= 1 AND importance_level <= 10),

    -- Display Order
    display_order INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_executive_categories_summary ON executive_news_categories(summary_id);
CREATE INDEX IF NOT EXISTS idx_executive_categories_type ON executive_news_categories(category_type);

-- =====================================================
-- Table: executive_news_sources
-- Source articles referenced in each category
-- =====================================================
CREATE TABLE IF NOT EXISTS executive_news_sources (
    source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID NOT NULL REFERENCES executive_news_categories(category_id) ON DELETE CASCADE,

    -- Article Reference
    title VARCHAR(500) NOT NULL,
    url VARCHAR(1024) NOT NULL,
    source_name VARCHAR(100),             -- "TechCrunch", "Thairath", "Hacker News", etc.
    published_at TIMESTAMP WITH TIME ZONE,

    -- Angela's Note
    angela_note TEXT,                     -- Brief note from Angela about this article

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_executive_sources_category ON executive_news_sources(category_id);
CREATE INDEX IF NOT EXISTS idx_executive_sources_url ON executive_news_sources(url);

-- =====================================================
-- Trigger: Auto-update updated_at
-- =====================================================
CREATE OR REPLACE FUNCTION update_executive_news_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_executive_news_timestamp ON executive_news_summaries;
CREATE TRIGGER trigger_update_executive_news_timestamp
    BEFORE UPDATE ON executive_news_summaries
    FOR EACH ROW
    EXECUTE FUNCTION update_executive_news_timestamp();

-- =====================================================
-- Comments
-- =====================================================
COMMENT ON TABLE executive_news_summaries IS 'Daily executive news summaries written by Angela for David';
COMMENT ON TABLE executive_news_categories IS 'News categories within each daily summary (MCP-based grouping)';
COMMENT ON TABLE executive_news_sources IS 'Source articles referenced in each category summary';

COMMENT ON COLUMN executive_news_summaries.angela_mood IS 'Angela mood: optimistic, concerned, excited, neutral, thoughtful';
COMMENT ON COLUMN executive_news_categories.category_type IS 'MCP type: tech, topic, thai, trending';
COMMENT ON COLUMN executive_news_categories.importance_level IS '1-10 scale of importance for David';
