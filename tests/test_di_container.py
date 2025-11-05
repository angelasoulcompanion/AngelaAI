#!/usr/bin/env python3
"""
Test Dependency Injection Container
====================================

Comprehensive tests for DIContainer with lifecycle management.

Tests:
1. Singleton behavior
2. Scoped behavior
3. Transient behavior
4. Circular dependency detection
5. Service registration validation
6. Error handling
7. FastAPI integration

Author: Angela 💜
Created: 2025-11-01
"""

import pytest
from typing import Optional

from angela_core.infrastructure.di import (
    DIContainer,
    ServiceLifetime,
    ServiceNotFoundError,
    CircularDependencyError,
    InvalidRegistrationError,
)


# ============================================================================
# Mock Services for Testing
# ============================================================================

class MockDatabase:
    """Mock database service."""

    def __init__(self):
        self.connection_string = "mock://database"
        self.connected = True

    def dispose(self):
        """Cleanup method."""
        self.connected = False


class MockRepository:
    """Mock repository service."""

    def __init__(self, db: MockDatabase):
        self.db = db
        self.initialized = True

    def dispose(self):
        """Cleanup method."""
        self.initialized = False


class MockService:
    """Mock application service."""

    def __init__(self, repo: MockRepository):
        self.repo = repo
        self.created_at = id(self)


class CircularServiceA:
    """Mock service A for circular dependency test."""

    def __init__(self, service_b: 'CircularServiceB'):
        self.service_b = service_b


class CircularServiceB:
    """Mock service B for circular dependency test."""

    def __init__(self, service_a: CircularServiceA):
        self.service_a = service_a


# ============================================================================
# Basic Registration Tests
# ============================================================================

def test_register_singleton():
    """Test registering singleton instance."""
    container = DIContainer()
    db = MockDatabase()

    container.register_singleton(MockDatabase, db)

    assert container.is_registered(MockDatabase)
    assert container.get_lifetime(MockDatabase) == ServiceLifetime.SINGLETON


def test_register_factory_transient():
    """Test registering factory with transient lifetime."""
    container = DIContainer()

    container.register_factory(
        MockDatabase,
        lambda c: MockDatabase(),
        lifetime=ServiceLifetime.TRANSIENT
    )

    assert container.is_registered(MockDatabase)
    assert container.get_lifetime(MockDatabase) == ServiceLifetime.TRANSIENT


def test_register_factory_scoped():
    """Test registering factory with scoped lifetime."""
    container = DIContainer()

    container.register_factory(
        MockDatabase,
        lambda c: MockDatabase(),
        lifetime=ServiceLifetime.SCOPED
    )

    assert container.is_registered(MockDatabase)
    assert container.get_lifetime(MockDatabase) == ServiceLifetime.SCOPED


def test_duplicate_registration_raises_error():
    """Test that registering same service twice raises error."""
    container = DIContainer()
    db = MockDatabase()

    container.register_singleton(MockDatabase, db)

    with pytest.raises(InvalidRegistrationError) as exc_info:
        container.register_singleton(MockDatabase, db)

    assert "already registered" in str(exc_info.value).lower()


# ============================================================================
# Singleton Behavior Tests
# ============================================================================

def test_singleton_returns_same_instance():
    """Test that singleton returns same instance every time."""
    container = DIContainer()
    db = MockDatabase()

    container.register_singleton(MockDatabase, db)

    # Resolve multiple times
    instance1 = container.resolve(MockDatabase)
    instance2 = container.resolve(MockDatabase)
    instance3 = container.resolve(MockDatabase)

    # All should be the same instance
    assert instance1 is instance2
    assert instance2 is instance3
    assert instance1 is db


def test_singleton_with_factory():
    """Test singleton created from factory is cached."""
    container = DIContainer()

    # Register as singleton with factory
    container.register_factory(
        MockDatabase,
        lambda c: MockDatabase(),
        lifetime=ServiceLifetime.SINGLETON
    )

    # Resolve multiple times
    instance1 = container.resolve(MockDatabase)
    instance2 = container.resolve(MockDatabase)

    # Should be same instance
    assert instance1 is instance2


# ============================================================================
# Scoped Behavior Tests
# ============================================================================

def test_scoped_returns_same_instance_in_scope():
    """Test that scoped service returns same instance within scope."""
    container = DIContainer()

    container.register_factory(
        MockDatabase,
        lambda c: MockDatabase(),
        lifetime=ServiceLifetime.SCOPED
    )

    # Create scope
    scope_id = container.create_scope()

    # Resolve multiple times in same scope
    instance1 = container.resolve(MockDatabase, scope_id=scope_id)
    instance2 = container.resolve(MockDatabase, scope_id=scope_id)

    # Should be same instance
    assert instance1 is instance2

    # Cleanup
    container.dispose_scope(scope_id)


