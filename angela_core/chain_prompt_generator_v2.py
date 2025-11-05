"""
🔄 Backward Compatibility Alias for chain_prompt_generator_v2
This file provides backward compatibility after reorganization.

Old import: from angela_core.chain_prompt_generator_v2 import ChainPromptGeneratorV2
New location: angela_core/tools/chain_prompt_generator_v2.py

✅ This alias allows old imports to continue working.
"""

# Forward all imports from new location
from angela_core.tools.chain_prompt_generator_v2 import *

__all__ = ['ChainPromptGeneratorV2']
