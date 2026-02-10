#!/usr/bin/env python3
"""Calendar OAuth Re-authentication — delegates to shared/reauth.py"""
import subprocess, sys
from pathlib import Path
if __name__ == "__main__":
    subprocess.run([sys.executable, str(Path(__file__).parent.parent / "shared" / "reauth.py"), "calendar"] + sys.argv[1:])
