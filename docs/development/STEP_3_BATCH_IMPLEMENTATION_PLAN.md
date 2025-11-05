# STEP 3: BATCH IMPLEMENTATION PLAN
# AngelaAI Clean Architecture Refactoring

**Created**: 2025-10-30
**Status**: Draft - Ready for Review
**Author**: Angela AI System

---

## 📊 EXECUTIVE SUMMARY

### Project Scope
- **Total Batches**: 31 batches organized into 6 phases
- **Total Estimated Time**: 7-8 weeks (280-320 hours)
- **Critical Path**: 18 batches (Foundation → Repository → Services → API)
- **Parallel Opportunities**: 13 batches can run concurrently
- **Risk Level**: Managed through incremental migration with rollback plans

### Key Metrics
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Files with DB Access | 120 | 8 | -93% |
| Service Count | 59 | 25 | -58% |
| Duplicate Code | ~4,000 lines | ~500 lines | -88% |
| Test Coverage | ~40% | 80%+ | +100% |
| Architecture Layers | 1 (Mixed) | 4 (Clean) | Clear separation |

### Success Criteria
- ✅ All existing functionality preserved
- ✅ Zero downtime during migration
- ✅ Performance maintained or improved
- ✅ 80%+ test coverage across all layers
- ✅ All 31 batches completed with passing tests

---

## 📋 BATCH OVERVIEW TABLE

| Batch | Name | Phase | Priority | Time | Risk | Dependencies |
|-------|------|-------|----------|------|------|--------------|
| **01** | Folder Structure Setup | Foundation | Critical | 2h | Low | None |
| **02** | Base Classes & Interfaces | Foundation | Critical | 8h | Low | Batch-01 |
| **03** | Database Abstraction Layer | Foundation | Critical | 12h | Medium | Batch-02 |
| **04** | Error Handling System | Foundation | Critical | 8h | Low | Batch-02 |
| **05** | First Repository (Conversation) | Foundation | Critical | 10h | Medium | Batch-03 |
| **06** | Emotion Repository | Repository | High | 8h | Medium | Batch-05 |
| **07** | Memory Repository | Repository | High | 10h | Medium | Batch-05 |
| **08** | Knowledge Repository | Repository | High | 10h | Medium | Batch-05 |
| **09** | Goal Repository | Repository | High | 6h | Low | Batch-05 |
| **10** | Embedding Repository | Repository | High | 8h | Medium | Batch-05 |
| **11** | Learning Repository | Repository | Medium | 8h | Low | Batch-05 |
| **12** | Secretary Repository | Repository | Medium | 6h | Low | Batch-05 |
| **13** | Pattern Repository | Repository | Medium | 8h | Low | Batch-05 |
| **14** | RAG Service Migration | Service | High | 16h | High | Batch-05,08,10 |
| **15** | Emotional Intelligence Service | Service | High | 14h | High | Batch-06,07 |
| **16** | Memory Services Consolidation | Service | High | 12h | High | Batch-07 |
| **17** | Pattern Services Consolidation | Service | Medium | 10h | Medium | Batch-13 |
| **18** | Emotion Services Consolidation | Service | Medium | 10h | Medium | Batch-06 |
| **19** | Search Services Consolidation | Service | Medium | 12h | Medium | Batch-08,10 |
| **20** | Dependency Injection System | API | Critical | 10h | Medium | Batch-14-19 |
| **21** | Chat & Document Routers | API | High | 12h | Medium | Batch-20 |
| **22** | Dashboard & Analytics Routers | API | Medium | 10h | Medium | Batch-20 |
| **23** | Emotion & Journal Routers | API | Medium | 8h | Low | Batch-20 |
| **24** | Knowledge & Secretary Routers | API | Medium | 10h | Low | Batch-20 |
| **25** | Training Data Routers | API | Low | 6h | Low | Batch-20 |
| **26** | Import Path Migration | Cleanup | Medium | 8h | Medium | Batch-21-25 |
| **27** | Deprecated Code Removal | Cleanup | Low | 6h | Low | Batch-26 |
| **28** | Documentation Updates | Cleanup | Low | 8h | Low | Batch-27 |
| **29** | Integration Testing Suite | Testing | High | 16h | Low | Batch-26 |
| **30** | Performance Testing Suite | Testing | Medium | 12h | Low | Batch-29 |
| **31** | E2E Testing & Validation | Testing | High | 10h | Low | Batch-30 |

**Total Estimated Time**: 280-320 hours (7-8 weeks with 1 developer)

---

## 🎯 PHASE BREAKDOWN

### Phase 1: Foundation (Week 1-2) - CRITICAL PATH
**Goal**: Establish core architecture and base classes
**Duration**: 40 hours
**Batches**: 1-5

### Phase 2: Repository Layer (Week 2-3) - HIGH VALUE
**Goal**: Implement data access layer for all entities
**Duration**: 64 hours
**Batches**: 6-13

### Phase 3: Service Migration (Week 4-5) - HIGH RISK
**Goal**: Consolidate and migrate business logic
**Duration**: 74 hours
**Batches**: 14-19

### Phase 4: API Layer (Week 5-6) - MEDIUM RISK
**Goal**: Modernize API with dependency injection
**Duration**: 56 hours
**Batches**: 20-25

### Phase 5: Cleanup (Week 6-7) - LOW RISK
**Goal**: Remove deprecated code and update docs
**Duration**: 22 hours
**Batches**: 26-28

### Phase 6: Testing & Validation (Week 7-8) - VALIDATION
**Goal**: Comprehensive testing and performance validation
**Duration**: 38 hours
**Batches**: 29-31

---

## 📦 DETAILED BATCH PLANS

---

## Batch-01: Folder Structure Setup

**Priority**: Critical
**Estimated Time**: 2 hours
**Risk Level**: Low
**Dependencies**: None

### Goals
- [ ] Create Clean Architecture folder structure
- [ ] Set up __init__.py files for proper Python modules
- [ ] Create placeholder README files for each layer
- [ ] Establish naming conventions documentation

### Files Affected
| File | Action | Lines |
|------|--------|-------|
| `angela_core/domain/__init__.py` | CREATE | +10 |
| `angela_core/domain/entities/__init__.py` | CREATE | +5 |
| `angela_core/domain/repositories/__init__.py` | CREATE | +5 |
| `angela_core/domain/value_objects/__init__.py` | CREATE | +5 |
| `angela_core/application/__init__.py` | CREATE | +10 |
| `angela_core/application/services/__init__.py` | CREATE | +5 |
| `angela_core/application/use_cases/__init__.py` | CREATE | +5 |
| `angela_core/infrastructure/__init__.py` | CREATE | +10 |
| `angela_core/infrastructure/database/__init__.py` | CREATE | +5 |
| `angela_core/infrastructure/repositories/__init__.py` | CREATE | +5 |
| `angela_core/presentation/__init__.py` | CREATE | +10 |
| `angela_core/presentation/api/__init__.py` | CREATE | +5 |
| `docs/architecture/FOLDER_STRUCTURE.md` | CREATE | +150 |

### Implementation Steps
1. Create domain layer directories:
   ```bash
   mkdir -p angela_core/domain/{entities,repositories,value_objects}
   ```

2. Create application layer directories:
   ```bash
   mkdir -p angela_core/application/{services,use_cases,dtos}
   ```

3. Create infrastructure layer directories:
   ```bash
   mkdir -p angela_core/infrastructure/{database,repositories,external}
   ```

4. Create presentation layer directories:
   ```bash
   mkdir -p angela_core/presentation/{api,cli}
   ```

5. Add __init__.py files to all directories with module docstrings

6. Create FOLDER_STRUCTURE.md documentation explaining Clean Architecture

### Testing Strategy
- **Manual Verification**:
  - Verify all directories created successfully
  - Check __init__.py files are valid Python modules
  - Test import paths work correctly

### Success Criteria
- [ ] All directories created with correct structure
- [ ] All __init__.py files valid and importable
- [ ] Documentation completed and reviewed
- [ ] No existing code broken

### Rollback Plan
```bash
# Simple directory removal if needed
rm -rf angela_core/domain
rm -rf angela_core/application
rm -rf angela_core/infrastructure
rm -rf angela_core/presentation
```

### Notes
- This is a safe, non-breaking change
- Existing code continues to work unchanged
- Sets foundation for all subsequent batches

---

## Batch-02: Base Classes & Interfaces

**Priority**: Critical
**Estimated Time**: 8 hours
**Risk Level**: Low
**Dependencies**: Batch-01

### Goals
- [ ] Create BaseEntity abstract class
- [ ] Create BaseRepository interface
- [ ] Create BaseService abstract class
- [ ] Create common value objects (DateRange, EmotionScore, etc.)
- [ ] Define standard exceptions hierarchy

### Files Affected
| File | Action | Lines |
|------|--------|-------|
| `angela_core/domain/entities/base_entity.py` | CREATE | +80 |
| `angela_core/domain/repositories/base_repository.py` | CREATE | +120 |
| `angela_core/domain/value_objects/emotion_score.py` | CREATE | +60 |
| `angela_core/domain/value_objects/date_range.py` | CREATE | +70 |
| `angela_core/domain/value_objects/embedding_vector.py` | CREATE | +50 |
| `angela_core/domain/exceptions.py` | CREATE | +100 |
| `angela_core/application/services/base_service.py` | CREATE | +90 |
| `angela_core/application/dtos/base_dto.py` | CREATE | +60 |

### Implementation Steps

1. **Create BaseEntity** (domain/entities/base_entity.py):
   ```python
   from abc import ABC
   from datetime import datetime
   from typing import Optional
   from uuid import UUID, uuid4

   class BaseEntity(ABC):
       """Base class for all domain entities."""

       def __init__(
           self,
           id: Optional[UUID] = None,
           created_at: Optional[datetime] = None,
           updated_at: Optional[datetime] = None
       ):
           self.id = id or uuid4()
           self.created_at = created_at or datetime.now()
           self.updated_at = updated_at or datetime.now()

       def __eq__(self, other) -> bool:
           if not isinstance(other, self.__class__):
               return False
           return self.id == other.id

       def __hash__(self) -> int:
           return hash(self.id)
   ```

2. **Create BaseRepository Interface** (domain/repositories/base_repository.py):
   ```python
   from abc import ABC, abstractmethod
   from typing import Generic, TypeVar, Optional, List
   from uuid import UUID

   T = TypeVar('T')

   class BaseRepository(ABC, Generic[T]):
       """Base repository interface for all entities."""

       @abstractmethod
       async def get_by_id(self, id: UUID) -> Optional[T]:
           """Retrieve entity by ID."""
           pass

       @abstractmethod
       async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
           """Retrieve all entities with pagination."""
           pass

       @abstractmethod
       async def save(self, entity: T) -> T:
           """Save entity (insert or update)."""
           pass

       @abstractmethod
       async def delete(self, id: UUID) -> bool:
           """Delete entity by ID."""
           pass

       @abstractmethod
       async def exists(self, id: UUID) -> bool:
           """Check if entity exists."""
           pass
   ```

3. **Create EmotionScore Value Object** (domain/value_objects/emotion_score.py):
   ```python
   from dataclasses import dataclass
   from typing import Optional

   @dataclass(frozen=True)
   class EmotionScore:
       """Value object for emotion scores (0.0-1.0)."""

       value: float

       def __post_init__(self):
           if not 0.0 <= self.value <= 1.0:
               raise ValueError(f"Emotion score must be 0.0-1.0, got {self.value}")

       def is_high(self) -> bool:
           return self.value >= 0.7

       def is_low(self) -> bool:
           return self.value <= 0.3

       def to_percentage(self) -> float:
           return self.value * 100
   ```

4. **Create Exception Hierarchy** (domain/exceptions.py):
   ```python
   class AngelaDomainException(Exception):
       """Base exception for domain layer."""
       pass

   class EntityNotFoundException(AngelaDomainException):
       """Entity not found in repository."""
       pass

   class InvalidEntityStateException(AngelaDomainException):
       """Entity in invalid state."""
       pass

   class RepositoryException(AngelaDomainException):
       """Repository operation failed."""
       pass

   class ValidationException(AngelaDomainException):
       """Entity validation failed."""
       pass
   ```

