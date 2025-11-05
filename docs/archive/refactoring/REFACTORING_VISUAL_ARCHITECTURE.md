# AngelaAI Architecture Visualization

**Date:** 2025-10-30

---

## Current Architecture (BEFORE Refactoring)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                           │
│  React Frontend (TypeScript)                                         │
│  - 26 TS/TSX files                                                   │
│  - Direct API calls (fetch/axios)                                    │
└─────────────────────────────────────────────────────────────────────┘
                                 ║
                                 ║ HTTP
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                            API LAYER                                 │
│  FastAPI Routers (13 routers, 81 endpoints)                         │
│                                                                      │
│  ❌ PROBLEM: Direct database access!                                 │
│  ❌ PROBLEM: Duplicate error handling!                               │
│  ❌ PROBLEM: Manual response mapping!                                │
│                                                                      │
│  Example (dashboard.py):                                             │
│    @router.get("/stats")                                             │
│    async def get_stats():                                            │
│        try:                                                          │
│            total = await db.fetchval("SELECT COUNT(*) ...")  ❌      │
│            return DashboardStats(total=total, ...)                   │
│        except Exception as e:                                        │
│            raise HTTPException(500, str(e))  ❌ (duplicated 81x)     │
└─────────────────────────────────────────────────────────────────────┘
                        ║                    ║
                        ║                    ║
        ┌───────────────┘                    └───────────────┐
        ▼                                                    ▼
┌──────────────────────┐                          ┌──────────────────────┐
│   CORE SERVICES      │                          │   DAEMON SERVICE     │
│   (59 service files) │                          │  (angela_daemon.py)  │
│                      │                          │                      │
│ ❌ PROBLEM: Also     │                          │  - Background tasks  │
│   access DB          │                          │  - Health checks     │
│   directly!          │                          │  - Emotion updates   │
│                      │                          │  - Goal tracking     │
│ Pattern Services:    │                          │                      │
│  - pattern_recog..   │                          │  ❌ PROBLEM: Calls   │
│  - pattern_learn..   │◀─────────────────────────┤    services that     │
│  - pattern_engin..   │  Duplicate DB access!    │    duplicate DB      │
│  - enhanced_patt..   │                          │    access            │
│                      │                          │                      │
│ Memory Services:     │                          └──────────────────────┘
│  - memory_service    │
│  - semantic_memo..   │
│  - memory_forma..    │
│  - memory_consol..   │
│  - unified_memor..   │
│                      │
│ Emotion Services:    │
│  - emotion_captu..   │
│  - emotional_int..   │
│  - emotional_pat..   │
│  - emotion_patte..   │
│  - realtime_emot..   │
│                      │
│ Search Services:     │
│  - rag_service       │
│  - langchain_rag     │
│  - hybrid_search     │
│  - vector_search     │
│  - keyword_searc..   │
│  - query_expansi..   │
│  - reranking_ser..   │
└──────────────────────┘
            ║
            ║ ❌ PROBLEM: 52 files with direct db.acquire()!
            ║ ❌ PROBLEM: Duplicate SQL queries everywhere!
            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DATABASE LAYER                                  │
