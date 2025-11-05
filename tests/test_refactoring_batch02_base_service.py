#!/usr/bin/env python3
"""
Tests for Batch-02: BaseService
Tests the base service patterns and utilities.
"""

import pytest
import asyncio
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.application.services.base_service import BaseService


# ============================================================================
# TEST SERVICE IMPLEMENTATIONS
# ============================================================================

class TestService(BaseService):
    """Concrete service for testing."""

    def __init__(self):
        super().__init__()
        self.operations_performed = []

    async def successful_operation(self, data: str) -> str:
        """Test operation that succeeds."""
        start_time = await self._log_operation_start("successful_operation", data=data)
        self.operations_performed.append(f"success: {data}")
        await self._log_operation_success("successful_operation", start_time)
        return f"processed: {data}"

    async def failing_operation(self, should_fail: bool = True):
        """Test operation that fails."""
        start_time = await self._log_operation_start("failing_operation")
        try:
            if should_fail:
                raise ValueError("Intentional failure")
            self.operations_performed.append("success")
            await self._log_operation_success("failing_operation", start_time)
        except Exception as e:
            await self._log_operation_error("failing_operation", e, start_time)
            raise

    async def operation_with_validation(self, data: dict):
        """Test operation with validation."""
        await self._validate_required_fields(data, ["name", "email"], "user")
        await self._validate_field_types(data, {"name": str, "email": str})
        return "validated"


class CustomNameService(BaseService):
    """Service with custom name."""

    def get_service_name(self) -> str:
        return "MyCustomService"


# ============================================================================
# TESTS
# ============================================================================

class TestBaseServiceInitialization:
    """Test service initialization."""

    @pytest.mark.asyncio
    async def test_service_initializes(self):
        """Test service initializes with default values."""
        service = TestService()

        assert service._operations_count == 0
        assert service._errors_count == 0
        assert service._last_operation_time is None
        assert service._last_error_time is None
        assert service._operation_durations == []

    @pytest.mark.asyncio
    async def test_service_name_default(self):
        """Test default service name is class name."""
        service = TestService()
        assert service.get_service_name() == "TestService"

    @pytest.mark.asyncio
    async def test_service_name_custom(self):
        """Test custom service name."""
        service = CustomNameService()
        assert service.get_service_name() == "MyCustomService"


class TestOperationLogging:
    """Test operation logging and tracking."""

    @pytest.mark.asyncio
    async def test_successful_operation_logging(self):
        """Test logging of successful operation."""
        service = TestService()

        result = await service.successful_operation("test_data")

        assert result == "processed: test_data"
        assert service._operations_count == 1
        assert service._errors_count == 0
        assert service._last_operation_time is not None
        assert len(service._operation_durations) == 1
        assert service._operation_durations[0] > 0

    @pytest.mark.asyncio
    async def test_failed_operation_logging(self):
        """Test logging of failed operation."""
        service = TestService()

        with pytest.raises(ValueError):
            await service.failing_operation(should_fail=True)

        assert service._operations_count == 0  # Failed operations don't count
        assert service._errors_count == 1
        assert service._last_error_time is not None

    @pytest.mark.asyncio
    async def test_multiple_operations_tracking(self):
        """Test tracking multiple operations."""
        service = TestService()

        # Perform 5 successful operations
        for i in range(5):
            await service.successful_operation(f"data_{i}")

        assert service._operations_count == 5
        assert len(service._operation_durations) == 5

    @pytest.mark.asyncio
    async def test_operation_durations_limited(self):
        """Test operation durations list is limited to 100."""
        service = TestService()

        # Perform 150 operations
        for i in range(150):
            await service.successful_operation(f"data_{i}")

        # Should only keep last 100
        assert len(service._operation_durations) == 100
        assert service._operations_count == 150


class TestValidationUtilities:
    """Test validation utility methods."""

    @pytest.mark.asyncio
    async def test_validate_required_fields_success(self):
        """Test validation passes with all required fields."""
        service = TestService()
        data = {"name": "John", "email": "john@example.com", "age": 30}

        # Should not raise
        await service._validate_required_fields(data, ["name", "email"], "user")

    @pytest.mark.asyncio
    async def test_validate_required_fields_missing(self):
        """Test validation fails with missing fields."""
        service = TestService()
        data = {"name": "John"}  # Missing email

        with pytest.raises(ValueError) as exc_info:
            await service._validate_required_fields(data, ["name", "email"], "user")

        assert "Missing required user fields" in str(exc_info.value)
        assert "email" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_required_fields_none_value(self):
        """Test validation fails with None values."""
        service = TestService()
        data = {"name": "John", "email": None}

        with pytest.raises(ValueError) as exc_info:
            await service._validate_required_fields(data, ["name", "email"], "user")

        assert "email" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_field_types_success(self):
        """Test type validation passes with correct types."""
        service = TestService()
        data = {"name": "John", "age": 30, "active": True}

        # Should not raise
        await service._validate_field_types(data, {
            "name": str,
            "age": int,
            "active": bool
        })

    @pytest.mark.asyncio
    async def test_validate_field_types_wrong_type(self):
        """Test type validation fails with wrong types."""
        service = TestService()
        data = {"name": "John", "age": "thirty"}  # age should be int

        with pytest.raises(TypeError) as exc_info:
            await service._validate_field_types(data, {"name": str, "age": int})

        assert "age" in str(exc_info.value)
        assert "expected int" in str(exc_info.value)
        assert "got str" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_range_success(self):
        """Test range validation passes."""
        service = TestService()

        # Should not raise
        await service._validate_range(5, min_value=1, max_value=10, field_name="score")

    @pytest.mark.asyncio
    async def test_validate_range_too_low(self):
        """Test range validation fails when value too low."""
        service = TestService()

        with pytest.raises(ValueError) as exc_info:
            await service._validate_range(0, min_value=1, max_value=10, field_name="score")

        assert "score must be >= 1" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_range_too_high(self):
        """Test range validation fails when value too high."""
        service = TestService()

        with pytest.raises(ValueError) as exc_info:
            await service._validate_range(15, min_value=1, max_value=10, field_name="score")

        assert "score must be <= 10" in str(exc_info.value)


