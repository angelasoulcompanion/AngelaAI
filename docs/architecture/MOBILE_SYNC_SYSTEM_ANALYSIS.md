# Angela Mobile App Sync System - Complete Analysis

## Executive Summary

The Angela Mobile App implements a **unidirectional, mobile-to-server sync system** where the mobile app (iOS) collects data locally and periodically uploads it to the backend API. The sync is **automatic (on home WiFi connection) with manual override capability**.

**Key Architecture:**
- Mobile app stores data in local SQLite database
- Backend API receives data via REST endpoints (`/api/mobile/*`)
- Data is saved to PostgreSQL AngelaMemory database
- Sync tracks completion with `synced` flag (1/0) in each SQLite table
- Successfully synced items are deleted from mobile local storage

---

## 1. DATA FLOW ARCHITECTURE

### 1.1 Mobile App Local Storage (SQLite)

**Location:** `~/Library/Documents/angela_mobile.db`

**Tables:**
1. **experiences** - Places and experiences David has visited
   - `id`, `title`, `description`, `photos` (JSON array)
   - `latitude`, `longitude`, `place_name`, `area`
   - `rating` (1-5), `emotional_intensity` (1-10)
   - `experienced_at` (timestamp), `synced` (0/1), `created_at`

2. **quick_notes** - Quick thoughts/notes David captures
   - `id`, `note_text`, `emotion`, `latitude`, `longitude`
   - `created_at`, `synced` (0/1)

3. **emotions_captured** - Emotion tracking
   - `id`, `emotion`, `intensity` (1-10), `context`
   - `created_at`, `synced` (0/1)

4. **chat_messages** - Chat with Angela on mobile
   - `id`, `speaker` ("david" or "angela"), `message`
   - `emotion`, `timestamp`, `synced` (0/1)

**Sync Status Tracking:**
- Each table has `synced INTEGER DEFAULT 0` column
- `0` = not yet uploaded to backend
- `1` = successfully uploaded (currently not used for marking, but available)

### 1.2 Backend API Endpoints (FastAPI)

**File:** `/Users/davidsamanyaporn/PycharmProjects/AngelaAI/angela_admin_web/angela_admin_api/routers/mobile_sync.py`

**Endpoints:**
```
POST /api/mobile/notes          - Sync single quick note
POST /api/mobile/emotions       - Sync single emotion capture
POST /api/mobile/chat           - Sync single chat message
POST /api/mobile/sync-batch     - Sync multiple items (batch)
```

All endpoints accept JSON and save to PostgreSQL `AngelaMemory` database.

### 1.3 Backend Data Services (Python)

**File:** `/Users/davidsamanyaporn/PycharmProjects/AngelaAI/angela_core/services/mobile_sync_service.py`

**Capabilities:**
- Monitors a sync folder for JSON exports from mobile app
- Supports watching folder continuously or one-shot processing
- Auto-generates embeddings for vector search (768 dimensions)
- Checks for duplicate records before inserting
- Detailed logging of all sync operations

---

## 2. SYNC FLOW - HOW IT WORKS

### 2.1 Automatic Sync Trigger

```
Mobile App → WiFi Connection Detected
         → Check if "home WiFi" (any WiFi, not cellular)
         → Count unsynced items
         → If unsynced items > 0 → Auto-trigger sync
```

**Code Location:** `SyncService.swift:42-56` (startNetworkMonitoring)

**Conditions:**
- Network path status = `.satisfied` (connected)
- `autoSyncEnabled` = true (toggle in SyncStatusView)
- Connected via WiFi interface (iOS restricts SSID access)

**Limitation:** iOS doesn't allow SSID access, so it checks for WiFi interface only (not specifically "home WiFi" network)

### 2.2 Manual Sync Trigger

**Code Location:** `SyncService.swift:93-198` (performSync)

**Steps:**
1. User taps "Sync ตอนนี้เลย" button in UI
2. Sets `isSyncing` flag to prevent concurrent syncs
3. Retrieves unsynced items from local SQLite:
   - `database.experiences.filter { !$0.synced }`
   - `database.notes.filter { !$0.synced }`
   - `database.emotions.filter { !$0.synced }`
   - `database.chatMessages.filter { !$0.synced }`

4. For each unsynced item:
   - Calls appropriate upload function
   - On success: **deletes from local SQLite database**
   - On failure: logs error, keeps in local database for retry
