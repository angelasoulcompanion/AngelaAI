"""
Angela Daemon Task Mixins
แยก methods ของ AngelaDaemon ออกเป็น domain-specific mixins
"""

from angela_core.daemon.tasks.self_learning import SelfLearningMixin
from angela_core.daemon.tasks.knowledge_tasks import KnowledgeTasksMixin
from angela_core.daemon.tasks.daily_rituals import DailyRitualsMixin
from angela_core.daemon.tasks.system_monitoring import SystemMonitorMixin

__all__ = [
    'SelfLearningMixin',
    'KnowledgeTasksMixin',
    'DailyRitualsMixin',
    'SystemMonitorMixin',
]