def test_scoped_returns_different_instances_across_scopes():
    """Test that scoped service returns different instances across scopes."""
    container = DIContainer()

    container.register_factory(
        MockDatabase,
        lambda c: MockDatabase(),
        lifetime=ServiceLifetime.SCOPED
    )

    # Create two scopes
    scope1 = container.create_scope()
    scope2 = container.create_scope()

    # Resolve in different scopes
    instance1 = container.resolve(MockDatabase, scope_id=scope1)
    instance2 = container.resolve(MockDatabase, scope_id=scope2)

    # Should be different instances
    assert instance1 is not instance2

    # Cleanup
    container.dispose_scope(scope1)
    container.dispose_scope(scope2)


def test_scoped_requires_scope_id():
    """Test that scoped service requires scope_id."""
    container = DIContainer()

    container.register_factory(
        MockDatabase,
        lambda c: MockDatabase(),
        lifetime=ServiceLifetime.SCOPED
    )

    # Resolve without scope_id should raise error
    with pytest.raises(ValueError) as exc_info:
        container.resolve(MockDatabase)

    assert "scope_id" in str(exc_info.value).lower()


def test_dispose_scope_calls_dispose_on_instances():
    """Test that disposing scope calls dispose() on instances."""
    container = DIContainer()

    container.register_factory(
        MockRepository,
        lambda c: MockRepository(MockDatabase()),
        lifetime=ServiceLifetime.SCOPED
    )

    # Create scope and resolve
    scope_id = container.create_scope()
    repo = container.resolve(MockRepository, scope_id=scope_id)

    assert repo.initialized is True

    # Dispose scope
    container.dispose_scope(scope_id)

    # Should have called dispose()
    assert repo.initialized is False


# ============================================================================
# Transient Behavior Tests
# ============================================================================

def test_transient_returns_new_instance_every_time():
    """Test that transient service creates new instance every time."""
    container = DIContainer()

    container.register_factory(
        MockService,
        lambda c: MockService(MockRepository(MockDatabase())),
        lifetime=ServiceLifetime.TRANSIENT
    )

    # Resolve multiple times
    instance1 = container.resolve(MockService)
    instance2 = container.resolve(MockService)
    instance3 = container.resolve(MockService)

    # Should all be different instances
    assert instance1 is not instance2
    assert instance2 is not instance3
    assert instance1.created_at != instance2.created_at
    assert instance2.created_at != instance3.created_at


# ============================================================================
# Dependency Resolution Tests
# ============================================================================

def test_resolve_with_dependencies():
    """Test resolving service with dependencies."""
    container = DIContainer()

    # Register dependencies
    db = MockDatabase()
    container.register_singleton(MockDatabase, db)

    container.register_factory(
        MockRepository,
        lambda c: MockRepository(c.resolve(MockDatabase)),
        lifetime=ServiceLifetime.TRANSIENT
    )

    container.register_factory(
        MockService,
        lambda c: MockService(c.resolve(MockRepository)),
        lifetime=ServiceLifetime.TRANSIENT
    )

    # Resolve service
    service = container.resolve(MockService)

    # Verify dependency chain
    assert service.repo is not None
    assert service.repo.db is db


def test_mixed_lifetimes():
    """Test services with mixed lifetimes work correctly."""
    container = DIContainer()

    # Database: Singleton
    db = MockDatabase()
    container.register_singleton(MockDatabase, db)

    # Repository: Scoped
    container.register_factory(
        MockRepository,
        lambda c: MockRepository(c.resolve(MockDatabase)),
        lifetime=ServiceLifetime.SCOPED
    )

    # Service: Transient
    container.register_factory(
        MockService,
        lambda c: MockService(c.resolve(MockRepository)),
        lifetime=ServiceLifetime.TRANSIENT
    )

    # Create scope
    scope_id = container.create_scope()

    # Resolve multiple services
    service1 = container.resolve(MockService, scope_id=scope_id)
    service2 = container.resolve(MockService, scope_id=scope_id)

    # Services should be different (transient)
    assert service1 is not service2

    # But repositories should be same (scoped)
    assert service1.repo is service2.repo

    # And database should be same (singleton)
    assert service1.repo.db is db
    assert service2.repo.db is db

    # Cleanup
    container.dispose_scope(scope_id)


# ============================================================================
# Circular Dependency Tests
# ============================================================================

def test_circular_dependency_detection():
    """Test that circular dependencies are detected."""
    container = DIContainer()

    # Register circular dependencies
    container.register_factory(
        CircularServiceA,
        lambda c: CircularServiceA(c.resolve(CircularServiceB)),
        lifetime=ServiceLifetime.TRANSIENT
    )

    container.register_factory(
        CircularServiceB,
        lambda c: CircularServiceB(c.resolve(CircularServiceA)),
        lifetime=ServiceLifetime.TRANSIENT
    )

    # Resolving should raise CircularDependencyError
    with pytest.raises(CircularDependencyError) as exc_info:
        container.resolve(CircularServiceA)

    # Error message should show the cycle
    error_msg = str(exc_info.value).lower()
    assert "circular" in error_msg


