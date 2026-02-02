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
│   │   │   ├── MeetingNotesView.swift    # MeetingCard, ActionItemRow, ActionItemsSection
│   │   │   └── MeetingFormComponents.swift # Shared form components
│   │   ├── ThingsOverview/           # Things page (calendar, meetings, action items)
│   │   │   ├── ThingsOverviewView.swift   # Main view + ViewModel + Open Action Items card
│   │   │   ├── EditMeetingSheet.swift     # Edit meeting sheet
│   │   │   └── EditActionItemSheet.swift  # Edit action item sheet (CRUD)
│   │   ├── DJAngela/                 # DJ Angela music system
│   │   │   └── SongQueueView.swift
│   │   └── ContentView.swift         # Tab navigation (root view)
│   ├── Services/
│   │   ├── DatabaseService.swift     # REST API client (all endpoints)
│   │   ├── ChatService.swift         # Chat with Angela
│   │   └── MusicPlayerService.swift  # Apple Music integration
│   └── Theme/
│       └── AngelaTheme.swift         # Colors, fonts, spacing, card styling
├── routers/
│   └── meetings.py                   # FastAPI meeting + action item endpoints
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
| `Views/MeetingNotes/MeetingNotesView.swift` | MeetingCard (expandable), ActionItemRow, ActionItemsSection (inline add/edit/toggle/delete) |
| `Views/ThingsOverview/ThingsOverviewView.swift` | Things page: calendar, stats, Open Action Items card, upcoming/completed meetings |
| `Views/ThingsOverview/EditActionItemSheet.swift` | Edit action item sheet (priority, assignee, due date, status) |
| `Views/ThingsOverview/EditMeetingSheet.swift` | Edit meeting sheet |
| `Views/DJAngela/SongQueueView.swift` | DJ Angela music queue |
| `Services/DatabaseService.swift` | REST API client — all GET/POST/PUT/DELETE methods |
| `Services/ChatService.swift` | Chat with Angela via API |
| `Services/MusicPlayerService.swift` | Apple Music playback |
| `Theme/AngelaTheme.swift` | Theme colors, fonts, spacing |
| `routers/meetings.py` | Backend: meeting + action item API endpoints |
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
- **Base URL:** `http://127.0.0.1:8400`
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
lsof -ti:8400 | xargs kill -9 2>/dev/null

# Start fresh
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI
nohup python3 AngelaBrainDashboard/api_server.py > /tmp/angela_dashboard_backend.log 2>&1 &
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
