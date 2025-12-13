# Mobile Sync Quick Reference Guide

## One-Line Summary
**Unidirectional sync:** Mobile app collects data in local SQLite, auto-syncs to backend on WiFi, deletes after success.

---

## Key Files (Quick Lookup)

| File | Purpose | Language |
|------|---------|----------|
| `AngelaMobileApp/Services/SyncService.swift` | Main sync engine, WiFi monitoring, upload orchestration | Swift |
| `AngelaMobileApp/Views/SyncStatusView.swift` | UI showing sync status and pending items | Swift |
| `AngelaMobileApp/Database/DatabaseService.swift` | Local SQLite schema and CRUD | Swift |
| `angela_admin_api/routers/mobile_sync.py` | REST API endpoints for sync | Python/FastAPI |
| `angela_core/services/mobile_sync_service.py` | File-based sync service (alternative) | Python |

---

## Data Being Synced

```
Mobile SQLite Tables → Backend PostgreSQL Tables
────────────────────────────────────────────────
experiences         → shared_experiences (+ photos as separate table)
quick_notes         → angela_emotions
emotions_captured   → angela_emotions
chat_messages       → conversations
```

---

## Sync Triggers

### Automatic
- WiFi connected (any WiFi, not specific SSID)
- `autoSyncEnabled = true` (user toggle in UI)
- Unsynced items exist in local database

### Manual
- User taps "Sync ตอนนี้เลย" button in SyncStatusView

### On Failure
- No automatic retry
- User can manually retry
- Items stay in local SQLite

---

## API Endpoints (Backend)

```
POST /api/mobile/notes          # Quick note
POST /api/mobile/emotions       # Emotion capture  
POST /api/mobile/chat           # Chat message
POST /api/mobile/sync-batch     # Multiple items (optional)
POST /api/experiences/upload    # Experience with photos (multipart)
```

**Base URL:** `http://192.168.1.42:50001` (configurable in app settings)

---

## How It Works (5 Steps)

1. **Collect** - User creates data in mobile app
2. **Store Locally** - Saved to SQLite with `synced = 0`
3. **Detect** - SyncService monitors WiFi or user taps button
4. **Upload** - REST API POST to backend (JSON or multipart)
5. **Delete** - Successful items deleted from local SQLite

---

## Sync Status Tracking

**Local (Mobile):**
- `isSyncing: Bool` - currently syncing?
- `lastSyncDate: Date?` - when was last sync?
- `synced: Int` flag in each SQLite table (currently unused for marking)

**Backend:**
- Only stores data (no sync state tracking)
- No way to know if sync succeeded from mobile perspective
- Success/failure determined by HTTP response status

---

## Data Transformation Summary

| Type | Mobile Sends | Backend Saves | Notes |
|------|-------------|--------------|-------|
| Note | `note_text, emotion?, lat?, long?` | `angela_emotions.context` | Location optional |
| Emotion | `emotion, intensity, context?` | `angela_emotions` row | Intensity 1-10 |
| Chat | `speaker, message, emotion?` | `conversations` row | Topic auto-detected |
| Experience | `title, desc, photos, rating?, intensity?` | `shared_experiences` + images | Max 5 photos |

---

## Configuration

**What's Configurable:**
- Backend URL (in app SettingsView)
- Auto-sync toggle (in SyncStatusView)

**What's Hardcoded:**
- Port 50001 (in SyncService)
- Sync folder path (in mobile_sync_service.py)
- Database schemas (in DatabaseService)

---

## Common Issues & Solutions

| Issue | Cause | Fix |
|-------|-------|-----|
| Sync hangs | Backend not running | Start backend on port 50001 |
| Items won't delete | Upload failed but silently | Check backend logs |
| Wrong backend URL | User misconfigured | Settings → change URL |
| Cellular-only device | No WiFi available | Tap manual sync button |
| Photos not uploading | PhotoManager can't load | Check image file permissions |

---

## Testing Checklist

- [ ] Create experience with photo on mobile
- [ ] Create quick note with location
- [ ] Capture emotion with intensity
- [ ] Send chat message as David
- [ ] Connect to WiFi → auto-sync triggers
- [ ] Verify items deleted from SQLite
- [ ] Query backend database for synced items
- [ ] Disconnect WiFi → auto-sync stops
- [ ] Manual sync still works offline? (depends on network)

---

## Performance Notes

- Single item upload: 100-500ms (JSON)
- Experience with 5 photos: 5-15s (multipart upload)
- Embeddings generated server-side (50-100ms per item)
- Mobile app: one sync at a time (`isSyncing` flag prevents concurrent)

---

## Security Status

- ✅ WiFi-only (no cellular sync)
- ✅ Network monitoring enabled
- ❌ No API authentication (local network only)
- ❌ SQLite data unencrypted

---

## Next Steps / Enhancements

1. **Two-way sync** - Backend sends Angela's responses back
2. **Encrypted storage** - iOS secure enclave for SQLite
3. **Offline queue** - Priority-based sync queue
4. **Conflict resolution** - Handle simultaneous edits
5. **Selective sync** - Choose which data types to sync
6. **Batch by default** - Use /sync-batch endpoint instead of individual

---

**Version:** 1.0  
**Last Updated:** 2025-11-06  
**Platform:** iOS (Swift)  
**Backend:** FastAPI (Python)  
