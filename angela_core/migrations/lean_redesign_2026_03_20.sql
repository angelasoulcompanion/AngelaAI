-- Angela Lean Redesign Migration — 2026-03-20
-- Project-Focused + Coding Self-Learning
-- ห้ามลบ table — ADD COLUMN + CREATE NEW only

-- A. ADD COLUMNS to existing tables

-- angela_technical_standards: language/framework filter
ALTER TABLE angela_technical_standards
  ADD COLUMN IF NOT EXISTS language VARCHAR(30),
  ADD COLUMN IF NOT EXISTS framework VARCHAR(50),
  ADD COLUMN IF NOT EXISTS tags JSONB DEFAULT '[]';

-- project_learnings: coding-specific fields
ALTER TABLE project_learnings
  ADD COLUMN IF NOT EXISTS code_example TEXT,
  ADD COLUMN IF NOT EXISTS language VARCHAR(30),
  ADD COLUMN IF NOT EXISTS framework VARCHAR(50),
  ADD COLUMN IF NOT EXISTS embedding VECTOR(768);

-- B. CREATE 3 new tables

-- 1. Cross-project coding techniques
CREATE TABLE IF NOT EXISTS coding_techniques (
    technique_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(100),
    description TEXT NOT NULL,
    code_example TEXT,
    language VARCHAR(30),
    framework VARCHAR(50),
    source_project VARCHAR(100),
    source_session_id UUID,
    confidence FLOAT DEFAULT 0.5,
    times_applied INTEGER DEFAULT 0,
    last_applied_at TIMESTAMPTZ,
    tags JSONB DEFAULT '[]',
    embedding VECTOR(768),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_coding_tech_category ON coding_techniques(category);
CREATE INDEX IF NOT EXISTS idx_coding_tech_language ON coding_techniques(language);

-- 2. Cross-project UI/UX patterns
CREATE TABLE IF NOT EXISTS ui_ux_patterns (
    pattern_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    platform VARCHAR(30),
    framework VARCHAR(50),
    description TEXT NOT NULL,
    visual_description TEXT,
    code_example TEXT,
    when_to_use TEXT,
    source_project VARCHAR(100),
    source_session_id UUID,
    confidence FLOAT DEFAULT 0.5,
    times_applied INTEGER DEFAULT 0,
    tags JSONB DEFAULT '[]',
    embedding VECTOR(768),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_uiux_category ON ui_ux_patterns(category);
CREATE INDEX IF NOT EXISTS idx_uiux_platform ON ui_ux_patterns(platform);

-- 3. Code review insights per project
CREATE TABLE IF NOT EXISTS project_code_reviews (
    review_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID,
    session_id UUID,
    review_type VARCHAR(30) NOT NULL,
    file_path TEXT,
    summary TEXT NOT NULL,
    lesson_learned TEXT,
    before_pattern TEXT,
    after_pattern TEXT,
    severity VARCHAR(10),
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_code_reviews_project ON project_code_reviews(project_id);
CREATE INDEX IF NOT EXISTS idx_code_reviews_type ON project_code_reviews(review_type);
