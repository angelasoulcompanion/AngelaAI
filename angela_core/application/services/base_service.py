#!/usr/bin/env python3
"""
Base Service Implementation
Provides common patterns and utilities for all application services.

Services contain business logic and orchestrate operations between
repositories, external services, and domain entities.
"""

from abc import ABC
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from functools import wraps
import logging
import asyncio
import time

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """
    Abstract base service with common patterns.

    Provides:
    - Structured logging with operation tracking
    - Error handling and recovery patterns
    - Performance monitoring
    - Validation utilities
    - Operation statistics

    Subclasses should:
    1. Call super().__init__() in their __init__
    2. Use _log_operation_* methods for operation tracking
    3. Use _validate_* methods for input validation
    4. Override get_service_name() for custom service identification

    Example:
        class ChatService(BaseService):
            def __init__(self, conversation_repo, llm_service):
                super().__init__()
                self.conversation_repo = conversation_repo
                self.llm_service = llm_service

            async def send_message(self, message: str):
                await self._log_operation_start("send_message", message_length=len(message))
                try:
                    response = await self.llm_service.chat(message)
                    await self._log_operation_success("send_message")
                    return response
                except Exception as e:
                    await self._log_operation_error("send_message", e)
                    raise
    """

    def __init__(self):
        """Initialize base service with logging and statistics."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._operations_count = 0
        self._errors_count = 0
        self._last_operation_time: Optional[datetime] = None
        self._last_error_time: Optional[datetime] = None
        self._operation_durations: List[float] = []  # Track last 100 operations

        self.logger.debug(f"{self.get_service_name()} initialized")

    # ========================================================================
    # SERVICE IDENTIFICATION
    # ========================================================================

    def get_service_name(self) -> str:
        """
        Get service name for logging and identification.

        Subclasses can override this for custom service names.

        Returns:
            Service name (default: class name)
        """
        return self.__class__.__name__

    # ========================================================================
    # OPERATION LOGGING & TRACKING
    # ========================================================================

    async def _log_operation_start(
        self,
        operation: str,
        level: int = logging.INFO,
        **context
    ) -> float:
        """
        Log operation start with context.

        Args:
            operation: Operation name (e.g., "send_message")
            level: Logging level (default: INFO)
            **context: Additional context to log

        Returns:
            Start timestamp (for duration calculation)
        """
        start_time = time.time()
        self.logger.log(
            level,
            f"▶️  {self.get_service_name()}.{operation} - Starting",
            extra=context
        )
        return start_time

    async def _log_operation_success(
        self,
        operation: str,
        start_time: Optional[float] = None,
        level: int = logging.INFO,
        **context
    ):
        """
        Log successful operation completion.

        Args:
            operation: Operation name
            start_time: Start timestamp (from _log_operation_start)
            level: Logging level (default: INFO)
            **context: Additional context to log
        """
        self._operations_count += 1
        self._last_operation_time = datetime.now()

        # Calculate duration if start_time provided
        duration_info = {}
        if start_time is not None:
            duration = time.time() - start_time
            self._operation_durations.append(duration)
            # Keep only last 100 durations
            if len(self._operation_durations) > 100:
                self._operation_durations.pop(0)
            duration_info = {"duration_ms": round(duration * 1000, 2)}

        self.logger.log(
            level,
            f"✅ {self.get_service_name()}.{operation} - Success",
            extra={**context, **duration_info}
        )

    async def _log_operation_error(
        self,
        operation: str,
        error: Exception,
        start_time: Optional[float] = None,
        level: int = logging.ERROR,
        **context
    ):
        """
        Log operation error with details.

        Args:
            operation: Operation name
            error: Exception that occurred
            start_time: Start timestamp (from _log_operation_start)
            level: Logging level (default: ERROR)
            **context: Additional context to log
        """
        self._errors_count += 1
        self._last_error_time = datetime.now()

        # Calculate duration if start_time provided
        duration_info = {}
        if start_time is not None:
            duration = time.time() - start_time
            duration_info = {"duration_ms": round(duration * 1000, 2)}

        self.logger.log(
            level,
            f"❌ {self.get_service_name()}.{operation} - Failed: {error}",
            extra={
                **context,
                **duration_info,
                "error_type": type(error).__name__,
                "error_message": str(error)
            },
            exc_info=True
        )

    # ========================================================================
    # VALIDATION UTILITIES
    # ========================================================================

    async def _validate_required_fields(
        self,
        data: Dict[str, Any],
        required_fields: List[str],
        data_name: str = "input"
    ):
        """
        Validate that required fields are present in data.

        Args:
            data: Data dictionary to validate
            required_fields: List of required field names
            data_name: Name of data for error messages (default: "input")

        Raises:
            ValueError: If any required fields are missing
        """
        missing = [field for field in required_fields if field not in data or data[field] is None]
        if missing:
            error_msg = f"Missing required {data_name} fields: {', '.join(missing)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

    async def _validate_field_types(
        self,
        data: Dict[str, Any],
        field_types: Dict[str, type]
    ):
        """
        Validate field types in data.

        Args:
            data: Data dictionary to validate
            field_types: Dict of field_name -> expected_type

        Raises:
            TypeError: If any field has wrong type
        """
        for field, expected_type in field_types.items():
            if field in data and data[field] is not None:
                if not isinstance(data[field], expected_type):
                    error_msg = (
                        f"Field '{field}' has wrong type: "
                        f"expected {expected_type.__name__}, "
                        f"got {type(data[field]).__name__}"
                    )
                    self.logger.error(error_msg)
                    raise TypeError(error_msg)

    async def _validate_range(
        self,
        value: float,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        field_name: str = "value"
    ):
        """
        Validate that value is within specified range.

        Args:
            value: Value to validate
            min_value: Minimum allowed value (inclusive)
            max_value: Maximum allowed value (inclusive)
            field_name: Name of field for error messages

        Raises:
            ValueError: If value is out of range
        """
        if min_value is not None and value < min_value:
            error_msg = f"{field_name} must be >= {min_value}, got {value}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        if max_value is not None and value > max_value:
            error_msg = f"{field_name} must be <= {max_value}, got {value}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

    # ========================================================================
    # ERROR HANDLING UTILITIES
    # ========================================================================

    async def _retry_on_failure(
        self,
        operation: Callable,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        exponential_backoff: bool = True,
        retry_exceptions: tuple = (Exception,)
    ) -> Any:
        """
        Retry operation on failure with exponential backoff.

        Args:
            operation: Async function to retry
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (seconds)
            exponential_backoff: Use exponential backoff if True
            retry_exceptions: Tuple of exceptions to retry on

        Returns:
            Result of successful operation

        Raises:
            Last exception if all retries fail
        """
        last_exception = None

        for attempt in range(1, max_retries + 1):
            try:
                return await operation()
            except retry_exceptions as e:
                last_exception = e
                if attempt < max_retries:
                    delay = retry_delay * (2 ** (attempt - 1)) if exponential_backoff else retry_delay
                    self.logger.warning(
                        f"Attempt {attempt}/{max_retries} failed, retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(f"All {max_retries} attempts failed")

        raise last_exception

    async def _safe_execute(
        self,
        operation: Callable,
        default_value: Any = None,
        log_errors: bool = True
    ) -> Any:
        """
        Safely execute operation, returning default value on error.

        Args:
            operation: Async function to execute
            default_value: Value to return on error (default: None)
            log_errors: Whether to log errors (default: True)

        Returns:
            Operation result or default_value on error
        """
        try:
            return await operation()
        except Exception as e:
            if log_errors:
                self.logger.error(f"Safe execution failed: {e}", exc_info=True)
            return default_value

    # ========================================================================
    # SERVICE STATISTICS
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """
        Get service statistics.

        Returns:
            Dictionary with service statistics
        """
        avg_duration = None
        if self._operation_durations:
            avg_duration = round(sum(self._operation_durations) / len(self._operation_durations) * 1000, 2)

        return {
            "service_name": self.get_service_name(),
            "operations_count": self._operations_count,
            "errors_count": self._errors_count,
            "success_rate": (
                round((self._operations_count - self._errors_count) / self._operations_count * 100, 2)
                if self._operations_count > 0 else 0.0
            ),
            "last_operation_time": self._last_operation_time.isoformat() if self._last_operation_time else None,
            "last_error_time": self._last_error_time.isoformat() if self._last_error_time else None,
            "avg_operation_duration_ms": avg_duration,
            "recent_operations_count": len(self._operation_durations)
        }

    def reset_stats(self):
        """Reset service statistics (useful for testing)."""
        self._operations_count = 0
        self._errors_count = 0
        self._last_operation_time = None
        self._last_error_time = None
        self._operation_durations = []
        self.logger.debug(f"{self.get_service_name()} statistics reset")
