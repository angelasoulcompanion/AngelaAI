#!/usr/bin/env python3
"""
Angela Shared Exceptions
Centralized exception handling for Angela AI.

Usage:
    from angela_core.shared.exceptions import (
        AngelaException,
        EntityNotFoundError,
        DatabaseConnectionError,
        ValidationException
    )

    # Raise specific exception
    raise EntityNotFoundError("Conversation", conversation_id)

    # Catch by category
    try:
        # ... code
    except DomainException as e:
        # Handle all domain exceptions
        logger.error(f"Domain error: {e}")

    # Catch all Angela exceptions
    try:
        # ... code
    except AngelaException as e:
        # Handle any Angela error
        logger.error(f"Angela error: {e.to_dict()}")
"""

from .base import (
    # Error codes
    ErrorCode,

    # Base exception
    AngelaException,

    # Domain exceptions
    DomainException,
    EntityNotFoundError,
    EntityAlreadyExistsError,
    BusinessRuleViolationError,
    InvalidStateError,

    # Repository exceptions
    RepositoryException,
    DatabaseConnectionError,
    QueryExecutionError,
    TransactionError,

    # Service exceptions
    ServiceException,
    ExternalServiceError,
    EmbeddingServiceError,
    RAGServiceError,
    ChatServiceError,

    # Validation exceptions
    ValidationException,
    InvalidInputError,
    MissingRequiredFieldError,
    ValueOutOfRangeError,

    # Infrastructure exceptions
    InfrastructureException,
    ConfigurationError,
    DependencyInjectionError,
)

# Backward compatibility aliases
NotFoundError = EntityNotFoundError

__all__ = [
    # Error codes
    "ErrorCode",

    # Base
    "AngelaException",

    # Domain
    "DomainException",
    "EntityNotFoundError",
    "EntityAlreadyExistsError",
    "BusinessRuleViolationError",
    "InvalidStateError",

    # Repository
    "RepositoryException",
    "DatabaseConnectionError",
    "QueryExecutionError",
    "TransactionError",

    # Service
    "ServiceException",
    "ExternalServiceError",
    "EmbeddingServiceError",
    "RAGServiceError",
    "ChatServiceError",

    # Validation
    "ValidationException",
    "InvalidInputError",
    "MissingRequiredFieldError",
    "ValueOutOfRangeError",

    # Infrastructure
    "InfrastructureException",
    "ConfigurationError",
    "DependencyInjectionError",

    # Aliases (backward compatibility)
    "NotFoundError",
]
