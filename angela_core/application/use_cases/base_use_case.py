#!/usr/bin/env python3
"""
Base Use Case Implementation
Provides common patterns for all application use cases.

Use cases represent application-specific business rules and orchestrate
the flow of data between services, repositories, and domain entities.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import time

logger = logging.getLogger(__name__)

# Type variables for generic use case input/output
TInput = TypeVar('TInput')
TOutput = TypeVar('TOutput')


# ============================================================================
# USE CASE RESULT CLASSES
# ============================================================================

class ResultStatus(Enum):
    """Status of use case execution."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL_SUCCESS = "partial_success"
    VALIDATION_ERROR = "validation_error"


@dataclass
class UseCaseResult(Generic[TOutput]):
    """
    Standardized result wrapper for use case execution.

    Provides consistent structure for all use case results with
    success status, data, errors, and metadata.

    Attributes:
        success: Whether execution succeeded
        status: Detailed status (SUCCESS, FAILURE, etc.)
        data: Result data (if successful)
        error: Error message (if failed)
        errors: List of validation/business errors
        metadata: Additional metadata (duration, timestamps, etc.)

    Example:
        # Success
        return UseCaseResult(
            success=True,
            status=ResultStatus.SUCCESS,
            data=conversation,
            metadata={'duration_ms': 150}
        )

        # Failure
        return UseCaseResult(
            success=False,
            status=ResultStatus.FAILURE,
            error="Database connection failed"
        )

        # Validation error
        return UseCaseResult(
            success=False,
            status=ResultStatus.VALIDATION_ERROR,
            errors=["Message cannot be empty", "Model not found"]
        )
    """
    success: bool
    status: ResultStatus
    data: Optional[TOutput] = None
    error: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def ok(data: TOutput, metadata: Optional[Dict[str, Any]] = None) -> 'UseCaseResult[TOutput]':
        """
        Create successful result.

        Args:
            data: Result data
            metadata: Optional metadata

        Returns:
            Success result with data
        """
        return UseCaseResult(
            success=True,
            status=ResultStatus.SUCCESS,
            data=data,
            metadata=metadata or {}
        )

    @staticmethod
    def fail(
        error: str,
        status: ResultStatus = ResultStatus.FAILURE,
        errors: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'UseCaseResult':
        """
        Create failure result.

        Args:
            error: Primary error message
            status: Failure status (default: FAILURE)
            errors: List of additional errors
            metadata: Optional metadata

        Returns:
            Failure result with error details
        """
        return UseCaseResult(
            success=False,
            status=status,
            error=error,
            errors=errors or [],
            metadata=metadata or {}
        )

    @staticmethod
    def validation_error(
        errors: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'UseCaseResult':
        """
        Create validation error result.

        Args:
            errors: List of validation errors
            metadata: Optional metadata

        Returns:
            Validation error result
        """
        return UseCaseResult(
            success=False,
            status=ResultStatus.VALIDATION_ERROR,
            error="Validation failed",
            errors=errors,
            metadata=metadata or {}
        )


# ============================================================================
# BASE USE CASE
# ============================================================================

class BaseUseCase(ABC, Generic[TInput, TOutput]):
    """
    Abstract base use case with common execution patterns.

    Use cases represent application-specific business rules.
    They orchestrate services, repositories, and domain logic.

    Execution flow (Template Method Pattern):
    1. _before_execute() - Pre-execution hook
    2. _validate() - Input validation
    3. _execute_impl() - Main business logic (MUST OVERRIDE)
    4. _after_execute() - Post-execution hook
    5. _on_success() / _on_failure() - Result handlers

    Subclasses MUST:
    - Implement _execute_impl() with main business logic

    Subclasses MAY:
    - Override _validate() for custom input validation
    - Override _before_execute() for setup logic
    - Override _after_execute() for cleanup logic
    - Override _on_success() / _on_failure() for result handling

    Example:
        class SendMessageUseCase(BaseUseCase[SendMessageInput, SendMessageOutput]):
            def __init__(self, chat_service, conversation_repo):
                super().__init__()
                self.chat_service = chat_service
                self.conversation_repo = conversation_repo

            async def _validate(self, input: SendMessageInput) -> List[str]:
                errors = []
                if not input.message:
                    errors.append("Message cannot be empty")
                if len(input.message) > 10000:
                    errors.append("Message too long")
                return errors

            async def _execute_impl(self, input: SendMessageInput) -> SendMessageOutput:
                # Main business logic
                response = await self.chat_service.send(input.message)
                await self.conversation_repo.save(input.message, response)
                return SendMessageOutput(response=response)
    """

    def __init__(self):
        """Initialize base use case with logging and tracking."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._execution_count = 0
        self._success_count = 0
        self._failure_count = 0

    # ========================================================================
    # PUBLIC INTERFACE
    # ========================================================================

    async def execute(self, input: TInput) -> UseCaseResult[TOutput]:
        """
        Execute use case with full error handling and logging.

        This is the main entry point for use case execution.
        It implements the Template Method pattern.

        Args:
            input: Use case input data

        Returns:
            UseCaseResult with success/failure status and data/errors
        """
        start_time = time.time()
        self._execution_count += 1

        try:
            # Pre-execution hook
            await self._before_execute(input)

            # Validate input
            validation_errors = await self._validate(input)
            if validation_errors:
                result = UseCaseResult.validation_error(
                    errors=validation_errors,
                    metadata=self._build_metadata(start_time)
                )
                await self._on_failure(input, result)
                return result

            # Execute main logic
            self.logger.debug(f"Executing {self.__class__.__name__}")
            data = await self._execute_impl(input)

            # Build success result
            result = UseCaseResult.ok(
                data=data,
                metadata=self._build_metadata(start_time)
            )

            # Post-execution hook
            await self._after_execute(input, result)

            # Success handler
            await self._on_success(input, result)
            self._success_count += 1

            return result

        except Exception as e:
            # Build failure result
            self.logger.error(f"Use case execution failed: {e}", exc_info=True)
            result = UseCaseResult.fail(
                error=str(e),
                metadata=self._build_metadata(start_time, error=e)
            )

            # Failure handler
            await self._on_failure(input, result)
            self._failure_count += 1

            return result

    # ========================================================================
    # ABSTRACT METHODS - MUST BE IMPLEMENTED BY SUBCLASSES
    # ========================================================================

    @abstractmethod
    async def _execute_impl(self, input: TInput) -> TOutput:
        """
        Implement main use case business logic.

        Subclasses MUST override this method.

        Args:
            input: Validated input data

        Returns:
            Use case output data

        Raises:
            Any exceptions will be caught and converted to failure results
        """
        ...

    # ========================================================================
    # OPTIONAL OVERRIDE METHODS
    # ========================================================================

    async def _validate(self, input: TInput) -> List[str]:
        """
        Validate use case input.

        Subclasses can override this for custom validation.

        Args:
            input: Input data to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        return []

    async def _before_execute(self, input: TInput):
        """
        Pre-execution hook.

        Called before validation and execution.
        Useful for setup, logging, or initialization.

        Args:
            input: Use case input
        """
        pass

    async def _after_execute(self, input: TInput, result: UseCaseResult[TOutput]):
        """
        Post-execution hook.

        Called after successful execution.
        Useful for cleanup, logging, or side effects.

        Args:
            input: Use case input
            result: Execution result
        """
        pass

    async def _on_success(self, input: TInput, result: UseCaseResult[TOutput]):
        """
        Success handler.

        Called when execution succeeds.
        Useful for events, notifications, or analytics.

        Args:
            input: Use case input
            result: Success result
        """
        self.logger.info(
            f"✅ {self.__class__.__name__} completed successfully",
            extra=result.metadata
        )

    async def _on_failure(self, input: TInput, result: UseCaseResult):
        """
        Failure handler.

        Called when execution fails or validation fails.
        Useful for error logging, alerts, or recovery.

        Args:
            input: Use case input
            result: Failure result
        """
        self.logger.error(
            f"❌ {self.__class__.__name__} failed: {result.error}",
            extra={
                "errors": result.errors,
                "status": result.status.value,
                **result.metadata
            }
        )

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _build_metadata(
        self,
        start_time: float,
        error: Optional[Exception] = None
    ) -> Dict[str, Any]:
        """
        Build metadata for result.

        Args:
            start_time: Execution start timestamp
            error: Optional error if execution failed

        Returns:
            Metadata dictionary
        """
        duration_ms = round((time.time() - start_time) * 1000, 2)

        metadata = {
            "use_case": self.__class__.__name__,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
            "execution_count": self._execution_count
        }

        if error:
            metadata["error_type"] = type(error).__name__

        return metadata

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """
        Get use case execution statistics.

        Returns:
            Dictionary with execution stats
        """
        return {
            "use_case": self.__class__.__name__,
            "execution_count": self._execution_count,
            "success_count": self._success_count,
            "failure_count": self._failure_count,
            "success_rate": (
                round(self._success_count / self._execution_count * 100, 2)
                if self._execution_count > 0 else 0.0
            )
        }

    def reset_stats(self):
        """Reset execution statistics (useful for testing)."""
        self._execution_count = 0
        self._success_count = 0
        self._failure_count = 0
        self.logger.debug(f"{self.__class__.__name__} statistics reset")