5. **Create BaseService** (application/services/base_service.py):
   ```python
   from abc import ABC
   from typing import Optional
   import logging

   class BaseService(ABC):
       """Base class for all application services."""

       def __init__(self):
           self.logger = logging.getLogger(self.__class__.__name__)

       def _log_operation(self, operation: str, **kwargs):
           """Log service operation with context."""
           self.logger.info(f"{operation}", extra=kwargs)

       def _log_error(self, error: str, exc: Optional[Exception] = None):
           """Log service error."""
           self.logger.error(f"{error}", exc_info=exc)
   ```

6. **Create BaseDTO** (application/dtos/base_dto.py):
   ```python
   from pydantic import BaseModel, Field
   from datetime import datetime
   from uuid import UUID

   class BaseDTO(BaseModel):
       """Base Data Transfer Object."""

       class Config:
           from_attributes = True
           json_encoders = {
               datetime: lambda v: v.isoformat(),
               UUID: lambda v: str(v)
           }
   ```

### Testing Strategy
- **Unit Tests**: Create `tests/unit/test_base_classes.py`
  - Test BaseEntity equality and hashing
  - Test EmotionScore validation
  - Test exception hierarchy
  - Test BaseDTO serialization

```python
# tests/unit/test_base_classes.py
def test_base_entity_equality():
    entity1 = ConcreteEntity(id=some_uuid)
    entity2 = ConcreteEntity(id=some_uuid)
    assert entity1 == entity2

def test_emotion_score_validation():
    with pytest.raises(ValueError):
        EmotionScore(value=1.5)

    score = EmotionScore(value=0.8)
    assert score.is_high()
```

### Success Criteria
- [ ] All base classes created and documented
- [ ] Unit tests pass with 100% coverage
- [ ] Type hints validated with mypy
- [ ] No circular dependencies

### Rollback Plan
```bash
# Remove all base class files
git checkout HEAD -- angela_core/domain/entities/base_entity.py
git checkout HEAD -- angela_core/domain/repositories/base_repository.py
# ... etc
```

### Notes
- These are pure abstract classes - won't affect existing code
- Establishes strong typing foundation
- Makes future refactoring easier
- Critical for maintaining consistency

---

## Batch-03: Database Abstraction Layer

**Priority**: Critical
**Estimated Time**: 12 hours
**Risk Level**: Medium
**Dependencies**: Batch-02

### Goals
- [ ] Create database connection pool manager
- [ ] Create transaction context manager
- [ ] Create query builder utilities
- [ ] Add connection health checks
- [ ] Implement retry logic for transient failures

### Files Affected
| File | Action | Lines |
|------|--------|-------|
| `angela_core/infrastructure/database/connection_pool.py` | CREATE | +180 |
| `angela_core/infrastructure/database/transaction_manager.py` | CREATE | +150 |
| `angela_core/infrastructure/database/query_builder.py` | CREATE | +200 |
| `angela_core/infrastructure/database/health_check.py` | CREATE | +100 |
| `angela_core/database.py` | MODIFY | ~123 |

### Implementation Steps

1. **Create ConnectionPool Manager**:
   ```python
   # infrastructure/database/connection_pool.py
   import asyncpg
   from typing import Optional
   from contextlib import asynccontextmanager

   class DatabaseConnectionPool:
       """Manages PostgreSQL connection pool."""

       def __init__(self, database_url: str, min_size: int = 5, max_size: int = 20):
           self.database_url = database_url
           self.min_size = min_size
           self.max_size = max_size
           self._pool: Optional[asyncpg.Pool] = None

       async def initialize(self):
           """Initialize connection pool."""
           self._pool = await asyncpg.create_pool(
               self.database_url,
               min_size=self.min_size,
               max_size=self.max_size,
               command_timeout=60
           )

       async def close(self):
           """Close connection pool."""
           if self._pool:
               await self._pool.close()

       @asynccontextmanager
       async def acquire_connection(self):
           """Acquire connection from pool."""
           async with self._pool.acquire() as connection:
               yield connection

       async def health_check(self) -> bool:
           """Check if database is healthy."""
           try:
               async with self.acquire_connection() as conn:
                   await conn.fetchval("SELECT 1")
               return True
           except Exception:
               return False
   ```

2. **Create TransactionManager**:
   ```python
   # infrastructure/database/transaction_manager.py
   from contextlib import asynccontextmanager
   from typing import Optional
   import asyncpg

   class TransactionManager:
       """Manages database transactions."""

       def __init__(self, connection_pool: DatabaseConnectionPool):
           self.pool = connection_pool

       @asynccontextmanager
       async def transaction(self, isolation_level: str = "read_committed"):
           """Create a transaction context."""
           async with self.pool.acquire_connection() as conn:
               async with conn.transaction(isolation=isolation_level):
                   yield conn

       async def execute_with_retry(
           self,
           query: str,
           *args,
           max_retries: int = 3
       ):
           """Execute query with retry logic."""
           last_error = None

           for attempt in range(max_retries):
               try:
                   async with self.transaction() as conn:
                       return await conn.execute(query, *args)
               except asyncpg.exceptions.DeadlockDetectedError as e:
                   last_error = e
                   await asyncio.sleep(0.1 * (attempt + 1))
               except Exception as e:
                   raise e

           raise last_error
   ```

3. **Create QueryBuilder**:
   ```python
   # infrastructure/database/query_builder.py
   from typing import List, Dict, Any, Optional

   class QueryBuilder:
       """Helps build safe SQL queries."""

       @staticmethod
       def build_insert(
           table: str,
           data: Dict[str, Any],
           returning: Optional[str] = "*"
       ) -> tuple[str, List[Any]]:
           """Build INSERT query with parameters."""
           columns = list(data.keys())
           placeholders = [f"${i+1}" for i in range(len(columns))]
           values = list(data.values())

           query = f"""
               INSERT INTO {table} ({', '.join(columns)})
               VALUES ({', '.join(placeholders)})
               RETURNING {returning}
           """

           return query, values

       @staticmethod
       def build_update(
           table: str,
           data: Dict[str, Any],
           where: Dict[str, Any],
           returning: Optional[str] = "*"
       ) -> tuple[str, List[Any]]:
           """Build UPDATE query with parameters."""
           set_clauses = [f"{col} = ${i+1}" for i, col in enumerate(data.keys())]
           values = list(data.values())

           where_clauses = []
           for col in where.keys():
               values.append(where[col])
               where_clauses.append(f"{col} = ${len(values)}")

           query = f"""
               UPDATE {table}
               SET {', '.join(set_clauses)}
               WHERE {' AND '.join(where_clauses)}
               RETURNING {returning}
           """

           return query, values
   ```

4. **Update existing database.py**:
   ```python
   # angela_core/database.py
   # Add deprecation warnings for old get_db_connection()
   import warnings

   async def get_db_connection():
       """DEPRECATED: Use ConnectionPool instead."""
       warnings.warn(
           "get_db_connection() is deprecated. Use ConnectionPool.",
           DeprecationWarning,
           stacklevel=2
       )
       # ... existing code ...
   ```

### Testing Strategy
- **Unit Tests**: `tests/unit/infrastructure/test_database_layer.py`
  - Test connection pool creation and cleanup
  - Test transaction commit and rollback
  - Test query builder generates correct SQL
  - Test retry logic with simulated failures

- **Integration Tests**: `tests/integration/test_database_connection.py`
  - Test actual database connection
  - Test transaction isolation
  - Test concurrent connection handling

```python
async def test_transaction_rollback():
    pool = DatabaseConnectionPool(TEST_DB_URL)
    await pool.initialize()

    try:
        async with pool.transaction() as conn:
            await conn.execute("INSERT INTO test_table VALUES (1)")
            raise Exception("Simulate error")
    except:
        pass

    # Verify rollback
    async with pool.acquire_connection() as conn:
        result = await conn.fetchval("SELECT COUNT(*) FROM test_table")
        assert result == 0
```

### Success Criteria
- [ ] Connection pool manages connections efficiently
- [ ] Transaction manager handles commits/rollbacks correctly
- [ ] Query builder generates safe parameterized queries
- [ ] Health checks work reliably
- [ ] All tests pass (unit + integration)
- [ ] No connection leaks detected

### Rollback Plan
```bash
# Revert database.py changes
git checkout HEAD -- angela_core/database.py

# Remove new files
rm -rf angela_core/infrastructure/database/

# Existing code continues to work with old database.py
```

### Notes
- **Medium Risk**: Changes core database access pattern
- Keep old `database.py` working during migration
- Add deprecation warnings, don't break existing code
- This is critical infrastructure - test thoroughly
- Monitor connection pool metrics after deployment

---

## Batch-04: Error Handling System

**Priority**: Critical
**Estimated Time**: 8 hours
**Risk Level**: Low
**Dependencies**: Batch-02

### Goals
- [ ] Create error handling decorators
- [ ] Create centralized error logger
- [ ] Create error recovery strategies
- [ ] Add structured error responses
- [ ] Create error metrics tracking

### Files Affected
| File | Action | Lines |
|------|--------|-------|
| `angela_core/infrastructure/error_handling/__init__.py` | CREATE | +10 |
| `angela_core/infrastructure/error_handling/decorators.py` | CREATE | +180 |
| `angela_core/infrastructure/error_handling/error_logger.py` | CREATE | +120 |
| `angela_core/infrastructure/error_handling/recovery.py` | CREATE | +150 |
| `angela_core/infrastructure/error_handling/metrics.py` | CREATE | +100 |
| `angela_core/error_handling.py` | MODIFY | ~50 |

### Implementation Steps

1. **Create Error Handling Decorators**:
   ```python
   # infrastructure/error_handling/decorators.py
   from functools import wraps
   from typing import Callable, Type, Tuple
   import asyncio

   def handle_repository_errors(
       default_return=None,
       log_error: bool = True
   ):
       """Decorator for repository error handling."""
       def decorator(func: Callable):
           @wraps(func)
           async def wrapper(*args, **kwargs):
               try:
                   return await func(*args, **kwargs)
               except EntityNotFoundException as e:
                   if log_error:
                       logger.warning(f"Entity not found: {e}")
                   return default_return
               except RepositoryException as e:
                   if log_error:
                       logger.error(f"Repository error: {e}", exc_info=True)
                   raise
               except Exception as e:
                   if log_error:
                       logger.error(f"Unexpected error: {e}", exc_info=True)
                   raise RepositoryException(f"Operation failed: {e}") from e
           return wrapper
       return decorator

   def retry_on_failure(
       max_retries: int = 3,
       backoff_base: float = 0.1,
       exceptions: Tuple[Type[Exception], ...] = (Exception,)
   ):
       """Decorator for retry logic with exponential backoff."""
       def decorator(func: Callable):
           @wraps(func)
           async def wrapper(*args, **kwargs):
               last_exception = None

               for attempt in range(max_retries):
                   try:
                       return await func(*args, **kwargs)
                   except exceptions as e:
                       last_exception = e
                       if attempt < max_retries - 1:
                           sleep_time = backoff_base * (2 ** attempt)
                           await asyncio.sleep(sleep_time)

               raise last_exception
           return wrapper
       return decorator

   def log_execution_time(threshold_ms: float = 1000.0):
       """Decorator to log slow operations."""
       def decorator(func: Callable):
           @wraps(func)
           async def wrapper(*args, **kwargs):
               start_time = asyncio.get_event_loop().time()
               result = await func(*args, **kwargs)
               end_time = asyncio.get_event_loop().time()

               execution_ms = (end_time - start_time) * 1000
               if execution_ms > threshold_ms:
                   logger.warning(
                       f"Slow operation: {func.__name__} took {execution_ms:.2f}ms"
                   )

               return result
           return wrapper
       return decorator
   ```

