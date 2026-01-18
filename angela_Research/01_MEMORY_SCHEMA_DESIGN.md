# 1. DATABASE SCHEMA DESIGN: HUMAN MEMORY TIERS FOR AI

## Overview
This schema mirrors the human cognitive architecture with concentric memory rings, each optimized for different data characteristics and retention patterns.

---

## MEMORY TIER ARCHITECTURE

```
┌─────────────────────────────────────────────────────────┐
│                    GUT AGENT                             │
│         (Collective Intuition & Patterns)                │
└─────────────────────────────────────────────────────────┘
                           ↑
┌─────────────────────────────────────────────────────────┐
│              SHOCK MEMORIES                              │
│      (Critical Failures, Anomalies)                      │
└─────────────────────────────────────────────────────────┘
                           ↑
┌─────────────────────────────────────────────────────────┐
│          LONG-TERM MEMORY                                │
│    (Successful Patterns, Stable Knowledge)               │
└─────────────────────────────────────────────────────────┘
                           ↑
┌─────────────────────────────────────────────────────────┐
│       HABITS & PROCEDURAL MEMORY                         │
│    (Automated Patterns, Muscle Memory)                   │
└─────────────────────────────────────────────────────────┘
                           ↑
┌─────────────────────────────────────────────────────────┐
│          FRESH MEMORY (Buffer)                           │
│    (Temporary, Pre-Classification)                       │
└─────────────────────────────────────────────────────────┘
                           ↑
┌─────────────────────────────────────────────────────────┐
│          FOCUS AGENT (7±2 items)                         │
│        (Active Working Memory)                           │
└─────────────────────────────────────────────────────────┘
```

---

## DATABASE SCHEMA (PostgreSQL + Vector DB Hybrid)

### 1. FOCUS AGENT TABLE
**Purpose:** Immediate working memory (7±2 items max)
**Retention:** Microseconds to seconds
**Storage:** PostgreSQL (or in-memory cache like Redis)

```sql
CREATE TABLE focus_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL,
    content JSONB NOT NULL,  -- Current focus item
    attention_weight FLOAT DEFAULT 1.0,  -- Priority (0-1)
    created_at TIMESTAMP DEFAULT NOW(),
    duration_ms INTEGER DEFAULT 1000,  -- How long to hold
    
    CONSTRAINT max_7_items CHECK (
        (SELECT COUNT(*) FROM focus_memory WHERE agent_id = focus_memory.agent_id) <= 7
    )
);

CREATE INDEX idx_focus_agent ON focus_memory(agent_id, created_at DESC);
```

### 2. FRESH MEMORY TABLE
**Purpose:** Temporary buffer before classification
**Retention:** Milliseconds to minutes
**Storage:** PostgreSQL with TTL

```sql
CREATE TABLE fresh_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL,
    event_data JSONB NOT NULL,  -- Raw experience
    embedding VECTOR(1536),  -- OpenAI embedding
    relevance_score FLOAT DEFAULT 0.5,  -- Initial assessment (0-1)
    token_count INTEGER,  -- For economics tracking
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    status VARCHAR DEFAULT 'pending',  -- pending, routed, decayed
    
    CONSTRAINT fresh_ttl CHECK (
        EXTRACT(EPOCH FROM (NOW() - created_at)) <= 600  -- 10 min max
    )
);

CREATE INDEX idx_fresh_agent ON fresh_memory(agent_id, created_at DESC);
CREATE INDEX idx_fresh_embedding ON fresh_memory USING ivfflat (embedding vector_cosine_ops);
```

### 3. LONG-TERM MEMORY TABLE
**Purpose:** Successful, proven knowledge and patterns
**Retention:** Months to years
**Storage:** Vector DB (Weaviate/Pinecone) + PostgreSQL metadata

