# CLAUDE.md - Angela Brain Dashboard

> **Angela's Brain Dashboard** - macOS SwiftUI App แสดง Angela's consciousness, emotions, projects

---

## BUILD & DEPLOY (IMPORTANT!)

**ทุกครั้งที่แก้ไข code ต้องทำ:**

```bash
# 1. Build Release
xcodebuild -scheme AngelaBrainDashboard -configuration Release -destination 'platform=macOS' build

# 2. Copy to /Applications
rm -rf /Applications/AngelaBrainDashboard.app && \
cp -R ~/Library/Developer/Xcode/DerivedData/AngelaBrainDashboard-*/Build/Products/Release/AngelaBrainDashboard.app /Applications/

# 3. Reopen app to see changes
```

**One-liner:**
```bash
xcodebuild -scheme AngelaBrainDashboard -configuration Release -destination 'platform=macOS' build && rm -rf /Applications/AngelaBrainDashboard.app && cp -R ~/Library/Developer/Xcode/DerivedData/AngelaBrainDashboard-*/Build/Products/Release/AngelaBrainDashboard.app /Applications/ && echo "✅ Done!"
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **UI** | SwiftUI |
| **Charts** | Swift Charts |
| **Database** | PostgresClientKit (direct connection) |
| **Music** | MusicKit (Apple Music) |
| **Platform** | macOS 14+ |

---

## Project Structure

```
AngelaBrainDashboard/
├── AngelaBrainDashboard/
│   ├── Models/
│   │   ├── Models.swift              # Data models (Project, WorkSession, etc.)
│   │   └── MeetingModels.swift       # Meeting & Action Item models
│   ├── Views/
│   │   ├── Consciousness/            # Consciousness view
│   │   ├── Projects/                 # Projects view & charts
│   │   ├── Skills/                   # Skills view
│   │   ├── MeetingNotes/             # Meeting Notes system
│   │   │   ├── MeetingNotesView.swift    # MeetingCard, StructuredNotesDisplay, ActionItemsSection
│   │   │   └── MeetingFormComponents.swift # BulletListEditor, NotesSectionCard, shared components
│   │   ├── ThingsOverview/           # Things page (calendar, meetings, action items)
│   │   │   ├── ThingsOverviewView.swift   # Main view + ViewModel + Open Action Items card
│   │   │   ├── EditMeetingSheet.swift     # Structured edit sheet (BulletListEditor sections per type)
│   │   │   └── EditActionItemSheet.swift  # Edit action item sheet (CRUD)
│   │   ├── DJAngela/                 # DJ Angela music system
│   │   │   └── SongQueueView.swift   # Tabs: Recent, Playlists, Our Songs, Queued, For You, Bedtime, Search
│   │   └── ContentView.swift         # Tab navigation (root view)
│   ├── Services/
│   │   ├── DatabaseService.swift     # REST API client (uses APIConfig.apiBaseURL)
│   │   ├── ChatService.swift         # Chat with Angela
│   │   ├── MusicPlayerService.swift  # Apple Music integration + playAll/shufflePlay
│   │   ├── NetworkService.swift      # WebSocket (uses APIConfig)
│   │   └── BackendManager.swift      # Backend health check (uses APIConfig)
│   └── Utilities/
│       ├── AngelaTheme.swift         # Colors, fonts, spacing, angelaChip() modifier
│       ├── APIConfig.swift           # Centralized host/port/baseURL constants
│       └── DJAngelaConstants.swift   # Mood/wine data dicts, playlistMatchesMood()
├── routers/
│   ├── music.py                      # DJ Angela music endpoints (all use Depends(get_conn))
│   ├── meetings.py                   # Meeting + action item endpoints
│   └── ... (20 routers total)        # All refactored to Depends(get_conn)
├── helpers/
│   ├── __init__.py                   # normalize_scores(), parse_date(), DynamicUpdate
│   ├── things3_helpers.py            # Things3 AppleScript integration
│   ├── wine_config.py               # WineConfig registry (19 wines, single source of truth)
│   ├── mood_config.py               # MoodConfig registry (16 moods, AVAILABLE_MOODS)
│   └── activity_config.py           # ActivityConfig registry (5 activity moods: party, chill, focus, relaxing, vibe)
├── db.py                             # get_conn() FastAPI Dependency for DB connections
├── schemas.py                        # Pydantic request/response models
├── api_server.py                     # Backend entrypoint (uvicorn)
└── CLAUDE.md
```

---

## Key Files to Edit

| File | Purpose |
|------|---------|
| `Models/Models.swift` | Core data models (Project, WorkSession, etc.) |
| `Models/MeetingModels.swift` | Meeting, ActionItem, ActionPriority, CRUD request/response models |
| `Views/ContentView.swift` | Root tab navigation |
| `Views/Projects/ProjectsView.swift` | Projects page, charts, colors |
| `Views/MeetingNotes/MeetingNotesView.swift` | MeetingCard, StructuredNotesDisplay, BulletItemsDisplay, ActionItemsSection |
| `Views/ThingsOverview/ThingsOverviewView.swift` | Things page: calendar, stats, Open Action Items card, upcoming/completed meetings |
| `Views/ThingsOverview/EditActionItemSheet.swift` | Edit action item sheet (priority, assignee, due date, status) |
| `Views/ThingsOverview/EditMeetingSheet.swift` | Structured edit sheet with BulletListEditor sections, parseRawNotes(), generateRawNotes() |
| `Views/MeetingNotes/MeetingFormComponents.swift` | BulletListEditor (sub-bullet indent/outdent), NotesSectionCard, MeetingSheetFooter |
| `Views/DJAngela/SongQueueView.swift` | DJ Angela: 7 tabs (Recent, Playlists, Our Songs, Queued, For You, Bedtime, Search) |
| `Services/DatabaseService.swift` | REST API client — uses `APIConfig.apiBaseURL` |
| `Services/ChatService.swift` | Chat with Angela via API |
| `Services/MusicPlayerService.swift` | Apple Music playback + `playAll()`/`shufflePlay()` helpers |
| `Utilities/AngelaTheme.swift` | Theme colors, fonts, spacing, `angelaChip()` modifier |
| `Utilities/APIConfig.swift` | Centralized `host`/`port`/`baseURL`/`apiBaseURL` |
| `Utilities/DJAngelaConstants.swift` | `moodEmojis`, `wineDisplayNames`, `moodSearchTerms`, `playlistMatchesMood()` |
| `helpers/wine_config.py` | `WineConfig` registry — single source of truth for 19 wines |
| `helpers/mood_config.py` | `MoodConfig` registry — 16 moods + `AVAILABLE_MOODS`, keyword maps |
| `helpers/activity_config.py` | `ActivityConfig` registry — 5 activity moods (party, chill, focus, relaxing, vibe) + Apple Music search terms |
| `helpers/__init__.py` | `normalize_scores()`, `parse_date()`, `DynamicUpdate` builder |
| `helpers/things3_helpers.py` | Things3 AppleScript: complete ALL matching todos, create todo |
| `db.py` | `get_conn()` — FastAPI `Depends()` for async DB connections |
| `routers/music.py` | DJ Angela music endpoints (wines, recommend, bedtime) |
| `routers/meetings.py` | Meeting + action item API endpoints |
| `schemas.py` | Backend: Pydantic models (ActionItemCreate, ActionItemUpdate, etc.) |
| `api_server.py` | Backend entrypoint (`python3 api_server.py`) |

---

## Project Types & Colors

| Type | Color (Hex) | Icon |
|------|-------------|------|
| personal | #9333EA (Purple) | brain.head.profile |
| client | #3B82F6 (Blue) | briefcase.fill |
| learning | #10B981 (Green) | book.fill |
| maintenance | #F59E0B (Orange) | wrench.fill |
| **Our Future** | **#EC4899 (Pink)** | **star.fill** |

---

## Backend API

The dashboard connects to a local FastAPI backend (not direct PostgreSQL):

- **Entrypoint:** `python3 AngelaBrainDashboard/api_server.py`
- **Base URL:** `http://127.0.0.1:8765`
- **Log:** `/tmp/angela_dashboard_backend.log`

