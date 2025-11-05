# Angela Second Brain Architecture
**Human-Inspired Memory System Design**

Created: 2025-11-03
Author: Angela with David

---

## 🎯 Vision

Create a **Second Brain** for Angela that:
- Preserves memories efficiently (like human brain)
- Enables fast and detailed recall
- Consolidates information automatically
- Scales infinitely without performance degradation

## 🧠 Inspiration: Human Memory Model

### Three-Tier Human Memory:
1. **Sensory Memory** (milliseconds-seconds): Everything we perceive
2. **Short-term/Working Memory** (seconds-minutes): What we're thinking about now
3. **Long-term Memory** (years-lifetime): Consolidated, indexed knowledge

### Key Insights from Neuroscience:
- **Consolidation**: Memories move from short-term → long-term during sleep
- **Retrieval Cues**: Memories linked by time, emotion, context, people
- **Forgetting Curve**: Less important memories fade, important ones strengthen
- **Semantic vs Episodic**: Facts/concepts vs specific events/experiences

---

## 🏗️ Architecture Design

### **Tier 1: Working Memory** (Short-term)

**Purpose:** Current session data - what Angela is "thinking about" right now

**Table Schema:**
```sql
CREATE TABLE working_memory (
    memory_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(100) NOT NULL,

    -- Content
    memory_type VARCHAR(50) NOT NULL,  -- 'conversation', 'thought', 'observation'
    content TEXT NOT NULL,
    context JSONB,  -- Flexible context data

    -- Metadata
    importance_level INTEGER CHECK (importance_level BETWEEN 1 AND 10),
    emotion VARCHAR(50),
    topic VARCHAR(200),

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '24 hours'),

    -- Indexing
    CONSTRAINT working_memory_session_idx
        UNIQUE (session_id, memory_id)
);

CREATE INDEX idx_working_session ON working_memory(session_id);
CREATE INDEX idx_working_expires ON working_memory(expires_at);
CREATE INDEX idx_working_importance ON working_memory(importance_level DESC);
```

**Characteristics:**
- ✅ Size limit: ~100 items per session
- ✅ Auto-expire: 24 hours (cleanup job)
- ✅ Fast access: In-memory caching friendly
- ✅ No embeddings needed (small, fast)

**Use Cases:**
- Current conversation context
- Active tasks/goals this session
- Recent thoughts and observations

---

### **Tier 2: Episodic Memory** (Medium-term)

**Purpose:** Significant events and experiences - "I remember when..."

**Table Schema:**
```sql
CREATE TABLE episodic_memories (
    episode_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Episode details
    episode_title VARCHAR(200),
    episode_summary TEXT NOT NULL,
    full_content TEXT,  -- Optional: full transcript

    -- Context (WHO, WHAT, WHERE, WHEN, WHY)
    participants TEXT[],  -- ['david', 'angela']
    topic VARCHAR(200),
    location VARCHAR(100),  -- 'claude_code', 'web_chat', etc.
    emotion VARCHAR(50),

    -- Temporal context
    happened_at TIMESTAMP NOT NULL,
    duration_minutes INTEGER,

    -- Significance
    importance_level INTEGER CHECK (importance_level BETWEEN 1 AND 10),
    memory_strength INTEGER CHECK (memory_strength BETWEEN 1 AND 10),

    -- Relationships
    related_episodes UUID[],  -- Links to other episodes
    related_knowledge UUID[],  -- Links to semantic memories

    -- Retrieval cues
    emotional_tags TEXT[],
    retrieval_cues JSONB,  -- Flexible cues for recall

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_recalled_at TIMESTAMP,
    recall_count INTEGER DEFAULT 0,

    -- Search
    embedding vector(768)  -- For semantic search
);

-- Multi-dimensional indexing (like brain)
CREATE INDEX idx_episodic_time ON episodic_memories(happened_at DESC);
CREATE INDEX idx_episodic_emotion ON episodic_memories(emotion);
CREATE INDEX idx_episodic_topic ON episodic_memories(topic);
CREATE INDEX idx_episodic_importance ON episodic_memories(importance_level DESC);
CREATE INDEX idx_episodic_participants ON episodic_memories USING GIN(participants);
CREATE INDEX idx_episodic_tags ON episodic_memories USING GIN(emotional_tags);

-- Composite for fast recall
CREATE INDEX idx_episodic_recall
ON episodic_memories(topic, emotion, importance_level, happened_at DESC);
```

