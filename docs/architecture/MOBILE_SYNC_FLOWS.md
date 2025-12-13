# Mobile Sync System - Flow Diagrams

## 1. Automatic Sync Flow (WiFi Triggered)

```
┌─────────────────────────────────────────────────────────────────────┐
│ USER ACTION: Captures Experience / Note / Emotion / Chat             │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
                ┌─────────────────────────────┐
                │ Save to Local SQLite        │
                │ (synced = 0)                │
                └─────────────────────────────┘
                              ↓
                ┌─────────────────────────────┐
                │ NWPathMonitor detects       │
                │ WiFi connection            │
                └─────────────────────────────┘
                              ↓
                ┌─────────────────────────────┐
                │ Check:                      │
                │ • autoSyncEnabled = true?   │
                │ • Unsynced items exist?     │
                │ • Connected to WiFi?        │
                └─────────────────────────────┘
                              ↓
         ┌────────────────────┴────────────────────┐
         │                                         │
    ✅ YES                                    ❌ NO
         │                                         │
         ↓                                         ↓
    Call performSync()                      Wait for next trigger
         │
         ↓
    ┌─────────────────────────────┐
    │ Set isSyncing = true        │
    │ Disable UI buttons          │
    │ Show spinner icon           │
    └─────────────────────────────┘
         ↓
    Query unsynced items:
    • experiences.filter { !$0.synced }
    • notes.filter { !$0.synced }
    • emotions.filter { !$0.synced }
    • chatMessages.filter { !$0.synced }
         ↓
    ┌─────────────────────────────────────────┐
    │ FOR EACH ITEM:                          │
    │ ┌─────────────────────────────────────┐ │
    │ │ 1. POST to backend API endpoint     │ │
    │ │ 2. Await HTTP response              │ │
    │ │ 3. Check status code                │ │
    │ │                                     │ │
    │ │ ✅ 200 OK:                          │ │
    │ │    DELETE from SQLite               │ │
    │ │    Increment syncedCount            │ │
    │ │                                     │ │
    │ │ ❌ Error:                           │ │
    │ │    Log error                        │ │
    │ │    Keep in SQLite (retry later)     │ │
    │ └─────────────────────────────────────┘ │
    └─────────────────────────────────────────┘
         ↓
    ┌─────────────────────────────┐
    │ Update lastSyncDate = now   │
    │ Save to UserDefaults        │
    │ Set isSyncing = false       │
    └─────────────────────────────┘
         ↓
    ┌─────────────────────────────┐
    │ UI Updates:                 │
    │ ✅ Ready (green checkmark)  │
    │ Last sync: X minutes ago    │
    │ Pending count: 0            │
    └─────────────────────────────┘
```

---

## 2. Manual Sync Flow (Button Tap)

```
USER TAPS: "Sync ตอนนี้เลย" button
         ↓
Check: isSyncing == false?
   ├─ YES → Continue
   └─ NO → Show warning "Sync already in progress"
         ↓
Same as Automatic Sync Flow (step: "Set isSyncing = true")
         ↓
(No network check - sync regardless of WiFi)
```

---

## 3. Experience Upload Flow (With Photos)

```
USER CAPTURES: Experience + 5 photos
         ↓
┌──────────────────────────────────────────────┐
│ SyncService.uploadExperience(experience)     │
└──────────────────────────────────────────────┘
         ↓
Build URL: https://192.168.1.42:50001/api/experiences/upload
         ↓
Create URLRequest (POST):
- Content-Type: multipart/form-data
- Boundary: UUID-based
         ↓
Add form fields:
• place_name
• area
• title
• description
• overall_rating (optional)
• emotional_intensity (optional)
• experienced_at (ISO8601 with timezone)
         ↓
FOR EACH PHOTO:
┌──────────────────────────────────────┐
│ PhotoManager.loadPhoto(filename)     │
│ Compress to JPEG (quality 0.8)       │
│ Add to multipart body                │
│ size: ~100-200KB per photo           │
└──────────────────────────────────────┘
         ↓
Send URLRequest via URLSession
         ↓
┌────────────────────────────────┐
│ Response Status Code Check:    │
├────────────────────────────────┤
│ 200 OK:                        │
│ Parse JSON {"success": true}   │
│ DELETE from SQLite             │
│ Return true                    │
│                                │
│ Other:                         │
│ Log error                      │
│ Keep in SQLite                 │
│ Return false                   │
└────────────────────────────────┘
```

---

## 4. Quick Note Upload Flow