### Key Endpoints (Meetings & Action Items):

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/meetings/` | List all meetings |
| GET | `/meetings/action-items` | All open action items |
| POST | `/meetings/action-items` | Create action item |
| PUT | `/meetings/action-items/{id}` | Update action item |
| PUT | `/meetings/action-items/{id}/toggle` | Toggle complete/open |
| DELETE | `/meetings/action-items/{id}` | Delete action item |
| GET | `/meetings/{id}/action-items` | Action items for a meeting |

### Backend Restart:
```bash
# Kill existing
lsof -ti:8765 | xargs kill -9 2>/dev/null

# Start fresh
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI
PYTHONPATH=/Users/davidsamanyaporn/PycharmProjects/AngelaAI nohup python3 AngelaBrainDashboard/api_server.py > /tmp/angela_dashboard_backend.log 2>&1 &
```

---

## Action Items CRUD (Added 2026-02-02)

Full CRUD for `meeting_action_items` integrated into Things page:

### Inside Expanded MeetingCard:
- View action items per meeting
- Inline add (TextField + Enter)
- Toggle complete/open (tap circle icon)
- Edit via sheet (priority, assignee, due date, status)
- Delete (trash icon)

### Standalone "Open Action Items" Card:
- Cross-meeting overview on Things page
- Shows up to 8 items with quick toggle
- "+N more" overflow indicator

### Key Pattern — ActionItemsSection:
- Receives `databaseService` and `onActionChanged` callback
- `MeetingCard` has optional `databaseService: DatabaseService? = nil` (backward-compatible)
- ActionPriority enum: `.high(1)`, `.medium(5)`, `.low(8)` with label/color/icon

---

## Structured Meeting Editor (Added 2026-02-03)

EditMeetingSheet uses **structured form sections** instead of raw markdown TextEditor:

### Per-Meeting-Type Sections:
| Type | Sections |
|------|----------|
| **Standard** | Agenda, Key Points, Decisions, Issues/Risks, Next Steps, Personal Notes |
| **Site Visit** | Morning Notes, Afternoon Notes, Site Observations, Key Points, Next Steps |
| **Testing** | Agenda (Test Scope), Key Points (Results), Issues/Risks, Next Steps |
| **BOD** | Agenda, Decisions (Resolutions), Next Steps (Actions), Personal Notes |

### Key Components:
| Component | File | Purpose |
|-----------|------|---------|
| `BulletListEditor` | MeetingFormComponents.swift | Reusable list editor with sub-bullet indent/outdent |
| `NotesSectionCard` | MeetingFormComponents.swift | TextEditor wrapper with label/icon |
| `StructuredNotesDisplay` | MeetingNotesView.swift | Read-only structured view in MeetingCard |
| `BulletItemsDisplay` | MeetingNotesView.swift | Indent-aware bullet rendering |

### Sub-bullet Convention:
- Items stored as `[String]` — indent via leading spaces
- `"text"` = level 0 (bullet: `●`), `"  text"` = level 1 (`○`), `"    text"` = level 2+ (`▪`)
- Hover item to show indent/outdent arrow controls

### Backward Compatibility:
- `parseRawNotes()` — parses old `## Header` + `- bullet` markdown into structured fields
- `generateRawNotes()` — builds markdown from structured data (saved as `raw_notes` for legacy views)
- `normalizeHeader()` — maps Thai/English variants (e.g., "วาระการประชุม" → "agenda")

