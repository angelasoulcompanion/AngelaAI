#!/usr/bin/env python3
"""
Dependency Injection Container
===============================

A complete DI system with lifecycle management for AngelaAI.

Features:
- Singleton: One instance for entire application
- Scoped: One instance per request/scope
- Transient: New instance every time
- Circular dependency detection
- Type-safe resolution
- Clear error messages

Author: Angela 💜
Created: 2025-11-01
"""

from typing import Dict, Type, TypeVar, Callable, Any, Optional, Set
from enum import Enum
from uuid import uuid4
import inspect
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceLifetime(Enum):
    """
    Service lifetime options.

    - SINGLETON: One instance for entire application lifetime
    - SCOPED: One instance per scope (typically per HTTP request)
    - TRANSIENT: New instance created every time it's resolved
    """
    SINGLETON = "singleton"
    SCOPED = "scoped"
    TRANSIENT = "transient"


class ServiceNotFoundError(Exception):
    """Raised when a service is not registered in the container."""
    pass


class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected."""
    pass


class InvalidRegistrationError(Exception):
    """Raised when service registration is invalid."""
    pass


class DIContainer:
    """
    Dependency Injection Container with lifecycle management.

    This container manages the creation and lifecycle of services,
    supporting three lifetime options: singleton, scoped, and transient.

    Example:
        ```python
        container = DIContainer()

        # Register singleton
        container.register_singleton(Database, database_instance)

        # Register factory with scoped lifetime
        container.register_factory(
            UserRepository,
            lambda c: UserRepository(c.resolve(Database)),
            lifetime=ServiceLifetime.SCOPED
        )

        # Resolve service
        scope_id = container.create_scope()
        repo = container.resolve(UserRepository, scope_id=scope_id)
        ```
    """

    def __init__(self):
        """Initialize empty DI container."""
        # Store singleton instances
        self._singletons: Dict[Type, Any] = {}

        # Store factory functions for services
        self._factories: Dict[Type, Callable] = {}

        # Store lifetime configuration for each service
        self._lifetimes: Dict[Type, ServiceLifetime] = {}

        # Store scoped instances (per scope)
        # Format: {scope_id: {service_type: instance}}
        self._scoped_instances: Dict[str, Dict[Type, Any]] = {}

        # Track services currently being resolved (for circular dependency detection)
        self._resolving: Set[Type] = set()

        # Track current scope during resolution (for nested resolution)
        self._current_scope: Optional[str] = None

        logger.debug("🔧 DIContainer initialized")

    def register_singleton(self, interface: Type[T], instance: T) -> None:
        """
        Register a singleton instance.

        The same instance will be returned every time this service is resolved.

        Args:
            interface: The type/interface to register
            instance: The singleton instance to use

        Raises:
            InvalidRegistrationError: If interface is already registered

        Example:
            ```python
            db = Database()
            container.register_singleton(Database, db)
            ```
        """
        if interface in self._singletons or interface in self._factories:
            raise InvalidRegistrationError(
                f"Service {interface.__name__} is already registered. "
                f"Unregister it first before re-registering."
            )

        self._singletons[interface] = instance
        self._lifetimes[interface] = ServiceLifetime.SINGLETON

        logger.debug(f"✅ Registered singleton: {interface.__name__}")

    def register_factory(
        self,
        interface: Type[T],
        factory: Callable[[Any], T],
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    ) -> None:
        """
        Register a factory function with specified lifetime.

        Args:
            interface: The type/interface to register
            factory: Factory function that takes DIContainer and returns instance
            lifetime: Service lifetime (SINGLETON, SCOPED, or TRANSIENT)

        Raises:
            InvalidRegistrationError: If interface is already registered or factory is invalid

        Example:
            ```python
            container.register_factory(
                UserRepository,
                lambda c: UserRepository(c.resolve(Database)),
                lifetime=ServiceLifetime.SCOPED
            )
            ```
        """
        if interface in self._singletons or interface in self._factories:
            raise InvalidRegistrationError(
                f"Service {interface.__name__} is already registered. "
                f"Unregister it first before re-registering."
            )

        if not callable(factory):
            raise InvalidRegistrationError(
                f"Factory for {interface.__name__} must be callable."
            )

        # Validate factory signature
        sig = inspect.signature(factory)
        if len(sig.parameters) != 1:
            raise InvalidRegistrationError(
                f"Factory for {interface.__name__} must accept exactly 1 parameter (container). "
                f"Got {len(sig.parameters)} parameters."
            )

        self._factories[interface] = factory
        self._lifetimes[interface] = lifetime

        logger.debug(f"✅ Registered factory: {interface.__name__} ({lifetime.value})")

    def resolve(self, interface: Type[T], scope_id: Optional[str] = None) -> T:
        """
        Resolve a service from the container.

        Args:
            interface: The type/interface to resolve
            scope_id: Scope ID for scoped services (required for SCOPED lifetime)

        Returns:
            Resolved service instance

        Raises:
            ServiceNotFoundError: If service is not registered
            CircularDependencyError: If circular dependency is detected
            ValueError: If scope_id is required but not provided

        Example:
            ```python
            # Resolve singleton
            db = container.resolve(Database)

            # Resolve scoped service
            scope_id = container.create_scope()
            repo = container.resolve(UserRepository, scope_id=scope_id)
            ```
        """
        # Check if service is registered
        if interface not in self._singletons and interface not in self._factories:
            raise ServiceNotFoundError(
                f"Service {interface.__name__} is not registered in the container. "
                f"Available services: {', '.join(s.__name__ for s in self._get_registered_services())}"
            )

        # Detect circular dependencies
        if interface in self._resolving:
            dependency_chain = " -> ".join(s.__name__ for s in self._resolving)
            raise CircularDependencyError(
                f"Circular dependency detected: {dependency_chain} -> {interface.__name__}"
            )

        try:
            # Add to resolving set
            self._resolving.add(interface)

            # Set current scope if provided (for nested resolution)
            old_scope = self._current_scope
            if scope_id is not None:
                self._current_scope = scope_id

            try:
                # Get lifetime
                lifetime = self._lifetimes[interface]

                # Resolve based on lifetime
                if lifetime == ServiceLifetime.SINGLETON:
                    return self._resolve_singleton(interface)

                elif lifetime == ServiceLifetime.SCOPED:
                    # Use provided scope_id or current scope
                    effective_scope = scope_id or self._current_scope
                    if effective_scope is None:
                        raise ValueError(
                            f"Service {interface.__name__} has SCOPED lifetime but no scope_id provided. "
                            f"Call container.create_scope() first and pass the scope_id."
                        )
                    return self._resolve_scoped(interface, effective_scope)

                else:  # TRANSIENT
                    return self._resolve_transient(interface)

            finally:
                # Restore old scope
                self._current_scope = old_scope

        finally:
            # Remove from resolving set
            self._resolving.discard(interface)

    def _resolve_singleton(self, interface: Type[T]) -> T:
        """Resolve singleton service."""
        # If already instantiated, return it
        if interface in self._singletons:
            return self._singletons[interface]

        # Create instance using factory
        factory = self._factories[interface]
        instance = factory(self)

        # Store for future use
        self._singletons[interface] = instance

        logger.debug(f"🔨 Created singleton: {interface.__name__}")
        return instance

    def _resolve_scoped(self, interface: Type[T], scope_id: str) -> T:
        """Resolve scoped service."""
        # Check if scope exists
        if scope_id not in self._scoped_instances:
            raise ValueError(
                f"Scope '{scope_id}' does not exist. "
                f"Call container.create_scope() to create a scope first."
            )

        # Get scope
        scope = self._scoped_instances[scope_id]

        # If already instantiated in this scope, return it
        if interface in scope:
            return scope[interface]

        # Create instance using factory
        factory = self._factories[interface]
        instance = factory(self)

        # Store in scope
        scope[interface] = instance

        logger.debug(f"🔨 Created scoped instance: {interface.__name__} (scope: {scope_id[:8]}...)")
        return instance

    def _resolve_transient(self, interface: Type[T]) -> T:
        """Resolve transient service (always creates new instance)."""
        factory = self._factories[interface]
        instance = factory(self)

        logger.debug(f"🔨 Created transient instance: {interface.__name__}")
        return instance

    def create_scope(self) -> str:
        """
        Create a new scope for scoped dependencies.

        Returns:
            Unique scope ID

        Example:
            ```python
            scope_id = container.create_scope()
            try:
                repo = container.resolve(UserRepository, scope_id=scope_id)
                # Use repo...
            finally:
                container.dispose_scope(scope_id)
            ```
        """
        scope_id = str(uuid4())
        self._scoped_instances[scope_id] = {}

        logger.debug(f"🆕 Created scope: {scope_id[:8]}...")
        return scope_id

    def dispose_scope(self, scope_id: str) -> None:
        """
        Dispose a scope and cleanup scoped instances.

        This should be called when a scope (e.g., HTTP request) is finished
        to release resources.

        Args:
            scope_id: Scope ID to dispose

        Example:
            ```python
            scope_id = container.create_scope()
            try:
                # ... use services ...
            finally:
                container.dispose_scope(scope_id)
            ```
        """
        if scope_id not in self._scoped_instances:
            logger.warning(f"⚠️ Attempted to dispose non-existent scope: {scope_id[:8]}...")
            return

        # Get instances in this scope
        scope = self._scoped_instances[scope_id]

        # Call dispose() method on instances that have it
        for interface, instance in scope.items():
            if hasattr(instance, 'dispose') and callable(instance.dispose):
                try:
                    instance.dispose()
                    logger.debug(f"🧹 Disposed: {interface.__name__}")
                except Exception as e:
                    logger.error(f"❌ Error disposing {interface.__name__}: {e}")

        # Remove scope
        del self._scoped_instances[scope_id]
        logger.debug(f"🗑️ Disposed scope: {scope_id[:8]}...")

    def unregister(self, interface: Type) -> None:
        """
        Unregister a service.

        Args:
            interface: The type/interface to unregister

        Note:
            This does NOT dispose existing instances. Call dispose_all_scopes() first
            if you want to cleanup scoped instances.
        """
        # Remove from all stores
        self._singletons.pop(interface, None)
        self._factories.pop(interface, None)
        self._lifetimes.pop(interface, None)

        logger.debug(f"🗑️ Unregistered: {interface.__name__}")

    def dispose_all_scopes(self) -> None:
        """
        Dispose all scopes.

        Useful for testing or shutdown scenarios.
        """
        scope_ids = list(self._scoped_instances.keys())
        for scope_id in scope_ids:
            self.dispose_scope(scope_id)

        logger.debug("🧹 Disposed all scopes")

    def _get_registered_services(self) -> Set[Type]:
        """Get all registered service types."""
        return set(self._singletons.keys()) | set(self._factories.keys())

    def is_registered(self, interface: Type) -> bool:
        """
        Check if a service is registered.

        Args:
            interface: The type/interface to check

        Returns:
            True if registered, False otherwise
        """
        return interface in self._singletons or interface in self._factories

    def get_lifetime(self, interface: Type) -> Optional[ServiceLifetime]:
        """
        Get the lifetime of a registered service.

        Args:
            interface: The type/interface to check

        Returns:
            ServiceLifetime or None if not registered
        """
        return self._lifetimes.get(interface)

    def __repr__(self) -> str:
        """String representation of container."""
        num_services = len(self._get_registered_services())
        num_scopes = len(self._scoped_instances)
        return f"<DIContainer services={num_services} scopes={num_scopes}>"