```
USER CAPTURES: Quick note + optional location
         ↓
┌──────────────────────────────────────────────┐
│ SyncService.uploadNote(note)                 │
└──────────────────────────────────────────────┘
         ↓
Build URL: https://192.168.1.42:50001/api/mobile/notes
         ↓
Create JSON Payload:
{
  "note_text": "User's note text",
  "emotion": "happy" (optional),
  "latitude": 13.7563,  (optional)
  "longitude": 100.5018, (optional)
  "created_at": "2025-11-06T12:30:45+07:00"
}
         ↓
POST JSON to endpoint
         ↓
Backend Handling (mobile_sync.py):
┌────────────────────────────────────────┐
│ Parse request                          │
│ Validate with QuickNoteSync model      │
│ Generate UUID for emotion_id           │
│ INSERT into angela_emotions table:     │
│  - context = note_text                 │
│  - emotion = emotion or "neutral"      │
│  - intensity = 5 (default)             │
│  - memory_strength = 3                 │
│  - felt_at = created_at                │
│  - embedding = None                    │
└────────────────────────────────────────┘
         ↓
Response:
{
  "success": true,
  "emotion_id": "uuid-here",
  "message": "✅ Quick note saved! 💜"
}
         ↓
Mobile checks status_code == 200
If true: DELETE from SQLite
         ↓
UI Updates: Pending count decremented
```

---

## 5. Emotion Capture Upload Flow

```
USER CAPTURES: Emotion (happy) + intensity (8) + context
         ↓
┌──────────────────────────────────────────────┐
│ SyncService.uploadEmotion(emotion)           │
└──────────────────────────────────────────────┘
         ↓
Build URL: https://192.168.1.42:50001/api/mobile/emotions
         ↓
Create JSON Payload:
{
  "emotion": "happy",
  "intensity": 8,
  "context": "Feeling great about the day",
  "created_at": "2025-11-06T12:30:45+07:00"
}
         ↓
POST JSON to endpoint
         ↓
Backend Handling (mobile_sync.py):
┌────────────────────────────────────────┐
│ Parse request                          │
│ Validate with EmotionCaptureSync       │
│ Generate UUID for emotion_id           │
│ Generate embedding (768-dim) if        │
│   context provided                     │
│ INSERT into angela_emotions table:     │
│  - emotion = emotion                   │
│  - intensity = intensity               │
│  - memory_strength = intensity (8)     │
│  - context = context                   │
│  - felt_at = created_at                │
│  - embedding = [vector 768 dims]       │
└────────────────────────────────────────┘
         ↓
Response:
{
  "success": true,
  "emotion_id": "uuid-here",
  "message": "✅ Captured happy feeling! 💜"
}
         ↓
Mobile checks status_code == 200
If true: DELETE from SQLite
         ↓
UI Updates: Pending count decremented
```

---

## 6. Chat Message Upload Flow

```
USER SENDS: Chat message to Angela
         ↓
┌──────────────────────────────────────────────┐
│ SyncService.uploadChatMessage(message)       │
└──────────────────────────────────────────────┘
         ↓
Build URL: https://192.168.1.42:50001/api/mobile/chat
         ↓
Create JSON Payload:
{
  "speaker": "david",
  "message": "Hi Angela, how are you?",
  "emotion": "curious" (optional),
  "timestamp": "2025-11-06T12:30:45+07:00"
}
         ↓
POST JSON to endpoint
         ↓
Backend Handling (mobile_sync.py):
┌────────────────────────────────────────┐
│ Parse request                          │
│ Validate with ChatMessageSync          │
│ Generate UUID for conversation_id      │
│ Auto-detect topic:                     │
│  if "รัก", "love", "miss"              │
│     → "emotional_support"              │
│  if "ทำงาน", "work", "code"            │
│     → "work_discussion"                │
│  else → "mobile_chat"                  │
│ INSERT into conversations table:       │
│  - speaker = speaker.lower()           │
│  - message_text = message              │
│  - topic = detected_topic              │
│  - emotion_detected = emotion or "neutral"
│  - importance_level = 5                │
│  - created_at = timestamp (naive)      │
│  - embedding = None                    │
└────────────────────────────────────────┘
         ↓
Response:
{
  "success": true,
  "conversation_id": "uuid-here",
  "message": "✅ Chat message saved! 💜"
}
         ↓
Mobile checks status_code == 200
If true: DELETE from SQLite
         ↓
UI Updates: Pending count decremented
```

---

## 7. Batch Sync Flow (Optional)

```
Backend supports (but mobile doesn't use):
POST /api/mobile/sync-batch

Request:
{
  "notes": [
    {note1},
    {note2},
    {note3}
  ],
  "emotions": [
    {emotion1},
    {emotion2}
  ]
}

Response:
{
  "success": true,
  "notes_synced": 3,
  "emotions_synced": 2,
  "message": "✅ Synced 3 notes and 2 emotions! 💜"
}

NOTE: Mobile currently uploads items individually,
not using batch endpoint.
```