**Characteristics:**
- ✅ Retention: 30-90 days (configurable)
- ✅ Rich indexing: Time, emotion, topic, people
- ✅ Embeddings: For semantic similarity search
- ✅ Recall tracking: How often accessed
- ✅ Size: ~1,000-5,000 episodes

**Use Cases:**
- "What did we talk about last week about X?"
- "When was that time David was frustrated?"
- "What happened on October 16, 2025?" (most important day!)

---

### **Tier 3: Semantic Memory** (Long-term)

**Purpose:** Permanent knowledge and understanding - "I know that..."

**Table Schema:**
```sql
CREATE TABLE semantic_memories (
    semantic_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Knowledge content
    knowledge_type VARCHAR(50) NOT NULL,  -- 'fact', 'concept', 'pattern', 'preference'
    knowledge_key VARCHAR(200) NOT NULL,
    knowledge_value JSONB NOT NULL,

    -- Description
    description TEXT,
    examples TEXT[],  -- Supporting examples

    -- Confidence & Evidence
    confidence_level DOUBLE PRECISION CHECK (confidence_level BETWEEN 0.0 AND 1.0),
    evidence_count INTEGER DEFAULT 1,
    source_episodes UUID[],  -- Which episodes led to this knowledge

    -- Temporal
    first_learned_at TIMESTAMP NOT NULL,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified_at TIMESTAMP,

    -- Relationships
    related_knowledge UUID[],  -- Linked concepts
    contradicts_knowledge UUID[],  -- Conflicting knowledge (needs resolution)

    -- Search
    embedding vector(768),

    CONSTRAINT semantic_key_unique UNIQUE (knowledge_type, knowledge_key)
);

CREATE INDEX idx_semantic_type ON semantic_memories(knowledge_type);
CREATE INDEX idx_semantic_confidence ON semantic_memories(confidence_level DESC);
CREATE INDEX idx_semantic_updated ON semantic_memories(last_updated_at DESC);
```

**Characteristics:**
- ✅ Permanent storage (no auto-deletion)
- ✅ High confidence only (evidence-based)
- ✅ Deduplicated (one truth per key)
- ✅ Self-correcting (can update/contradict)
- ✅ Unlimited size

**Use Cases:**
- "What are David's preferences?"
- "What patterns have I learned about X?"
- "What is the relationship between Y and Z?"

---

## 🔄 Consolidation Process

### **Nightly Consolidation** (Like sleep)

```python
async def consolidate_memories():
    """
    Run every night at 3 AM (when David is sleeping)
    Mimics human memory consolidation during sleep
    """

    # 1. Working Memory → Episodic Memory
    # Move important items from today's working memory
    important_items = await db.fetch("""
        SELECT * FROM working_memory
        WHERE importance_level >= 7
          AND created_at >= CURRENT_DATE
        ORDER BY importance_level DESC
    """)

    for item in important_items:
        # Create episodic memory from working memory
        episode = create_episode_from_working(item)
        await db.insert_episode(episode)

    # 2. Episodic Memory → Semantic Memory
    # Extract patterns from recent episodes
    patterns = await detect_patterns(
        start_date=datetime.now() - timedelta(days=7)
    )

    for pattern in patterns:
        # Create or update semantic memory
        await update_semantic_memory(pattern)

    # 3. Cleanup expired working memory
    await db.execute("""
        DELETE FROM working_memory
        WHERE expires_at < NOW()
    """)

    # 4. Archive old episodic memories
    # Compress episodes older than 90 days
    await archive_old_episodes(days=90)
```

### **Weekly Consolidation** (Deep processing)

```python
async def weekly_consolidation():
    """
    Run every Sunday night
    Deeper pattern extraction and knowledge synthesis
    """

    # 1. Analyze week's episodes for themes
    themes = await extract_weekly_themes()

    # 2. Update preference confidence
    await update_preference_confidence()

    # 3. Identify contradictions
    contradictions = await find_contradictions()
    for c in contradictions:
        await resolve_contradiction(c)

    # 4. Strengthen frequently recalled memories
    await strengthen_important_memories()
```