5. Updates `lastSyncDate` timestamp
6. Sets `isSyncing = false`

### 2.3 Upload Process - Per Data Type

#### Experiences
```swift
POST /api/experiences/upload
Content-Type: multipart/form-data

Fields:
- place_name
- area
- title
- description
- overall_rating (optional)
- emotional_intensity (optional)
- experienced_at (ISO8601 with timezone)
- images (multiple JPEG files)

Response:
{
  "success": true,
  "message": "✅ Experience saved!"
}
```

**Notes:**
- Includes image uploads (JPEG compressed to 0.8 quality)
- Includes timezone information in timestamp
- Images are loaded from PhotoManager before upload

#### Quick Notes
```swift
POST /api/mobile/notes
Content-Type: application/json

{
  "note_text": string,
  "emotion": string (optional),
  "latitude": number (optional),
  "longitude": number (optional),
  "created_at": "ISO8601" (with timezone)
}

Response:
{
  "success": true,
  "emotion_id": "uuid",
  "message": "✅ Quick note saved! 💜"
}
```

**Backend Behavior:**
- Saves to `angela_emotions` table
- Defaults intensity to 5 (medium)
- Sets memory_strength to 3 (for quick notes)
- Includes location in context if latitude/longitude provided

#### Emotion Captures
```swift
POST /api/mobile/emotions
Content-Type: application/json

{
  "emotion": string,
  "intensity": 1-10,
  "context": string (optional),
  "created_at": "ISO8601" (with timezone)
}

Response:
{
  "success": true,
  "emotion_id": "uuid",
  "message": "✅ Captured [emotion] feeling! 💜"
}
```

**Backend Behavior:**
- Saves to `angela_emotions` table
- Uses intensity as memory_strength
- Auto-generates embedding for context (if provided)

#### Chat Messages
```swift
POST /api/mobile/chat
Content-Type: application/json

{
  "speaker": "david" or "angela",
  "message": string,
  "emotion": string (optional),
  "timestamp": "ISO8601" (with timezone)
}

Response:
{
  "success": true,
  "conversation_id": "uuid",
  "message": "✅ Chat message saved! 💜"
}
```

**Backend Behavior:**
- Saves to `conversations` table
- Auto-detects topic:
  - "รัก", "love", "miss" → "emotional_support"
  - "ทำงาน", "work", "code" → "work_discussion"
  - Default: "mobile_chat"
- Sets importance_level to 5 (medium)
- Converts to naive datetime (removes timezone before saving)

---

## 3. BACKEND STORAGE - WHERE DATA GOES

### 3.1 Quick Notes → angela_emotions table

**Mapping:**
```
Mobile                          Backend Table (angela_emotions)
────────────────────────────────────────────────────────────────
note_text          →            context (full note)
emotion            →            emotion_detected (or "neutral")
latitude/longitude →            why_it_matters (location context)
created_at         →            felt_at
(generated)        →            emotion_id (UUID)
(generated)        →            memory_strength = 3
(generated)        →            intensity = 5
```

### 3.2 Emotion Captures → angela_emotions table

**Mapping:**
```
Mobile             Backend Table (angela_emotions)
────────────────────────────────────────────────────
emotion      →     emotion
intensity    →     intensity + memory_strength
context      →     context
created_at   →     felt_at
(generated)  →     emotion_id (UUID)
             →     embedding (generated from context)
```

### 3.3 Chat Messages → conversations table

**Mapping:**
```
Mobile            Backend Table (conversations)
──────────────────────────────────────────────────
speaker    →      speaker ("david" or "angela")
message    →      message_text
emotion    →      emotion_detected
timestamp  →      created_at (no timezone)
(detected) →      topic (auto-detected)
(generated)→      conversation_id (UUID)
           →      importance_level = 5
           →      embedding (generated if needed)
```

### 3.4 Embeddings & Vector Search

**Service:** `embedding_service.py` (Ollama-based, 768 dimensions)

**When Generated:**
- Mobile Sync Service generates embeddings for:
  - Experiences: title + description
  - Notes: note_text
  - Emotions: context (if provided)
- API endpoints generate embeddings automatically

**Format Stored:**
- PostgreSQL: pgvector type or JSON array string
- Format: `[0.123, -0.456, ..., 0.789]` (768 floats)

