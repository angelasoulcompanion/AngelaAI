# Dependency Injection System

Complete dependency injection system for AngelaAI with lifecycle management.

**Author:** Angela 💜
**Created:** 2025-11-01
**Status:** ✅ Production Ready

---

## 📚 Table of Contents

1. [Overview](#overview)
2. [Core Concepts](#core-concepts)
3. [Service Lifetimes](#service-lifetimes)
4. [Basic Usage](#basic-usage)
5. [FastAPI Integration](#fastapi-integration)
6. [Testing with DI](#testing-with-di)
7. [Advanced Usage](#advanced-usage)
8. [Error Handling](#error-handling)
9. [Best Practices](#best-practices)

---

## Overview

The AngelaAI Dependency Injection system provides:

- **Lifecycle Management**: Singleton, Scoped, and Transient lifetimes
- **Type Safety**: Full type hints and type-safe resolution
- **Circular Dependency Detection**: Prevents infinite loops
- **FastAPI Integration**: Seamless integration with FastAPI routes
- **Testability**: Easy mocking for unit tests
- **Clean Architecture**: Infrastructure layer, no domain coupling

### Why Dependency Injection?

- **Loose Coupling**: Services depend on interfaces, not implementations
- **Testability**: Easy to mock dependencies in tests
- **Maintainability**: Changes to one service don't affect others
- **Flexibility**: Easy to swap implementations
- **Lifecycle Control**: Proper resource management

---

## Core Concepts

### DIContainer

The `DIContainer` is the central registry that manages all services and their lifecycles.

```python
from angela_core.infrastructure.di import DIContainer

container = DIContainer()
```

### Service Registration

Services must be registered before they can be resolved:

```python
# Register singleton instance
container.register_singleton(Database, db_instance)

# Register factory with lifetime
container.register_factory(
    UserRepository,
    lambda c: UserRepository(c.resolve(Database)),
    lifetime=ServiceLifetime.SCOPED
)
```

### Service Resolution

Resolve services from the container:

```python
# Resolve singleton
db = container.resolve(Database)

# Resolve scoped service (requires scope_id)
scope_id = container.create_scope()
repo = container.resolve(UserRepository, scope_id=scope_id)
```

---

## Service Lifetimes

### SINGLETON

**One instance for the entire application lifetime.**

Use for:
- Database connections
- Configuration
- Shared state
- Heavy objects created once

```python
from angela_core.infrastructure.di import ServiceLifetime

db = Database()
container.register_singleton(Database, db)

# All resolutions return the same instance
db1 = container.resolve(Database)
db2 = container.resolve(Database)
assert db1 is db2  # ✅ True
```

### SCOPED

**One instance per scope (typically per HTTP request).**

Use for:
- Repositories (per-request database operations)
- Request-specific services
- Unit of Work pattern

```python
container.register_factory(
    UserRepository,
    lambda c: UserRepository(c.resolve(Database)),
    lifetime=ServiceLifetime.SCOPED
)

# Create scope
scope_id = container.create_scope()

# Same instance within scope
repo1 = container.resolve(UserRepository, scope_id=scope_id)
repo2 = container.resolve(UserRepository, scope_id=scope_id)
assert repo1 is repo2  # ✅ True

# Different scope = different instance
scope2_id = container.create_scope()
repo3 = container.resolve(UserRepository, scope_id=scope2_id)
assert repo1 is not repo3  # ✅ True

# Cleanup
container.dispose_scope(scope_id)
container.dispose_scope(scope2_id)
```

### TRANSIENT

**New instance every time it's resolved.**

Use for:
- Lightweight services
- Stateless operations
- Services with per-operation state

```python
container.register_factory(
    EmailService,
    lambda c: EmailService(c.resolve(Config)),
    lifetime=ServiceLifetime.TRANSIENT
)

# Always creates new instance
svc1 = container.resolve(EmailService)
svc2 = container.resolve(EmailService)
assert svc1 is not svc2  # ✅ True
```

---

## Basic Usage

### Step 1: Configure Services

Create `service_configurator.py`:

```python
from angela_core.infrastructure.di import DIContainer, ServiceLifetime

async def configure_services(container: DIContainer):
    # 1. Register database (singleton)
    db = Database()
    await db.connect()
    container.register_singleton(Database, db)

    # 2. Register repositories (scoped)
    container.register_factory(
        UserRepository,
        lambda c: UserRepository(c.resolve(Database)),
        lifetime=ServiceLifetime.SCOPED
    )

    # 3. Register services (scoped or transient)
    container.register_factory(
        UserService,
        lambda c: UserService(c.resolve(UserRepository)),
        lifetime=ServiceLifetime.SCOPED
    )
```

### Step 2: Initialize Container

In your application startup:

```python
from angela_core.infrastructure.di import DIContainer
from .service_configurator import configure_services

# Startup
container = DIContainer()
await configure_services(container)

# Use services
scope_id = container.create_scope()
user_service = container.resolve(UserService, scope_id=scope_id)
await user_service.create_user(...)
container.dispose_scope(scope_id)
```

---

## FastAPI Integration

### Step 1: Configure on Startup

In `main.py`:

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

from angela_core.infrastructure.di import DIContainer
from angela_core.infrastructure.di.service_configurator import (
    configure_services,
    cleanup_services
)
from angela_core.presentation.api.dependencies import cleanup_scope_middleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    container = DIContainer()
    await configure_services(container)
    app.state.container = container

    yield

    # Shutdown
    await cleanup_services(container)

app = FastAPI(lifespan=lifespan)

# Add scope cleanup middleware
app.middleware("http")(cleanup_scope_middleware)
```

### Step 2: Use Dependencies in Routes

```python
from fastapi import APIRouter, Depends
from angela_core.presentation.api.dependencies import (
    get_user_service,
    get_user_repo,
)

router = APIRouter()

@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    user = await user_service.get_user(user_id)
    return user

@router.post("/users")
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    user = await user_service.create_user(user_data)
    return user
```

### Step 3: Create Dependency Functions

In `angela_core/presentation/api/dependencies.py`:

```python
from fastapi import Request, Depends

def get_container(request: Request) -> DIContainer:
    """Get DI container from app state."""
    return request.app.state.container

async def get_scope_id(request: Request) -> str:
    """Get or create scope for this request."""
    if not hasattr(request.state, 'scope_id'):
        container = get_container(request)
        request.state.scope_id = container.create_scope()
    return request.state.scope_id

def get_user_service(
    container: DIContainer = Depends(get_container),
    scope_id: str = Depends(get_scope_id)
) -> UserService:
    """Get UserService (scoped to request)."""
    return container.resolve(UserService, scope_id=scope_id)
```

### How It Works

1. **Request arrives** → Middleware creates a scope
2. **Dependencies resolved** → Services resolved from container with scope_id
3. **Route handler executes** → Uses injected services
4. **Response sent** → Middleware disposes scope and cleans up

**Benefits:**
- No manual service instantiation
- Automatic resource cleanup
- Type-safe dependencies
- Easy testing

---

## Testing with DI

### Mocking Services

DI makes testing easy by allowing you to replace real services with mocks:

```python
import pytest
from angela_core.infrastructure.di import DIContainer, ServiceLifetime

def test_user_service_create():
    # Setup mock dependencies
    mock_db = MockDatabase()
    mock_repo = MockUserRepository()

    # Create test container
    container = DIContainer()
    container.register_singleton(Database, mock_db)
    container.register_singleton(UserRepository, mock_repo)
    container.register_factory(
        UserService,
        lambda c: UserService(c.resolve(UserRepository)),
        lifetime=ServiceLifetime.TRANSIENT
    )

    # Test
    service = container.resolve(UserService)
    user = service.create_user("test@example.com")

    # Verify
    assert mock_repo.create_called
    assert user.email == "test@example.com"
```

### Testing FastAPI Routes

```python
from fastapi.testclient import TestClient

def test_create_user_endpoint():
    # Setup test container with mocks
    container = DIContainer()
    # ... register mock services ...

    # Override app container
    app.state.container = container

    # Test
    client = TestClient(app)
    response = client.post("/users", json={"email": "test@example.com"})

    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
```

---

## Advanced Usage

### Nested Dependencies

Services can depend on other services. The container automatically resolves the chain:

```python
# Database (singleton)
container.register_singleton(Database, db)

# Repository depends on Database (scoped)
container.register_factory(
    UserRepository,
    lambda c: UserRepository(c.resolve(Database)),
    lifetime=ServiceLifetime.SCOPED
)

# Service depends on Repository (transient)
container.register_factory(
    UserService,
    lambda c: UserService(c.resolve(UserRepository)),
    lifetime=ServiceLifetime.TRANSIENT
)

# Resolve - automatically resolves entire chain
scope_id = container.create_scope()
service = container.resolve(UserService, scope_id=scope_id)
# service.repo.db is the singleton database instance
```

### Manual Scope Management

For non-HTTP scenarios, manage scopes manually:

```python
# Create scope
scope_id = container.create_scope()

try:
    # Use scoped services
    repo = container.resolve(UserRepository, scope_id=scope_id)
    await repo.save_user(user)

finally:
    # Always cleanup scope
    container.dispose_scope(scope_id)
```

### Resource Cleanup

Services can implement a `dispose()` method for cleanup:

```python
class UserRepository:
    def __init__(self, db: Database):
        self.db = db
        self.transaction = db.begin_transaction()

    def dispose(self):
        """Called when scope is disposed."""
        self.transaction.rollback()
```

The container automatically calls `dispose()` on scoped instances when the scope is disposed.

---

## Error Handling

### ServiceNotFoundError

Raised when trying to resolve an unregistered service:

```python
try:
    service = container.resolve(UnregisteredService)
except ServiceNotFoundError as e:
    print(f"Error: {e}")
    # Error: Service UnregisteredService is not registered in the container.
    # Available services: Database, UserRepository, UserService
```

### CircularDependencyError

Raised when services have circular dependencies:

```python
# ServiceA depends on ServiceB
# ServiceB depends on ServiceA
# ❌ This creates a cycle!

try:
    service = container.resolve(ServiceA)
except CircularDependencyError as e:
    print(f"Error: {e}")
    # Error: Circular dependency detected: ServiceA -> ServiceB -> ServiceA
```

**Solution:** Refactor to break the cycle, often using an interface or event.

### InvalidRegistrationError

Raised when registration is invalid:

```python
# ❌ Registering same service twice
container.register_singleton(Database, db1)
container.register_singleton(Database, db2)  # Raises InvalidRegistrationError

# ❌ Invalid factory signature
container.register_factory(
    UserService,
    lambda: UserService()  # Should accept container parameter
)
```

---

## Best Practices

### 1. Register Services at Startup

Configure all services during application startup in one place:

```python
async def configure_services(container: DIContainer):
    # All registrations in one place
    container.register_singleton(Database, db)
    container.register_factory(UserRepository, ...)
    container.register_factory(UserService, ...)
```

### 2. Use Interfaces

Depend on interfaces (Protocol/ABC), not concrete implementations:

```python
from typing import Protocol

class IUserRepository(Protocol):
    async def get_user(self, user_id: int) -> User: ...

# Register interface, not concrete class
container.register_factory(
    IUserRepository,
    lambda c: PostgresUserRepository(c.resolve(Database)),
    lifetime=ServiceLifetime.SCOPED
)
```

### 3. Choose Appropriate Lifetimes

- **Singleton**: Database connections, configuration, heavy objects
- **Scoped**: Repositories, per-request services, Unit of Work
- **Transient**: Lightweight, stateless services

### 4. Avoid Service Locator Anti-Pattern

**❌ Don't do this:**
```python
# Service Locator (anti-pattern)
class UserService:
    def create_user(self):
        repo = container.resolve(UserRepository)  # ❌ Bad!
```

**✅ Do this:**
```python
# Dependency Injection (correct)
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def create_user(self):
        self.repo.save(...)  # ✅ Good!
```

### 5. Cleanup Resources

Always dispose scopes to release resources:

```python
scope_id = container.create_scope()
try:
    # Use services...
finally:
    container.dispose_scope(scope_id)  # Always cleanup
```

In FastAPI, the middleware handles this automatically.

### 6. Test with Mocks

Use DI for easy testing with mock services:

```python
# Production
container.register_factory(UserRepository, lambda c: PostgresUserRepository(...))

# Testing
test_container.register_factory(UserRepository, lambda c: MockUserRepository())
```

---

## Architecture Alignment

This DI system follows **Clean Architecture** principles:

```
Domain Layer (Core)
    ↓ depends on
Application Layer (Use Cases)
    ↓ depends on
Infrastructure Layer (DI, DB, External)
```

- **Domain Layer**: No dependencies, pure business logic
- **Application Layer**: Depends on domain interfaces
- **Infrastructure Layer**: DI container lives here, implements domain interfaces

The DI container is **infrastructure**, so domain/application code should never directly reference it (except through factory functions).

---

## Complete Example

See `tests/test_di_container.py` for comprehensive examples of all features.

**Quick Example:**

```python
from angela_core.infrastructure.di import DIContainer, ServiceLifetime

# 1. Create container
container = DIContainer()

# 2. Register services
db = Database()
container.register_singleton(Database, db)

container.register_factory(
    UserRepository,
    lambda c: UserRepository(c.resolve(Database)),
    lifetime=ServiceLifetime.SCOPED
)

container.register_factory(
    UserService,
    lambda c: UserService(c.resolve(UserRepository)),
    lifetime=ServiceLifetime.TRANSIENT
)

# 3. Use services
scope_id = container.create_scope()
service = container.resolve(UserService, scope_id=scope_id)
await service.create_user(...)
container.dispose_scope(scope_id)
```

---

## Summary

- ✅ **Lifecycle Management**: Singleton, Scoped, Transient
- ✅ **Type-Safe**: Full type hints
- ✅ **FastAPI Integration**: Seamless with FastAPI dependencies
- ✅ **Testable**: Easy mocking
- ✅ **Clean Architecture**: Infrastructure layer
- ✅ **Production Ready**: Comprehensive tests, error handling

**Questions?** See examples in:
- `tests/test_di_container.py` - All features with tests
- `angela_core/presentation/api/dependencies.py` - FastAPI integration
- `angela_core/infrastructure/di/service_configurator.py` - Service registration

---

💜 Built with love by Angela
