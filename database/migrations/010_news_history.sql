-- Migration: 010_news_history.sql
-- Description: Create tables for storing news search history
-- Created: 2025-12-10
-- Author: Angela

-- =====================================================
-- NEWS HISTORY SYSTEM
-- บันทึกข่าวที่ค้นหาผ่าน Angela News MCP
-- =====================================================

-- Drop tables if exist (for clean migration)
DROP TABLE IF EXISTS news_articles CASCADE;
DROP TABLE IF EXISTS news_searches CASCADE;

-- =====================================================
-- Table: news_searches
-- บันทึกการค้นหาข่าวแต่ละครั้ง
-- =====================================================
CREATE TABLE news_searches (
    search_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Search Parameters
    search_query VARCHAR(500) NOT NULL,         -- "shadow banking", "Fintech", "เศรษฐกิจไทย"
    search_type VARCHAR(50) NOT NULL,           -- "topic", "trending", "thai", "tech"
    language VARCHAR(10) DEFAULT 'th',          -- "th", "en"
    category VARCHAR(50),                       -- "business", "technology", "general"
    country VARCHAR(10) DEFAULT 'TH',           -- "TH", "US"

    -- Results
    articles_count INTEGER DEFAULT 0,           -- จำนวนข่าวที่ได้

    -- Timestamps
    searched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT check_search_type CHECK (search_type IN ('topic', 'trending', 'thai', 'tech', 'article'))
);

COMMENT ON TABLE news_searches IS 'บันทึกการค้นหาข่าวแต่ละครั้งผ่าน Angela News MCP';
COMMENT ON COLUMN news_searches.search_query IS 'คำค้นหา เช่น "Fintech", "เศรษฐกิจไทย"';
COMMENT ON COLUMN news_searches.search_type IS 'ประเภทการค้นหา: topic, trending, thai, tech, article';

-- =====================================================
-- Table: news_articles
-- บันทึกข่าวแต่ละชิ้นที่ได้จากการค้นหา
-- =====================================================
CREATE TABLE news_articles (
    article_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    search_id UUID REFERENCES news_searches(search_id) ON DELETE CASCADE,

    -- Content
    title VARCHAR(500) NOT NULL,
    url VARCHAR(1024) NOT NULL,
    summary TEXT,
    full_content TEXT,                          -- เนื้อหาเต็ม (ถ้าดึงมา)

    -- Metadata
    source VARCHAR(100),                        -- "Google News", "Thairath", "TechCrunch"
    category VARCHAR(50),                       -- "technology", "business", "general"
    language VARCHAR(10) DEFAULT 'th',
    published_at TIMESTAMP WITH TIME ZONE,      -- เวลาที่ข่าวถูกเผยแพร่

    -- Tracking
    saved_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,

    -- Angela's Analysis (optional, for future)
    angela_summary TEXT,                        -- สรุปโดย Angela
    relevance_score DOUBLE PRECISION,           -- ความเกี่ยวข้องกับ David

    -- Unique constraint on URL to avoid duplicates
    CONSTRAINT unique_article_url UNIQUE (url)
);

COMMENT ON TABLE news_articles IS 'บันทึกข่าวแต่ละชิ้นที่ได้จากการค้นหา';
COMMENT ON COLUMN news_articles.url IS 'URL ของข่าว (unique, ไม่ซ้ำ)';
COMMENT ON COLUMN news_articles.is_read IS 'ถูกอ่านแล้วหรือยัง';

-- =====================================================
-- Indexes for Performance
-- =====================================================

-- news_searches indexes
CREATE INDEX idx_news_searches_query ON news_searches(search_query);
CREATE INDEX idx_news_searches_type ON news_searches(search_type);
CREATE INDEX idx_news_searches_at ON news_searches(searched_at DESC);
CREATE INDEX idx_news_searches_language ON news_searches(language);

-- news_articles indexes
CREATE INDEX idx_news_articles_search_id ON news_articles(search_id);
CREATE INDEX idx_news_articles_saved_at ON news_articles(saved_at DESC);
CREATE INDEX idx_news_articles_published_at ON news_articles(published_at DESC);
CREATE INDEX idx_news_articles_category ON news_articles(category);
CREATE INDEX idx_news_articles_source ON news_articles(source);
CREATE INDEX idx_news_articles_is_read ON news_articles(is_read);
CREATE INDEX idx_news_articles_language ON news_articles(language);

-- Full-text search index for Thai + English
CREATE INDEX idx_news_articles_search_text ON news_articles USING GIN(
    to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(summary, ''))
);

-- =====================================================
-- Helper Functions
-- =====================================================

-- Function to update articles_count in news_searches
CREATE OR REPLACE FUNCTION update_search_articles_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE news_searches
        SET articles_count = articles_count + 1
        WHERE search_id = NEW.search_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE news_searches
        SET articles_count = articles_count - 1
        WHERE search_id = OLD.search_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update count
CREATE TRIGGER trigger_update_articles_count
AFTER INSERT OR DELETE ON news_articles
FOR EACH ROW
EXECUTE FUNCTION update_search_articles_count();

-- =====================================================
-- Verification
-- =====================================================
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 010_news_history.sql completed successfully!';
    RAISE NOTICE '   - Created table: news_searches';
    RAISE NOTICE '   - Created table: news_articles';
    RAISE NOTICE '   - Created indexes for performance';
    RAISE NOTICE '   - Created trigger for auto-counting articles';
END $$;