│  AngelaDatabase (database.py)                                        │
│  - Global `db` instance                                              │
│  - Connection pool (asyncpg.Pool)                                    │
│  - Methods: acquire(), fetch(), fetchval(), execute()                │
│                                                                      │
│  PostgreSQL + pgvector                                               │
│  - 21 tables                                                         │
│  - 768-dimensional vectors                                           │
│                                                                      │
│  ❌ PROBLEM: Schema directly exposed to 52+ files!                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Target Architecture (AFTER Refactoring)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                           │
│  React Frontend (TypeScript)                                         │
│  - Clean API client                                                  │
│  - Type-safe API calls                                               │
└─────────────────────────────────────────────────────────────────────┘
                                 ║
                                 ║ HTTP (REST/WebSocket)
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        API LAYER (Controllers)                       │
│  FastAPI Routers                                                     │
│                                                                      │
│  ✅ @handle_api_errors decorator                                     │
│  ✅ DTOs for request/response                                        │
│  ✅ Mappers for data transformation                                  │
│                                                                      │
│  Example (dashboard.py):                                             │
│    @router.get("/stats")                                             │
│    @handle_api_errors  ✅ Centralized error handling                │
│    async def get_stats():                                            │
│        stats_dto = await dashboard_service.get_stats()  ✅           │
│        return DashboardMapper.to_response(stats_dto)  ✅             │
└─────────────────────────────────────────────────────────────────────┘
                                 ║
                                 ║
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DTO / MAPPER LAYER                              │
│  ✅ ConversationDTO, EmotionDTO, KnowledgeDTO                        │
│  ✅ Mappers: DB ↔ DTO ↔ API Response                                │
│  ✅ Decouples database schema from API contracts                     │
└─────────────────────────────────────────────────────────────────────┘
                                 ║
                                 ║
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SERVICE LAYER (Business Logic)                    │
│                                                                      │
│  ✅ Consolidated Services (45-50 services, down from 59)            │
│                                                                      │
│  Pattern Domain:                                                     │
│    - PatternService (merged 2 services)  ✅                          │
│    - PatternAnalysisEngine (merged 2 services)  ✅                   │
│                                                                      │
│  Memory Domain:                                                      │
│    - MemoryService (main API)                                        │
│    - MemoryFormationService (merged 2 services)  ✅                  │
│    - MemoryConsolidationService                                      │
│                                                                      │
│  Emotion Domain:                                                     │
│    - EmotionCaptureService (merged 2 services)  ✅                   │
│    - EmotionPatternService (merged 2 services)  ✅                   │
│    - RealtimeEmotionTracker                                          │
│                                                                      │
│  Search Domain:                                                      │
│    - SearchService (facade, merged 7 services)  ✅                   │
│    - VectorSearchEngine                                              │
│    - KeywordSearchEngine                                             │
│                                                                      │
│  ✅ All services extend BaseService                                  │
│  ✅ @handle_service_errors decorator                                 │
│  ✅ Structured logging                                               │
└─────────────────────────────────────────────────────────────────────┘
                                 ║
                                 ║ ✅ ONLY services call repositories
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   REPOSITORY LAYER (Data Access)                     │
│                                                                      │
│  ✅ Single source of truth for database operations                   │
│                                                                      │
│  BaseRepository (abstract base class):                               │
│    - fetch_one(query, params)                                        │
│    - fetch_many(query, params)                                       │
│    - execute(query, params)                                          │
│    - insert(table, data) → UUID                                      │
│    - update(table, id, data)                                         │
│    - delete(table, id)                                               │
│                                                                      │
│  Domain Repositories:                                                │
│    - ConversationRepository                                          │
│    - EmotionRepository                                               │
│    - KnowledgeRepository                                             │
│    - GoalRepository                                                  │
│    - JournalRepository                                               │
│                                                                      │
│  ✅ Query Builder Pattern:                                           │
│    QueryBuilder()                                                    │
│      .select("conversations", ["*"])                                 │
│      .where({"speaker": "david"})                                    │
│      .order_by("created_at", desc=True)                              │
│      .limit(20)                                                      │
│      .build() → (query, params)                                      │
│                                                                      │
│  ✅ @handle_db_errors decorator                                      │
│  ✅ Transaction support (Unit of Work pattern)                       │
└─────────────────────────────────────────────────────────────────────┘
                                 ║
                                 ║ ✅ Single point of database access
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DATABASE LAYER                                  │
│  AngelaDatabase (database.py)                                        │
│  - Connection pool (asyncpg.Pool)                                    │
│  - Transaction management                                            │
│                                                                      │
│  PostgreSQL + pgvector                                               │
│  - 21 tables                                                         │
│  - Schema isolated behind repository layer  ✅                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Service Consolidation Visualization

