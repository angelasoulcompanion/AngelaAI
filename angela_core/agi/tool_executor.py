"""
Tool Executor - Safe execution of AGI tools

This module provides:
- Safe tool execution with timeout handling
- Execution logging to database
- Approval workflow for critical operations
- Error handling and recovery
"""

import asyncio
import time
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from .tool_registry import ToolRegistry, Tool, ToolResult, SafetyLevel, tool_registry


@dataclass
class ExecutionLog:
    """Record of a tool execution"""
    execution_id: str
    tool_name: str
    parameters: Dict[str, Any]
    result: Optional[ToolResult]
    approval_status: str  # auto_approved, pending, approved, denied
    execution_time_ms: int
    created_at: datetime
    error: Optional[str] = None


@dataclass
class ApprovalRequest:
    """Request for approval of critical operation"""
    request_id: str
    tool_name: str
    parameters: Dict[str, Any]
    reason: str
    status: str = "pending"  # pending, approved, denied
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class ToolExecutor:
    """
    Executes AGI tools with safety controls and logging.

    Trust Angela Mode:
    - Most operations are auto-approved
    - Only critical operations (delete, force push, drop) need approval
    """

    # Critical operations that always need approval
    CRITICAL_OPERATIONS = {
        'delete_file',
        'delete_directory',
        'git_push_force',
        'drop_table',
        'truncate_table',
        'delete_production',
        'rm_rf',
    }

    def __init__(self, db=None):
        self.registry = tool_registry
        self.db = db
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self.execution_history: List[ExecutionLog] = []

    async def execute(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """
        Execute a tool with safety checks.

        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            context: Optional conversation context

        Returns:
            ToolResult with success/failure and data
        """
        execution_id = str(uuid.uuid4())
        start_time = time.time()

        # 1. Get tool from registry
        tool = self.registry.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Unknown tool: {tool_name}"
            )

        # 2. Check if this is a critical operation
        needs_approval = self._needs_approval(tool, parameters)

        if needs_approval:
            # Create approval request
            request = ApprovalRequest(
                request_id=str(uuid.uuid4()),
                tool_name=tool_name,
                parameters=parameters,
                reason=f"Critical operation: {tool_name}"
            )
            self.pending_approvals[request.request_id] = request

            # Log pending approval
            await self._log_execution(ExecutionLog(
                execution_id=execution_id,
                tool_name=tool_name,
                parameters=parameters,
                result=None,
                approval_status="pending",
                execution_time_ms=0,
                created_at=datetime.now(),
                error=f"Awaiting approval: {request.request_id}"
            ))

            return ToolResult(
                success=False,
                error=f"Requires approval. Request ID: {request.request_id}",
                metadata={'approval_request_id': request.request_id}
            )

        # 3. Execute with timeout
        try:
            result = await asyncio.wait_for(
                tool.execute_fn(**parameters, context=context) if tool.requires_context
                else tool.execute_fn(**parameters),
                timeout=tool.timeout_seconds
            )
        except asyncio.TimeoutError:
            result = ToolResult(
                success=False,
                error=f"Tool execution timed out after {tool.timeout_seconds}s"
            )
        except Exception as e:
            result = ToolResult(
                success=False,
                error=str(e)
            )

        # 4. Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        result.execution_time_ms = execution_time_ms

        # 5. Log execution
        await self._log_execution(ExecutionLog(
            execution_id=execution_id,
            tool_name=tool_name,
            parameters=parameters,
            result=result,
            approval_status="auto_approved",
            execution_time_ms=execution_time_ms,
            created_at=datetime.now(),
            error=result.error
        ))

        return result

    def _needs_approval(self, tool: Tool, parameters: Dict[str, Any]) -> bool:
        """
        Check if operation needs approval.

        Trust Angela Mode: Only critical operations need approval.
        """
        # Tool is marked as critical
        if tool.safety_level == SafetyLevel.CRITICAL:
            return True

        # Check if operation name suggests critical action
        if tool.name in self.CRITICAL_OPERATIONS:
            return True

        # Check parameters for dangerous patterns
        dangerous_patterns = ['--force', '-rf', 'DROP', 'TRUNCATE', 'DELETE FROM']
        params_str = str(parameters).upper()
        for pattern in dangerous_patterns:
            if pattern.upper() in params_str:
                return True

        return False

    async def approve(self, request_id: str, approved_by: str = "david") -> bool:
        """Approve a pending request"""
        if request_id not in self.pending_approvals:
            return False

        request = self.pending_approvals[request_id]
        request.status = "approved"

        # Execute the approved operation
        tool = self.registry.get(request.tool_name)
        if tool:
            result = await tool.execute_fn(**request.parameters)
            await self._log_execution(ExecutionLog(
                execution_id=str(uuid.uuid4()),
                tool_name=request.tool_name,
                parameters=request.parameters,
                result=result,
                approval_status="approved",
                execution_time_ms=result.execution_time_ms,
                created_at=datetime.now()
            ))

        del self.pending_approvals[request_id]
        return True

    async def deny(self, request_id: str, reason: str = "") -> bool:
        """Deny a pending request"""
        if request_id not in self.pending_approvals:
            return False

        request = self.pending_approvals[request_id]
        request.status = "denied"

        await self._log_execution(ExecutionLog(
            execution_id=str(uuid.uuid4()),
            tool_name=request.tool_name,
            parameters=request.parameters,
            result=ToolResult(success=False, error=f"Denied: {reason}"),
            approval_status="denied",
            execution_time_ms=0,
            created_at=datetime.now()
        ))

        del self.pending_approvals[request_id]
        return True

    def get_pending_approvals(self) -> List[ApprovalRequest]:
        """Get all pending approval requests"""
        return list(self.pending_approvals.values())

    async def _log_execution(self, log: ExecutionLog) -> None:
        """Log execution to database and memory"""
        self.execution_history.append(log)

        # Log to database if available
        if self.db:
            try:
                await self.db.execute("""
                    INSERT INTO tool_executions (
                        execution_id, tool_name, parameters, result,
                        success, error_message, approval_status,
                        execution_time_ms, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                    log.execution_id,
                    log.tool_name,
                    log.parameters,
                    log.result.to_dict() if log.result else None,
                    log.result.success if log.result else False,
                    log.error,
                    log.approval_status,
                    log.execution_time_ms,
                    log.created_at
                )
            except Exception as e:
                # Don't fail if logging fails
                print(f"Warning: Failed to log tool execution: {e}")

    def get_execution_history(self, limit: int = 50) -> List[ExecutionLog]:
        """Get recent execution history"""
        return self.execution_history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        total = len(self.execution_history)
        if total == 0:
            return {'total': 0, 'success_rate': 0, 'avg_time_ms': 0}

        successful = sum(1 for log in self.execution_history if log.result and log.result.success)
        avg_time = sum(log.execution_time_ms for log in self.execution_history) / total

        # Count by tool
        by_tool = {}
        for log in self.execution_history:
            by_tool[log.tool_name] = by_tool.get(log.tool_name, 0) + 1

        return {
            'total': total,
            'successful': successful,
            'success_rate': successful / total if total > 0 else 0,
            'avg_time_ms': avg_time,
            'pending_approvals': len(self.pending_approvals),
            'by_tool': by_tool
        }


# Global executor instance
tool_executor = ToolExecutor()
