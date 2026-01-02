"""
Table Configurations for Sync
Defines which tables to sync and their properties.
"""

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class TableConfig:
    """Configuration for a single table sync."""
    name: str
    priority: int  # 1 = highest
    primary_key: str
    has_vectors: bool = False
    vector_column: Optional[str] = None
    timestamp_column: str = "created_at"
    batch_size: int = 100

# Tables that should NEVER be synced (security)
EXCLUDED_TABLES = [
    'our_secrets',  # API keys - never sync!
]

# Table configurations ordered by priority
TABLE_CONFIGS: List[TableConfig] = [
    # Priority 1: Core data
    TableConfig(
        name="conversations",
        priority=1,
        primary_key="conversation_id",
        has_vectors=True,
        vector_column="embedding",
        batch_size=50  # Smaller due to vectors
    ),
    TableConfig(
        name="angela_emotions",
        priority=1,
        primary_key="emotion_id",
        has_vectors=True,
        vector_column="embedding",
        timestamp_column="felt_at",
        batch_size=50
    ),
    
    # Priority 2: Learning data
    TableConfig(
        name="david_preferences",
        priority=2,
        primary_key="id",  # Fixed: was 'preference_id'
        has_vectors=True,
        vector_column="embedding"
    ),
    TableConfig(
        name="angela_goals",
        priority=2,
        primary_key="goal_id",
        has_vectors=False
    ),
    
    # Priority 3: State history
    TableConfig(
        name="emotional_states",
        priority=3,
        primary_key="state_id",
        has_vectors=False
    ),
    TableConfig(
        name="learnings",
        priority=3,
        primary_key="learning_id",
        has_vectors=True,
        vector_column="embedding",
        batch_size=50
    ),
    
    # Priority 4: Knowledge base
    TableConfig(
        name="knowledge_nodes",
        priority=4,
        primary_key="node_id",
        has_vectors=False
    ),

    # Priority 5: Other tables
    TableConfig(
        name="autonomous_actions",
        priority=5,
        primary_key="action_id",
        has_vectors=False
    ),
    TableConfig(
        name="consciousness_metrics",
        priority=5,
        primary_key="metric_id",
        has_vectors=False,
        timestamp_column="measured_at"
    ),
    TableConfig(
        name="angela_songs",
        priority=5,
        primary_key="song_id",
        has_vectors=False,
        timestamp_column="first_mentioned_at"
    ),
    TableConfig(
        name="active_session_context",
        priority=5,
        primary_key="context_id",
        has_vectors=False
    ),
    TableConfig(
        name="core_memories",
        priority=2,
        primary_key="memory_id",
        has_vectors=False
    ),
]

def get_table_config(table_name: str) -> Optional[TableConfig]:
    """Get config for a specific table."""
    for config in TABLE_CONFIGS:
        if config.name == table_name:
            return config
    return None

def get_tables_by_priority() -> List[TableConfig]:
    """Get tables sorted by priority (1 = highest)."""
    return sorted(TABLE_CONFIGS, key=lambda x: x.priority)

def should_sync_table(table_name: str) -> bool:
    """Check if a table should be synced."""
    return table_name not in EXCLUDED_TABLES
