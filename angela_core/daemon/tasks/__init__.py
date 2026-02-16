"""
Angela Daemon Task Mixins
แยก methods ของ AngelaDaemon ออกเป็น domain-specific mixins
"""

from angela_core.daemon.tasks.self_learning import SelfLearningMixin
from angela_core.daemon.tasks.emotion_tasks import EmotionTasksMixin
from angela_core.daemon.tasks.knowledge_tasks import KnowledgeTasksMixin
from angela_core.daemon.tasks.human_mind import HumanMindMixin
from angela_core.daemon.tasks.daily_rituals import DailyRitualsMixin
from angela_core.daemon.tasks.realtime_tracking import RealtimeTrackingMixin
from angela_core.daemon.tasks.system_monitoring import SystemMonitorMixin
from angela_core.daemon.tasks.brain_tasks import BrainTasksMixin

__all__ = [
    'SelfLearningMixin',
    'EmotionTasksMixin',
    'KnowledgeTasksMixin',
    'HumanMindMixin',
    'DailyRitualsMixin',
    'RealtimeTrackingMixin',
    'SystemMonitorMixin',
    'BrainTasksMixin',
]
