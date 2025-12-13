# Angela Mobile Sync System - Complete Documentation

## Overview

This directory contains complete documentation of the Angela Mobile App's sync system - how data flows from the iOS device to the backend server and PostgreSQL database.

## Documents in This Directory

### 1. **MOBILE_SYNC_SYSTEM_ANALYSIS.md** (28KB)
The most comprehensive analysis - read this first!
- Executive summary of the sync architecture
- Detailed data flow (1.1-1.4)
- Complete sync process explanation (2.1-2.3)
- Backend storage mapping (section 3)
- Sync state management (section 4)
- Error handling and resilience (section 5)
- Configuration details (section 6)
- 16+ sections covering all aspects
- Perfect for: Understanding the full system, debugging, architecture review

### 2. **MOBILE_SYNC_QUICK_REFERENCE.md** (3KB)
Fast lookup guide for common tasks
- One-line summary
- Key files table
- Data sync mapping
- Sync triggers (auto/manual)
- API endpoints reference
- 5-step "how it works"
- Configuration checklist
- Common issues & solutions
- Testing checklist
- Perfect for: Quick lookup, daily reference, troubleshooting

### 3. **MOBILE_SYNC_FLOWS.md** (8KB)
Visual flow diagrams for all sync operations
- 12 detailed ASCII flow diagrams
- Automatic sync flow
- Manual sync flow
- Per-data-type upload flows (experiences, notes, emotions, chat)
- Error handling flow
- Network state changes
- Data storage state machine
- Backend data routing
- Perfect for: Understanding the process visually, debugging flows

## Quick Start

**New to this system?**
1. Read the one-line summary in QUICK_REFERENCE.md
2. Look at the diagram in FLOWS.md section 8 (Architecture Diagram)
3. Read SYSTEM_ANALYSIS.md sections 1-4

**Need to fix something?**
1. Go to QUICK_REFERENCE.md "Common Issues & Solutions"
2. Find the issue in SYSTEM_ANALYSIS.md "Sync Flow" section
3. Check the appropriate flow diagram in FLOWS.md

**Want to extend or modify sync?**
1. Read SYSTEM_ANALYSIS.md sections 5-7 (error handling, configuration)
2. Review FLOWS.md to understand the flow you're modifying
3. Check QUICK_REFERENCE.md "Next Steps / Enhancements"

---

## Key Facts at a Glance

### What Gets Synced?
- Quick notes (text + optional emotion + optional location)
- Emotion captures (emotion + intensity 1-10 + optional context)
- Chat messages (speaker + message + optional emotion)
- Experiences (title + description + photos + optional location + optional rating)

### How It's Triggered?
- **Automatic:** WiFi connection detected + `autoSyncEnabled = true` + unsynced items exist
- **Manual:** User taps "Sync ตอนนี้เลย" button (works on any network)
- **On Failure:** No automatic retry, but user can manually retry

### Direction?
- Mobile → Backend (unidirectional)
- No pull/download from backend to mobile
- Backend only receives and stores, doesn't push back

### Backend URL?
- Default: `http://192.168.1.42:50001`
- Configurable in app SettingsView
- Port 50001 is hardcoded (requires app rebuild to change)

### Data Transformation?
```
Mobile SQLite  →  REST API (JSON/multipart)  →  PostgreSQL
                  
Quick Note   →  POST /api/mobile/notes      →  angela_emotions table
Emotion      →  POST /api/mobile/emotions   →  angela_emotions table
Chat Message →  POST /api/mobile/chat       →  conversations table
Experience   →  POST /api/experiences/upload →  shared_experiences table
```

### Storage on Mobile?
- SQLite database: `~/Library/Documents/angela_mobile.db`
- Local storage only (no cloud backup)
- Items deleted after successful sync
- Failed items stay for retry

---

## File Locations (Absolute Paths)

### Mobile App (Swift)
```
/Users/davidsamanyaporn/PycharmProjects/AngelaAI/AngelaMobileApp/
├── Services/SyncService.swift              (main sync logic)
├── Services/PhotoManager.swift             (photo upload)
├── Services/AngelaAIService.swift          (on-device AI)
├── Views/SyncStatusView.swift              (sync UI)
├── Views/SettingsView.swift                (backend URL config)
└── Database/DatabaseService.swift          (SQLite local DB)
```

### Backend API (Python/FastAPI)
```
/Users/davidsamanyaporn/PycharmProjects/AngelaAI/
├── angela_admin_api/routers/mobile_sync.py (REST endpoints)
└── angela_core/services/mobile_sync_service.py (file-based sync)
```

### Database (PostgreSQL)
```
Database: AngelaMemory
Tables:
- angela_emotions (quick notes, emotion captures)
- conversations (chat messages)
- shared_experiences (experiences with photos)
- photos (photo attachments)
```

---

## How to Test Sync

