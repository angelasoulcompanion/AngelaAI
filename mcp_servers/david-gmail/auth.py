#!/usr/bin/env python3
"""David Gmail OAuth Re-authentication — delegates to shared/reauth.py with --user david."""
import subprocess, sys
from pathlib import Path

if __name__ == "__main__":
    cmd = [
        sys.executable,
        str(Path(__file__).parent.parent / "shared" / "reauth.py"),
        "gmail",
        "--user",
        "david",
    ] + sys.argv[1:]
    subprocess.run(cmd)