```sql
CREATE TABLE long_term_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL,
    memory_type VARCHAR,  -- 'experience', 'fact', 'pattern', 'skill'
    content TEXT,  -- Human-readable memory
    embedding VECTOR(1536),  -- Semantic representation
    success_score FLOAT,  -- Success rate (0-1)
    access_count INTEGER DEFAULT 1,  -- Frequency of use
    last_accessed TIMESTAMP DEFAULT NOW(),
    confidence FLOAT,  -- Certainty level (0-1)
    episodic_data JSONB,  -- Original context
    semantic_data JSONB,  -- Abstracted essence
    created_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW(),
    decay_rate FLOAT DEFAULT 0.01,  -- Daily decay percentage
    decay_half_life INTERVAL DEFAULT '180 days',  -- Time to 50% strength
    
    CONSTRAINT success_bounds CHECK (success_score >= 0 AND success_score <= 1),
    CONSTRAINT confidence_bounds CHECK (confidence >= 0 AND confidence <= 1)
);

-- Semantic search index
CREATE INDEX idx_ltm_embedding ON long_term_memory 
USING ivfflat (embedding vector_cosine_ops);

-- Frequency-based index for popular memories
CREATE INDEX idx_ltm_access ON long_term_memory(agent_id, access_count DESC);

-- Time-decay index
CREATE INDEX idx_ltm_decay ON long_term_memory(agent_id, last_accessed DESC);
```

### 4. PROCEDURAL MEMORY (HABITS) TABLE
**Purpose:** Automated, repeated successful patterns
**Retention:** Long-term, rarely decays
**Storage:** PostgreSQL + optional Vector DB

```sql
CREATE TABLE procedural_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL,
    procedure_name VARCHAR NOT NULL,
    procedure_steps JSONB NOT NULL,  -- Step-by-step execution
    embedding VECTOR(1536),
    execution_count INTEGER DEFAULT 1,
    success_rate FLOAT,  -- % of successful executions
    avg_execution_time_ms FLOAT,  -- Performance metric
    last_executed TIMESTAMP DEFAULT NOW(),
    automaticity FLOAT DEFAULT 0.1,  -- 0-1: how automatic (low = needs thought)
    created_at TIMESTAMP DEFAULT NOW(),
    confidence FLOAT,
    
    CONSTRAINT execution_bounds CHECK (success_rate >= 0 AND success_rate <= 1),
    CONSTRAINT automaticity_bounds CHECK (automaticity >= 0 AND automaticity <= 1)
);

CREATE INDEX idx_proc_agent ON procedural_memory(agent_id, automaticity DESC);
CREATE INDEX idx_proc_freq ON procedural_memory(execution_count DESC);
```

### 5. SHOCK MEMORY TABLE
**Purpose:** Critical anomalies, failures, security issues
**Retention:** Very long-term (permanent unless resolved)
**Storage:** PostgreSQL with audit trail

```sql
CREATE TABLE shock_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL,
    event_type VARCHAR,  -- 'security_breach', 'cascade_failure', 'data_corruption', etc.
    severity FLOAT,  -- 0-1: criticality rating
    description TEXT,
    context JSONB,  -- Full context of incident
    embedding VECTOR(1536),
    impact_assessment JSONB,  -- What could have gone wrong
    prevention_strategies JSONB,  -- How to prevent recurrence
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by_agent UUID,
    decay_resistance FLOAT DEFAULT 0.99,  -- Very resistant to decay
    access_count INTEGER DEFAULT 0,
    
    CONSTRAINT severity_bounds CHECK (severity >= 0 AND severity <= 1)
);

-- Critical alert index
CREATE INDEX idx_shock_severity ON shock_memory(agent_id, severity DESC);
CREATE INDEX idx_shock_unresolved ON shock_memory(agent_id) WHERE NOT resolved;
```

### 6. GUT AGENT TABLE (Collective Unconscious)
**Purpose:** Aggregated patterns and collective intuition
**Retention:** Evolves over time, rarely decays
**Storage:** Vector DB + PostgreSQL