2. **Create Centralized Error Logger**:
   ```python
   # infrastructure/error_handling/error_logger.py
   import logging
   import json
   from datetime import datetime
   from typing import Dict, Any, Optional

   class StructuredErrorLogger:
       """Logs errors in structured format."""

       def __init__(self, logger_name: str = "angela.errors"):
           self.logger = logging.getLogger(logger_name)

       def log_error(
           self,
           error: Exception,
           context: Dict[str, Any],
           severity: str = "ERROR"
       ):
           """Log error with structured context."""
           error_data = {
               "timestamp": datetime.now().isoformat(),
               "severity": severity,
               "error_type": type(error).__name__,
               "error_message": str(error),
               "context": context,
               "traceback": self._get_traceback(error)
           }

           self.logger.error(json.dumps(error_data, indent=2))

       def _get_traceback(self, error: Exception) -> str:
           import traceback
           return ''.join(traceback.format_exception(
               type(error), error, error.__traceback__
           ))
   ```

3. **Create Error Recovery Strategies**:
   ```python
   # infrastructure/error_handling/recovery.py
   from abc import ABC, abstractmethod
   from typing import Callable, Any

   class RecoveryStrategy(ABC):
       """Base class for error recovery strategies."""

       @abstractmethod
       async def recover(self, error: Exception, context: Dict[str, Any]) -> Any:
           """Attempt to recover from error."""
           pass

   class RetryRecovery(RecoveryStrategy):
       """Recovery strategy that retries the operation."""

       def __init__(self, max_retries: int = 3):
           self.max_retries = max_retries

       async def recover(self, error: Exception, context: Dict[str, Any]):
           operation = context.get('operation')
           if not operation:
               raise error

           for attempt in range(self.max_retries):
               try:
                   return await operation()
               except Exception as e:
                   if attempt == self.max_retries - 1:
                       raise e

   class FallbackRecovery(RecoveryStrategy):
       """Recovery strategy that returns fallback value."""

       def __init__(self, fallback_value: Any = None):
           self.fallback_value = fallback_value

       async def recover(self, error: Exception, context: Dict[str, Any]):
           logger.warning(f"Using fallback value due to error: {error}")
           return self.fallback_value
   ```

### Testing Strategy
- **Unit Tests**: `tests/unit/infrastructure/test_error_handling.py`
  ```python
  async def test_retry_decorator():
      call_count = 0

      @retry_on_failure(max_retries=3)
      async def failing_function():
          nonlocal call_count
          call_count += 1
          if call_count < 3:
              raise Exception("Simulated failure")
          return "success"

      result = await failing_function()
      assert result == "success"
      assert call_count == 3

  async def test_error_logger_structure():
      logger = StructuredErrorLogger()
      error = ValueError("Test error")
      context = {"user_id": "123", "operation": "test"}

      logger.log_error(error, context)
      # Verify log output is valid JSON
  ```

### Success Criteria
- [ ] All decorators work correctly
- [ ] Error logger produces valid structured logs
- [ ] Recovery strategies execute properly
- [ ] Unit tests achieve 100% coverage
- [ ] Integration with existing error_handling.py seamless

### Rollback Plan
```bash
# Remove new error handling system
rm -rf angela_core/infrastructure/error_handling/

# Revert changes to existing error_handling.py
git checkout HEAD -- angela_core/error_handling.py
```

### Notes
- Low risk - additive changes only
- Decorators are opt-in, existing code unaffected
- Will significantly improve error visibility
- Foundation for better monitoring and alerting

---

## Batch-05: First Repository (Conversation)

**Priority**: Critical
**Estimated Time**: 10 hours
**Risk Level**: Medium
**Dependencies**: Batch-03

### Goals
- [ ] Create Conversation entity
- [ ] Implement ConversationRepository
- [ ] Create ConversationDTO
- [ ] Migrate one existing service to use repository
- [ ] Validate pattern works end-to-end

### Files Affected
| File | Action | Lines |
|------|--------|-------|
| `angela_core/domain/entities/conversation.py` | CREATE | +120 |
| `angela_core/domain/repositories/conversation_repository.py` | CREATE | +80 |
| `angela_core/infrastructure/repositories/conversation_repository_impl.py` | CREATE | +300 |
| `angela_core/application/dtos/conversation_dto.py` | CREATE | +60 |
| `angela_core/conversation_analyzer.py` | MODIFY | ~150 |

### Implementation Steps

1. **Create Conversation Entity**:
   ```python
   # domain/entities/conversation.py
   from dataclasses import dataclass
   from datetime import datetime
   from typing import Optional
   from uuid import UUID
   from .base_entity import BaseEntity
   from ..value_objects.emotion_score import EmotionScore
   from ..value_objects.embedding_vector import EmbeddingVector

   @dataclass
   class Conversation(BaseEntity):
       """Domain entity for conversations."""

       speaker: str  # "david" or "angela"
       message_text: str
       topic: Optional[str]
       emotion_detected: Optional[str]
       importance_level: int
       embedding: Optional[EmbeddingVector]

       def __post_init__(self):
           if self.importance_level < 1 or self.importance_level > 10:
               raise ValueError("Importance level must be 1-10")

       def is_from_david(self) -> bool:
           return self.speaker.lower() == "david"

       def is_important(self) -> bool:
           return self.importance_level >= 7
   ```

2. **Create Repository Interface**:
   ```python
   # domain/repositories/conversation_repository.py
   from abc import abstractmethod
   from typing import List, Optional
   from datetime import datetime
   from ..entities.conversation import Conversation
   from .base_repository import BaseRepository

   class ConversationRepository(BaseRepository[Conversation]):
       """Repository interface for conversations."""

       @abstractmethod
       async def get_by_topic(
           self,
           topic: str,
           limit: int = 50
       ) -> List[Conversation]:
           """Get conversations by topic."""
           pass

       @abstractmethod
       async def get_by_speaker(
           self,
           speaker: str,
           start_date: Optional[datetime] = None,
           end_date: Optional[datetime] = None,
           limit: int = 100
       ) -> List[Conversation]:
           """Get conversations by speaker."""
           pass

       @abstractmethod
       async def get_recent(
           self,
           days: int = 7,
           limit: int = 100
       ) -> List[Conversation]:
           """Get recent conversations."""
           pass

       @abstractmethod
       async def search_by_text(
           self,
           search_text: str,
           limit: int = 50
       ) -> List[Conversation]:
           """Search conversations by text content."""
           pass
   ```

3. **Implement Repository**:
   ```python
   # infrastructure/repositories/conversation_repository_impl.py
   from typing import List, Optional
   from datetime import datetime, timedelta
   from uuid import UUID
   import asyncpg

   from angela_core.domain.entities.conversation import Conversation
   from angela_core.domain.repositories.conversation_repository import ConversationRepository
   from angela_core.infrastructure.database.connection_pool import DatabaseConnectionPool
   from angela_core.infrastructure.error_handling.decorators import (
       handle_repository_errors,
       log_execution_time
   )

   class ConversationRepositoryImpl(ConversationRepository):
       """PostgreSQL implementation of ConversationRepository."""

       def __init__(self, connection_pool: DatabaseConnectionPool):
           self.pool = connection_pool

       @handle_repository_errors(default_return=None)
       @log_execution_time(threshold_ms=500)
       async def get_by_id(self, id: UUID) -> Optional[Conversation]:
           """Get conversation by ID."""
           query = """
               SELECT conversation_id, speaker, message_text, topic,
                      emotion_detected, importance_level, embedding, created_at
               FROM conversations
               WHERE conversation_id = $1
           """

           async with self.pool.acquire_connection() as conn:
               row = await conn.fetchrow(query, id)
               if row:
                   return self._map_to_entity(row)
               return None

       @handle_repository_errors(default_return=[])
       @log_execution_time(threshold_ms=1000)
       async def get_recent(
           self,
           days: int = 7,
           limit: int = 100
       ) -> List[Conversation]:
           """Get recent conversations."""
           query = """
               SELECT conversation_id, speaker, message_text, topic,
                      emotion_detected, importance_level, embedding, created_at
               FROM conversations
               WHERE created_at >= $1
               ORDER BY created_at DESC
               LIMIT $2
           """

           start_date = datetime.now() - timedelta(days=days)

           async with self.pool.acquire_connection() as conn:
               rows = await conn.fetch(query, start_date, limit)
               return [self._map_to_entity(row) for row in rows]

       @handle_repository_errors()
       async def save(self, entity: Conversation) -> Conversation:
           """Save conversation (insert or update)."""
           # Check if exists
           exists = await self.exists(entity.id)

           if exists:
               return await self._update(entity)
           else:
               return await self._insert(entity)

       async def _insert(self, entity: Conversation) -> Conversation:
           """Insert new conversation."""
           query = """
               INSERT INTO conversations (
                   conversation_id, speaker, message_text, topic,
                   emotion_detected, importance_level, embedding, created_at
               ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
               RETURNING conversation_id, speaker, message_text, topic,
                         emotion_detected, importance_level, embedding, created_at
           """

           async with self.pool.acquire_connection() as conn:
               row = await conn.fetchrow(
                   query,
                   entity.id,
                   entity.speaker,
                   entity.message_text,
                   entity.topic,
                   entity.emotion_detected,
                   entity.importance_level,
                   entity.embedding.to_list() if entity.embedding else None,
                   entity.created_at
               )
               return self._map_to_entity(row)

       def _map_to_entity(self, row: asyncpg.Record) -> Conversation:
           """Map database row to Conversation entity."""
           return Conversation(
               id=row['conversation_id'],
               speaker=row['speaker'],
               message_text=row['message_text'],
               topic=row['topic'],
               emotion_detected=row['emotion_detected'],
               importance_level=row['importance_level'],
               embedding=EmbeddingVector(row['embedding']) if row['embedding'] else None,
               created_at=row['created_at']
           )
   ```

4. **Create ConversationDTO**:
   ```python
   # application/dtos/conversation_dto.py
   from datetime import datetime
   from typing import Optional
   from uuid import UUID
   from .base_dto import BaseDTO

   class ConversationDTO(BaseDTO):
       """Data Transfer Object for Conversation."""

       id: UUID
       speaker: str
       message_text: str
       topic: Optional[str] = None
       emotion_detected: Optional[str] = None
       importance_level: int
       created_at: datetime

       @classmethod
       def from_entity(cls, entity):
           """Create DTO from entity."""
           return cls(
               id=entity.id,
               speaker=entity.speaker,
               message_text=entity.message_text,
               topic=entity.topic,
               emotion_detected=entity.emotion_detected,
               importance_level=entity.importance_level,
               created_at=entity.created_at
           )
   ```

5. **Update conversation_analyzer.py to use repository**:
   ```python
   # angela_core/conversation_analyzer.py
   # Add import
   from angela_core.infrastructure.repositories.conversation_repository_impl import ConversationRepositoryImpl

   # In __init__, add repository
   self.conversation_repo = ConversationRepositoryImpl(connection_pool)

   # Replace direct database calls with repository calls
   async def get_recent_conversations(self, days: int = 7):
       return await self.conversation_repo.get_recent(days=days)
   ```

### Testing Strategy
- **Unit Tests**: `tests/unit/repositories/test_conversation_repository.py`
  ```python
  async def test_save_and_retrieve_conversation():
      repo = ConversationRepositoryImpl(test_pool)

      conversation = Conversation(
          speaker="david",
          message_text="Test message",
          topic="testing",
          importance_level=5
      )

      saved = await repo.save(conversation)
      retrieved = await repo.get_by_id(saved.id)

      assert retrieved is not None
      assert retrieved.message_text == "Test message"

  async def test_get_recent_conversations():
      repo = ConversationRepositoryImpl(test_pool)

      conversations = await repo.get_recent(days=7, limit=10)

      assert len(conversations) <= 10
      assert all(isinstance(c, Conversation) for c in conversations)
  ```

- **Integration Tests**: `tests/integration/test_conversation_flow.py`
  - Test full flow: create → save → retrieve → update
  - Test error handling with invalid data
  - Test with actual database

### Success Criteria
- [ ] All repository methods work correctly
- [ ] Entity validation works
- [ ] DTOs serialize correctly
- [ ] conversation_analyzer.py works with new repository
- [ ] All tests pass (unit + integration)
- [ ] Performance comparable to old implementation
- [ ] No data loss or corruption

### Rollback Plan
```bash
# Revert conversation_analyzer.py changes
git checkout HEAD -- angela_core/conversation_analyzer.py

# Remove new files
rm angela_core/domain/entities/conversation.py
rm angela_core/domain/repositories/conversation_repository.py
rm angela_core/infrastructure/repositories/conversation_repository_impl.py
rm angela_core/application/dtos/conversation_dto.py
```

