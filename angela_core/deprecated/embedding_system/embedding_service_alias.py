"""
🔄 Backward Compatibility Alias for embedding_service
This file provides backward compatibility after reorganization.

Old import: from angela_core.embedding_service import embedding
New location: angela_core/daemon/embedding_service.py

✅ This alias allows old imports to continue working.
"""

# Forward all imports from new location
from angela_core.daemon.embedding_service import *
from angela_core.daemon.embedding_service import embedding

# For backward compatibility with different import styles
try:
    from angela_core.daemon.embedding_service import generate_embedding
except ImportError:
    # If generate_embedding doesn't exist, create alias
    generate_embedding = embedding.generate_embedding

__all__ = ['embedding', 'generate_embedding', 'AngelaEmbeddingService']
