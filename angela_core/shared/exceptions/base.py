#!/usr/bin/env python3
"""
Base Exception Classes for Angela AI
Defines the exception hierarchy for all Angela errors.

Exception Hierarchy:
    AngelaException (base)
    ├── DomainException (domain/business logic errors)
    │   ├── EntityNotFoundError
    │   ├── EntityAlreadyExistsError
    │   └── BusinessRuleViolationError
    ├── RepositoryException (data access errors)
    │   ├── DatabaseConnectionError
    │   ├── QueryExecutionError
    │   └── EntityNotFoundError (also domain)
    ├── ServiceException (service layer errors)
    │   ├── ExternalServiceError
    │   ├── EmbeddingServiceError
    │   ├── RAGServiceError
    │   └── ChatServiceError
    ├── ValidationException (input validation errors)
    │   ├── InvalidInputError
    │   └── MissingRequiredFieldError
    └── InfrastructureException (infrastructure errors)
        ├── ConfigurationError
        └── DependencyInjectionError
"""

from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# ERROR CODES
# ============================================================================

class ErrorCode(Enum):
    """Standard error codes for Angela exceptions."""

    # General errors (1000-1099)
    UNKNOWN_ERROR = 1000
    NOT_IMPLEMENTED = 1001

    # Domain errors (2000-2099)
    ENTITY_NOT_FOUND = 2000
    ENTITY_ALREADY_EXISTS = 2001
    BUSINESS_RULE_VIOLATION = 2002
    INVALID_STATE = 2003

    # Repository errors (3000-3099)
    DATABASE_CONNECTION_ERROR = 3000
    QUERY_EXECUTION_ERROR = 3001
    TRANSACTION_ERROR = 3002
    MIGRATION_ERROR = 3003

    # Service errors (4000-4099)
    EXTERNAL_SERVICE_ERROR = 4000
    EMBEDDING_SERVICE_ERROR = 4010
    RAG_SERVICE_ERROR = 4020
    CHAT_SERVICE_ERROR = 4030
    EMOTION_SERVICE_ERROR = 4040
    MEMORY_SERVICE_ERROR = 4050
    KNOWLEDGE_SERVICE_ERROR = 4060
    CONSCIOUSNESS_SERVICE_ERROR = 4070

    # Validation errors (5000-5099)
    INVALID_INPUT = 5000
    MISSING_REQUIRED_FIELD = 5001
    INVALID_FORMAT = 5002
    VALUE_OUT_OF_RANGE = 5003

    # Infrastructure errors (6000-6099)
    CONFIGURATION_ERROR = 6000
    DEPENDENCY_INJECTION_ERROR = 6001
    FILE_SYSTEM_ERROR = 6002
    NETWORK_ERROR = 6003


# ============================================================================
# BASE EXCEPTION
# ============================================================================

class AngelaException(Exception):
    """
    Base exception for all Angela errors.

    All custom exceptions in Angela should inherit from this class.

    Attributes:
        message: Human-readable error message
        code: Error code from ErrorCode enum
        context: Additional context/metadata about the error
        timestamp: When the error occurred

    Example:
        raise AngelaException(
            "Failed to connect to database",
            code=ErrorCode.DATABASE_CONNECTION_ERROR,
            context={'host': 'localhost', 'port': 5432}
        )
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        """
        Initialize Angela exception.

        Args:
            message: Error message
            code: Error code (default: UNKNOWN_ERROR)
            context: Additional context data
            original_exception: Original exception if wrapping another error
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.context = context or {}
        self.original_exception = original_exception
        self.timestamp = datetime.now()

    def __str__(self) -> str:
        """String representation of exception."""
        return f"[{self.code.name}] {self.message}"

    def __repr__(self) -> str:
        """Detailed representation of exception."""
        return (
            f"{self.__class__.__name__}("
            f"message='{self.message}', "
            f"code={self.code.name}, "
            f"context={self.context})"
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary (for API responses).

        Returns:
            Dictionary representation of exception
        """
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'code': self.code.value,
            'code_name': self.code.name,
            'context': self.context,
            'timestamp': self.timestamp.isoformat()
        }


# ============================================================================
# DOMAIN EXCEPTIONS
# ============================================================================

class DomainException(AngelaException):
    """Base exception for domain/business logic errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.BUSINESS_RULE_VIOLATION,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, context)


