#!/usr/bin/env python3
"""
Tests for Batch-02: Shared Exceptions
Tests the exception hierarchy and error handling.
"""

import pytest
from datetime import datetime
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.shared.exceptions import (
    # Error codes
    ErrorCode,

    # Base
    AngelaException,

    # Domain
    DomainException,
    EntityNotFoundError,
    EntityAlreadyExistsError,
    BusinessRuleViolationError,
    InvalidStateError,

    # Repository
    RepositoryException,
    DatabaseConnectionError,
    QueryExecutionError,
    TransactionError,

    # Service
    ServiceException,
    ExternalServiceError,
    EmbeddingServiceError,
    RAGServiceError,
    ChatServiceError,

    # Validation
    ValidationException,
    InvalidInputError,
    MissingRequiredFieldError,
    ValueOutOfRangeError,

    # Infrastructure
    InfrastructureException,
    ConfigurationError,
    DependencyInjectionError,
)


class TestErrorCodes:
    """Test error code enum."""

    def test_error_codes_exist(self):
        """Test that all error codes are defined."""
        assert ErrorCode.UNKNOWN_ERROR.value == 1000
        assert ErrorCode.ENTITY_NOT_FOUND.value == 2000
        assert ErrorCode.DATABASE_CONNECTION_ERROR.value == 3000
        assert ErrorCode.EXTERNAL_SERVICE_ERROR.value == 4000
        assert ErrorCode.INVALID_INPUT.value == 5000
        assert ErrorCode.CONFIGURATION_ERROR.value == 6000

    def test_error_code_names(self):
        """Test error code names are descriptive."""
        assert ErrorCode.ENTITY_NOT_FOUND.name == "ENTITY_NOT_FOUND"
        assert ErrorCode.INVALID_INPUT.name == "INVALID_INPUT"


class TestAngelaException:
    """Test base Angela exception."""

    def test_create_basic_exception(self):
        """Test creating basic exception."""
        exc = AngelaException("Test error")

        assert str(exc) == "[UNKNOWN_ERROR] Test error"
        assert exc.message == "Test error"
        assert exc.code == ErrorCode.UNKNOWN_ERROR
        assert exc.context == {}
        assert exc.original_exception is None
        assert isinstance(exc.timestamp, datetime)

    def test_create_exception_with_code(self):
        """Test creating exception with specific error code."""
        exc = AngelaException(
            "Database failed",
            code=ErrorCode.DATABASE_CONNECTION_ERROR
        )

        assert str(exc) == "[DATABASE_CONNECTION_ERROR] Database failed"
        assert exc.code == ErrorCode.DATABASE_CONNECTION_ERROR

    def test_create_exception_with_context(self):
        """Test creating exception with context."""
        context = {"host": "localhost", "port": 5432}
        exc = AngelaException("Connection failed", context=context)

        assert exc.context == context
        assert exc.context["host"] == "localhost"

    def test_create_exception_with_original(self):
        """Test wrapping original exception."""
        original = ValueError("Original error")
        exc = AngelaException(
            "Wrapped error",
            original_exception=original
        )

        assert exc.original_exception is original
        assert isinstance(exc.original_exception, ValueError)

    def test_exception_to_dict(self):
        """Test converting exception to dictionary."""
        exc = AngelaException(
            "Test error",
            code=ErrorCode.INVALID_INPUT,
            context={"field": "email"}
        )

        result = exc.to_dict()

        assert result["error_type"] == "AngelaException"
        assert result["message"] == "Test error"
        assert result["code"] == ErrorCode.INVALID_INPUT.value
        assert result["code_name"] == "INVALID_INPUT"
        assert result["context"] == {"field": "email"}
        assert "timestamp" in result

    def test_exception_repr(self):
        """Test exception repr."""
        exc = AngelaException(
            "Test",
            code=ErrorCode.UNKNOWN_ERROR,
            context={"key": "value"}
        )

        repr_str = repr(exc)
        assert "AngelaException" in repr_str
        assert "Test" in repr_str
        assert "UNKNOWN_ERROR" in repr_str


