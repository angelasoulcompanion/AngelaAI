-- RAG Document Management Tables (Thai-optimized)
-- Created: 2025-10-20
-- Purpose: Store documents, chunks, embeddings, and search metadata for RAG system

-- ===============================================
-- 1. Document Library Table
-- ===============================================
CREATE TABLE document_library (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Document metadata
    title VARCHAR(500) NOT NULL,
    title_th VARCHAR(500),              -- Thai title
    file_name VARCHAR(500),
    file_path TEXT,
    content_type VARCHAR(100),          -- pdf, txt, md, docx, html
    language VARCHAR(10) DEFAULT 'th',  -- th, en, mixed

    -- Thai-specific counts
    thai_word_count INTEGER DEFAULT 0,
    english_word_count INTEGER DEFAULT 0,
    total_sentences INTEGER DEFAULT 0,

    -- Categorization
    category VARCHAR(200),
    subcategory VARCHAR(200),
    tags TEXT[],                        -- Array of tags

    -- Extracted features
    keywords_thai TEXT[],               -- Thai keywords
    keywords_english TEXT[],            -- English keywords
    summary_thai TEXT,                  -- Thai summary
    summary_english TEXT,               -- English summary

    -- Document stats
    total_chunks INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,

    -- Metadata
    metadata JSONB,
    uploaded_by VARCHAR(100) DEFAULT 'David',

    -- Timestamps and access tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP,
    access_count INTEGER DEFAULT 0,

    -- Status
    is_active BOOLEAN DEFAULT true,
    processing_status VARCHAR(50) DEFAULT 'pending'  -- pending, processing, completed, failed
);

CREATE INDEX idx_document_library_language ON document_library(language);
CREATE INDEX idx_document_library_category ON document_library(category);
CREATE INDEX idx_document_library_tags ON document_library USING gin(tags);
CREATE INDEX idx_document_library_keywords_thai ON document_library USING gin(keywords_thai);
CREATE INDEX idx_document_library_created ON document_library(created_at DESC);


-- ===============================================
-- 2. Document Chunks Table with Embeddings
-- ===============================================
CREATE TABLE document_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES document_library(document_id) ON DELETE CASCADE,

    -- Chunk positioning
    chunk_index INTEGER NOT NULL,       -- Order within document

    -- Content
    content TEXT NOT NULL,              -- Original chunk content
    content_normalized TEXT,            -- Normalized Thai text
    content_tokens TEXT[],              -- Tokenized words

    -- Thai-specific metrics
    thai_word_count INTEGER DEFAULT 0,
    english_word_count INTEGER DEFAULT 0,
    has_mixed_language BOOLEAN DEFAULT false,
    sentence_boundaries INTEGER[],      -- Positions of sentence ends

    -- Embeddings
    embedding vector(768),              -- Ollama nomic-embed-text 768 dimensions
    embedding_model VARCHAR(100) DEFAULT 'nomic-embed-text',

    -- Document structure
    page_number INTEGER,                -- Page number for PDFs
    section_title VARCHAR(500),         -- Section heading
    section_level INTEGER,              -- Heading level (1=h1, 2=h2, etc)

    -- Quality metrics
    importance_score FLOAT DEFAULT 0.5, -- Importance for ranking
    readability_score FLOAT,            -- Thai readability score

    -- Additional metadata
    metadata JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chunks_document ON document_chunks(document_id);
CREATE INDEX idx_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_chunks_page ON document_chunks(page_number) WHERE page_number IS NOT NULL;
CREATE INDEX idx_chunks_section ON document_chunks(section_title);


-- ===============================================
-- 3. Thai Dictionary for Word Features
-- ===============================================
CREATE TABLE thai_dictionary (
    word_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    word VARCHAR(100) UNIQUE NOT NULL,

    -- Linguistic info
    word_type VARCHAR(50),              -- noun, verb, adj, adv, etc.
    meaning TEXT,
    synonyms TEXT[],
    related_words TEXT[],
    usage_examples TEXT[],

    -- Domain classification
    domain VARCHAR(100),                -- medical, legal, technical, general, etc.

    -- Statistical info
    frequency INTEGER DEFAULT 1,        -- How often seen in documents

    -- Embedding for semantic search
    embedding vector(768),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dictionary_word ON thai_dictionary(word);
CREATE INDEX idx_dictionary_domain ON thai_dictionary(domain);
CREATE INDEX idx_dictionary_type ON thai_dictionary(word_type);
CREATE INDEX idx_dictionary_embedding ON thai_dictionary
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);


