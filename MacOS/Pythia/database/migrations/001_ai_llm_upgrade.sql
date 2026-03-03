-- Pythia Migration 001: AI LLM Upgrade
-- Adds LLM-related columns and tables for hybrid AI services

-- Sentiment: LLM narrative + news scoring
ALTER TABLE ai_sentiment_results ADD COLUMN IF NOT EXISTS llm_narrative TEXT;
ALTER TABLE ai_sentiment_results ADD COLUMN IF NOT EXISTS news_headlines JSONB;
ALTER TABLE ai_sentiment_results ADD COLUMN IF NOT EXISTS technical_score DOUBLE PRECISION;
ALTER TABLE ai_sentiment_results ADD COLUMN IF NOT EXISTS news_score DOUBLE PRECISION;
ALTER TABLE ai_sentiment_results ADD COLUMN IF NOT EXISTS combined_score DOUBLE PRECISION;
ALTER TABLE ai_sentiment_results ADD COLUMN IF NOT EXISTS llm_provider VARCHAR(20);

-- Forecasts: LLM interpretation + risk factors
ALTER TABLE ai_forecasts ADD COLUMN IF NOT EXISTS llm_interpretation TEXT;
ALTER TABLE ai_forecasts ADD COLUMN IF NOT EXISTS risk_factors JSONB;
ALTER TABLE ai_forecasts ADD COLUMN IF NOT EXISTS llm_provider VARCHAR(20);

-- Conversations: enhanced for multi-turn chat
ALTER TABLE ai_conversations ADD COLUMN IF NOT EXISTS session_id UUID;
ALTER TABLE ai_conversations ADD COLUMN IF NOT EXISTS llm_provider VARCHAR(20);
ALTER TABLE ai_conversations ADD COLUMN IF NOT EXISTS llm_model VARCHAR(50);
ALTER TABLE ai_conversations ADD COLUMN IF NOT EXISTS tokens_used INTEGER DEFAULT 0;

-- LLM usage tracking
CREATE TABLE IF NOT EXISTS llm_usage_log (
    usage_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider VARCHAR(20) NOT NULL,
    model VARCHAR(50) NOT NULL,
    feature VARCHAR(50) NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    cost_estimate DOUBLE PRECISION DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Research chunks for future chunked RAG
CREATE TABLE IF NOT EXISTS research_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES research_documents(document_id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_research_chunks_document ON research_chunks(document_id);