class TestDomainExceptions:
    """Test domain exception hierarchy."""

    def test_entity_not_found_error(self):
        """Test EntityNotFoundError."""
        exc = EntityNotFoundError("Conversation", "123e4567-e89b-12d3-a456-426614174000")

        assert "Conversation with ID" in str(exc)
        assert "not found" in str(exc)
        assert exc.code == ErrorCode.ENTITY_NOT_FOUND
        assert exc.context["entity_type"] == "Conversation"
        assert "123e4567" in exc.context["entity_id"]

    def test_entity_already_exists_error(self):
        """Test EntityAlreadyExistsError."""
        exc = EntityAlreadyExistsError("User", "david@example.com")

        assert "User" in str(exc)
        assert "already exists" in str(exc)
        assert exc.code == ErrorCode.ENTITY_ALREADY_EXISTS
        assert exc.context["identifier"] == "david@example.com"

    def test_business_rule_violation_error(self):
        """Test BusinessRuleViolationError."""
        exc = BusinessRuleViolationError(
            "Importance must be between 1-10",
            details="Got value 15"
        )

        assert "Business rule violated" in str(exc)
        assert "Importance must be between 1-10" in str(exc)
        assert "Got value 15" in str(exc)
        assert exc.code == ErrorCode.BUSINESS_RULE_VIOLATION

    def test_invalid_state_error(self):
        """Test InvalidStateError."""
        exc = InvalidStateError(
            "Order",
            current_state="pending",
            expected_state="confirmed"
        )

        assert "Order" in str(exc)
        assert "invalid state" in str(exc)
        assert "pending" in str(exc)
        assert "confirmed" in str(exc)
        assert exc.code == ErrorCode.INVALID_STATE


class TestRepositoryExceptions:
    """Test repository exception hierarchy."""

    def test_database_connection_error(self):
        """Test DatabaseConnectionError."""
        exc = DatabaseConnectionError("Connection timeout")

        assert "Failed to connect to database" in str(exc)
        assert "Connection timeout" in str(exc)
        assert exc.code == ErrorCode.DATABASE_CONNECTION_ERROR

    def test_database_connection_error_with_original(self):
        """Test DatabaseConnectionError wrapping original exception."""
        original = ConnectionError("Network unreachable")
        exc = DatabaseConnectionError(
            "Connection failed",
            original_exception=original
        )

        assert exc.original_exception is original

    def test_query_execution_error(self):
        """Test QueryExecutionError."""
        query = "SELECT * FROM conversations WHERE id = $1"
        exc = QueryExecutionError(query, details="Syntax error")

        assert "Query execution failed" in str(exc)
        assert "SELECT * FROM conversations" in str(exc)
        assert "Syntax error" in str(exc)
        assert exc.context["query"] == query

    def test_transaction_error(self):
        """Test TransactionError."""
        exc = TransactionError("commit", details="Deadlock detected")

        assert "Transaction failed during commit" in str(exc)
        assert "Deadlock detected" in str(exc)
        assert exc.context["operation"] == "commit"


class TestServiceExceptions:
    """Test service exception hierarchy."""

    def test_external_service_error(self):
        """Test ExternalServiceError."""
        exc = ExternalServiceError(
            "Ollama",
            "generate_embedding",
            details="Connection refused"
        )

        assert "Ollama" in str(exc)
        assert "generate_embedding" in str(exc)
        assert "Connection refused" in str(exc)
        assert exc.context["service_name"] == "Ollama"
        assert exc.context["operation"] == "generate_embedding"

    def test_embedding_service_error(self):
        """Test EmbeddingServiceError."""
        exc = EmbeddingServiceError("Model not loaded")

        assert "Embedding generation failed" in str(exc)
        assert "Model not loaded" in str(exc)
        assert exc.code == ErrorCode.EMBEDDING_SERVICE_ERROR

    def test_rag_service_error(self):
        """Test RAGServiceError."""
        exc = RAGServiceError("search", details="No results found")

        assert "RAG search failed" in str(exc)
        assert "No results found" in str(exc)
        assert exc.context["operation"] == "search"

    def test_chat_service_error(self):
        """Test ChatServiceError."""
        exc = ChatServiceError("API rate limit exceeded")

        assert "Chat service operation failed" in str(exc)
        assert "rate limit" in str(exc)
        assert exc.code == ErrorCode.CHAT_SERVICE_ERROR