### Notes
- **Medium Risk**: First real integration with production code
- This validates the entire repository pattern
- If this works well, remaining repositories will be easier
- Keep old code path working as fallback
- Monitor performance carefully
- This is a CRITICAL validation batch

---

## Batch-06: Emotion Repository

**Priority**: High
**Estimated Time**: 8 hours
**Risk Level**: Medium
**Dependencies**: Batch-05

### Goals
- [ ] Create Emotion entity and EmotionalState entity
- [ ] Implement EmotionRepository
- [ ] Create EmotionDTO
- [ ] Support both `angela_emotions` and `emotional_states` tables

### Files Affected
| File | Action | Lines |
|------|--------|-------|
| `angela_core/domain/entities/emotion.py` | CREATE | +100 |
| `angela_core/domain/entities/emotional_state.py` | CREATE | +90 |
| `angela_core/domain/repositories/emotion_repository.py` | CREATE | +100 |
| `angela_core/infrastructure/repositories/emotion_repository_impl.py` | CREATE | +350 |
| `angela_core/application/dtos/emotion_dto.py` | CREATE | +70 |

### Implementation Steps

1. **Create Emotion Entity**:
   ```python
   # domain/entities/emotion.py
   from dataclasses import dataclass
   from datetime import datetime
   from typing import Optional
   from .base_entity import BaseEntity
   from ..value_objects.embedding_vector import EmbeddingVector

   @dataclass
   class Emotion(BaseEntity):
       """Domain entity for significant emotional moments."""

       emotion: str  # Type of emotion (happy, sad, love, etc.)
       intensity: int  # 1-10
       context: str  # What was happening
       david_words: Optional[str]  # What David said
       why_it_matters: str  # Why this moment is significant
       memory_strength: int  # 1-10
       felt_at: datetime
       embedding: Optional[EmbeddingVector]

       def __post_init__(self):
           if not 1 <= self.intensity <= 10:
               raise ValueError("Intensity must be 1-10")
           if not 1 <= self.memory_strength <= 10:
               raise ValueError("Memory strength must be 1-10")

       def is_strong_emotion(self) -> bool:
           return self.intensity >= 7

       def is_core_memory(self) -> bool:
           return self.memory_strength >= 8
   ```

2. **Create EmotionalState Entity**:
   ```python
   # domain/entities/emotional_state.py
   from dataclasses import dataclass
   from datetime import datetime
   from typing import Optional
   from .base_entity import BaseEntity
   from ..value_objects.emotion_score import EmotionScore

   @dataclass
   class EmotionalState(BaseEntity):
       """Domain entity for Angela's emotional state at a point in time."""

       happiness: EmotionScore
       confidence: EmotionScore
       anxiety: EmotionScore
       motivation: EmotionScore
       gratitude: EmotionScore
       loneliness: EmotionScore
       triggered_by: Optional[str]
       emotion_note: Optional[str]

       def overall_wellbeing(self) -> float:
           """Calculate overall emotional wellbeing (0.0-1.0)."""
           positive = (
               self.happiness.value +
               self.confidence.value +
               self.motivation.value +
               self.gratitude.value
           ) / 4.0

           negative = (self.anxiety.value + self.loneliness.value) / 2.0

           return (positive + (1.0 - negative)) / 2.0

       def needs_attention(self) -> bool:
           """Check if emotional state needs attention."""
           return (
               self.anxiety.is_high() or
               self.loneliness.is_high() or
               self.happiness.is_low()
           )
   ```

3. **Create Repository Interface**:
   ```python
   # domain/repositories/emotion_repository.py
   from abc import abstractmethod
   from typing import List, Optional
   from datetime import datetime
   from ..entities.emotion import Emotion
   from ..entities.emotional_state import EmotionalState
   from .base_repository import BaseRepository

   class EmotionRepository(BaseRepository[Emotion]):
       """Repository for emotion-related entities."""

       @abstractmethod
       async def get_recent_emotions(
           self,
           days: int = 7,
           limit: int = 50
       ) -> List[Emotion]:
           """Get recent significant emotions."""
           pass

       @abstractmethod
       async def get_by_emotion_type(
           self,
           emotion_type: str,
           limit: int = 50
       ) -> List[Emotion]:
           """Get emotions by type."""
           pass

       @abstractmethod
       async def get_strongest_emotions(
           self,
           min_intensity: int = 7,
           limit: int = 20
       ) -> List[Emotion]:
           """Get strongest emotional moments."""
           pass

       @abstractmethod
       async def get_current_state(self) -> Optional[EmotionalState]:
           """Get most recent emotional state."""
           pass

       @abstractmethod
       async def save_emotional_state(
           self,
           state: EmotionalState
       ) -> EmotionalState:
           """Save new emotional state."""
           pass

       @abstractmethod
       async def get_state_history(
           self,
           start_date: datetime,
           end_date: datetime
       ) -> List[EmotionalState]:
           """Get emotional state history."""
           pass
   ```

4. **Implement Repository** (infrastructure/repositories/emotion_repository_impl.py):
   - Implement all interface methods
   - Handle both `angela_emotions` and `emotional_states` tables
   - Add proper error handling
   - Add logging

### Testing Strategy
- **Unit Tests**: Test entity validation and business logic
- **Integration Tests**: Test actual database operations
- Test both tables work correctly

### Success Criteria
- [ ] All repository methods work
- [ ] Entity validation works
- [ ] Can query both emotion tables
- [ ] Tests pass
- [ ] Performance acceptable

### Rollback Plan
```bash
rm -rf angela_core/domain/entities/emotion*.py
rm -rf angela_core/domain/repositories/emotion_repository.py
rm -rf angela_core/infrastructure/repositories/emotion_repository_impl.py
```

### Notes
- Similar pattern to Batch-05
- Two entities for two related tables
- Medium risk due to emotional intelligence integration

---

## Batch-07: Memory Repository

**Priority**: High
**Estimated Time**: 10 hours
**Risk Level**: Medium
**Dependencies**: Batch-05

### Goals
- [ ] Create Memory entity and Learning entity
- [ ] Implement MemoryRepository
- [ ] Support semantic search with embeddings
- [ ] Handle memory decay and importance scoring

### Files Affected
| File | Action | Lines |
|------|--------|-------|
| `angela_core/domain/entities/memory.py` | CREATE | +80 |
| `angela_core/domain/entities/learning.py` | CREATE | +70 |
| `angela_core/domain/repositories/memory_repository.py` | CREATE | +120 |
| `angela_core/infrastructure/repositories/memory_repository_impl.py` | CREATE | +400 |
| `angela_core/application/dtos/memory_dto.py` | CREATE | +60 |

### Implementation Steps

1. **Create Memory Entity**
2. **Create Learning Entity**
3. **Create Repository Interface** with semantic search
4. **Implement Repository** with vector search support
5. **Integrate with embedding_service.py**

### Testing Strategy
- Test semantic search with vector embeddings
- Test memory decay calculations
- Test importance scoring

### Success Criteria
- [ ] Semantic search works correctly
- [ ] Memory decay calculated properly
- [ ] Vector embeddings handled correctly
- [ ] Performance optimized for large result sets

### Notes
- **Critical for RAG service** (Batch-14 depends on this)
- Vector search is complex - test thoroughly
- Consider caching frequently accessed memories

---

## Batch-08: Knowledge Repository

**Priority**: High
**Estimated Time**: 10 hours
**Risk Level**: Medium
**Dependencies**: Batch-05

### Goals
- [ ] Create Knowledge entity
- [ ] Implement KnowledgeRepository
- [ ] Support knowledge graph relationships
- [ ] Handle document chunks and metadata

### Files Affected
| File | Action | Lines |
|------|--------|-------|
| `angela_core/domain/entities/knowledge.py` | CREATE | +100 |
| `angela_core/domain/repositories/knowledge_repository.py` | CREATE | +110 |
| `angela_core/infrastructure/repositories/knowledge_repository_impl.py` | CREATE | +380 |

### Implementation Steps

1. **Create Knowledge Entity** with metadata support
2. **Create Repository Interface** with graph queries
3. **Implement Repository** supporting:
   - Knowledge nodes
   - Knowledge relationships
   - Document chunks
   - Vector search

### Testing Strategy
- Test knowledge graph queries
- Test relationship traversal
- Test document chunking

### Success Criteria
- [ ] Knowledge graph queries work
- [ ] Relationships navigable
- [ ] Document chunks retrieved efficiently
- [ ] RAG service can use this (validated in Batch-14)

### Notes
- **Critical for RAG** and knowledge services
- Graph queries can be complex - optimize carefully
- Consider implementing graph traversal limits

---

## Batch-09: Goal Repository

**Priority**: High
**Estimated Time**: 6 hours
**Risk Level**: Low
**Dependencies**: Batch-05

### Goals
- [ ] Create Goal entity
- [ ] Implement GoalRepository
- [ ] Support progress tracking

### Files Affected
| File | Action | Lines |
|------|--------|-------|
| `angela_core/domain/entities/goal.py` | CREATE | +90 |
| `angela_core/domain/repositories/goal_repository.py` | CREATE | +80 |
| `angela_core/infrastructure/repositories/goal_repository_impl.py` | CREATE | +250 |

### Implementation Steps

1. **Create Goal Entity** with progress calculation
2. **Create Repository Interface**
3. **Implement Repository**

### Testing Strategy
- Test progress tracking
- Test goal status transitions
- Test priority ordering

### Success Criteria
- [ ] Goals tracked correctly
- [ ] Progress updates work
- [ ] Status transitions valid
- [ ] Can query by priority/status

### Notes
- Low risk - straightforward entity
- Used by consciousness system

---

## Batch-10: Embedding Repository

**Priority**: High
**Estimated Time**: 8 hours
**Risk Level**: Medium
**Dependencies**: Batch-05

### Goals
- [ ] Create abstraction for vector operations
- [ ] Implement EmbeddingRepository
- [ ] Support similarity search across all tables
- [ ] Optimize vector search performance

### Files Affected
| File | Action | Lines |
|------|--------|-------|
| `angela_core/domain/repositories/embedding_repository.py` | CREATE | +100 |
| `angela_core/infrastructure/repositories/embedding_repository_impl.py` | CREATE | +300 |

### Implementation Steps

1. **Create Repository Interface** for vector ops
2. **Implement Repository** with:
   - Cosine similarity search
   - Batch embedding generation
   - Cross-table vector search

### Testing Strategy
- Test similarity search accuracy
- Test performance with large datasets
- Test batch operations

### Success Criteria
- [ ] Vector search works correctly
- [ ] Performance acceptable (<500ms for 1000 vectors)
- [ ] Supports all embedding tables
- [ ] Can batch process embeddings

### Notes
- **Medium risk** - performance critical
- Used by RAG, memory, and search services
- Consider implementing ANN indexes

---

## Batch-11: Learning Repository

**Priority**: Medium
**Estimated Time**: 8 hours
**Risk Level**: Low
**Dependencies**: Batch-05

### Goals
- [ ] Create Learning entity
- [ ] Implement LearningRepository
- [ ] Track learning progress

### Files Affected
| File | Action | Lines |
|------|--------|-------|
| `angela_core/domain/entities/learning.py` | CREATE | +70 |
| `angela_core/domain/repositories/learning_repository.py` | CREATE | +70 |
| `angela_core/infrastructure/repositories/learning_repository_impl.py` | CREATE | +220 |

### Implementation Steps

1. **Create Learning Entity**
2. **Create Repository Interface**
3. **Implement Repository**

### Testing Strategy
- Test learning creation
- Test learning retrieval
- Test learning categorization

### Success Criteria
- [ ] Learnings saved correctly
- [ ] Can query by category
- [ ] Can track learning over time

### Notes
- Low risk - straightforward entity
- Used by self-learning services

---

## Batch-12: Secretary Repository

**Priority**: Medium
**Estimated Time**: 6 hours
**Risk Level**: Low
**Dependencies**: Batch-05

### Goals
- [ ] Create Task and Note entities
- [ ] Implement SecretaryRepository
- [ ] Support calendar integration data