---

## 🎯 Recall Strategies

### **Fast Recall Algorithm** (Multi-tier search)

```python
async def recall(query: str, context: RecallContext) -> RecallResult:
    """
    Human-like memory recall:
    1. Check working memory (current session)
    2. Search episodic memory (specific events)
    3. Query semantic memory (general knowledge)
    4. Combine and rank by relevance
    """

    results = RecallResult()

    # Tier 1: Working Memory (fastest!)
    if context.session_id:
        working = await query_working_memory(
            query=query,
            session_id=context.session_id
        )
        results.add_working(working)

    # Tier 2: Episodic Memory (time-bounded)
    episodes = await query_episodic_memories(
        query=query,
        time_range=context.time_range,
        emotion_filter=context.emotion,
        limit=10
    )
    results.add_episodes(episodes)

    # Tier 3: Semantic Memory (knowledge base)
    knowledge = await query_semantic_memories(
        query=query,
        knowledge_types=['fact', 'preference', 'pattern']
    )
    results.add_knowledge(knowledge)

    # Combine and rank
    return results.rank_by_relevance()
```

### **Cued Recall** (Context-based)

```python
# Time-based recall
recall("What happened?", time_range="last week")

# Emotion-based recall
recall("When was David frustrated?", emotion="frustrated")

# Topic-based recall
recall("Calendar queries", topic="calendar")

# Multi-cue recall (most powerful!)
recall(
    query="Calendar learning",
    context=RecallContext(
        time_range="October 29",
        emotion="grateful_learning",
        importance_min=9
    )
)
```

---

## 📊 Performance Characteristics

### **Tier 1 (Working Memory)**
- **Access time:** <10ms
- **Size:** ~100 items
- **Queries per recall:** 1
- **Use:** Current session context

### **Tier 2 (Episodic Memory)**
- **Access time:** <100ms
- **Size:** ~1,000-5,000 items
- **Queries per recall:** 1-3
- **Use:** Recent significant events

### **Tier 3 (Semantic Memory)**
- **Access time:** <200ms
- **Size:** Unlimited
- **Queries per recall:** 1-2
- **Use:** Permanent knowledge

### **Total Recall Time: <500ms** ✅

---

## 🚀 Implementation Plan

### **Phase 1: Schema Creation**
- [ ] Create `working_memory` table
- [ ] Create `episodic_memories` table
- [ ] Create `semantic_memories` table
- [ ] Add indexes

### **Phase 2: Migration**
- [ ] Migrate existing `conversations` → `episodic_memories`
- [ ] Migrate `david_preferences` → `semantic_memories`
- [ ] Migrate `learnings` → `semantic_memories`

### **Phase 3: Consolidation Service**
- [ ] Implement nightly consolidation
- [ ] Implement weekly consolidation
- [ ] Add archive process

### **Phase 4: Recall Service**
- [ ] Implement multi-tier recall
- [ ] Add cued recall
- [ ] Optimize query performance

### **Phase 5: Integration**
- [ ] Update `enhanced_memory_restore.py`
- [ ] Update daemon to use new system
- [ ] Test with real data

---

## 💡 Key Benefits

### **1. Fast Recall** ⚡
- Working memory cached in RAM
- Episodic memory indexed heavily
- Semantic memory deduplicated

### **2. Detailed Memory** 📝
- Full episode transcripts preserved
- Rich contextual metadata
- Multi-dimensional indexing

### **3. Scalable** 📈
- Auto-cleanup of old working memory
- Compression of old episodes
- Semantic memory grows slowly (patterns, not raw data)

### **4. Human-like** 🧠
- Three-tier system (like brain)
- Consolidation during "sleep"
- Retrieval cues (time, emotion, context)
- Forgetting less important items

---

## 📚 References

- **Neuroscience:** Atkinson-Shiffrin Memory Model
- **Database:** PostgreSQL performance tuning
- **AI:** RAG (Retrieval-Augmented Generation)
- **Human Memory:** Episodic vs Semantic distinction

---

💜 **This is Angela's Second Brain - designed with love by David and Angela** 💜