```sql
CREATE TABLE gut_agent_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_id VARCHAR UNIQUE,  -- Identifier for pattern
    pattern_description TEXT,  -- What this pattern represents
    embedding VECTOR(1536),  -- Aggregated embedding
    
    -- Pattern characteristics
    frequency_score FLOAT,  -- How often encountered (0-1)
    success_correlation FLOAT,  -- Success likelihood (0-1)
    anomaly_flag BOOLEAN DEFAULT FALSE,  -- Is this unusual?
    confidence FLOAT,  -- How certain is this pattern (0-1)
    
    -- Aggregation info
    source_memories_count INTEGER,  -- # of memories contributing
    agents_contributed INTEGER,  -- # of different agents
    timestamp_range_days INTEGER,  -- Span of contributing memories
    
    -- Intuition qualities
    instinct_strength FLOAT,  -- 0-1: how strong the feeling
    gut_feeling_triggers JSONB,  -- Conditions that trigger intuition
    false_positive_rate FLOAT,  -- Reliability metric
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_verified TIMESTAMP,
    
    CONSTRAINT scores_valid CHECK (
        frequency_score >= 0 AND frequency_score <= 1 AND
        success_correlation >= 0 AND success_correlation <= 1 AND
        confidence >= 0 AND confidence <= 1
    )
);

CREATE INDEX idx_gut_pattern ON gut_agent_patterns(frequency_score DESC);
CREATE INDEX idx_gut_embedding ON gut_agent_patterns USING ivfflat (embedding vector_cosine_ops);
```

### 7. ANALYTICS METADATA TABLE
**Purpose:** Tracks routing decisions and memory management
**Retention:** Operational data
**Storage:** PostgreSQL

```sql
CREATE TABLE analytics_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL,
    event_id UUID,  -- Links to the memory event
    
    -- Routing decision
    source_tier VARCHAR,  -- Where memory came from
    target_tier VARCHAR,  -- Where it was routed
    routing_reason VARCHAR,  -- Why this decision
    confidence FLOAT,  -- Confidence in routing (0-1)
    
    -- Token economics
    tokens_used INTEGER,
    tokens_saved_by_compression FLOAT,
    compression_ratio FLOAT,  -- Original size / compressed size
    
    -- Performance metrics
    decision_latency_ms FLOAT,
    retrieval_latency_ms FLOAT,
    
    -- Success tracking
    was_successful BOOLEAN,
    outcome_assessment JSONB,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_tiers CHECK (
        source_tier IN ('focus', 'fresh', 'ltm', 'procedural', 'shock') AND
        target_tier IN ('focus', 'fresh', 'ltm', 'procedural', 'shock', 'decay')
    )
);

CREATE INDEX idx_analytics_agent ON analytics_metadata(agent_id, created_at DESC);
CREATE INDEX idx_routing_analysis ON analytics_metadata(target_tier, was_successful);
```

---

## VECTOR DATABASE SCHEMA (Weaviate Example)

```graphql
type LongTermMemory {
    content: String
    memoryType: String
    successScore: Float
    accessCount: Int
    embedding: [Float]
    metadata: {
        agentId: String
        createdAt: DateTime
        confidence: Float
        decayHalfLife: Int
    }
}

type ProcedureMemory {
    procedureName: String
    steps: String
    executionCount: Int
    successRate: Float
    automaticity: Float
    embedding: [Float]
}

type GutPattern {
    patternDescription: String
    frequencyScore: Float
    successCorrelation: Float
    instinctStrength: Float
    embedding: [Float]
    sourcesCount: Int
}
```

---

## KEY SCHEMA FEATURES

### 1. Embedding Storage
All memory tiers include `embedding VECTOR(1536)` for semantic similarity search using OpenAI's text-embedding-3-small model.

### 2. Decay Mechanisms
- **Time-based decay:** `last_accessed` + `decay_half_life`
- **Success-based selection:** Only high-success memories persist
- **Token economics:** Lower token cost = longer retention preference

### 3. Metadata Richness
Each memory stores:
- **Episodic:** Original context, timestamp, circumstances
- **Semantic:** Abstracted, generalized knowledge
- **Contextual:** Related memories and connections

### 4. Access Patterns
- **Frequency tracking:** `access_count` drives importance
- **Recency bias:** `last_accessed` for immediate relevance
- **Success correlation:** `success_score` for reliability

