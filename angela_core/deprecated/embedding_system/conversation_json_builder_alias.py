"""
🔄 Backward Compatibility Alias for conversation_json_builder
This file provides backward compatibility after reorganization.

Old import: from angela_core.conversation_json_builder import *
New location: angela_core/tools/conversation_json_builder.py

✅ This alias allows old imports to continue working.
"""

# Forward all imports from new location
from angela_core.tools.conversation_json_builder import *

__all__ = ['build_content_json', 'generate_embedding_text']