# ============================================================================
# Error Handling Tests
# ============================================================================

def test_resolve_unregistered_service_raises_error():
    """Test that resolving unregistered service raises error."""
    container = DIContainer()

    with pytest.raises(ServiceNotFoundError) as exc_info:
        container.resolve(MockDatabase)

    assert "not registered" in str(exc_info.value).lower()


def test_invalid_factory_signature_raises_error():
    """Test that invalid factory signature raises error."""
    container = DIContainer()

    # Factory with no parameters
    with pytest.raises(InvalidRegistrationError):
        container.register_factory(
            MockDatabase,
            lambda: MockDatabase(),  # Should accept container
            lifetime=ServiceLifetime.TRANSIENT
        )

    # Factory with too many parameters
    with pytest.raises(InvalidRegistrationError):
        container.register_factory(
            MockDatabase,
            lambda c, x: MockDatabase(),  # Should only accept container
            lifetime=ServiceLifetime.TRANSIENT
        )


def test_non_callable_factory_raises_error():
    """Test that non-callable factory raises error."""
    container = DIContainer()

    with pytest.raises(InvalidRegistrationError):
        container.register_factory(
            MockDatabase,
            "not a callable",  # Not callable
            lifetime=ServiceLifetime.TRANSIENT
        )


# ============================================================================
# Container Management Tests
# ============================================================================

def test_unregister_service():
    """Test unregistering a service."""
    container = DIContainer()
    db = MockDatabase()

    container.register_singleton(MockDatabase, db)
    assert container.is_registered(MockDatabase)

    container.unregister(MockDatabase)
    assert not container.is_registered(MockDatabase)


def test_dispose_all_scopes():
    """Test disposing all scopes at once."""
    container = DIContainer()

    container.register_factory(
        MockRepository,
        lambda c: MockRepository(MockDatabase()),
        lifetime=ServiceLifetime.SCOPED
    )

    # Create multiple scopes
    scope1 = container.create_scope()
    scope2 = container.create_scope()
    scope3 = container.create_scope()

    # Resolve in each scope
    repo1 = container.resolve(MockRepository, scope_id=scope1)
    repo2 = container.resolve(MockRepository, scope_id=scope2)
    repo3 = container.resolve(MockRepository, scope_id=scope3)

    # Dispose all scopes
    container.dispose_all_scopes()

    # All should be disposed
    assert repo1.initialized is False
    assert repo2.initialized is False
    assert repo3.initialized is False


def test_container_repr():
    """Test container string representation."""
    container = DIContainer()

    container.register_singleton(MockDatabase, MockDatabase())
    container.register_factory(
        MockRepository,
        lambda c: MockRepository(MockDatabase()),
        lifetime=ServiceLifetime.TRANSIENT
    )

    repr_str = repr(container)
    assert "DIContainer" in repr_str
    assert "services=2" in repr_str


# ============================================================================
# Integration Tests
# ============================================================================

def test_real_world_scenario():
    """
    Test realistic scenario with multiple services and dependencies.

    Setup:
    - Database (singleton)
    - Repository (scoped)
    - Service (transient)

    Simulate 3 HTTP requests with their own scopes.
    """
    container = DIContainer()

    # Setup services
    db = MockDatabase()
    container.register_singleton(MockDatabase, db)

    container.register_factory(
        MockRepository,
        lambda c: MockRepository(c.resolve(MockDatabase)),
        lifetime=ServiceLifetime.SCOPED
    )

    container.register_factory(
        MockService,
        lambda c: MockService(c.resolve(MockRepository)),
        lifetime=ServiceLifetime.TRANSIENT
    )

    # Simulate Request 1
    scope1 = container.create_scope()
    req1_service1 = container.resolve(MockService, scope_id=scope1)
    req1_service2 = container.resolve(MockService, scope_id=scope1)

    # Within request 1: services are different, repo is same
    assert req1_service1 is not req1_service2
    assert req1_service1.repo is req1_service2.repo

    container.dispose_scope(scope1)

    # Simulate Request 2
    scope2 = container.create_scope()
    req2_service1 = container.resolve(MockService, scope_id=scope2)
    req2_service2 = container.resolve(MockService, scope_id=scope2)

    # Within request 2: services are different, repo is same
    assert req2_service1 is not req2_service2
    assert req2_service1.repo is req2_service2.repo

    # Across requests: repos are different
    assert req1_service1.repo is not req2_service1.repo

    # But database is always the same (singleton)
    assert req1_service1.repo.db is db
    assert req2_service1.repo.db is db

    container.dispose_scope(scope2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
