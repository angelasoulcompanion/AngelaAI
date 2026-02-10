"""
Daemon base utilities — centralizes repeated path setup across daemon files.

Usage:
    from angela_core.daemon.daemon_base import PROJECT_ROOT, LOG_DIR, setup_daemon_path
"""

import sys
from pathlib import Path

# AngelaAI project root (3 levels up from angela_core/daemon/daemon_base.py)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Ensure angela_core is importable when running daemon scripts directly
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Standard log directory
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