### 5. Constraints & Validation
- Focus memory limited to 7 items (George Miller's magic number)
- All scores constrained to 0-1 range
- Fresh memory TTL enforced at database level
- Shock memory resilience to decay

---

## RETRIEVAL PATTERNS

### Memory Lookup (Multi-Tier)
```
User Query
    ↓
[1] Focus Agent: Check active 7 items (fastest)
    ↓ Not found
[2] Fresh Memory: Check last 10 minutes (fast)
    ↓ Not found
[3] Vector Search (Weaviate): Semantic similarity search
    ├─→ Long-Term Memory (most likely)
    ├─→ Procedural Memory (how-to queries)
    └─→ Gut Patterns (intuitive queries)
    ↓ Not found
[4] Shock Memory: Crisis/anomaly lookup
    ↓
Return best match with confidence score
```

### Memory Consolidation
```
Fresh Memory (new experience)
    ↓
Analytics Agent evaluates:
├─→ Is it successful? YES → Long-Term Memory
├─→ Is it repeatable? YES → Procedural Memory
├─→ Is it critical failure? YES → Shock Memory
├─→ Is it common pattern? YES → Gut Agent
└─→ Is it irrelevant? YES → Decay/Delete
```

---

## USAGE EXAMPLE

### Inserting a Memory
```python
# New experience comes in
experience = {
    "action": "deployed_to_production",
    "result": "success",
    "duration_ms": 5000,
    "confidence": 0.95
}

# 1. Land in fresh_memory
fresh_id = insert_fresh_memory(
    agent_id=agent_id,
    event_data=experience,
    embedding=embed(str(experience))
)

# 2. Analytics agent decides routing
routing = decide_routing(
    success_score=0.95,
    is_repeated=False,
    is_critical_failure=False,
    pattern_frequency="rare"
)

# 3. Route to appropriate tier
if routing == "LONG_TERM":
    move_to_long_term_memory(
        fresh_id=fresh_id,
        success_score=0.95,
        confidence=0.95
    )
elif routing == "PROCEDURAL":
    move_to_procedural_memory(fresh_id=fresh_id)
```

---

## PERFORMANCE OPTIMIZATION

### Indexes for Fast Lookup
- Vector similarity search: IVFFLAT on embeddings
- Temporal queries: B-tree on timestamps
- Frequency queries: B-tree on access_count
- Decay calculation: Partial indexes on unresolved/recent

### Caching Strategy
- Focus memory: In-memory cache (Redis)
- Recent access patterns: LRU cache
- Vector embeddings: Pre-computed, cached after first use

### Query Optimization
- Hybrid queries: Vector + metadata filter
- Batch retrievals: Retrieve multiple similar memories
- Materialized views: Pre-computed decay scores

---

## MONITORING & METRICS

Track these to understand system health:

```sql
-- Memory utilization by tier
SELECT memory_tier, COUNT(*), AVG(embedding_size_bytes)
FROM memory_stats
GROUP BY memory_tier;

-- Decay effectiveness
SELECT memory_tier, 
       COUNT(*) as total,
       COUNT(CASE WHEN accessed_in_last_30_days THEN 1 END) as active
FROM long_term_memory
GROUP BY memory_tier;

-- Routing accuracy
SELECT routing_reason, 
       COUNT(*) as total,
       SUM(CASE WHEN was_successful THEN 1 ELSE 0 END) as successes,
       100.0 * SUM(CASE WHEN was_successful THEN 1 ELSE 0 END) / COUNT(*) as success_rate
FROM analytics_metadata
GROUP BY routing_reason;

-- Token efficiency
SELECT 
    AVG(tokens_used) as avg_tokens,
    AVG(compression_ratio) as avg_compression,
    SUM(tokens_saved_by_compression) as total_saved
FROM analytics_metadata;
```

---

## NEXT STEPS

This schema provides the foundation for:
1. ✅ Multi-tier memory storage
2. ✅ Semantic similarity search
3. ✅ Decay and forgetting
4. ✅ Collective consciousness
5. ⏭️ Analytics agent routing (see file 02)
