"""
Angela Secretary Package
Intelligent task detection and reminder management
"""

from .task_manager import TaskManager, TaskIntent, task_manager
from .secretary_service import SecretaryService, secretary

__all__ = [
    'TaskManager',
    'TaskIntent',
    'task_manager',
    'SecretaryService',
    'secretary'
]