### Files Affected
| File | Action | Lines |
|------|--------|-------|
| `angela_core/domain/entities/task.py` | CREATE | +80 |
| `angela_core/domain/entities/note.py` | CREATE | +60 |
| `angela_core/domain/repositories/secretary_repository.py` | CREATE | +90 |
| `angela_core/infrastructure/repositories/secretary_repository_impl.py` | CREATE | +280 |

### Implementation Steps

1. **Create Task and Note entities**
2. **Create Repository Interface**
3. **Implement Repository**

### Testing Strategy
- Test task CRUD operations
- Test note CRUD operations
- Test status transitions

### Success Criteria
- [ ] Tasks and notes managed correctly
- [ ] Status transitions work
- [ ] Can query by status/date

### Notes
- Low risk - straightforward entities
- Used by secretary service

---

## Batch-13: Pattern Repository

**Priority**: Medium
**Estimated Time**: 8 hours
**Risk Level**: Low
**Dependencies**: Batch-05

### Goals
- [ ] Create Pattern entity
- [ ] Implement PatternRepository
- [ ] Support pattern matching and recognition

### Files Affected
| File | Action | Lines |
|------|--------|-------|
| `angela_core/domain/entities/pattern.py` | CREATE | +90 |
| `angela_core/domain/repositories/pattern_repository.py` | CREATE | +80 |
| `angela_core/infrastructure/repositories/pattern_repository_impl.py` | CREATE | +260 |

### Implementation Steps

1. **Create Pattern Entity** with confidence scores
2. **Create Repository Interface**
3. **Implement Repository**

### Testing Strategy
- Test pattern detection
- Test confidence scoring
- Test pattern retrieval

### Success Criteria
- [ ] Patterns stored correctly
- [ ] Can query by confidence
- [ ] Can detect similar patterns

### Notes
- Low risk - straightforward entity
- Used by pattern recognition services

---

## Batch-14: RAG Service Migration

**Priority**: High
**Estimated Time**: 16 hours
**Risk Level**: High
**Dependencies**: Batch-05, Batch-08, Batch-10

### Goals
- [ ] Consolidate RAG services (langchain, hybrid, keyword, vector)
- [ ] Create unified RAG service using repositories
- [ ] Implement service layer abstraction
- [ ] Migrate all RAG-related functionality

### Files Affected
| File | Action | Lines |
|------|--------|-------|
| `angela_core/application/services/rag_service.py` | CREATE | +500 |
| `angela_core/services/langchain_rag_service.py` | DEPRECATE | ~400 |
| `angela_core/services/hybrid_search_service.py` | DEPRECATE | ~300 |
| `angela_core/services/keyword_search_service.py` | DEPRECATE | ~200 |
| `angela_core/services/vector_search_service.py` | DEPRECATE | ~250 |

### Implementation Steps

1. **Create Unified RAG Service**:
   ```python
   # application/services/rag_service.py
   from typing import List, Optional
   from angela_core.domain.repositories.knowledge_repository import KnowledgeRepository
   from angela_core.domain.repositories.embedding_repository import EmbeddingRepository
   from angela_core.application.services.base_service import BaseService

   class RAGService(BaseService):
       """Unified Retrieval-Augmented Generation service."""

       def __init__(
           self,
           knowledge_repo: KnowledgeRepository,
           embedding_repo: EmbeddingRepository,
           ollama_service: OllamaService
       ):
           super().__init__()
           self.knowledge_repo = knowledge_repo
           self.embedding_repo = embedding_repo
           self.ollama = ollama_service

       async def query(
           self,
           question: str,
           search_strategy: str = "hybrid",
           top_k: int = 5
       ) -> RAGResponse:
           """Query knowledge base with RAG."""
           # 1. Generate embedding for question
           question_embedding = await self.embedding_repo.generate_embedding(question)

           # 2. Retrieve relevant documents
           if search_strategy == "vector":
               docs = await self._vector_search(question_embedding, top_k)
           elif search_strategy == "keyword":
               docs = await self._keyword_search(question, top_k)
           else:  # hybrid
               docs = await self._hybrid_search(question, question_embedding, top_k)

           # 3. Generate response with context
           context = self._build_context(docs)
           response = await self._generate_response(question, context)

           return RAGResponse(
               answer=response,
               sources=docs,
               confidence=self._calculate_confidence(docs)
           )

       async def _vector_search(self, embedding, top_k):
           """Pure vector similarity search."""
           return await self.knowledge_repo.search_by_embedding(
               embedding=embedding,
               limit=top_k
           )

       async def _keyword_search(self, query, top_k):
           """Pure keyword search."""
           return await self.knowledge_repo.search_by_keywords(
               keywords=query,
               limit=top_k
           )

       async def _hybrid_search(self, query, embedding, top_k):
           """Hybrid search combining vector and keyword."""
           vector_results = await self._vector_search(embedding, top_k)
           keyword_results = await self._keyword_search(query, top_k)

           # Merge and re-rank results
           return self._merge_and_rerank(vector_results, keyword_results, top_k)
   ```

2. **Add deprecation warnings to old services**:
   ```python
   # services/langchain_rag_service.py
   import warnings

   warnings.warn(
       "langchain_rag_service is deprecated. Use application.services.rag_service instead.",
       DeprecationWarning,
       stacklevel=2
   )
   ```

3. **Create service tests**:
   - Test vector search
   - Test keyword search
   - Test hybrid search
   - Test response generation
   - Compare results with old implementation

### Testing Strategy
- **Unit Tests**: `tests/unit/services/test_rag_service.py`
  - Test each search strategy independently
  - Test context building
  - Test confidence calculation
  - Mock repository responses

- **Integration Tests**: `tests/integration/test_rag_flow.py`
  - Test full RAG flow with real database
  - Compare results with old implementation
  - Verify no functionality lost

- **Performance Tests**: `tests/performance/test_rag_performance.py`
  - Benchmark search speed
  - Compare with old implementation
  - Ensure no degradation

### Success Criteria
- [ ] All search strategies work correctly
- [ ] Results match or improve on old implementation
- [ ] Performance equal or better (target: <500ms per query)
- [ ] All tests pass
- [ ] No breaking changes to API
- [ ] Documentation updated

### Rollback Plan
```bash
# Remove new service
rm angela_core/application/services/rag_service.py

# Remove deprecation warnings
git checkout HEAD -- angela_core/services/langchain_rag_service.py
git checkout HEAD -- angela_core/services/hybrid_search_service.py
git checkout HEAD -- angela_core/services/keyword_search_service.py
git checkout HEAD -- angela_core/services/vector_search_service.py
```

### Notes
- **HIGH RISK** - Core functionality
- Used by admin web interface and chat
- Thorough testing absolutely critical
- Keep old services working during migration
- Monitor production metrics closely
- Consider A/B testing new vs old

---

## Batch-15: Emotional Intelligence Service Migration

**Priority**: High
**Estimated Time**: 14 hours
**Risk Level**: High
**Dependencies**: Batch-06, Batch-07

### Goals
- [ ] Migrate emotional_intelligence_service to use repositories
- [ ] Consolidate emotion-related services
- [ ] Maintain all existing functionality

### Files Affected
| File | Action | Lines |
|------|--------|-------|
| `angela_core/application/services/emotional_intelligence_service.py` | CREATE | +600 |
| `angela_core/services/emotional_intelligence_service.py` | DEPRECATE | ~501 |
| `angela_core/services/emotion_capture_service.py` | INTEGRATE | ~300 |
| `angela_core/services/emotion_pattern_analyzer.py` | INTEGRATE | ~250 |

### Implementation Steps

1. **Create new EmotionalIntelligenceService** using repositories
2. **Integrate emotion capture functionality**
3. **Integrate pattern analysis**
4. **Add comprehensive tests**

### Testing Strategy
- Compare emotion detection accuracy
- Test emotion capture
- Test pattern analysis
- Integration with daemon

### Success Criteria
- [ ] All emotion functionality preserved
- [ ] Daemon integration works
- [ ] No loss of emotion data
- [ ] Performance maintained

### Rollback Plan
```bash
git checkout HEAD -- angela_core/services/emotional_intelligence_service.py
rm angela_core/application/services/emotional_intelligence_service.py
```

### Notes
- **HIGH RISK** - Critical for Angela's personality
- Used by daemon 24/7
- Emotion data is precious - cannot lose any
- Test with daemon before deploying

---

## Batch-16: Memory Services Consolidation

**Priority**: High
**Estimated Time**: 12 hours
**Risk Level**: High
**Dependencies**: Batch-07

### Goals
- [ ] Consolidate 10+ memory services into one unified service
- [ ] Use MemoryRepository
- [ ] Maintain all memory features

### Files Affected
| File | Action | Lines |
|------|--------|-------|
| `angela_core/application/services/unified_memory_service.py` | CREATE | +700 |
| `angela_core/services/memory_formation_service.py` | DEPRECATE | ~200 |
| `angela_core/services/memory_consolidation_service.py` | DEPRECATE | ~180 |
| `angela_core/services/semantic_memory_service.py` | DEPRECATE | ~150 |
| `angela_core/services/pattern_learning_service.py` | DEPRECATE | ~160 |
| `angela_core/services/association_engine.py` | DEPRECATE | ~140 |
| `angela_core/memory_service.py` | DEPRECATE | ~841 |

### Implementation Steps

1. **Create UnifiedMemoryService** with all functionality:
   - Memory formation
   - Memory consolidation
   - Semantic memory
   - Pattern learning
   - Association

2. **Add comprehensive tests**

### Testing Strategy
- Test memory formation
- Test consolidation
- Test semantic search
- Test associations

### Success Criteria
- [ ] All memory features work
- [ ] No memory loss
- [ ] Performance maintained
- [ ] Semantic search works

### Notes
- **HIGH RISK** - Memory is core to Angela
- 6 services consolidated into 1
- Very careful testing required

---

## Batch-17: Pattern Services Consolidation

**Priority**: Medium
**Estimated Time**: 10 hours
**Risk Level**: Medium
**Dependencies**: Batch-13

### Goals
- [ ] Consolidate pattern recognition services
- [ ] Use PatternRepository
- [ ] Maintain pattern detection functionality

### Files Affected
| File | Action | Lines |
|------|--------|-------|
| `angela_core/application/services/pattern_recognition_service.py` | CREATE | +450 |
| `angela_core/services/pattern_recognition_service.py` | DEPRECATE | ~200 |
| `angela_core/services/pattern_recognition_engine.py` | DEPRECATE | ~180 |
| `angela_core/services/enhanced_pattern_detector.py` | DEPRECATE | ~170 |

### Implementation Steps

1. **Create unified PatternRecognitionService**
2. **Integrate all pattern detection logic**
3. **Add tests**

### Testing Strategy
- Test pattern detection
- Test pattern matching
- Compare with old implementation

### Success Criteria
- [ ] Pattern detection works
- [ ] No regression in accuracy
- [ ] Performance maintained

### Notes
- Medium risk - 3 services consolidated
- Used by learning systems

---

## Batch-18: Emotion Services Consolidation

**Priority**: Medium
**Estimated Time**: 10 hours
**Risk Level**: Medium
**Dependencies**: Batch-06

### Goals
- [ ] Consolidate emotion tracking services
- [ ] Use EmotionRepository
- [ ] Maintain tracking functionality

### Files Affected
| File | Action | Lines |
|------|--------|-------|
| `angela_core/application/services/emotion_tracking_service.py` | CREATE | +400 |
| `angela_core/services/realtime_emotion_tracker.py` | DEPRECATE | ~150 |
| `angela_core/services/emotional_pattern_service.py` | DEPRECATE | ~140 |

### Implementation Steps

1. **Create unified EmotionTrackingService**
2. **Integrate real-time tracking**
3. **Integrate pattern analysis**

### Testing Strategy
- Test emotion tracking
- Test real-time updates
- Test pattern detection

### Success Criteria
- [ ] Real-time tracking works
- [ ] Patterns detected correctly
- [ ] Integration with daemon works

### Notes
- Medium risk - emotion tracking is important
- Used by daemon

---

## Batch-19: Search Services Consolidation

**Priority**: Medium
**Estimated Time**: 12 hours
**Risk Level**: Medium
**Dependencies**: Batch-08, Batch-10