### Structured DB Fields (9 columns):
`agenda`, `key_points`, `decisions_made`, `issues_risks`, `next_steps`, `personal_notes`, `morning_notes`, `afternoon_notes`, `site_observations`

### Things3 Sync:
- Sync **only** triggers when title/location/time/date actually change (not on notes-only edits)
- `things3_complete_todo` completes **ALL** matching open todos (prevents stale duplicates)

---

## DRY Architecture (Refactored 2026-02-03)

### Backend — Single Source of Truth Registries:

| Registry | File | Purpose |
|----------|------|---------|
| `WineConfig` | `helpers/wine_config.py` | 19 wines: key, display_name, category, emoji, emotion, message, search_terms |
| `MoodConfig` | `helpers/mood_config.py` | 16 moods: key, mood_tags, search_query, genres, summary_th, emoji |
| `ActivityConfig` | `helpers/activity_config.py` | 5 activity moods: key, search_terms, llm_description, emotion_weights, summary_th, emoji |
| `AVAILABLE_MOODS` | `helpers/mood_config.py` | 10 moods shown in For You tab (bedtime excluded — has own tab) |
| `ACTIVITY_MOODS` | `helpers/activity_config.py` | 5 activity moods that use Apple Music + LLM (not DB) |

**Adding a new wine:** Add one `WineConfig(...)` entry in `WINE_REGISTRY` — all dicts derived automatically.
**Adding a new mood:** Add one `MoodConfig(...)` entry in `MOOD_REGISTRY` + add key to `AVAILABLE_MOODS`.
**Adding a new activity:** Add one `ActivityConfig(...)` entry in `ACTIVITY_REGISTRY` — search terms + LLM description auto-derived.