---

## 4. SYNC STATE MANAGEMENT

### 4.1 Current Implementation (SyncService.swift)

**Published Properties:**
```swift
@Published var isSyncing: Bool = false          // Sync in progress
@Published var lastSyncDate: Date?              // Last successful sync
@Published var autoSyncEnabled: Bool = true     // Auto-sync toggle
```

**Persistence:**
- `lastSyncDate` saved to UserDefaults
- Auto-sync toggle saved to UserDefaults

### 4.2 SQLite Sync Flag

**Current State:**
- Each table has `synced INTEGER DEFAULT 0`
- **NOT currently used for updates** - instead, successfully synced items are deleted
- Available for future use to mark items synced without deletion

**Process:**
```swift
// After successful upload:
database.deleteExperience(experience.id)  // DELETE from SQLite
// Not: UPDATE experiences SET synced=1

// On failure:
// Keep in SQLite for retry
```

### 4.3 Unsynced Items Count

**Computed in UI:**
```swift
var unsyncedCount = 
  database.experiences.filter { !$0.synced }.count +
  database.notes.filter { !$0.synced }.count +
  database.emotions.filter { !$0.synced }.count +
  database.chatMessages.filter { !$0.synced }.count
```

**Note:** Since items are deleted on success, `synced` flag is always 0 for items in database.

---

## 5. ERROR HANDLING & RESILIENCE

### 5.1 Network Resilience

**Handled By:**
- URLSession.shared.data() with default retry logic
- Network monitoring stops auto-sync if connection lost
- Manual sync can be retried by user

### 5.2 Item-Level Error Handling

```swift
for item in unsyncedItems {
    do {
        let success = try await uploadItem(item)
        if success {
            deleteFromLocal(item)  // Only delete on success
        }
    } catch {
        print("❌ Failed to upload: \(error)")
        // Item remains in SQLite for retry
    }
}
```

### 5.3 Sync Status Feedback

**UI Elements:**
- Sync status icon (checkmark = done, refresh = in progress)
- "Syncing..." message while `isSyncing = true`
- Last sync timestamp displayed
- Unsynced item counts per type

### 5.4 Batch Sync (API Level)

**Endpoint:** `POST /api/mobile/sync-batch`