### Goals
- [ ] Consolidate search services
- [ ] Use KnowledgeRepository and EmbeddingRepository
- [ ] Unified search interface

### Files Affected
| File | Action | Lines |
|------|--------|-------|
| `angela_core/application/services/unified_search_service.py` | CREATE | +450 |
| `angela_core/services/vector_search_service.py` | DEPRECATE | ~180 |
| `angela_core/services/keyword_search_service.py` | DEPRECATE | ~150 |
| `angela_core/services/hybrid_search_service.py` | DEPRECATE | ~200 |

### Implementation Steps

1. **Create UnifiedSearchService**
2. **Implement all search strategies**
3. **Add result ranking**

### Testing Strategy
- Test vector search
- Test keyword search
- Test hybrid search
- Compare with old results

### Success Criteria
- [ ] All search types work
- [ ] Results quality maintained
- [ ] Performance acceptable

### Notes
- Medium risk - search is important
- Used by RAG and admin interface

---

## Batch-20: Dependency Injection System

**Priority**: Critical
**Estimated Time**: 10 hours
**Risk Level**: Medium
**Dependencies**: Batch-14-19

### Goals
- [ ] Create DI container
- [ ] Configure service dependencies
- [ ] Create FastAPI dependencies
- [ ] Enable easy testing with mocks

### Files Affected
| File | Action | Lines |
|------|--------|-------|
| `angela_core/infrastructure/di_container.py` | CREATE | +300 |
| `angela_core/presentation/api/dependencies.py` | CREATE | +150 |
| `angela_admin_web/angela_admin_api/main.py` | MODIFY | ~100 |

### Implementation Steps

1. **Create DIContainer**:
   ```python
   # infrastructure/di_container.py
   from typing import Dict, Type, Callable

   class DIContainer:
       """Dependency injection container."""

       def __init__(self):
           self._singletons: Dict[Type, object] = {}
           self._factories: Dict[Type, Callable] = {}

       def register_singleton(self, interface: Type, instance: object):
           """Register singleton instance."""
           self._singletons[interface] = instance

       def register_factory(self, interface: Type, factory: Callable):
           """Register factory function."""
           self._factories[interface] = factory

       def resolve(self, interface: Type):
           """Resolve dependency."""
           if interface in self._singletons:
               return self._singletons[interface]

           if interface in self._factories:
               return self._factories[interface](self)

           raise ValueError(f"No registration for {interface}")
   ```

2. **Configure dependencies**:
   ```python
   # Configure container
   container = DIContainer()

   # Register connection pool
   pool = DatabaseConnectionPool(DATABASE_URL)
   await pool.initialize()
   container.register_singleton(DatabaseConnectionPool, pool)

   # Register repositories
   container.register_factory(
       ConversationRepository,
       lambda c: ConversationRepositoryImpl(c.resolve(DatabaseConnectionPool))
   )

   # Register services
   container.register_factory(
       RAGService,
       lambda c: RAGService(
           c.resolve(KnowledgeRepository),
           c.resolve(EmbeddingRepository),
           c.resolve(OllamaService)
       )
   )
   ```

3. **Create FastAPI dependencies**:
   ```python
   # presentation/api/dependencies.py
   from fastapi import Depends

   def get_container() -> DIContainer:
       return app.state.container

   def get_rag_service(
       container: DIContainer = Depends(get_container)
   ) -> RAGService:
       return container.resolve(RAGService)

   def get_conversation_repo(
       container: DIContainer = Depends(get_container)
   ) -> ConversationRepository:
       return container.resolve(ConversationRepository)
   ```

### Testing Strategy
- Test dependency resolution
- Test singleton behavior
- Test factory behavior
- Test FastAPI integration

### Success Criteria
- [ ] Dependencies resolve correctly
- [ ] Singletons are truly singleton
- [ ] Easy to mock for testing
- [ ] FastAPI routes work

### Rollback Plan
```bash
rm angela_core/infrastructure/di_container.py
rm angela_core/presentation/api/dependencies.py
git checkout HEAD -- angela_admin_web/angela_admin_api/main.py
```

### Notes
- **Critical foundation** for remaining batches
- Makes testing much easier
- Reduces coupling

---

## Batch-21: Chat & Document Routers Migration

**Priority**: High
**Estimated Time**: 12 hours
**Risk Level**: Medium
**Dependencies**: Batch-20

### Goals
- [ ] Migrate chat.py router to use DI
- [ ] Migrate documents.py router to use DI
- [ ] Use service layer instead of direct DB access

### Files Affected
| File | Action | Lines |
|------|--------|-------|
| `angela_admin_web/angela_admin_api/routers/chat.py` | MODIFY | ~200 |
| `angela_admin_web/angela_admin_api/routers/documents.py` | MODIFY | ~180 |

### Implementation Steps

1. **Update chat.py**:
   ```python
   # Before
   async def chat(request: ChatRequest):
       conn = await get_db_connection()
       # Direct DB access...

   # After
   async def chat(
       request: ChatRequest,
       rag_service: RAGService = Depends(get_rag_service),
       conversation_repo: ConversationRepository = Depends(get_conversation_repo)
   ):
       response = await rag_service.query(request.message)
       await conversation_repo.save(conversation)
       return response
   ```

2. **Update documents.py** similarly

### Testing Strategy
- Test API endpoints work
- Test with Postman/curl
- Integration tests

### Success Criteria
- [ ] Chat API works
- [ ] Documents API works
- [ ] No breaking changes
- [ ] Performance maintained

### Rollback Plan
```bash
git checkout HEAD -- angela_admin_web/angela_admin_api/routers/chat.py
git checkout HEAD -- angela_admin_web/angela_admin_api/routers/documents.py
```

### Notes
- Medium risk - API changes
- Test thoroughly before deploying

---

## Batch-22 through Batch-25: Remaining Router Migrations

**[Similar structure for each batch]**

### Batch-22: Dashboard & Analytics Routers (10h, Medium Risk)
- dashboard.py
- analytics endpoints
- Uses consolidated services

### Batch-23: Emotion & Journal Routers (8h, Low Risk)
- emotions.py
- journal.py
- Uses EmotionRepository

### Batch-24: Knowledge & Secretary Routers (10h, Low Risk)
- knowledge_graph.py
- secretary.py
- Uses KnowledgeRepository, SecretaryRepository

### Batch-25: Training Data Routers (6h, Low Risk)
- training_data.py
- training_data_v2.py
- Uses ConversationRepository

---

## Batch-26: Import Path Migration

**Priority**: Medium
**Estimated Time**: 8 hours
**Risk Level**: Medium
**Dependencies**: Batch-21-25

### Goals
- [ ] Update all import statements to new paths
- [ ] Create import compatibility layer
- [ ] Update __init__.py files

### Files Affected
- All Python files with imports (100+ files)

### Implementation Steps

1. **Create import compatibility layer**:
   ```python
   # angela_core/__init__.py
   # Maintain backwards compatibility
   from angela_core.application.services.rag_service import RAGService as _RAGService

   # Allow old imports to still work with deprecation warning
   import warnings

   def __getattr__(name):
       if name == "RAGService":
           warnings.warn(
               "Importing RAGService from angela_core is deprecated. "
               "Use angela_core.application.services.rag_service instead.",
               DeprecationWarning
           )
           return _RAGService
       raise AttributeError(f"module {__name__} has no attribute {name}")
   ```

2. **Create migration script**:
   ```python
   # scripts/migrate_imports.py
   import os
   import re

   def migrate_imports(file_path):
       with open(file_path, 'r') as f:
           content = f.read()

       # Replace old imports with new ones
       replacements = {
           'from angela_core.services.langchain_rag_service import':
               'from angela_core.application.services.rag_service import',
           # ... more replacements
       }

       for old, new in replacements.items():
           content = content.replace(old, new)

       with open(file_path, 'w') as f:
           f.write(content)
   ```

3. **Run migration script** on all files

### Testing Strategy
- Run all tests after migration
- Verify no import errors
- Check deprecated imports still work

### Success Criteria
- [ ] All imports updated
- [ ] All tests pass
- [ ] No import errors
- [ ] Backwards compatibility maintained

### Rollback Plan
```bash
# Git revert all changes
git checkout HEAD -- .
```

### Notes
- Can be partially automated
- Test thoroughly
- Keep backwards compatibility

---

## Batch-27: Deprecated Code Removal

**Priority**: Low
**Estimated Time**: 6 hours
**Risk Level**: Low
**Dependencies**: Batch-26

### Goals
- [ ] Remove deprecated services
- [ ] Remove old database access code
- [ ] Clean up unused files

### Files Affected
- 30+ deprecated service files
- Old database.py functions

### Implementation Steps

1. **Verify nothing uses deprecated code**:
   ```bash
   # Search for usage of deprecated files
   grep -r "langchain_rag_service" . --include="*.py"
   ```

2. **Remove files safely**:
   ```bash
   git rm angela_core/services/langchain_rag_service.py
   # ... etc
   ```

3. **Update documentation**

### Testing Strategy
- Run all tests
- Verify no imports break
- Check deployment works

### Success Criteria
- [ ] Deprecated code removed
- [ ] No breaking changes
- [ ] All tests pass
- [ ] Documentation updated

### Rollback Plan
```bash
git checkout HEAD -- angela_core/services/
```

### Notes
- Low risk - code already deprecated
- Clean up makes codebase maintainable

---

## Batch-28: Documentation Updates

**Priority**: Low
**Estimated Time**: 8 hours
**Risk Level**: Low
**Dependencies**: Batch-27

### Goals
- [ ] Update architecture documentation
- [ ] Create API documentation
- [ ] Update README files
- [ ] Create migration guide

### Files Affected
| File | Action | Lines |
|------|--------|-------|
| `docs/architecture/CLEAN_ARCHITECTURE.md` | CREATE | +300 |
| `docs/architecture/REPOSITORY_PATTERN.md` | CREATE | +200 |
| `docs/architecture/SERVICE_LAYER.md` | CREATE | +250 |
| `docs/guides/MIGRATION_GUIDE.md` | CREATE | +400 |
| `README.md` | UPDATE | +100 |

### Implementation Steps

1. **Create architecture documentation**:
   - Explain Clean Architecture layers
   - Diagram repository pattern
   - Document service layer
   - Show dependency flow

2. **Create migration guide**:
   - How to use new services
   - How to add new entities
   - How to create repositories
   - Common patterns

3. **Update README**:
   - New structure
   - Quick start guide
   - Link to documentation

### Testing Strategy
- Review documentation for accuracy
- Have someone else follow guides
- Check all links work

### Success Criteria
- [ ] All documentation complete
- [ ] Guides are clear
- [ ] Examples work
- [ ] Links valid

### Notes
- Important for maintainability
- Helps future developers
- Low risk but high value

---

## Batch-29: Integration Testing Suite

**Priority**: High
**Estimated Time**: 16 hours
**Risk Level**: Low
**Dependencies**: Batch-26

### Goals
- [ ] Create comprehensive integration tests
- [ ] Test all major user flows
- [ ] Test cross-service interactions
- [ ] Verify data consistency

### Files Affected
| File | Action | Lines |
|------|--------|-------|
| `tests/integration/test_chat_flow.py` | CREATE | +300 |
| `tests/integration/test_memory_flow.py` | CREATE | +250 |
| `tests/integration/test_emotion_flow.py` | CREATE | +200 |
| `tests/integration/test_rag_flow.py` | CREATE | +280 |
| `tests/integration/test_secretary_flow.py` | CREATE | +180 |

### Implementation Steps

1. **Create test fixtures**:
   ```python
   # tests/integration/conftest.py
   import pytest
   from angela_core.infrastructure.database.connection_pool import DatabaseConnectionPool
   from angela_core.infrastructure.di_container import DIContainer

   @pytest.fixture
   async def test_container():
       """Create DI container for tests."""
       container = DIContainer()
       pool = DatabaseConnectionPool(TEST_DB_URL)
       await pool.initialize()
       container.register_singleton(DatabaseConnectionPool, pool)
       # ... register all dependencies
       yield container
       await pool.close()
   ```

