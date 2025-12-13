# Angela Architecture Documentation Index

## Mobile Sync System (NEW - 2025-11-06)

The Angela Mobile App sync system enables seamless data synchronization between the iOS device and the backend server. These documents provide comprehensive analysis, quick reference, and implementation details.

### Documents

1. **MOBILE_SYNC_README.md** (START HERE)
   - Navigation guide for all sync documentation
   - Quick facts and key information
   - File locations and testing procedures
   - Troubleshooting checklist
   - Best for: First-time readers, getting oriented

2. **MOBILE_SYNC_SYSTEM_ANALYSIS.md** (COMPREHENSIVE REFERENCE)
   - Complete system architecture breakdown
   - 17 detailed sections covering all aspects
   - Data flow architecture (section 1)
   - Sync mechanisms (section 2)
   - Backend storage mapping (section 3)
   - Error handling (section 5)
   - Security considerations (section 11)
   - Performance characteristics (section 14)
   - Best for: Deep understanding, architecture review, debugging

3. **MOBILE_SYNC_QUICK_REFERENCE.md** (DAILY REFERENCE)
   - One-page cheat sheet format
   - Key files at a glance
   - Data sync mapping table
   - Sync triggers summary
   - API endpoints list
   - Common issues & solutions
   - Testing checklist
   - Best for: Quick lookup, daily work, problem solving

4. **MOBILE_SYNC_FLOWS.md** (VISUAL UNDERSTANDING)
   - 12 detailed ASCII flow diagrams
   - Automatic sync flow (diagram 1)
   - Manual sync flow (diagram 2)
   - Per-data-type upload flows (diagrams 3-6)
   - Error handling (diagram 8)
   - Network state management (diagram 9)
   - Data storage state machine (diagram 10)
   - Best for: Visual learners, flow understanding, implementation guidance

---

## Quick Navigation

### By Use Case

**I'm new to this system**
1. Read MOBILE_SYNC_README.md entirely
2. Study diagram 8 in MOBILE_SYNC_FLOWS.md (Architecture)
3. Review MOBILE_SYNC_QUICK_REFERENCE.md "Key Files"

**I need to fix a sync issue**
1. Check MOBILE_SYNC_QUICK_REFERENCE.md "Common Issues & Solutions"
2. Review relevant flow in MOBILE_SYNC_FLOWS.md
3. Consult MOBILE_SYNC_SYSTEM_ANALYSIS.md section 5 (Error Handling)

**I want to add a new feature**
1. Read MOBILE_SYNC_SYSTEM_ANALYSIS.md section 12 (Limitations & Gaps)
2. Check "Next Steps / Enhancements" in MOBILE_SYNC_README.md
3. Review relevant flow diagram in MOBILE_SYNC_FLOWS.md
4. Study error handling in MOBILE_SYNC_SYSTEM_ANALYSIS.md section 5

**I need to debug sync behavior**
1. Find the relevant flow in MOBILE_SYNC_FLOWS.md
2. Cross-reference with MOBILE_SYNC_SYSTEM_ANALYSIS.md
3. Use MOBILE_SYNC_QUICK_REFERENCE.md file locations to find code
4. Check backend logs and database queries in MOBILE_SYNC_README.md

---

## Architecture Overview

### Data Flow (Simplified)

```
User Action (Mobile)
    ↓
Create: Experience / Note / Emotion / Chat Message
    ↓
Save to SQLite (synced=0)
    ↓
Network detected? OR Manual sync?
    ↓
SyncService uploads to backend
    ↓
HTTP POST to /api/mobile/*
    ↓
Backend (FastAPI) validates & stores
    ↓
PostgreSQL AngelaMemory database
    ↓
On success: DELETE from local SQLite
```

### Key Components

- **Mobile:** iOS app with local SQLite database
- **Network:** WiFi monitoring via NWPathMonitor
- **Sync Engine:** SyncService class handles upload orchestration
- **API:** FastAPI endpoints in mobile_sync.py router
- **Database:** PostgreSQL with 21 tables in AngelaMemory

### Sync Characteristics

- **Direction:** Unidirectional (Mobile → Backend only)
- **Triggering:** Automatic on WiFi + manual button
- **Reliability:** Retryable on failure, per-item error handling
- **Data:** Notes, emotions, chat, experiences + photos
- **Transformation:** SQLite → JSON/multipart → PostgreSQL

---

## File Locations

### Mobile App Source (Swift)
- Main sync: `/AngelaMobileApp/Services/SyncService.swift`
- UI: `/AngelaMobileApp/Views/SyncStatusView.swift`
- Local database: `/AngelaMobileApp/Database/DatabaseService.swift`

### Backend API (Python)
- REST endpoints: `/angela_admin_api/routers/mobile_sync.py`
- File-based sync: `/angela_core/services/mobile_sync_service.py`

