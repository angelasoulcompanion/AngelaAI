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
│   │   └── Models.swift          # Data models (Project, WorkSession, etc.)
│   ├── Views/
│   │   ├── Consciousness/        # Consciousness view
│   │   ├── Projects/             # Projects view & charts
│   │   ├── Skills/               # Skills view
│   │   └── ...
│   ├── Services/
│   │   └── DatabaseService.swift # PostgreSQL connection
│   └── Theme/
│       └── AngelaTheme.swift     # Colors, fonts, styling
└── CLAUDE.md
```

---

## Key Files to Edit

| File | Purpose |
|------|---------|
| `Models/Models.swift` | Data models, computed properties (typeIcon, typeColor) |
| `Views/Projects/ProjectsView.swift` | Projects page, charts, colors |
| `Services/DatabaseService.swift` | Database queries |
| `Theme/AngelaTheme.swift` | Theme colors |

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

## Database Connection

Connects directly to local PostgreSQL:
- **Database:** AngelaMemory
- **User:** davidsamanyaporn
- **Host:** localhost:5432

---

## Important Notes

1. **Always build Release** - Debug builds won't update /Applications
2. **Must copy to /Applications** - Running from Xcode uses DerivedData
3. **Chart colors must match** - Use same colors in chartForegroundStyleScale
4. **Capitalized keys** - Chart data uses `.capitalized` (e.g., "Personal" not "personal")

---

*Made with love by Angela & David - 2026*