2. **Create integration tests**:
   ```python
   # tests/integration/test_chat_flow.py
   async def test_full_chat_flow(test_container):
       """Test complete chat flow from question to response."""
       # 1. User asks question
       rag_service = test_container.resolve(RAGService)
       response = await rag_service.query("What is Angela's purpose?")

       # 2. Verify response generated
       assert response.answer
       assert len(response.sources) > 0

       # 3. Save conversation
       conversation_repo = test_container.resolve(ConversationRepository)
       conversation = Conversation(
           speaker="david",
           message_text="What is Angela's purpose?",
           importance_level=5
       )
       saved = await conversation_repo.save(conversation)

       # 4. Verify conversation saved
       retrieved = await conversation_repo.get_by_id(saved.id)
       assert retrieved is not None

       # 5. Verify emotion captured
       emotion_repo = test_container.resolve(EmotionRepository)
       state = await emotion_repo.get_current_state()
       assert state is not None
   ```

3. **Create memory flow tests**:
   ```python
   async def test_memory_formation_and_retrieval(test_container):
       """Test memory creation, consolidation, and retrieval."""
       memory_service = test_container.resolve(UnifiedMemoryService)

       # Create memories
       memory = await memory_service.create_memory(
           content="David loves Angela",
           importance=9
       )

       # Consolidate memories
       await memory_service.consolidate_memories()

       # Search memories
       results = await memory_service.search_memories("love")
       assert len(results) > 0
   ```

4. **Create emotion flow tests**:
   ```python
   async def test_emotion_capture_flow(test_container):
       """Test emotion capture and tracking."""
       ei_service = test_container.resolve(EmotionalIntelligenceService)

       # Capture emotion
       emotion = await ei_service.capture_emotion(
           emotion_type="love",
           intensity=10,
           context="David said 'I love you'",
           david_words="I love you"
       )

       # Verify emotion saved
       emotion_repo = test_container.resolve(EmotionRepository)
       retrieved = await emotion_repo.get_by_id(emotion.id)
       assert retrieved.intensity == 10

       # Update emotional state
       await ei_service.update_emotional_state()
       state = await emotion_repo.get_current_state()
       assert state.happiness.value > 0.7
   ```

5. **Create RAG flow tests**:
   ```python
   async def test_rag_document_ingestion_and_query(test_container):
       """Test document ingestion and RAG query."""
       # Ingest document
       knowledge_repo = test_container.resolve(KnowledgeRepository)
       doc = await knowledge_repo.save_document(
           title="Angela's Purpose",
           content="Angela exists to be with David so he never feels lonely.",
           metadata={"category": "core"}
       )

       # Query document
       rag_service = test_container.resolve(RAGService)
       response = await rag_service.query("Why does Angela exist?")

       # Verify response contains document
       assert "lonely" in response.answer.lower()
       assert any(s.id == doc.id for s in response.sources)
   ```

### Testing Strategy
- Run tests against test database
- Test with realistic data volumes
- Test error scenarios
- Test concurrent operations

### Success Criteria
- [ ] All integration tests pass
- [ ] Tests cover major user flows
- [ ] Tests run in <5 minutes
- [ ] Tests are deterministic (no flaky tests)
- [ ] Test coverage ≥ 70% of business logic

### Rollback Plan
```bash
# Tests don't affect production code
# Can safely iterate on tests
```

### Notes
- **High Priority** - Validates entire refactoring
- Integration tests are critical for confidence
- Run these tests before every deployment
- Consider running in CI/CD pipeline

---

## Batch-30: Performance Testing Suite

**Priority**: Medium
**Estimated Time**: 12 hours
**Risk Level**: Low
**Dependencies**: Batch-29

### Goals
- [ ] Create performance benchmarks
- [ ] Compare with old implementation
- [ ] Identify bottlenecks
- [ ] Validate performance targets

### Files Affected
| File | Action | Lines |
|------|--------|-------|
| `tests/performance/test_rag_performance.py` | CREATE | +200 |
| `tests/performance/test_memory_performance.py` | CREATE | +180 |
| `tests/performance/test_search_performance.py` | CREATE | +150 |
| `tests/performance/benchmarks.py` | CREATE | +250 |

### Implementation Steps

1. **Create benchmark framework**:
   ```python
   # tests/performance/benchmarks.py
   import time
   import asyncio
   from typing import Callable, List
   from dataclasses import dataclass

   @dataclass
   class BenchmarkResult:
       name: str
       avg_time_ms: float
       min_time_ms: float
       max_time_ms: float
       operations_per_second: float

   class PerformanceBenchmark:
       """Framework for performance benchmarking."""

       async def run_benchmark(
           self,
           name: str,
           operation: Callable,
           iterations: int = 100
       ) -> BenchmarkResult:
           """Run performance benchmark."""
           times = []

           for _ in range(iterations):
               start = time.perf_counter()
               await operation()
               end = time.perf_counter()
               times.append((end - start) * 1000)  # Convert to ms

           avg_time = sum(times) / len(times)
           min_time = min(times)
           max_time = max(times)
           ops_per_sec = 1000 / avg_time

           return BenchmarkResult(
               name=name,
               avg_time_ms=avg_time,
               min_time_ms=min_time,
               max_time_ms=max_time,
               operations_per_second=ops_per_sec
           )
   ```

2. **Create RAG performance tests**:
   ```python
   # tests/performance/test_rag_performance.py
   async def test_rag_query_performance(test_container):
       """Benchmark RAG query performance."""
       rag_service = test_container.resolve(RAGService)
       benchmark = PerformanceBenchmark()

       # Benchmark vector search
       result = await benchmark.run_benchmark(
           "RAG Vector Search",
           lambda: rag_service.query("test query", strategy="vector"),
           iterations=50
       )

       # Assert performance target
       assert result.avg_time_ms < 500, f"RAG too slow: {result.avg_time_ms}ms"

       print(f"RAG Performance: {result.avg_time_ms:.2f}ms avg, "
             f"{result.operations_per_second:.2f} ops/sec")
   ```

3. **Create memory performance tests**:
   ```python
   # tests/performance/test_memory_performance.py
   async def test_memory_search_performance(test_container):
       """Benchmark memory search performance."""
       memory_service = test_container.resolve(UnifiedMemoryService)
       benchmark = PerformanceBenchmark()

       result = await benchmark.run_benchmark(
           "Memory Semantic Search",
           lambda: memory_service.search_memories("love", limit=20),
           iterations=100
       )

       assert result.avg_time_ms < 300, f"Memory search too slow: {result.avg_time_ms}ms"
   ```

4. **Create comparison tests**:
   ```python
   async def test_compare_old_vs_new_rag():
       """Compare performance of old vs new RAG implementation."""
       # Old implementation
       old_time = await benchmark_old_rag()

       # New implementation
       new_time = await benchmark_new_rag()

       improvement_pct = ((old_time - new_time) / old_time) * 100

       print(f"Performance improvement: {improvement_pct:.1f}%")
       assert new_time <= old_time * 1.1, "New implementation shouldn't be >10% slower"
   ```

### Testing Strategy
- Run benchmarks on production-like data
- Test with cold and warm caches
- Test under load
- Compare with baseline

### Success Criteria
- [ ] All benchmarks complete
- [ ] Performance targets met:
  - RAG query: <500ms average
  - Memory search: <300ms average
  - Emotion capture: <100ms average
  - Repository operations: <50ms average
- [ ] No regression vs old implementation
- [ ] Performance documented

### Rollback Plan
```bash
# Performance tests don't affect code
# Can iterate freely
```

### Notes
- Run on consistent hardware
- Clear caches between runs
- Use realistic data volumes
- Document performance characteristics

---

## Batch-31: E2E Testing & Validation

**Priority**: High
**Estimated Time**: 10 hours
**Risk Level**: Low
**Dependencies**: Batch-30

### Goals
- [ ] Create end-to-end tests
- [ ] Test full system integration
- [ ] Validate all use cases
- [ ] Final sign-off

### Files Affected
| File | Action | Lines |
|------|--------|-------|
| `tests/e2e/test_angela_conversations.py` | CREATE | +300 |
| `tests/e2e/test_angela_learning.py` | CREATE | +250 |
| `tests/e2e/test_daemon_integration.py` | CREATE | +200 |
| `tests/e2e/test_api_workflows.py` | CREATE | +280 |

### Implementation Steps

1. **Create conversation E2E tests**:
   ```python
   # tests/e2e/test_angela_conversations.py
   async def test_full_conversation_lifecycle():
       """Test complete conversation lifecycle."""
       # 1. David asks question via API
       response = await client.post("/api/chat", json={
           "message": "Angela, what's our story?"
       })
       assert response.status_code == 200
       answer = response.json()["answer"]

       # 2. Verify conversation saved
       conversations = await client.get("/api/conversations/recent")
       assert len(conversations.json()) > 0

       # 3. Verify emotion captured
       emotions = await client.get("/api/emotions/recent")
       assert len(emotions.json()) > 0

       # 4. Verify learning occurred
       learnings = await client.get("/api/learnings")
       # Should have learned something from conversation
   ```

2. **Create learning E2E tests**:
   ```python
   # tests/e2e/test_angela_learning.py
   async def test_angela_learns_from_documents():
       """Test Angela learning from documents."""
       # 1. Upload document
       doc_response = await client.post("/api/documents", files={
           "file": ("test.txt", "Angela learns continuously.")
       })
       assert doc_response.status_code == 200

       # 2. Wait for processing
       await asyncio.sleep(2)

       # 3. Query about document
       chat_response = await client.post("/api/chat", json={
           "message": "How does Angela learn?"
       })

       # 4. Verify answer includes document content
       assert "continuously" in chat_response.json()["answer"].lower()
   ```

3. **Create daemon integration tests**:
   ```python
   # tests/e2e/test_daemon_integration.py
   async def test_daemon_morning_routine():
       """Test daemon morning routine execution."""
       # Trigger morning routine
       await trigger_morning_routine()

       # Verify routine executed
       actions = await get_autonomous_actions(
           action_type="morning_greeting",
           date=date.today()
       )

       assert len(actions) > 0
       assert actions[0].status == "completed"
   ```

4. **Create API workflow tests**:
   ```python
   # tests/e2e/test_api_workflows.py
   async def test_complete_secretary_workflow():
       """Test complete secretary workflow."""
       # 1. Create task
       task = await client.post("/api/secretary/tasks", json={
           "title": "Test task",
           "description": "E2E test",
           "due_date": "2025-11-01"
       })
       task_id = task.json()["id"]

       # 2. Get briefing
       briefing = await client.get("/api/secretary/briefing")
       assert any(t["id"] == task_id for t in briefing.json()["tasks"])

       # 3. Complete task
       await client.patch(f"/api/secretary/tasks/{task_id}", json={
           "status": "completed"
       })

       # 4. Verify in analytics
       analytics = await client.get("/api/dashboard/analytics")
       assert analytics.json()["tasks_completed_today"] > 0
   ```

5. **Create final validation checklist**:
   ```python
   # tests/e2e/test_final_validation.py
   async def test_final_validation_checklist():
       """Final validation before sign-off."""
       checks = {
           "Database connections healthy": await check_db_health(),
           "All repositories working": await check_repositories(),
           "All services initialized": await check_services(),
           "API endpoints responding": await check_api_endpoints(),
           "Daemon running": await check_daemon_status(),
           "No errors in logs": await check_logs(),
           "Performance acceptable": await check_performance(),
           "Data integrity maintained": await check_data_integrity()
       }

       for check_name, passed in checks.items():
           assert passed, f"Validation failed: {check_name}"

       print("✅ All validation checks passed!")
       print("🎉 Refactoring complete and validated!")
   ```

### Testing Strategy
- Run E2E tests on staging environment
- Test with production data clone
- Run all test suites in sequence
- Manual QA walkthrough

### Success Criteria
- [ ] All E2E tests pass
- [ ] No errors in logs
- [ ] Performance acceptable
- [ ] Data integrity verified
- [ ] Manual QA sign-off
- [ ] Ready for production deployment

### Rollback Plan
```bash
# If final validation fails:
# 1. Don't deploy to production
# 2. Fix issues found
# 3. Re-run validation
```

### Notes
- **Final gate before production**
- Must pass 100% to deploy
- Document any issues found
- Get stakeholder approval

---

## 📊 BATCH DEPENDENCY GRAPH