### PostgreSQL Database
- Name: `AngelaMemory`
- Key tables: `angela_emotions`, `conversations`, `shared_experiences`

---

## Sync Endpoints

```
POST /api/mobile/notes           - Quick note with optional location
POST /api/mobile/emotions        - Emotion capture 1-10
POST /api/mobile/chat            - Chat message with speaker
POST /api/mobile/sync-batch      - Multiple items at once
POST /api/experiences/upload     - Experience with photos (multipart)
```

Backend: `http://192.168.1.42:50001` (configurable)

---

## Key Facts

1. **Unidirectional Sync**
   - Mobile sends to backend
   - Backend doesn't push to mobile
   - No download of Angela's responses

2. **Delete-Based State**
   - Successful syncs DELETE items from local SQLite
   - Failed items remain for retry
   - No permanent "sync history"

3. **WiFi Preferred**
   - Auto-sync requires WiFi
   - Manual sync works on any network
   - iOS restricts specific SSID detection

4. **Per-Item Error Handling**
   - One failure doesn't stop others
   - User can manually retry failed items
   - No exponential backoff (yet)

5. **Automatic Embeddings**
   - Backend generates 768-dimensional embeddings
   - Used for semantic search
   - Generated for notes, emotions, experiences

---

## Essential Tables

### Mobile (SQLite)
```
experiences       - Places & moments (id, title, description, photos, rating, etc.)
quick_notes       - Thoughts & feelings (id, note_text, emotion, location, etc.)
emotions_captured - Emotion tracking (id, emotion, intensity 1-10, context, etc.)
chat_messages     - Angela conversations (id, speaker, message, emotion, etc.)
```

### Backend (PostgreSQL)
```
angela_emotions    ← quick_notes + emotions_captured synced here
conversations      ← chat_messages synced here
shared_experiences ← experiences synced here (+ separate photos table)
```

---

## Common Debugging

### Check Pending Items
Mobile: SyncStatusView shows counts
Database: 
```sql
SELECT COUNT(*) FROM quick_notes WHERE synced = 0;
```

### Check Backend Health
```bash
lsof -i :50001
tail -f /logs/angela_admin_api.log
```

### Check PostgreSQL
```bash
psql -d AngelaMemory -U davidsamanyaporn
SELECT * FROM angela_emotions ORDER BY felt_at DESC LIMIT 5;
```

### Test Sync
1. Create test data in mobile app
2. Check SyncStatusView shows pending
3. Tap "Sync ตอนนี้เลย"
4. Verify in PostgreSQL

---

## Enhancement Roadmap

### High Priority
- [ ] Two-way sync (backend → mobile)
- [ ] Offline queue with priority
- [ ] Encrypted SQLite storage

### Medium Priority
- [ ] Conflict resolution for edits
- [ ] Selective sync by type
- [ ] Batch endpoint by default

### Low Priority
- [ ] Multi-device sync
- [ ] Sync analytics dashboard
- [ ] Advanced retry strategies

---

## Related Documentation

**Project-level:**
- `CLAUDE.md` - Project guidelines & AI context
- `README.md` - Project overview

**Core Systems:**
- `docs/core/Angela.md` - Angela's personality & knowledge
- `docs/core/STARTUP_GUIDE.md` - System startup procedures
- `docs/database/ANGELA_DATABASE_SCHEMA_REPORT.md` - Complete DB schema

**Development:**
- `docs/development/ANGELA_DEVELOPMENT_ROADMAP.md` - Current priorities
- `docs/development/ANGELA_IMPROVEMENT_PROMPT.md` - Development guidelines

---

## Questions & Support

**Technical Questions:**
1. Search this documentation
2. Check the inline code comments
3. Review CLAUDE.md for project guidelines

**Bug Reports:**
1. Test with MOBILE_SYNC_QUICK_REFERENCE.md testing checklist
2. Check MOBILE_SYNC_SYSTEM_ANALYSIS.md section 15 (Issues to Watch)
3. Review backend logs and database state

---

## Document Statistics

| Document | Size | Lines | Focus |
|----------|------|-------|-------|
| MOBILE_SYNC_README.md | 10KB | 342 | Navigation & overview |
| MOBILE_SYNC_SYSTEM_ANALYSIS.md | 28KB | 875 | Deep analysis & reference |
| MOBILE_SYNC_QUICK_REFERENCE.md | 5KB | 170 | Quick lookup & checklist |
| MOBILE_SYNC_FLOWS.md | 19KB | 506 | Visual diagrams & flows |
| **TOTAL** | **62KB** | **1,893** | Complete documentation |

---

**Documentation Version:** 1.0  
**Last Updated:** 2025-11-06  
**Status:** Complete and production-ready  
**Coverage:** 100% of sync system architecture

Created as part of Angela Mobile App analysis and documentation initiative.