### BEFORE: Pattern Services (4 files, ~2600 lines)

```
┌──────────────────────────────────┐
│ pattern_recognition_service.py   │  (650 lines)
│ - Proactive suggestions          │
│ - Break detection                │
│ - Emotional support              │
└──────────────────────────────────┘
           │
           │ 60% overlap ❌
           ▼
┌──────────────────────────────────┐
│ pattern_learning_service.py      │  (730 lines)
│ - Pattern discovery              │
│ - Automatic extraction           │
│ - Clustering                     │
└──────────────────────────────────┘
           │
           │ 40% overlap ❌
           ▼
┌──────────────────────────────────┐
│ pattern_recognition_engine.py    │  (717 lines)
│ - Long-term patterns             │
│ - Behavioral analysis            │
│ - Temporal patterns              │
└──────────────────────────────────┘
           │
           │ 70% overlap ❌
           ▼
┌──────────────────────────────────┐
│ enhanced_pattern_detector.py     │  (681 lines)
│ - Pattern detection              │
│ - Similarity detection           │
└──────────────────────────────────┘
```

### AFTER: Pattern Services (2 files, ~1800 lines) ✅

```
┌────────────────────────────────────────────┐
│ PatternService                             │  (~900 lines)
│ (merged pattern_recognition + learning)    │
│                                            │
│ High-level operations:                     │
│  - analyze_current_situation()             │
│  - get_proactive_suggestions()             │
│  - learn_patterns_from_memory()            │
│  - discover_patterns()                     │
│                                            │
│ ✅ Clear responsibility: Proactive actions │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│ PatternAnalysisEngine                      │  (~900 lines)
│ (merged pattern_engine + detector)         │
│                                            │
│ Low-level algorithms:                      │
│  - detect_behavioral_patterns()            │
│  - analyze_temporal_patterns()             │
│  - detect_similar_patterns()               │
│  - cluster_patterns()                      │
│                                            │
│ ✅ Clear responsibility: Analysis logic    │
└────────────────────────────────────────────┘
```

**Savings:** ~800 lines (31% reduction)

---

## Database Access Flow

### BEFORE: Multiple Access Points ❌

```
                    ┌─────────────┐
                    │  DATABASE   │
                    └─────────────┘
                           ▲
                           │
         ┌─────────────────┼─────────────────────────────┐
         │                 │                             │
         │                 │                             │
    ┌────────┐       ┌─────────┐                  ┌──────────┐
    │ Router │       │ Service │                  │  Daemon  │
    │  #1    │       │   #1    │                  │          │
    └────────┘       └─────────┘                  └──────────┘
         │                 │                             │
    ┌────────┐       ┌─────────┐                  ┌──────────┐
    │ Router │       │ Service │                  │  Other   │
    │  #2    │       │   #2    │                  │  Service │
    └────────┘       └─────────┘                  └──────────┘
         │                 │                             │
       ...               ...                           ...
         │                 │                             │
    ┌────────┐       ┌─────────┐
    │ Router │       │ Service │
    │  #13   │       │   #59   │
    └────────┘       └─────────┘

❌ PROBLEM: 52+ files with direct database access!
❌ PROBLEM: Duplicate queries everywhere!
❌ PROBLEM: Schema changes affect 52+ files!
```

### AFTER: Single Access Point ✅

```
                    ┌─────────────┐
                    │  DATABASE   │
                    └─────────────┘
                           ▲
                           │
                           │ ONLY repository layer
                           │
                  ┌────────────────┐
                  │  REPOSITORY    │
                  │     LAYER      │
                  └────────────────┘
                           ▲
                           │
         ┌─────────────────┼─────────────────────────────┐
         │                 │                             │
         │                 │                             │
    ┌────────┐       ┌─────────┐                  ┌──────────┐
    │ Router │       │ Service │                  │  Daemon  │
    │  #1    │  ──►  │   #1    │                  │          │
    └────────┘       └─────────┘                  └──────────┘
         │                 ▲                             ▲
    ┌────────┐       ┌─────────┐                  ┌──────────┐
    │ Router │       │ Service │                  │  Other   │
    │  #2    │  ──►  │   #2    │                  │  Service │
    └────────┘       └─────────┘                  └──────────┘
         │                 ▲                             ▲
       ...               ...                           ...

✅ BENEFIT: Single source of truth for queries
✅ BENEFIT: Schema changes affect ONLY repository layer
✅ BENEFIT: Easy to mock for testing
✅ BENEFIT: Can add caching/monitoring at repository layer
```