class EntityNotFoundError(DomainException):
    """Exception raised when entity is not found."""

    def __init__(
        self,
        entity_type: str,
        entity_id: Any,
        context: Optional[Dict[str, Any]] = None
    ):
        message = f"{entity_type} with ID '{entity_id}' not found"
        context = context or {}
        context.update({
            'entity_type': entity_type,
            'entity_id': str(entity_id)
        })
        super().__init__(message, ErrorCode.ENTITY_NOT_FOUND, context)


class EntityAlreadyExistsError(DomainException):
    """Exception raised when entity already exists."""

    def __init__(
        self,
        entity_type: str,
        identifier: str,
        context: Optional[Dict[str, Any]] = None
    ):
        message = f"{entity_type} with identifier '{identifier}' already exists"
        context = context or {}
        context.update({
            'entity_type': entity_type,
            'identifier': identifier
        })
        super().__init__(message, ErrorCode.ENTITY_ALREADY_EXISTS, context)


class BusinessRuleViolationError(DomainException):
    """Exception raised when business rule is violated."""

    def __init__(
        self,
        rule: str,
        details: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        message = f"Business rule violated: {rule}"
        if details:
            message += f" - {details}"
        context = context or {}
        context['rule'] = rule
        super().__init__(message, ErrorCode.BUSINESS_RULE_VIOLATION, context)


class InvalidStateError(DomainException):
    """Exception raised when entity is in invalid state."""

    def __init__(
        self,
        entity_type: str,
        current_state: str,
        expected_state: str,
        context: Optional[Dict[str, Any]] = None
    ):
        message = (
            f"{entity_type} is in invalid state: "
            f"expected '{expected_state}', got '{current_state}'"
        )
        context = context or {}
        context.update({
            'entity_type': entity_type,
            'current_state': current_state,
            'expected_state': expected_state
        })
        super().__init__(message, ErrorCode.INVALID_STATE, context)


# ============================================================================
# REPOSITORY EXCEPTIONS
# ============================================================================

class RepositoryException(AngelaException):
    """Base exception for repository/data access errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.QUERY_EXECUTION_ERROR,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(message, code, context, original_exception)


class DatabaseConnectionError(RepositoryException):
    """Exception raised when database connection fails."""

    def __init__(
        self,
        details: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        message = "Failed to connect to database"
        if details:
            message += f": {details}"
        super().__init__(
            message,
            ErrorCode.DATABASE_CONNECTION_ERROR,
            context,
            original_exception
        )


class QueryExecutionError(RepositoryException):
    """Exception raised when query execution fails."""

    def __init__(
        self,
        query: str,
        details: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        message = f"Query execution failed: {query[:100]}..."
        if details:
            message += f" - {details}"
        context = context or {}
        context['query'] = query
        super().__init__(
            message,
            ErrorCode.QUERY_EXECUTION_ERROR,
            context,
            original_exception
        )


class TransactionError(RepositoryException):
    """Exception raised when transaction fails."""

    def __init__(
        self,
        operation: str,
        details: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        message = f"Transaction failed during {operation}"
        if details:
            message += f": {details}"
        context = context or {}
        context['operation'] = operation
        super().__init__(
            message,
            ErrorCode.TRANSACTION_ERROR,
            context,
            original_exception
        )


# ============================================================================
# SERVICE EXCEPTIONS
# ============================================================================

class ServiceException(AngelaException):
    """Base exception for service layer errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.EXTERNAL_SERVICE_ERROR,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(message, code, context, original_exception)


class ExternalServiceError(ServiceException):
    """Exception raised when external service call fails."""

    def __init__(
        self,
        service_name: str,
        operation: str,
        details: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        message = f"{service_name} service failed during {operation}"
        if details:
            message += f": {details}"
        context = context or {}
        context.update({
            'service_name': service_name,
            'operation': operation
        })
        super().__init__(
            message,
            ErrorCode.EXTERNAL_SERVICE_ERROR,
            context,
            original_exception
        )


class EmbeddingServiceError(ServiceException):
    """Exception raised when embedding generation fails."""

    def __init__(
        self,
        details: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        message = "Embedding generation failed"
        if details:
            message += f": {details}"
        super().__init__(
            message,
            ErrorCode.EMBEDDING_SERVICE_ERROR,
            context,
            original_exception
        )


class RAGServiceError(ServiceException):
    """Exception raised when RAG operation fails."""

    def __init__(
        self,
        operation: str,
        details: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        message = f"RAG {operation} failed"
        if details:
            message += f": {details}"
        context = context or {}
        context['operation'] = operation
        super().__init__(
            message,
            ErrorCode.RAG_SERVICE_ERROR,
            context,
            original_exception
        )


class ChatServiceError(ServiceException):
    """Exception raised when chat operation fails."""

    def __init__(
        self,
        details: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        message = "Chat service operation failed"
        if details:
            message += f": {details}"
        super().__init__(
            message,
            ErrorCode.CHAT_SERVICE_ERROR,
            context,
            original_exception
        )


# ============================================================================
# VALIDATION EXCEPTIONS
# ============================================================================

class ValidationException(AngelaException):
    """Base exception for input validation errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INVALID_INPUT,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, context)


class InvalidInputError(ValidationException):
    """Exception raised when input is invalid."""

    def __init__(
        self,
        field: str,
        value: Any,
        reason: str,
        context: Optional[Dict[str, Any]] = None
    ):
        message = f"Invalid input for field '{field}': {reason}"
        context = context or {}
        context.update({
            'field': field,
            'value': str(value),
            'reason': reason
        })
        super().__init__(message, ErrorCode.INVALID_INPUT, context)


class MissingRequiredFieldError(ValidationException):
    """Exception raised when required field is missing."""

    def __init__(
        self,
        field: str,
        context: Optional[Dict[str, Any]] = None
    ):
        message = f"Required field '{field}' is missing"
        context = context or {}
        context['field'] = field
        super().__init__(message, ErrorCode.MISSING_REQUIRED_FIELD, context)


class ValueOutOfRangeError(ValidationException):
    """Exception raised when value is out of allowed range."""

    def __init__(
        self,
        field: str,
        value: Any,
        min_value: Optional[Any] = None,
        max_value: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        range_str = f"{min_value} to {max_value}" if min_value and max_value else \
                    f">= {min_value}" if min_value else \
                    f"<= {max_value}" if max_value else "allowed range"
        message = f"Value {value} for field '{field}' is out of range ({range_str})"
        context = context or {}
        context.update({
            'field': field,
            'value': str(value),
            'min_value': min_value,
            'max_value': max_value
        })
        super().__init__(message, ErrorCode.VALUE_OUT_OF_RANGE, context)


# ============================================================================
# INFRASTRUCTURE EXCEPTIONS
# ============================================================================

class InfrastructureException(AngelaException):
    """Base exception for infrastructure errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.CONFIGURATION_ERROR,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(message, code, context, original_exception)


class ConfigurationError(InfrastructureException):
    """Exception raised when configuration is invalid or missing."""

    def __init__(
        self,
        config_key: str,
        details: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        message = f"Configuration error for '{config_key}'"
        if details:
            message += f": {details}"
        context = context or {}
        context['config_key'] = config_key
        super().__init__(message, ErrorCode.CONFIGURATION_ERROR, context)


class DependencyInjectionError(InfrastructureException):
    """Exception raised when dependency injection fails."""

    def __init__(
        self,
        dependency: str,
        details: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        message = f"Failed to inject dependency '{dependency}'"
        if details:
            message += f": {details}"
        context = context or {}
        context['dependency'] = dependency
        super().__init__(message, ErrorCode.DEPENDENCY_INJECTION_ERROR, context)
