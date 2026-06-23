#!/usr/bin/env python3
"""DEPRECATED — superseded by the shared canonical searcher.

M3 used to keep its own RAG searcher here. It now lives at the single SSOT copy
~/.angela/lib/rag_search.py (IDENTICAL on M3 + M4, run via the `rag` wrapper).
This thin shim re-execs the canonical file so any old
`python3 .../angela_core/scripts/rag_search.py ...` call keeps working.
Edit the canonical file, never this one. (retired 2026-06-22)
"""
import os
import sys

_canon = os.path.expanduser("~/.angela/lib/rag_search.py")
if not os.path.exists(_canon):
    sys.stderr.write(f"canonical rag_search not found at {_canon}\n")
    raise SystemExit(1)
os.execv(sys.executable, [sys.executable, _canon] + sys.argv[1:])