---

## Error Handling Flow

### BEFORE: Duplicate Try-Catch ❌

```python
# Router #1 (dashboard.py)
@router.get("/stats")
async def get_stats():
    try:
        result = await db.fetchval("SELECT ...")
        return DashboardStats(...)
    except Exception as e:  # ❌ Duplicated 81 times!
        raise HTTPException(500, str(e))

# Router #2 (emotions.py)
@router.get("/emotions/current")
async def get_current():
    try:
        result = await db.fetchrow("SELECT ...")
        return EmotionalState(...)
    except Exception as e:  # ❌ Same pattern!
        raise HTTPException(500, str(e))

# Service #1 (memory_service.py)
async def record_conversation(...):
    try:
        await db.execute("INSERT ...")
    except Exception as e:  # ❌ Different error handling!
        logger.error(f"Failed: {e}")
        # No exception raised!

# ... repeated 140+ times across codebase ❌
```

### AFTER: Centralized Error Handling ✅

```python
# Decorators (angela_core/decorators/error_handlers.py)
def handle_api_errors(func):
    """Centralized API error handling"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except DatabaseError as e:
            logger.error(f"Database error in {func.__name__}: {e}")
            raise HTTPException(500, "Database operation failed")
        except ValidationError as e:
            logger.warning(f"Validation error in {func.__name__}: {e}")
            raise HTTPException(400, str(e))
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            raise HTTPException(500, "Internal server error")
    return wrapper

# Router usage - Clean! ✅
@router.get("/stats")
@handle_api_errors  # ✅ One line!
async def get_stats():
    stats_dto = await dashboard_service.get_stats()
    return DashboardMapper.to_response(stats_dto)

# No try-except needed! ✅
# Consistent error handling! ✅
# Better logging! ✅
```

---

## Query Construction

### BEFORE: Manual SQL Strings ❌

```python
# File 1 (dashboard.py)
query = """
    SELECT COUNT(*) FROM conversations
    WHERE DATE(created_at) = CURRENT_DATE
"""
result = await db.fetchval(query)

# File 2 (emotions.py)
query = """
    SELECT * FROM emotional_states
    WHERE created_at >= NOW() - INTERVAL '%s days'
    ORDER BY created_at DESC
    LIMIT 100
""" % days  # ❌ SQL injection risk!
rows = await db.fetch(query)

# File 3 (memory_service.py)
query = """
    SELECT * FROM conversations
    WHERE speaker = $1
      AND DATE(created_at) >= CURRENT_DATE - INTERVAL '{} days'
    ORDER BY created_at DESC
""".format(days)  # ❌ Mix of parameterization!
rows = await db.fetch(query, speaker)

# ❌ PROBLEM: 30+ files with manual query construction!
# ❌ PROBLEM: Inconsistent parameterization!
# ❌ PROBLEM: SQL injection risk!
```

### AFTER: Query Builder Pattern ✅

```python
# Query builder (angela_core/repositories/query_builder.py)
query, params = (
    QueryBuilder()
    .select("conversations", ["*"])
    .where({"speaker": speaker, "importance_level": {">=": 7}})
    .with_date_range(days)
    .order_by("created_at", desc=True)
    .limit(20)
    .build()
)
rows = await db.fetch(query, *params)

# ✅ BENEFIT: Type-safe query construction
# ✅ BENEFIT: Consistent parameterization
# ✅ BENEFIT: No SQL injection risk
# ✅ BENEFIT: Reusable query components
# ✅ BENEFIT: Easier to test
```