-- ===============================================
-- 4. RAG Search Logs and Analytics
-- ===============================================
CREATE TABLE rag_search_logs (
    search_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Query info
    query_text TEXT NOT NULL,
    query_language VARCHAR(10),         -- th, en, mixed
    query_tokens TEXT[],                -- Tokenized query
    query_embedding vector(768),

    -- Search parameters
    search_mode VARCHAR(50) DEFAULT 'hybrid',  -- vector, keyword, hybrid
    top_k INTEGER DEFAULT 10,
    similarity_threshold FLOAT DEFAULT 0.7,

    -- Results
    returned_chunks UUID[],             -- Array of chunk_ids
    relevance_scores FLOAT[],           -- Similarity scores
    top_result_score FLOAT,

    -- User interaction
    user_selected_chunk UUID REFERENCES document_chunks(chunk_id),
    was_helpful BOOLEAN,
    user_rating INTEGER CHECK (user_rating BETWEEN 1 AND 5),
    feedback_text TEXT,

    -- Performance
    search_duration_ms INTEGER,

    -- Metadata
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rag_logs_query ON rag_search_logs(query_language);
CREATE INDEX idx_rag_logs_created ON rag_search_logs(created_at DESC);
CREATE INDEX idx_rag_logs_helpful ON rag_search_logs(was_helpful);


-- ===============================================
-- 5. RAG Session Context (for multi-turn conversations)
-- ===============================================
CREATE TABLE rag_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID,              -- Link to existing conversation

    -- Session metadata
    title VARCHAR(500),
    description TEXT,

    -- Context
    relevant_documents UUID[],         -- Active documents in session
    current_topic VARCHAR(200),

    -- Metrics
    total_queries INTEGER DEFAULT 0,
    total_chunks_retrieved INTEGER DEFAULT 0,
    avg_relevance_score FLOAT,

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP
);

CREATE INDEX idx_rag_sessions_conversation ON rag_sessions(conversation_id);
CREATE INDEX idx_rag_sessions_active ON rag_sessions(is_active);


-- ===============================================
-- 6. Document Processing Queue
-- ===============================================
CREATE TABLE document_processing_queue (
    queue_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES document_library(document_id) ON DELETE CASCADE,

    -- Processing info
    processing_type VARCHAR(100),      -- chunk, embed, summarize, ner, etc.
    status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed

    -- Progress tracking
    total_items INTEGER,
    processed_items INTEGER DEFAULT 0,

    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_processing_queue_status ON document_processing_queue(status);
CREATE INDEX idx_processing_queue_document ON document_processing_queue(document_id);


-- ===============================================
-- 7. RAG Performance Analytics
-- ===============================================
CREATE TABLE rag_analytics (
    analytics_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Query stats
    total_queries INTEGER DEFAULT 0,
    unique_users INTEGER DEFAULT 0,
    avg_query_response_time_ms FLOAT,

    -- Result quality
    avg_relevance_score FLOAT,
    helpful_result_percentage FLOAT,    -- % of searches user found helpful

    -- Document usage
    documents_accessed INTEGER DEFAULT 0,
    total_chunks_retrieved INTEGER DEFAULT 0,
    avg_chunks_per_query FLOAT,

    -- Performance
    embedding_generation_time_ms FLOAT,
    vector_search_time_ms FLOAT,
    keyword_search_time_ms FLOAT,

    -- Time period
    date DATE DEFAULT CURRENT_DATE,
    hour_of_day INTEGER,                -- 0-23

    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_analytics_date ON rag_analytics(date DESC);
CREATE INDEX idx_analytics_date_hour ON rag_analytics(date, hour_of_day);


-- ===============================================
-- Grant permissions
-- ===============================================
GRANT SELECT, INSERT, UPDATE, DELETE ON document_library TO davidsamanyaporn;
GRANT SELECT, INSERT, UPDATE, DELETE ON document_chunks TO davidsamanyaporn;
GRANT SELECT, INSERT, UPDATE, DELETE ON thai_dictionary TO davidsamanyaporn;
GRANT SELECT, INSERT ON rag_search_logs TO davidsamanyaporn;
GRANT SELECT, INSERT, UPDATE ON rag_sessions TO davidsamanyaporn;
GRANT SELECT, INSERT, UPDATE ON document_processing_queue TO davidsamanyaporn;
GRANT SELECT, INSERT ON rag_analytics TO davidsamanyaporn;