class TestErrorHandlingUtilities:
    """Test error handling utility methods."""

    @pytest.mark.asyncio
    async def test_retry_on_failure_succeeds_first_try(self):
        """Test retry succeeds on first attempt."""
        service = TestService()
        call_count = [0]

        async def operation():
            call_count[0] += 1
            return "success"

        result = await service._retry_on_failure(operation, max_retries=3)

        assert result == "success"
        assert call_count[0] == 1

    @pytest.mark.asyncio
    async def test_retry_on_failure_succeeds_after_retries(self):
        """Test retry succeeds after failures."""
        service = TestService()
        call_count = [0]

        async def operation():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = await service._retry_on_failure(
            operation,
            max_retries=5,
            retry_delay=0.001  # Fast retry for testing
        )

        assert result == "success"
        assert call_count[0] == 3

    @pytest.mark.asyncio
    async def test_retry_on_failure_fails_all_attempts(self):
        """Test retry fails after all attempts."""
        service = TestService()
        call_count = [0]

        async def operation():
            call_count[0] += 1
            raise ValueError("Permanent failure")

        with pytest.raises(ValueError) as exc_info:
            await service._retry_on_failure(
                operation,
                max_retries=3,
                retry_delay=0.001
            )

        assert "Permanent failure" in str(exc_info.value)
        assert call_count[0] == 3

    @pytest.mark.asyncio
    async def test_safe_execute_success(self):
        """Test safe execute returns result on success."""
        service = TestService()

        async def operation():
            return "success"

        result = await service._safe_execute(operation)

        assert result == "success"

    @pytest.mark.asyncio
    async def test_safe_execute_failure_returns_default(self):
        """Test safe execute returns default value on failure."""
        service = TestService()

        async def operation():
            raise ValueError("Error")

        result = await service._safe_execute(operation, default_value="fallback")

        assert result == "fallback"

    @pytest.mark.asyncio
    async def test_safe_execute_failure_returns_none(self):
        """Test safe execute returns None by default on failure."""
        service = TestService()

        async def operation():
            raise ValueError("Error")

        result = await service._safe_execute(operation)

        assert result is None


class TestServiceStatistics:
    """Test service statistics tracking."""

    @pytest.mark.asyncio
    async def test_get_stats_initial(self):
        """Test getting stats for new service."""
        service = TestService()
        stats = service.get_stats()

        assert stats["service_name"] == "TestService"
        assert stats["operations_count"] == 0
        assert stats["errors_count"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["last_operation_time"] is None
        assert stats["last_error_time"] is None
        assert stats["avg_operation_duration_ms"] is None

    @pytest.mark.asyncio
    async def test_get_stats_after_operations(self):
        """Test stats after successful operations."""
        service = TestService()

        await service.successful_operation("data1")
        await service.successful_operation("data2")
        await service.successful_operation("data3")

        stats = service.get_stats()

        assert stats["operations_count"] == 3
        assert stats["errors_count"] == 0
        assert stats["success_rate"] == 100.0
        assert stats["last_operation_time"] is not None
        assert stats["avg_operation_duration_ms"] is not None
        assert stats["avg_operation_duration_ms"] >= 0  # May be 0 for very fast operations

    @pytest.mark.asyncio
    async def test_get_stats_with_failures(self):
        """Test stats after mixed success/failure."""
        service = TestService()

        await service.successful_operation("data1")
        await service.successful_operation("data2")

        try:
            await service.failing_operation(should_fail=True)
        except ValueError:
            pass

        stats = service.get_stats()

        assert stats["operations_count"] == 2
        assert stats["errors_count"] == 1
        # Success rate = (2 - 1) / 2 * 100 = 50%
        assert stats["success_rate"] == 50.0
        assert stats["last_error_time"] is not None

    @pytest.mark.asyncio
    async def test_reset_stats(self):
        """Test resetting service statistics."""
        service = TestService()

        await service.successful_operation("data")
        assert service._operations_count > 0

        service.reset_stats()

        assert service._operations_count == 0
        assert service._errors_count == 0
        assert service._last_operation_time is None
        assert service._operation_durations == []


def run_tests():
    """Run all base service tests."""
    print("\n" + "="*60)
    print("🧪 Running Batch-02 BaseService Tests")
    print("="*60)

    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes"
    ])


if __name__ == "__main__":
    run_tests()