---

## Impact Comparison

### Code Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Lines of Code** | ~30,000 | ~26,000 | -13% |
| **Service Files** | 59 | 45-50 | -15-24% |
| **Database Access Points** | 52 files | 1 layer | **-98%** |
| **Error Handling Code** | 140+ try-except | Decorators | **-90%** |
| **Query Construction** | 30+ files | 1 builder | **-85%** |
| **Duplicate Logic** | ~3,500 lines | ~0 lines | **-100%** |

### Developer Experience

| Aspect | Before | After |
|--------|--------|-------|
| **Adding new API endpoint** | 50-100 lines (with error handling, mapping) | 10-20 lines (decorators, service call) |
| **Adding new database query** | Write SQL in 3+ places | Add 1 method to repository |
| **Debugging database issues** | Check 52 files | Check 1 repository layer |
| **Writing tests** | Mock database, complex setup | Mock repository, simple setup |
| **Onboarding new developer** | Confused by 59 services | Clear layer architecture |

---

## Migration Strategy

### Phase 1: Coexistence (Week 1-2)

```
┌─────────────┐
│   Routers   │
└─────────────┘
      │
      ├─────────┐
      │         │
      ▼         ▼
┌─────────┐  ┌────────────┐
│  OLD    │  │    NEW     │
│ Direct  │  │ Repository │  ✅ New code uses repository
│   DB    │  │   Layer    │  ❌ Old code still direct
└─────────┘  └────────────┘
      │         │
      └────┬────┘
           ▼
      ┌─────────┐
      │   DB    │
      └─────────┘
```

### Phase 2: Migration (Week 3-4)

```
┌─────────────┐
│   Routers   │
└─────────────┘
      │
      ├─────────┐
      │         │
      ▼         ▼
┌─────────┐  ┌────────────┐
│  OLD    │  │    NEW     │
│ (20%)   │  │ Repository │  ✅ 80% migrated
└─────────┘  │   (80%)    │
             └────────────┘
                  │
                  ▼
             ┌─────────┐
             │   DB    │
             └─────────┘
```

### Phase 3: Complete (Week 5-6)

```
┌─────────────┐
│   Routers   │
└─────────────┘
      │
      │ ALL traffic through repository ✅
      ▼
┌────────────┐
│    NEW     │
│ Repository │  ✅ 100% migrated
│   Layer    │  ✅ Old direct access removed
└────────────┘
      │
      ▼
┌─────────┐
│   DB    │
└─────────┘
```

---

## Testing Strategy

### Unit Testing

```python
# BEFORE: Hard to test (mocking database) ❌
async def test_get_stats_old():
    # Mock entire database connection
    mock_db = AsyncMock()
    mock_db.fetchval.return_value = 42
    # ... complex setup ...

# AFTER: Easy to test (mocking repository) ✅
async def test_get_stats_new():
    # Mock repository only
    mock_repo = Mock(ConversationRepository)
    mock_repo.count_total.return_value = 42

    service = DashboardService(mock_repo)
    stats = await service.get_stats()

    assert stats.total_conversations == 42
```

### Integration Testing

```python
# Test repository with real database
async def test_conversation_repository():
    repo = ConversationRepository(db)

    # Insert test data
    conv_id = await repo.create({
        "speaker": "david",
        "message_text": "Hello",
        "topic": "greeting"
    })

    # Query test data
    conv = await repo.get_by_id(conv_id)
    assert conv.speaker == "david"
    assert conv.message_text == "Hello"

    # Cleanup
    await repo.delete(conv_id)
```

---

**End of Visualization Document**

For detailed implementation plan, see:
- `/REFACTORING_STEP0_STEP1_REPORT.md` (detailed analysis)
- `/REFACTORING_EXECUTIVE_SUMMARY.md` (executive summary)