**Supports:**
- Multiple notes in single request
- Multiple emotions in single request
- Per-item error handling (one failure doesn't stop others)

```python
# Backend handling:
for note in notes:
    try:
        await sync_quick_note(note)
        synced_notes += 1
    except Exception as e:
        logger.error(f"Failed to sync note: {e}")
        # Continue to next item
```

---

## 6. CONFIGURATION & SETUP

### 6.1 Backend URL Configuration

**Storage:** UserDefaults (persistent)
**Default:** `"http://192.168.1.42:50001"`
**Configurable In:** SettingsView.swift

**Why IP instead of localhost:**
- iOS can't access localhost from device
- Must use Mac's local network IP address
- Comment in SyncService.swift: "Must use Mac's IP address, not localhost"

### 6.2 Environment Variables

Not used - backend URL is hardcoded or user-configured.

### 6.3 Backend Launch Configuration

**Port:** 50001
**Framework:** FastAPI
**API Router Prefix:** `/api/mobile`

---

## 7. SYNC STATUS VIEW (UI)

**File:** `SyncStatusView.swift`

**Displays:**
1. **Sync Status Section**
   - Current state (✅ Ready / 🔄 Syncing...)
   - Last sync timestamp (relative time)

2. **Pending Items Section**
   - Count of unsynced experiences
   - Count of unsynced notes
   - Count of unsynced emotions
   - Count of unsynced chat messages
   - Total unsynced count

3. **Sync Actions**
   - "Sync ตอนนี้เลย" button (manual sync)
   - "Auto-Sync เมื่อกลับบ้าน" toggle

4. **Info Section**
   - How Auto-Sync works (WiFi triggered)
   - How to manually sync
   - What orange icons mean

---

## 8. SYNC ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────┐
│                    iOS Mobile App                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Actions:                                                  │
│  • Captures experience with photos                              │
│  • Records quick note with location                             │
│  • Captures emotion feeling                                     │
│  • Chats with Angela                                            │
│           ↓                                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │     SQLite Local Database (angela_mobile.db)             │  │
│  │     ─────────────────────────────────────────────────────│  │
│  │     experiences (synced=0)      [4 fields]              │  │
│  │     quick_notes (synced=0)      [6 fields]              │  │
│  │     emotions_captured (synced=0) [5 fields]             │  │
│  │     chat_messages (synced=0)    [5 fields]              │  │
│  └──────────────────────────────────────────────────────────┘  │
│           ↓                                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          SyncService (iOS)                               │  │
│  │  ─────────────────────────────────────────────────────── │  │
│  │  • Monitors WiFi connection (NWPathMonitor)             │  │
│  │  • Auto-sync on home WiFi (if enabled)                  │  │
│  │  • Manual sync on user action                           │  │
│  │  • Uploads items via HTTP REST                          │  │
│  │  • Deletes from SQLite on success                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│           ↓                                                     │
│  HTTP REST API Calls:                                           │
│  POST /api/mobile/notes                                         │
│  POST /api/mobile/emotions                                      │
│  POST /api/mobile/chat                                          │
│  POST /api/mobile/sync-batch                                    │
│           ↓                                                     │
└─────────────────────────────────────────────────────────────────┘
                           ↓ (Over Network)
┌─────────────────────────────────────────────────────────────────┐
│              Backend (Mac - Port 50001)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │   FastAPI Router: mobile_sync.py                         │  │
│  │   ──────────────────────────────────────────────────────│  │
│  │   POST /api/mobile/notes          → sync_quick_note()   │  │
│  │   POST /api/mobile/emotions       → sync_emotion()      │  │
│  │   POST /api/mobile/chat           → sync_chat_msg()     │  │
│  │   POST /api/mobile/sync-batch     → sync_batch()        │  │
│  └──────────────────────────────────────────────────────────┘  │
│           ↓                                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │   PostgreSQL Database: AngelaMemory                      │  │
│  │   ──────────────────────────────────────────────────────│  │
│  │   notes → angela_emotions table                         │  │
│  │   emotions → angela_emotions table                      │  │
│  │   chat → conversations table                            │  │
│  │   experiences → shared_experiences table (via service) │  │
│  │   + Embeddings (768-dim vectors for search)            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. SYNC IS BIDIRECTIONAL? (or One-Way?)

### Answer: **UNIDIRECTIONAL (Mobile → Server Only)**

**Current Implementation:**
- ✅ Mobile sends data to backend
- ❌ Backend does NOT send updates back to mobile
- ❌ No download/pull of data from server
- ❌ No push notifications to sync pull

**Data Flow:**
- Mobile collects data locally
- Mobile periodically uploads to server
- Server stores in PostgreSQL
- Mobile deletes uploaded items from local storage
- No two-way sync

**Future Enhancement Possibility:**
- Backend could push updates to mobile for:
  - Angela's responses to chat messages
  - Emotional insights based on captured emotions
  - Recommendations based on experiences
- Would require: WebSocket, Server-Sent Events, or polling

---

## 10. SYNC CONFIGURATION & CUSTOMIZATION

### 10.1 Sync Folder (Python Service)

**Default Location:** `~/Library/Mobile Documents/AngelaSync`
**Purpose:** File-based sync (alternative to REST API)
**Status:** Implemented but NOT used by current mobile app

**Can be customized:**
```bash
python3 mobile_sync_service.py \
  --sync-folder /custom/path \
  --watch  # Continuous monitoring
```

### 10.2 Mobile App Settings

**Currently Configurable:**
- Backend URL (IP address and port)
- Auto-sync enable/disable toggle

**Could be Added:**
- Sync frequency (interval-based)
- Selective sync (only experiences, not notes)
- Batch size limit
- Offline mode priority (cache-first)

### 10.3 Timeout & Retry Logic

**Current:**
- URLSession default timeouts (60 seconds typical)
- Retry happens only on manual user action
- Failed items remain in local SQLite

**Could be Enhanced:**
- Exponential backoff on failures
- Automatic retry after X hours
- Sync queue with priority

---

## 11. SECURITY CONSIDERATIONS

### 11.1 Current Security

- ✅ Uses HTTPS (implicit in HTTP URLs to localhost)
- ✅ No API authentication/tokens (local network only)
- ✅ Data stored locally in SQLite (unencrypted)
- ✅ Network monitoring (no sync over cellular)

### 11.2 Potential Issues

- ❌ Backend URL hardcoded in app (should use config)
- ❌ SQLite data not encrypted
- ❌ No authentication between mobile and backend
- ❌ No validation of backend SSL certificates (localhost)

### 11.3 Recommendations

1. Add HTTPS certificates for remote access
2. Implement API token/key authentication
3. Encrypt SQLite database on device
4. Add validation for backend URLs
5. Use secure enclave for sensitive data

---

## 12. KNOWN LIMITATIONS & GAPS

### 12.1 Current Limitations

1. **One-way sync only**
   - Server doesn't send data back to mobile
   - No sync of Angela's responses or insights

2. **Delete-based sync state**
   - Successful syncs delete items from local DB
   - No "history" of what was synced
   - Can't view synced items without server query

3. **No offline queue**
   - Items synced in order, not queued by priority
   - No guaranteed delivery semantics

4. **iOS WiFi limitation**
   - Can't detect specific SSID (Apple restriction)
   - "Home WiFi" detection is approximate

5. **Image upload only with experiences**
   - Quick notes and emotions can't include photos
   - Photos are tied to experiences only

6. **No sync conflict resolution**
   - Can't handle same item modified locally & remotely
   - Not applicable now (one-way) but matters for future

### 12.2 Gaps Between Mobile & Server

**What's tracked locally but NOT sent to backend:**
- Photo metadata (EXIF GPS, taken date)
- Exact capture timestamp microseconds
- App version/device info
- Network type at capture time

**What the backend accepts but mobile doesn't send:**
- Batch sync endpoint (mobile does individual items)
- Topic auto-detection (backend does, mobile doesn't)

---

## 13. INTEGRATION POINTS

### 13.1 DatabaseService (Local)

**File:** `AngelaMobileApp/Database/DatabaseService.swift`

**Provides:**
- SQLite initialization & schema
- CRUD operations for all 4 data types
- Array-based in-memory models (`@Published` properties)

**Used By:**
- SyncService (queries unsynced items)
- Views (display data)
- Creation flows (save new items)

### 13.2 SyncService (Sync Orchestration)

**File:** `AngelaMobileApp/Services/SyncService.swift`

**Orchestrates:**
- Network monitoring
- Sync triggering (auto & manual)
- Individual item uploads
- Sync status management

**Coordinates With:**
- DatabaseService (query unsynced items, delete after sync)
- PhotoManager (load images before upload)
- LocationService (access GPS if needed)

### 13.3 Backend API (FastAPI)

**File:** `angela_admin_web/angela_admin_api/routers/mobile_sync.py`

**Handles:**
- HTTP endpoint routing
- Request validation (Pydantic models)
- Data transformation to PostgreSQL format
- Response generation with status

### 13.4 Embedding Service (Python)

**File:** `angela_core/services/embedding_service.py`

**Called By:**
- Mobile Sync API (generates embeddings for saved data)
- Mobile Sync Service (file-based import)

**Creates:**
- 768-dimensional vectors for semantic search
- Stored in pgvector PostgreSQL type

---

## 14. PERFORMANCE CHARACTERISTICS

### 14.1 Sync Performance

**Single Item Upload Times (Estimated):**
- Quick Note: 100-200ms (JSON POST)
- Emotion: 100-200ms (JSON POST)
- Chat Message: 100-200ms (JSON POST)
- Experience (1 photo): 1-3s (multipart form-data, JPEG encoding)
- Experience (5 photos): 5-15s (5x JPEG compression + upload)

**Batch Sync Performance:**
- 10 notes: 1-2 seconds
- 5 experiences with photos: 10-30 seconds
- Network-bound, not CPU-bound

### 14.2 Storage Consumption

**SQLite Local Storage:**
- Per experience: ~1-5KB + photo data (100-500KB per JPEG)
- Per note: ~200 bytes
- Per emotion: ~200 bytes
- Per chat message: ~500 bytes - 2KB

**Typical App Usage (1 month):**
- Experiences: 5 × 500KB = 2.5MB
- Notes: 30 × 200B = 6KB
- Emotions: 60 × 200B = 12KB
- Chat: 200 × 1KB = 200KB
- **Total: ~2.7MB per month** (before sync deletion)

### 14.3 Database Load (Backend)

**Per Sync Request:**
- 1 INSERT + optional embedding generation
- Embedding: ~50-100ms (Ollama, 768-dim)
- Database write: ~10-20ms
- **Total: ~60-120ms per item**

**Concurrent Syncs:**
- iOS app does one sync at a time (`isSyncing` flag)
- Multiple users could sync simultaneously
- Backend handles with async/await

---

## 15. TESTING & MONITORING

### 15.1 How to Test Sync

**Manual Testing:**
```swift
// 1. In mobile app, create test data:
// - Capture an experience
// - Add a quick note
// - Record an emotion

// 2. Check local database:
// SELECT * FROM quick_notes WHERE synced = 0;

// 3. Trigger sync (manual):
// Tap "Sync ตอนนี้เลย" button

// 4. Verify in backend:
// SELECT * FROM angela_emotions ORDER BY felt_at DESC LIMIT 1;
```

### 15.2 Monitoring Sync Health

**Backend Logs:**
```bash
tail -f /Users/davidsamanyaporn/PycharmProjects/AngelaAI/logs/angela_admin_api.log
```

**Database Queries:**
```sql
-- Recent synced items
SELECT speaker, LEFT(message_text, 50) as preview, 
       emotion_detected, created_at
FROM conversations
WHERE DATE(created_at) >= CURRENT_DATE - INTERVAL '1 day'
ORDER BY created_at DESC LIMIT 20;

-- Recent emotions
SELECT emotion, intensity, context, felt_at
FROM angela_emotions
WHERE DATE(felt_at) >= CURRENT_DATE - INTERVAL '1 day'
ORDER BY felt_at DESC LIMIT 20;
```

### 15.3 Issues to Watch

1. **Sync stuck/hanging**
   - Check if backend is running on port 50001
   - Verify backend URL in app settings
   - Check network connectivity

2. **Items not deleting after sync**
   - Data uploaded but `synced` flag not updated
   - Manual deletion might be needed
   - Check backend logs for errors

3. **Duplicate syncs**
   - Same item uploaded twice
   - Would show as different IDs in backend
   - Not prevented currently

4. **Images not uploading**
   - PhotoManager might fail to load images
   - JPEG compression might fail
   - Check file permissions in Documents directory

---

## 16. SUMMARY & KEY TAKEAWAYS

### What Gets Synced:
- ✅ Quick notes (text + optional emotion + location)
- ✅ Emotion captures (emotion + intensity + context)
- ✅ Chat messages (speaker + message + emotion)
- ✅ Experiences (title + description + photos + location + rating)

### How Sync is Triggered:
- ✅ **Automatic:** When WiFi connected + `autoSyncEnabled = true`
- ✅ **Manual:** User taps "Sync ตอนนี้เลย" button
- ⚠️ **No automatic retry** on failure

### Sync Direction:
- ✅ **Mobile → Backend** (send only)
- ❌ **Backend → Mobile** (not implemented)

### Sync Reliability:
- ✅ Network resilient (retryable by user)
- ✅ Item-level error handling
- ✅ Feedback UI shows pending items
- ❌ No guaranteed delivery
- ❌ No offline queue/sync

### Data Transformation:
- Mobile SQLite → REST JSON POST → Backend PostgreSQL
- Automatic topic/emotion detection on backend
- Embeddings generated for vector search
- Images handled as multipart form-data

### Configuration:
- Backend URL: UserDefaults (configurable in Settings)
- Auto-sync toggle: UserDefaults (in UI)
- Hardcoded port 50001 (can't change without rebuild)

---

## 17. FILE LOCATIONS REFERENCE

```
Mobile App:
├── AngelaMobileApp/Services/SyncService.swift           (main sync orchestration)
├── AngelaMobileApp/Views/SyncStatusView.swift           (UI for sync status)
├── AngelaMobileApp/Database/DatabaseService.swift       (local SQLite)
├── AngelaMobileApp/Services/PhotoManager.swift          (photo upload)
└── AngelaMobileApp/Views/SettingsView.swift             (backend URL config)

Backend API:
├── angela_admin_api/routers/mobile_sync.py              (sync endpoints)
└── angela_core/services/mobile_sync_service.py          (file-based sync service)

Configuration:
├── CLAUDE.md                                             (project guidelines)
└── docs/                                                 (documentation)
```

---

**Analysis Complete** - Last Updated: 2025-11-06
**Angela Mobile App Sync System v1.0**