class TestValidationExceptions:
    """Test validation exception hierarchy."""

    def test_invalid_input_error(self):
        """Test InvalidInputError."""
        exc = InvalidInputError(
            "email",
            "invalid@",
            "Invalid email format"
        )

        assert "Invalid input for field 'email'" in str(exc)
        assert "Invalid email format" in str(exc)
        assert exc.context["field"] == "email"
        assert exc.context["value"] == "invalid@"
        assert exc.context["reason"] == "Invalid email format"

    def test_missing_required_field_error(self):
        """Test MissingRequiredFieldError."""
        exc = MissingRequiredFieldError("message")

        assert "Required field 'message' is missing" in str(exc)
        assert exc.context["field"] == "message"
        assert exc.code == ErrorCode.MISSING_REQUIRED_FIELD

    def test_value_out_of_range_error(self):
        """Test ValueOutOfRangeError."""
        exc = ValueOutOfRangeError(
            "importance",
            15,
            min_value=1,
            max_value=10
        )

        assert "importance" in str(exc)
        assert "out of range" in str(exc)
        assert "1 to 10" in str(exc)
        assert exc.context["value"] == "15"
        assert exc.context["min_value"] == 1
        assert exc.context["max_value"] == 10


class TestInfrastructureExceptions:
    """Test infrastructure exception hierarchy."""

    def test_configuration_error(self):
        """Test ConfigurationError."""
        exc = ConfigurationError(
            "DATABASE_URL",
            details="Environment variable not set"
        )

        assert "Configuration error for 'DATABASE_URL'" in str(exc)
        assert "Environment variable not set" in str(exc)
        assert exc.context["config_key"] == "DATABASE_URL"

    def test_dependency_injection_error(self):
        """Test DependencyInjectionError."""
        exc = DependencyInjectionError(
            "IConversationRepository",
            details="Interface not registered"
        )

        assert "Failed to inject dependency 'IConversationRepository'" in str(exc)
        assert "Interface not registered" in str(exc)
        assert exc.context["dependency"] == "IConversationRepository"


class TestExceptionCatching:
    """Test exception catching and hierarchy."""

    def test_catch_angela_exception(self):
        """Test catching base AngelaException catches all."""
        with pytest.raises(AngelaException):
            raise EntityNotFoundError("Test", "123")

        with pytest.raises(AngelaException):
            raise DatabaseConnectionError()

        with pytest.raises(AngelaException):
            raise ValidationException("Invalid")

    def test_catch_domain_exception(self):
        """Test catching DomainException."""
        with pytest.raises(DomainException):
            raise EntityNotFoundError("Test", "123")

        with pytest.raises(DomainException):
            raise BusinessRuleViolationError("Test rule")

    def test_catch_repository_exception(self):
        """Test catching RepositoryException."""
        with pytest.raises(RepositoryException):
            raise DatabaseConnectionError()

        with pytest.raises(RepositoryException):
            raise QueryExecutionError("SELECT 1")

    def test_catch_service_exception(self):
        """Test catching ServiceException."""
        with pytest.raises(ServiceException):
            raise ExternalServiceError("Test", "test_op")

        with pytest.raises(ServiceException):
            raise EmbeddingServiceError()

    def test_exception_inheritance(self):
        """Test exception inheritance chain."""
        assert issubclass(EntityNotFoundError, DomainException)
        assert issubclass(DomainException, AngelaException)
        assert issubclass(EntityNotFoundError, AngelaException)

        assert issubclass(DatabaseConnectionError, RepositoryException)
        assert issubclass(RepositoryException, AngelaException)


def run_tests():
    """Run all exception tests."""
    print("\n" + "="*60)
    print("🧪 Running Batch-02 Exception Tests")
    print("="*60)

    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes"
    ])


if __name__ == "__main__":
    run_tests()