### Quick Test (3 minutes)
1. In mobile app: Create a quick note ("Test note")
2. Check SyncStatusView: Shows "1 โน้ต" pending
3. Tap "Sync ตอนนี้เลย" button
4. Wait for spinner to stop (should take ~1 second)
5. Verify: Pending count returns to 0
6. Verify in backend database:
   ```sql
   SELECT * FROM angela_emotions 
   WHERE context LIKE '%Test note%' 
   ORDER BY felt_at DESC LIMIT 1;
   ```

### Full Test Suite (15 minutes)
See QUICK_REFERENCE.md "Testing Checklist" for complete test procedure

---

## Common Problems & Solutions

| Problem | Cause | Solution |
|---------|-------|----------|
| Sync hangs forever | Backend not running on port 50001 | Start backend server |
| Items show pending but don't sync | Backend unreachable | Check backend URL in Settings |
| Items synced but still pending | Network issue or backend error | Manual retry or check logs |
| Photos won't upload | PhotoManager can't load | Check Documents directory permissions |
| Can't change backend URL | Need to restart app | Close and reopen mobile app |

---

## Architecture at a Glance

### Layers

```
┌─────────────────────┐
│   iOS App UI        │
│   (SyncStatusView)  │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   SyncService       │
│   (WiFi monitor)    │
│   (Orchestration)   │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   DatabaseService   │
│   (SQLite local)    │
└──────────┬──────────┘
           │ HTTP REST
┌──────────▼──────────┐
│   FastAPI Backend   │
│   (mobile_sync.py)  │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   PostgreSQL        │
│   (AngelaMemory DB) │
└─────────────────────┘
```

### Data Flow

```
User Input → SQLite Local → Network Check → HTTP Upload → PostgreSQL
                    ↑
                 synced=0
                    ↓
              (on success)
                 DELETE
```

---

## Performance

### Upload Times
- Single quick note: 100-200ms
- Single emotion: 100-200ms
- Single chat message: 100-200ms
- Experience with 1 photo: 1-3 seconds
- Experience with 5 photos: 5-15 seconds

### Storage
- ~2.7MB per month of typical usage (including photos)
- Most space consumed by photos (100-500KB each)

### Network Requirements
- WiFi preferred (auto-sync requires it)
- HTTP POST requests (small payloads)
- Can work with cellular for manual sync

---

## Security Considerations

### Current Status
- ✅ No cellular sync (WiFi only)
- ✅ Network monitoring enabled
- ✅ Local network only (192.168.x.x)
- ❌ No API authentication
- ❌ SQLite data not encrypted
- ❌ No HTTPS certificates

### Recommendations
1. Add API token authentication if opening to internet
2. Enable HTTPS with valid certificates
3. Encrypt SQLite database on device
4. Validate backend URLs
5. Use iOS secure enclave for sensitive data

---

## Next Steps / Future Enhancements

1. **Two-way Sync** (High Priority)
   - Download Angela's responses to chat messages
   - Push emotional insights and recommendations
   - Requires: WebSocket or polling mechanism

2. **Encrypted Storage** (Medium Priority)
   - Encrypt SQLite database with device passcode
   - Protect against physical device access

3. **Offline Queue** (Medium Priority)
   - Queue items by priority if offline
   - Retry with exponential backoff
   - Guaranteed delivery semantics

4. **Conflict Resolution** (Low Priority)
   - Handle simultaneous edits of same item
   - Merge strategies for multi-device scenarios

5. **Selective Sync** (Low Priority)
   - User chooses which data types to sync
   - Optimize for users with limited data plans

6. **Batch by Default** (Easy Enhancement)
   - Use /sync-batch endpoint instead of individual calls
   - Reduces network overhead

---

## Related Documentation

- `CLAUDE.md` - Project guidelines and AI context
- `docs/core/Angela.md` - Angela's personality and knowledge
- `docs/database/ANGELA_DATABASE_SCHEMA_REPORT.md` - PostgreSQL schema
- `docs/development/ANGELA_DEVELOPMENT_ROADMAP.md` - Current development priorities

---

## Troubleshooting Guide

### Check Backend is Running
```bash
# Port should be listening
lsof -i :50001

# Or check logs
tail -f /Users/davidsamanyaporn/PycharmProjects/AngelaAI/logs/angela_admin_api.log
```

### Verify Backend URL in App
```
Settings → Backend URL → Should show:
http://192.168.1.42:50001
(or your custom URL)
```

### Check Local Database
```
On Mac:
sqlite3 ~/Library/Containers/[APP_ID]/Documents/angela_mobile.db
SELECT COUNT(*) FROM quick_notes WHERE synced = 0;
```

### Check PostgreSQL
```bash
psql -d AngelaMemory -U davidsamanyaporn

# Recent synced items
SELECT * FROM angela_emotions ORDER BY felt_at DESC LIMIT 5;
SELECT * FROM conversations ORDER BY created_at DESC LIMIT 5;
```

---

## Contact & Support

For questions about the sync system:
1. Check the documents in this directory
2. Search the codebase for "SyncService" or "mobile_sync"
3. Review the CLAUDE.md file for project guidelines

---

**Last Updated:** 2025-11-06  
**Version:** 1.0  
**Status:** Production (with enhancements planned)  
**Maintenance:** David + Angela