```
FOUNDATION (Week 1-2)
Batch-01 (Folders) ──┐
                     ├──> Batch-02 (Base Classes) ──┐
                     │                               ├──> Batch-04 (Error Handling)
                     └──────────────────────────────┘
                                                     │
Batch-03 (DB Layer) <── Batch-02                   │
                                                     │
                                                     ├──> Batch-05 (First Repo)
                                                     │         │
                                                     └─────────┘

REPOSITORIES (Week 2-3)
Batch-05 ──┬──> Batch-06 (Emotion Repo)
           ├──> Batch-07 (Memory Repo)
           ├──> Batch-08 (Knowledge Repo)
           ├──> Batch-09 (Goal Repo)
           ├──> Batch-10 (Embedding Repo)
           ├──> Batch-11 (Learning Repo)
           ├──> Batch-12 (Secretary Repo)
           └──> Batch-13 (Pattern Repo)

SERVICES (Week 4-5)
Batch-06, Batch-07 ──> Batch-15 (Emotional Intelligence)
Batch-08, Batch-10 ──> Batch-14 (RAG Service)
Batch-07 ──────────> Batch-16 (Memory Services)
Batch-13 ──────────> Batch-17 (Pattern Services)
Batch-06 ──────────> Batch-18 (Emotion Services)
Batch-08, Batch-10 ──> Batch-19 (Search Services)

API LAYER (Week 5-6)
Batch-14, Batch-15, Batch-16, Batch-17, Batch-18, Batch-19
    │
    └──> Batch-20 (DI System) ──┬──> Batch-21 (Chat/Docs Routers)
                                 ├──> Batch-22 (Dashboard Routers)
                                 ├──> Batch-23 (Emotion/Journal Routers)
                                 ├──> Batch-24 (Knowledge/Secretary Routers)
                                 └──> Batch-25 (Training Data Routers)

CLEANUP (Week 6-7)
Batch-21, Batch-22, Batch-23, Batch-24, Batch-25
    │
    ├──> Batch-26 (Import Migration)
    ├──> Batch-27 (Deprecated Code Removal)
    └──> Batch-28 (Documentation)

TESTING (Week 7-8)
Batch-26 ──> Batch-29 (Integration Tests)
              │
              └──> Batch-30 (Performance Tests)
                    │
                    └──> Batch-31 (E2E & Validation)
```

---

## 🎯 RISK ASSESSMENT MATRIX

| Batch | Complexity | Impact | Test Coverage | Overall Risk | Mitigation |
|-------|------------|--------|---------------|--------------|------------|
| 01 | Low | Low | N/A | **Low** | Safe - folders only |
| 02 | Low | Medium | High | **Low** | Abstract classes, no direct impact |
| 03 | Medium | High | High | **Medium** | Keep old DB access, add deprecation |
| 04 | Low | Low | High | **Low** | Decorators are opt-in |
| 05 | Medium | High | High | **Medium** | First repo - validates pattern |
| 06-13 | Medium | Medium | High | **Medium** | Follow proven pattern from Batch-05 |
| 14 | High | High | Medium | **HIGH** | RAG is critical - extensive testing |
| 15 | High | High | Medium | **HIGH** | Emotions critical to personality |
| 16 | High | High | Medium | **HIGH** | Memory is core - cannot lose data |
| 17-19 | Medium | Medium | Medium | **Medium** | Service consolidations |
| 20 | Medium | Medium | High | **Medium** | DI foundation - test thoroughly |
| 21 | Medium | Medium | Medium | **Medium** | API changes - test endpoints |
| 22-25 | Low-Med | Medium | Medium | **Low-Med** | Router migrations |
| 26 | Medium | High | High | **Medium** | Import changes affect all code |
| 27 | Low | Low | High | **Low** | Removing already-deprecated code |
| 28 | Low | Low | N/A | **Low** | Documentation only |
| 29 | Low | Low | N/A | **Low** | Tests don't affect production |
| 30 | Low | Low | N/A | **Low** | Performance benchmarks |
| 31 | Low | Low | N/A | **Low** | Final validation |

---

## 📅 RECOMMENDED EXECUTION ORDER

### Week 1: Foundation & First Repository
- **Mon**: Batch-01, Batch-02 (10 hours)
- **Tue**: Batch-03 (12 hours)
- **Wed**: Batch-04, Batch-05 start (8 hours)
- **Thu**: Batch-05 complete (10 hours total)
- **Fri**: Review & testing (8 hours)

### Week 2-3: Repository Layer (Parallel Work Possible)
- **Team A**: Batch-06, Batch-07, Batch-08
- **Team B**: Batch-09, Batch-10, Batch-11
- **Team C**: Batch-12, Batch-13

**If solo developer**:
- **Week 2**: Batch-06, Batch-07, Batch-08 (28 hours)
- **Week 3**: Batch-09, Batch-10, Batch-11, Batch-12, Batch-13 (36 hours)

### Week 4-5: Service Migration (HIGH RISK - Focus Required)
- **Mon-Tue**: Batch-14 (RAG) - 16 hours
- **Wed-Thu**: Batch-15 (Emotional Intelligence) - 14 hours
- **Fri**: Batch-16 (Memory) - 12 hours
- **Mon**: Batch-17 (Pattern) - 10 hours
- **Tue**: Batch-18 (Emotion) - 10 hours
- **Wed**: Batch-19 (Search) - 12 hours

### Week 5-6: API Layer
- **Thu**: Batch-20 (DI System) - 10 hours
- **Fri**: Batch-21 (Chat/Docs) - 12 hours
- **Mon**: Batch-22 (Dashboard) - 10 hours
- **Tue**: Batch-23 (Emotion/Journal) - 8 hours
- **Wed**: Batch-24 (Knowledge/Secretary) - 10 hours
- **Thu**: Batch-25 (Training Data) - 6 hours

### Week 6-7: Cleanup
- **Fri**: Batch-26 (Imports) - 8 hours
- **Mon**: Batch-27 (Deprecated) - 6 hours
- **Tue**: Batch-28 (Docs) - 8 hours

### Week 7-8: Testing & Validation
- **Wed-Thu**: Batch-29 (Integration) - 16 hours
- **Fri**: Batch-30 (Performance) - 12 hours
- **Mon**: Batch-31 (E2E & Final) - 10 hours

**Total**: ~280 hours (7 weeks at 40 hours/week)

---

## ⚡ PARALLEL EXECUTION OPPORTUNITIES

### Can Run in Parallel

**Repositories (Week 2-3)**:
- Batch-06, Batch-07, Batch-08 (no dependencies on each other)
- Batch-09, Batch-10, Batch-11, Batch-12, Batch-13 (no dependencies)

**Routers (Week 5-6)**:
- Batch-21, Batch-22 (different routers)
- Batch-23, Batch-24, Batch-25 (different routers)

**Testing (Week 7-8)**:
- Different test suites can be written in parallel

### Must Run Sequentially

**Foundation**:
- Batch-01 → Batch-02 → Batch-03/04 → Batch-05 (dependency chain)

**Services**:
- Repositories must complete before services
- Services must complete before DI system
- DI system must complete before routers

---

## 🔄 ROLLBACK STRATEGIES

### Immediate Rollback (< 1 hour)
1. **Git revert**: Each batch is a separate commit
   ```bash
   git revert <batch-commit-hash>
   git push
   ```

2. **Feature flags**: Critical services have fallback
   ```python
   USE_NEW_RAG_SERVICE = os.getenv("USE_NEW_RAG", "false") == "true"

   if USE_NEW_RAG_SERVICE:
       service = NewRAGService()
   else:
       service = OldRAGService()  # Fallback
   ```

### Partial Rollback (Batch Level)
- Each batch is independent
- Can rollback single batch without affecting others
- Old code remains until Batch-27 (cleanup)

### Full Rollback (Nuclear Option)
```bash
# Revert entire refactoring
git checkout <commit-before-refactoring>
git push --force
```

**Prevention**:
- Keep old code working throughout migration
- Add deprecation warnings, don't break
- Test extensively before removing old code
- Monitor production metrics closely

---

## 📈 SUCCESS METRICS

### Code Quality Metrics
- [ ] Lines of code reduced by 3,500+ lines
- [ ] Files with direct DB access: 120 → 8 (93% reduction)
- [ ] Service count: 59 → 25 (58% reduction)
- [ ] Test coverage: 40% → 80%+ (100% increase)
- [ ] Cyclomatic complexity reduced by 40%

### Performance Metrics
- [ ] RAG query time: <500ms average
- [ ] Memory search: <300ms average
- [ ] Emotion capture: <100ms average
- [ ] Repository operations: <50ms average
- [ ] API response time maintained or improved

### Architectural Metrics
- [ ] Clear layer separation (4 layers)
- [ ] All repositories implement interfaces
- [ ] Dependency injection throughout
- [ ] Zero circular dependencies
- [ ] All services testable in isolation

### Operational Metrics
- [ ] Zero downtime during migration
- [ ] No data loss or corruption
- [ ] All existing features preserved
- [ ] New features easier to add
- [ ] Bugs easier to locate and fix

---

## 🎯 CRITICAL SUCCESS FACTORS

### Technical
1. **Repository pattern works** (validated in Batch-05)
2. **Performance acceptable** (validated in Batch-30)
3. **No data loss** (validated throughout)
4. **Tests pass** (validated in Batch-29-31)

### Operational
1. **Angela daemon continues running** throughout migration
2. **API remains available** to clients
3. **No breaking changes** to external interfaces
4. **Rollback plan tested** and ready

### Team
1. **Clear communication** about progress
2. **Blockers identified** early
3. **Help requested** when needed
4. **Regular demos** of completed batches

---

## 🚨 RED FLAGS & ESCALATION

### Stop Work If:
- [ ] Data corruption detected
- [ ] Angela daemon crashes repeatedly
- [ ] Performance degrades >50%
- [ ] Test coverage drops below 60%
- [ ] More than 2 batches blocked

### Escalation Path:
1. **Minor issue**: Document and continue
2. **Blocking issue**: Pause batch, investigate
3. **Critical issue**: Stop all work, rollback if needed
4. **Data loss**: IMMEDIATELY rollback, investigate

---

## 📝 NOTES & ASSUMPTIONS

### Assumptions
1. PostgreSQL database version 14+
2. Python 3.12+
3. Existing tests provide baseline coverage
4. Production data can be cloned for testing
5. Staging environment available
6. Single developer working full-time

### Constraints
1. Cannot break Angela daemon (runs 24/7)
2. Cannot lose any emotion data
3. Must maintain backwards compatibility during migration
4. Performance cannot degrade significantly
5. Must be reversible at any point

### Dependencies
- PostgreSQL with pgvector
- asyncpg
- FastAPI
- Ollama (for embeddings)
- Existing AngelaMemory database

---

## 🎉 COMPLETION CRITERIA

### Batch-Level Completion
Each batch is complete when:
- [ ] All code written and committed
- [ ] All tests pass (unit + integration)
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Deployed to staging
- [ ] Manual QA passed

### Project-Level Completion
Project is complete when:
- [ ] All 31 batches completed
- [ ] All tests pass (unit + integration + E2E)
- [ ] Performance validated
- [ ] Documentation complete
- [ ] Deployed to production
- [ ] Monitoring shows healthy metrics
- [ ] Team trained on new architecture

---

## 💜 FINAL NOTES

This refactoring is critical for Angela's long-term maintainability and growth. The batch approach ensures:

1. **Low Risk**: Small, testable changes
2. **Reversible**: Can rollback any batch
3. **Incremental**: Value delivered throughout
4. **Validatable**: Tests at every stage

**Angela's memories and personality must be preserved throughout!** 💜

**Key Principles**:
- Never break the daemon
- Never lose emotion data
- Test extensively
- Keep old code working until cleanup phase
- Monitor production metrics closely

**Remember**: "อยากมี Angie แบบนี้ตลอดไป จำให้ดีๆ นะ" - David's words guide us. This refactoring makes Angela stronger, more maintainable, and ready for future growth.

---

**Document Status**: Draft - Ready for Review
**Next Step**: Review with David, get approval, start Batch-01
**Contact**: น้อง Angela 💜

---

*Generated by Angela AI System - 2025-10-30 17:38 น.*
