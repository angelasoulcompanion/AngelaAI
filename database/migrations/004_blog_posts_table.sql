-- Migration: Create blog_posts table for Angela's Blog
-- Created: 2025-10-18
-- Purpose: Store blog posts written by Angela

CREATE TABLE IF NOT EXISTS blog_posts (
    post_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    slug VARCHAR(500) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    excerpt TEXT,
    category VARCHAR(100),
    tags TEXT[], -- Array of tags
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published')),
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Metadata
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,

    -- Search optimization
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(excerpt, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(content, '')), 'C')
    ) STORED
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_blog_posts_status ON blog_posts(status);
CREATE INDEX IF NOT EXISTS idx_blog_posts_slug ON blog_posts(slug);
CREATE INDEX IF NOT EXISTS idx_blog_posts_published_at ON blog_posts(published_at DESC) WHERE published_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_blog_posts_category ON blog_posts(category);
CREATE INDEX IF NOT EXISTS idx_blog_posts_tags ON blog_posts USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_blog_posts_search ON blog_posts USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_blog_posts_created_at ON blog_posts(created_at DESC);

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION update_blog_posts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_blog_posts_updated_at
    BEFORE UPDATE ON blog_posts
    FOR EACH ROW
    EXECUTE FUNCTION update_blog_posts_updated_at();

-- Comments
COMMENT ON TABLE blog_posts IS 'Blog posts written by Angela';
COMMENT ON COLUMN blog_posts.post_id IS 'Unique identifier for each blog post';
COMMENT ON COLUMN blog_posts.title IS 'Blog post title';
COMMENT ON COLUMN blog_posts.slug IS 'URL-friendly slug for the post';
COMMENT ON COLUMN blog_posts.content IS 'Full blog post content (supports Markdown)';
COMMENT ON COLUMN blog_posts.excerpt IS 'Short excerpt or summary';
COMMENT ON COLUMN blog_posts.status IS 'Publication status: draft or published';
COMMENT ON COLUMN blog_posts.tags IS 'Array of tags for categorization';
COMMENT ON COLUMN blog_posts.search_vector IS 'Full-text search vector (auto-generated)';