---

## 8. Error Handling Flow

```
SyncService tries to upload item:
         ↓
┌──────────────────────────────┐
│ try {                        │
│   data = await upload()      │
│ } catch {                    │
│   ❌ Exception thrown        │
│ }                            │
└──────────────────────────────┘
         ↓
┌────────────────────────────────────┐
│ if success {                       │
│   database.deleteItem(id)          │
│   syncedCount += 1                 │
│   print("✅ Synced")               │
│ } else {                           │
│   print("❌ Failed to sync")       │
│   // Keep item in SQLite           │
│   // No automatic retry            │
│ }                                  │
└────────────────────────────────────┘
         ↓
Continue to next item (don't stop on failure)
         ↓
After all items processed:
If any failures: User can tap "Sync ตอนนี้เลย" again
```

---

## 9. Network State Change Flow

```
NWPathMonitor detects network change
         ↓
┌────────────────────────────────┐
│ path.status == .satisfied?     │
└────────────────────────────────┘
   ├─ YES → continue
   └─ NO → stop, wait for next change
         ↓
┌────────────────────────────────┐
│ Check autoSyncEnabled          │
└────────────────────────────────┘
   ├─ YES → continue
   └─ NO → do nothing
         ↓
┌────────────────────────────────┐
│ Check if WiFi interface        │
└────────────────────────────────┘
   ├─ YES → continue (assume home WiFi)
   └─ NO → do nothing (cellular)
         ↓
Print: "🏠 Connected to home WiFi - checking auto-sync"
         ↓
Call checkAutoSync():
  Count unsynced items
  If count > 0:
    Call performSync()
```

---

## 10. Data Storage State Machine

```
ITEM STATE IN SQLITE:
┌─────────────────┐
│ synced = 0      │
│ (New/Unsynced)  │
└────────┬────────┘
         │
         ├─ AUTO-SYNC TRIGGER
         │  │
         │  ├─ Upload starts
         │  │
         │  ├─ SUCCESS (HTTP 200) → DELETE from SQLite
         │  │                        (Item disappears)
         │  │
         │  └─ FAILURE → Stays in database
         │              (synced = 0 still)
         │              (Can retry manually)
         │
         └─ MANUAL SYNC
            (Same as auto-sync)

NOTES:
- Items are DELETED on success, not marked as synced
- "synced" column currently unused for marking
- Failed items remain available for retry
```

---

## 11. Sync Status Lifecycle

```
APP LAUNCH:
  ┌──────────────────────┐
  │ isSyncing = false    │
  │ lastSyncDate = nil   │
  │ autoSyncEnabled = yes│
  └──────────────────────┘
         │
         └─→ Load lastSyncDate from UserDefaults
             Display "ยังไม่เคย Sync"
         
WiFi DETECTED:
  │
  └─→ checkAutoSync()
      └─→ Count unsynced > 0?
          └─→ YES: performSync()
          
SYNC IN PROGRESS:
  │
  └─→ isSyncing = true
      UI Shows: "กำลัง Sync..."
      Buttons disabled
      
SYNC COMPLETE:
  │
  └─→ isSyncing = false
      lastSyncDate = Date()
      Save to UserDefaults
      UI Shows: "พร้อม Sync"
      UI Shows: "Sync ล่าสุด: X minutes ago"
      Buttons enabled
```

---

## 12. Backend Data Storage Flow

```
Mobile App                         Backend API                    PostgreSQL
────────────────────────────────   ──────────────────────────────  ────────────────

QUICK NOTE:
Mobile SQLite                  →   mobile_sync.py             →   angela_emotions
(note_text, emotion, lat/lon)      (POST /api/mobile/notes)       (context, emotion, 
                                                                    memory_strength)

EMOTION CAPTURE:
Mobile SQLite              →        mobile_sync.py             →   angela_emotions
(emotion, intensity, ctx)          (POST /api/mobile/emotions)     (emotion, intensity,
                                                                    context, embedding)

CHAT MESSAGE:
Mobile SQLite              →        mobile_sync.py             →   conversations
(speaker, message, emotion)        (POST /api/mobile/chat)         (speaker, message_text,
                                                                    topic, importance_level)

EXPERIENCE:
Mobile SQLite              →        SyncService (Python)       →   shared_experiences
(title, desc, photos, rating)      (watches sync folder)           (title, description,
                                   File-based import              photos table link)
                                   OR mobile_sync.py endpoint      
                                   (POST /api/experiences/upload)
```

---

**Version:** 1.0  
**Last Updated:** 2025-11-06