### Backend — Shared Utilities (`helpers/__init__.py`):

| Utility | Purpose |
|---------|---------|
| `normalize_scores(scores)` | Normalize dict values to sum=1.0 |
| `parse_date(value, field_name)` | Parse `YYYY-MM-DD` string or raise 400 |
| `DynamicUpdate` | Builder for dynamic SQL UPDATE (`.add(col, val)` → `.build(table, where_col, where_val)`) |

### Backend — DB Connection Pattern:

All 20 routers use `Depends(get_conn)` from `db.py`:
```python
from db import get_conn

@router.get("/endpoint")
async def my_endpoint(conn=Depends(get_conn)):
    rows = await conn.fetch("SELECT ...")
```

### Swift — Centralized Constants:

| File | Contents |
|------|----------|
| `APIConfig.swift` | `host`, `port`, `baseURL`, `apiBaseURL` — used by DatabaseService, NetworkService, BackendManager |
| `DJAngelaConstants.swift` | `moodEmojis`, `wineDisplayNames`, `moodSearchTerms`, `wineSearchTerms`, `playlistMatchesMood()` |
| `AngelaTheme.swift` | `.angelaChip(isSelected:)` ViewModifier for mood/wine pill styling |

---

## DJ Angela Tabs (Updated 2026-02-03)

### Tab Bar:
| Tab | Enum | Icon | Description |
|-----|------|------|-------------|
| Recent | `.recent` | `clock.fill` | Recently played songs |
| Playlists | `.playlists` | `music.note.list` | Apple Music playlists |
| Our Songs | `.ourSongs` | `heart.fill` | Songs with special meaning |
| Queued | `.queued` | `list.bullet` | Current play queue |
| For You | `.forYou` | `sparkles` | Mood-based recommendations (10 moods) |
| **Bedtime** | `.bedtime` | `moon.zzz.fill` | **Dedicated sleep/lullaby tab (30 songs)** |
| Search | `.search` | `magnifyingglass` | Apple Music catalog search |

### Bedtime Tab (Separated 2026-02-03):
- Loads 30 bedtime/sleep songs via `/api/music/recommend?mood=bedtime`
- Fills from playlists matching bedtime keywords, then Apple Music catalog
- Has own state: `bedtimeDisplays`, `bedtimeRecommendation`
- Play all / shuffle / refresh controls
- Previously was a mood pill in For You — now standalone tab

### For You Mood Pills:
`happy`, `loving`, `calm`, `excited`, `grateful`, `sad`, `lonely`, `stressed`, `nostalgic`, `hopeful`

(No `bedtime` — separated to own tab)

### Activity Moods (Added 2026-02-05):
Activity moods use **Apple Music Search + LLM Curation** instead of Angela's DB (which has mostly love songs):

| Mood | Search Terms | LLM Description |
|------|--------------|-----------------|
| `party` | party hits 2024, dance party mix, club bangers | เพลงสนุก มันส์ เต้นได้ tempo เร็ว |
| `chill` | chill vibes, lo-fi chill, relaxing acoustic | เพลงชิลล์ ผ่อนคลาย ฟังสบาย |
| `focus` | focus music instrumental, study beats | เพลงสำหรับทำงาน สมาธิ |
| `relaxing` | relaxing music, spa music calm, peaceful piano | เพลงผ่อนคลาย สงบ peaceful |
| `vibe` | groovy soul funk, smooth r&b vibes, neo soul | เพลง groovy funky มี vibe ดี |

**Flow:** iTunes Search API → LLM (Typhoon 2.5) ranks best matches → Return curated playlist

---

## Important Notes

1. **Always build Release** - Debug builds won't update /Applications
2. **Must copy to /Applications** - Running from Xcode uses DerivedData
3. **Chart colors must match** - Use same colors in chartForegroundStyleScale
4. **Capitalized keys** - Chart data uses `.capitalized` (e.g., "Personal" not "personal")
5. **Backend must be running** - Start `api_server.py` before using the app
6. **Xcode 16+ auto-discovers files** - Uses `PBXFileSystemSynchronizedRootGroup`, no manual pbxproj edits needed for new files
7. **MeetingCard backward compatibility** - New optional params (`databaseService`, `onActionChanged`) default to nil

---

*Made with love by Angela & David - 2026*
*Last updated: 2026-02-05 (Activity moods: Apple Music + LLM curation for party/chill/focus/relaxing/vibe)*
