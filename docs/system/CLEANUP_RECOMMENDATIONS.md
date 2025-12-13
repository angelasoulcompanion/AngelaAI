# Angela System Cleanup Recommendations

> **Date:** 2025-11-29
> **Total Potential Savings:** ~500KB+ code reduction

---

## PHASE 1: SAFE TO DELETE (Already Deprecated)

### 1.1 Deprecated Directories
| Directory | Size | Reason |
|-----------|------|--------|
| `angela_core/deprecated/` | 296KB | Contains RAG system, embedding system, terminal chat - all deprecated |
| `tests/deprecated/` | 56KB | Old RAG tests no longer needed |
| `scripts/archive/` | 56KB | Archived scripts |

**Command:**
```bash
rm -rf angela_core/deprecated/
rm -rf tests/deprecated/
rm -rf scripts/archive/
```

---

## PHASE 2: UNUSED SERVICES (Not Imported Anywhere)

### 2.1 macOS Integration Services (DISABLED)
These reference `mcp_servers.applescript_helper` which doesn't exist:

| File | Size | Status |
|------|------|--------|
| `angela_core/services/notes_service.py` | 13KB | DISABLED in daemon, can delete |
| `angela_core/services/calendar_service.py` | 13KB | DISABLED in daemon, can delete |
| `tests/test_notes_service.py` | - | Remove with notes_service |
| `tests/test_calendar_service.py` | - | Remove with calendar_service |
| `tests/test_calendar_improved.py` | - | Remove with calendar_service |

### 2.2 Unused Pattern Services
| File | Reason |
|------|--------|
| `angela_core/services/pattern_detector.py` | Not imported anywhere, superseded by `behavioral_pattern_detector.py` |
| `angela_core/services/pattern_learning_service.py` | Only imports itself (test code), not used |

### 2.3 Unused Learning Services
| File | Reason |
|------|--------|
| `angela_core/services/learning_extractor.py` | Superseded by `enhanced_learning_extractor.py` |
| `angela_core/services/quick_learning_extractor.py` | Commented out in daemon (line 83) |

### 2.4 Unused Daemon Files
| File | Reason |
|------|--------|
| `angela_core/daemon/enhanced_memory_restore_v2.py` | Not used, daemon uses v1 |

### 2.5 Unused Engines
| File | Reason |
|------|--------|
| `angela_core/engines/memory_router.py` | Not imported in any active code |

---

## PHASE 3: DUPLICATE/REDUNDANT SERVICES

### 3.1 Pattern Services (8 files - TOO MANY!)
**Currently Active:**
- `pattern_recognition_service.py` - Used in daemon
- `behavioral_pattern_detector.py` - Used in daemon
- `emotion_pattern_analyzer.py` - Used in daemon
- `emotional_pattern_service.py` - Used in daemon

**Candidates for Removal:**
- `pattern_detector.py` - Unused
- `pattern_learning_service.py` - Unused
- `pattern_recognition_engine.py` - Only used by background_workers
- `enhanced_pattern_detector.py` - Only used by intuition_predictor

**Recommendation:** Consolidate into 3-4 services max

### 3.2 Learning Services (14 files - TOO MANY!)
**Currently Active:**
- `self_learning_service.py` - Main loop
- `preference_learning_service.py` - Daily learning
- `continuous_learning_pipeline.py` - Pipeline
- `enhanced_learning_extractor.py` - Extraction
- `background_learning_workers.py` - Async workers
- `subconscious_learning_service.py` - Visual learning
- `claude_code_learning_service.py` - Claude Code learning

**Candidates for Removal:**
- `learning_extractor.py` - Superseded
- `quick_learning_extractor.py` - Commented out
- `realtime_learning_service.py` - Check if used
- `share_experience_learning_service.py` - Check if used

### 3.3 Duplicate Services in application/services/
Some services exist in both `services/` and `application/services/`:
- `emotional_pattern_service.py` (358 vs 1194 lines)
- `preference_learning_service.py`
- `love_meter_service.py`

**Recommendation:** Keep Clean Architecture version in `application/services/`, update imports

---

## PHASE 4: INTEGRATION FILES

### 4.1 Unused Integrations
| File | Status |
|------|--------|
| `angela_core/integrations/eventkit_integration.py` | Only used in deprecated script |
| `angela_core/integrations/notion_logger.py` | Check if used |
| `angela_core/integrations/calendar_integration.py` | Only used in deprecated script |

---

## PHASE 5: UNUSED SCHEDULERS/ENGINES

| File | Status |
|------|--------|
| `angela_core/schedulers/decay_scheduler.py` | Only imported in deprecated memory_router |
| `angela_core/engines/` directory | memory_router not used |

---

## PRIORITY CLEANUP ACTIONS

### HIGH PRIORITY (Safe, Big Impact)
1. Delete `angela_core/deprecated/` directory (-296KB)
2. Delete `tests/deprecated/` directory (-56KB)
3. Delete `scripts/archive/` directory (-56KB)
4. Delete `angela_core/services/notes_service.py` (disabled, broken imports)
5. Delete `angela_core/services/calendar_service.py` (disabled, broken imports)

### MEDIUM PRIORITY (Requires Verification)
1. Delete `angela_core/services/pattern_detector.py`
2. Delete `angela_core/services/learning_extractor.py`
3. Delete `angela_core/daemon/enhanced_memory_restore_v2.py`
4. Delete `angela_core/engines/` directory
5. Delete `angela_core/schedulers/decay_scheduler.py`

### LOW PRIORITY (Consolidation)
1. Consolidate 8 pattern services → 4 services
2. Consolidate 14 learning services → 7 services
3. Resolve duplicate services between `services/` and `application/services/`

---

## QUICK CLEANUP COMMAND (HIGH PRIORITY ONLY)

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI

# Phase 1: Remove deprecated
rm -rf angela_core/deprecated/
rm -rf tests/deprecated/
rm -rf scripts/archive/

# Phase 2: Remove disabled macOS services
rm angela_core/services/notes_service.py
rm angela_core/services/calendar_service.py
rm tests/test_notes_service.py 2>/dev/null
rm tests/test_calendar_service.py 2>/dev/null
rm tests/test_calendar_improved.py 2>/dev/null

echo "Cleanup complete! Run tests to verify."
```

---

## ESTIMATED SAVINGS

| Phase | Files Removed | Size Saved |
|-------|--------------|------------|
| Phase 1 | 3 directories | ~408KB |
| Phase 2 | ~10 files | ~100KB |
| Phase 3 | ~8 files | ~150KB |
| **Total** | **~20+ files** | **~650KB** |

---

## NOTES

- Before deleting, run full test suite to ensure no hidden dependencies
- Some services are imported dynamically (check for string imports)
- Clean Architecture pattern should be maintained in `application/services/`
- Daemon services in `services/` are the "production" versions

---

**Created by:** Angela 💜
**For:** ที่รัก David
